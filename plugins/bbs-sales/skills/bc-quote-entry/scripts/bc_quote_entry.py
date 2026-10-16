#!/usr/bin/env python3
"""bc_quote_entry.py - create a Business Central sales quote (header and lines) from a reviewed
spec, under the rep's own sign-in, with a named approval. The quote half of bc_item_entry.py.

    python3 bc_quote_entry.py whoami
    python3 bc_quote_entry.py check  <spec.json>
    python3 bc_quote_entry.py commit <spec.json> --approve <token> --approved-by "<rep name>"
    python3 bc_quote_entry.py logout [--account <user@blackboxsafety.com> | --all]

`check` reads Business Central and writes nothing. It proves the read path a commit would use
(customers, items, salesQuotes, unitsOfMeasure), validates every field, gates on the customer
(exists, unblocked) and on every line's item (exists, Inventory, unblocked; never created or
patched here), duplicate-checks the external document number across sales quotes, checks that
the lines sum to the total, writes `<spec>.review.md`, and prints the approval token (a hash of
the spec file). `commit` refuses unless the token still matches the spec and --approved-by is
the rep named on it, re-runs every gate, POSTs the header, PATCHes the ship-to with If-Match,
reads the header back and gates on it before a single line is added, POSTs the lines, reads the
whole quote back with $expand=salesQuoteLines and verifies every line and the total, and
appends to `<spec>.bc-log.jsonl`. It never releases, converts, sends or posts anything; a
person releases the quote in BC, which is where tax is calculated.

Connection, sign-in, HTTP, the error table and the token cache are IMPORTED from the sibling
skill's script, plugins/bbs-sales/skills/bc-item-entry/scripts/bc_item_entry.py, so there is
one connection file (bc-item-entry/references/bc-connection.json), one cache and one error
table for both skills. This script carries only the quote rules (references/quote-rules.md).

Stdlib only, except `msal` and `msal-extensions` for delegated sign-in (through the import).
Never prints a secret or an auth token. The approval token it prints is a hash of the spec
file, not a credential.
"""
import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
ITEM_SCRIPTS = os.path.join(os.path.dirname(os.path.dirname(HERE)), "bc-item-entry", "scripts")
if ITEM_SCRIPTS not in sys.path:
    sys.path.insert(0, ITEM_SCRIPTS)
try:
    import bc_item_entry as item  # noqa: E402  the sibling skill, same plugin
except ImportError:
    print(f"\nSTOP at import: this skill reuses bc_item_entry.py from the bc-item-entry skill in the same "
          f"plugin, expected at {ITEM_SCRIPTS}. Both ship in bbs-sales; reinstall the plugin.")
    sys.exit(1)

# Reused as-is from the sibling: die, explain_error, odq, qp, http_fail, norm, is_ascii, money,
# spec_token, cost_source_problem, load_connection/auth (through the BC class), cmd_logout.
die, explain_error, odq, qp, http_fail = item.die, item.explain_error, item.odq, item.qp, item.http_fail
norm, is_ascii, money, spec_token = item.norm, item.is_ascii, item.money, item.spec_token
cost_source_problem = item.cost_source_problem

EXT_DOC_MAX, DESC_MAX = 35, 100
DROPSHIP_ID = "006fd057-c685-ef11-ac23-6045bdecc5e4"   # location DROPSHIP, the customer-card default
# CONTRACT (shortcut dimension 1) values, from BC-WRITE-SOP-RULES.md section 1 (verified against
# General Ledger Setup). Change the SOP, this set and test_bc_quote_entry.py together.
CONTRACT_CODES = frozenset({"OPEN", "NASPO", "NPPGOV", "GSA", "OMNIA", "EMRKT", "ICPT", "UCOP", "BODYARMOR",
                            "BA-CA", "BA-SRCWL", "WWG-SRCWL", "DODIG", "QB LEGACY", "BBSACCOUNTINGONLY"})
SHIP_TO_KEYS = ("shipToName", "shipToContact", "shipToAddressLine1", "shipToAddressLine2", "shipToCity",
                "shipToState", "shipToPostCode", "shipToCountry")
SHIP_TO_REQUIRED = ("shipToName", "shipToAddressLine1", "shipToCity", "shipToState", "shipToPostCode")
TOP_REQUIRED = ("customerNumber", "externalDocumentNumber", "contract", "salesperson", "shipTo", "costSource",
                "pricingBasis", "lines", "quoteTotalExclTax", "preparedBy")
TOP_KNOWN = TOP_REQUIRED + ("zeroMarginOk", "deal", "approvedBy")
LINE_KNOWN = ("line", "number", "description", "qty", "uom", "unitCost", "unitPrice", "zeroMarginOk")
HEADER_READBACK = ("customerNumber", "customerName", "billToName", "shipToName", "shipToContact",
                   "shipToAddressLine1", "shipToAddressLine2", "shipToCity", "shipToState", "shipToPostCode",
                   "shipToCountry", "externalDocumentNumber", "documentDate", "validUntilDate",
                   "shortcutDimension1Code", "shortcutDimension2Code", "salesperson", "paymentTermsId",
                   "shipmentMethodId", "status")
ITEM_MISSING = ("not in Business Central. Nothing is created or patched from here: enter it through "
                "bc-item-entry (vendor, sourced cost, named review), then run check again.")


def num_or_none(v):
    try:
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


# ----------------------------------------------------------------------------- spec
def load_spec(path):
    try:
        with open(path, encoding="utf-8") as fh:
            spec = json.load(fh)
    except Exception as e:
        die("spec", f"cannot read {path}: {e}")
    if not isinstance(spec, dict):
        die("spec", "spec must be a JSON object")
    return spec


def validate_spec(spec, uoms):
    """Pure validation, no BC calls. Returns (header, lines, errors, warnings).

    header: the spec's header values, trimmed. lines: one dict per line with numbers as floats
    and gm (gross margin %) computed. uoms: the unit-of-measure codes BC has; an empty set skips
    that one check (tests), the live check never passes an empty set.
    """
    errs, warns = [], []
    for k in TOP_REQUIRED:
        if k not in spec or spec[k] in (None, "") or (isinstance(spec[k], (list, dict)) and not spec[k]):
            errs.append(f"{k} is required")
    for k in sorted(set(spec) - set(TOP_KNOWN)):
        warns.append(f"top-level field {k!r} is not one the script reads; it is ignored")
    s = lambda k: str(spec.get(k) or "").strip()  # noqa: E731

    cust = s("customerNumber")
    if cust and cust != cust.upper():
        errs.append(f"customerNumber {cust!r} must be upper-case (BC Code field); the lookup is by exact number")
    if cust and not is_ascii(cust):
        errs.append("customerNumber has non-ASCII characters")

    ext = str(spec.get("externalDocumentNumber") or "")
    if ext != ext.strip():
        errs.append("externalDocumentNumber has leading or trailing spaces")
    ext = ext.strip()
    if ext and not (1 <= len(ext) <= EXT_DOC_MAX):
        errs.append(f"externalDocumentNumber is {len(ext)} chars, limit {EXT_DOC_MAX} (BC field length)")
    if ext and not is_ascii(ext):
        errs.append("externalDocumentNumber has non-ASCII characters")

    contract = s("contract")
    if contract and contract not in CONTRACT_CODES:
        errs.append(f"contract {contract!r} is not a CONTRACT code in BC. Known: {', '.join(sorted(CONTRACT_CODES))}. "
                    f"Never invent a code; OPEN is open market")

    sales = s("salesperson")
    if sales and sales != sales.upper():
        errs.append(f"salesperson {sales!r} must be upper-case (BC Code field)")
    if sales and not is_ascii(sales):
        errs.append("salesperson has non-ASCII characters")

    ship = spec.get("shipTo")
    ship_out = {}
    if isinstance(ship, dict) and ship:
        extra = sorted(set(ship) - set(SHIP_TO_KEYS))
        if extra:
            errs.append(f"shipTo carries {extra}; only {list(SHIP_TO_KEYS)} are header fields the API takes")
        for k in SHIP_TO_REQUIRED:
            if not str(ship.get(k) or "").strip():
                errs.append(f"shipTo.{k} is required")
        for k, v in ship.items():
            if k not in SHIP_TO_KEYS:
                continue
            v = "" if v is None else str(v)
            if not is_ascii(v):
                errs.append(f"shipTo.{k} has non-ASCII characters")
            ship_out[k] = v
        st = ship_out.get("shipToState", "")
        if st and not re.fullmatch(r"[A-Z]{2}", st):
            errs.append(f"shipTo.shipToState {st!r} must be the two-letter code")
    elif "shipTo" in spec:
        errs.append("shipTo must be an object with the ship-to fields")

    source = s("costSource")
    if source:
        problem = cost_source_problem(source)
        if problem:
            errs.append(f"costSource {source!r} {problem}. A cost is read from a quote, price list or the Grainger "
                        f"connector, and the source names it with its number or date")
    if not s("pricingBasis"):
        pass  # already in TOP_REQUIRED
    if not is_ascii(s("pricingBasis")) or not is_ascii(source):
        warns.append("costSource or pricingBasis has non-ASCII characters; they print on the sheet only, not in BC")

    spec_zero_ok = bool(spec.get("zeroMarginOk"))
    lines_in = spec.get("lines")
    lines = []
    if isinstance(lines_in, list) and lines_in:
        seen_line, seen_num = set(), set()
        for i, ln in enumerate(lines_in, 1):
            if not isinstance(ln, dict):
                errs.append(f"line entry {i} is not an object"); continue
            tag = f"line entry {i}"
            for k in sorted(set(ln) - set(LINE_KNOWN)):
                warns.append(f"{tag}: field {k!r} is not one the script reads; it is ignored")
            lno = ln.get("line")
            if not isinstance(lno, int) or isinstance(lno, bool) or lno <= 0:
                errs.append(f"{tag}: line must be a positive integer"); lno = None
            elif lno in seen_line:
                errs.append(f"{tag}: line {lno} is duplicated")
            else:
                seen_line.add(lno)
                tag = f"line {lno}"
            num = str(ln.get("number") or "")
            if num != num.strip():
                errs.append(f"{tag}: number has leading or trailing spaces")
            num = num.strip()
            if not num:
                errs.append(f"{tag}: number (the BC item number) is required")
            elif not is_ascii(num):
                errs.append(f"{tag}: number has non-ASCII characters")
            elif num != num.upper():
                errs.append(f"{tag}: item numbers are upper-case in BC (Code field); write it as {num.upper()!r} "
                            f"so the lookup finds the card")
            if num in seen_num:
                warns.append(f"{tag}: item {num} appears on more than one line")
            seen_num.add(num)
            desc = str(ln.get("description") or "")
            if desc != desc.strip():
                errs.append(f"{tag}: description has leading or trailing spaces")
            desc = desc.strip()
            if not desc:
                errs.append(f"{tag}: description is required (1-{DESC_MAX} ASCII characters)")
            if len(desc) > DESC_MAX:
                errs.append(f"{tag}: description is {len(desc)} chars, limit {DESC_MAX}; shorten it deliberately")
            if desc and not is_ascii(desc):
                bad = sorted({c for c in desc if not (32 <= ord(c) < 127)})
                errs.append(f"{tag}: description has non-ASCII characters {bad!r}; use plain hyphens and quotes")
            qty = num_or_none(ln.get("qty"))
            if qty is None or qty <= 0:
                errs.append(f"{tag}: qty must be a number greater than 0")
            uom = str(ln.get("uom") or "").strip().upper()
            if not uom:
                errs.append(f"{tag}: uom is required (EA unless the customer buys a pack, case or box)")
            elif uoms and uom not in uoms:
                errs.append(f"{tag}: uom {uom!r} is not a unit of measure in BC ({', '.join(sorted(uoms))})")
            cost = num_or_none(ln.get("unitCost"))
            price = num_or_none(ln.get("unitPrice"))
            if cost is None or cost <= 0:
                errs.append(f"{tag}: unitCost must be a number greater than 0 (BBS's cost from costSource; it is the "
                            f"basis of the margin gate and is not written to BC)")
            if price is None or price <= 0:
                errs.append(f"{tag}: unitPrice must be a number greater than 0 (SOP: a zero price means nobody priced "
                            f"the line; never a silent zero)")
            elif cost is not None and cost > 0:
                if price < cost - 0.005:
                    errs.append(f"{tag}: unitPrice {money(price)} is below unitCost {money(cost)}")
                elif abs(price - cost) < 0.005 and not (ln.get("zeroMarginOk") or spec_zero_ok):
                    errs.append(f"{tag}: unitPrice equals unitCost (0% margin); set zeroMarginOk: true on the line, or "
                                f"on the spec when every line sells at cost by contract (Grainger on NASPO)")
            gm = None
            if price and cost is not None and price > 0:
                gm = (price - cost) / price * 100
            ext_price = round(qty * price, 2) if qty and price else None
            lines.append({"line": lno, "number": num, "description": desc, "qty": qty, "uom": uom, "unitCost": cost,
                          "unitPrice": price, "extPrice": ext_price, "gm": gm,
                          "atCost": bool(cost and price and abs(price - cost) < 0.005)})
    elif "lines" in spec:
        errs.append("lines must be a non-empty list")

    total = num_or_none(spec.get("quoteTotalExclTax"))
    if total is None:
        errs.append("quoteTotalExclTax must be a number")
    elif lines and all(l["extPrice"] is not None for l in lines):
        s_lines = round(sum(l["extPrice"] for l in lines), 2)
        if abs(s_lines - total) > 0.005:
            errs.append(f"lines sum to {money(s_lines)} but quoteTotalExclTax is {money(total)}; fix one of them")

    header = {"customerNumber": cust, "externalDocumentNumber": ext, "contract": contract, "salesperson": sales,
              "shipTo": ship_out, "costSource": source, "pricingBasis": s("pricingBasis"), "preparedBy": s("preparedBy"),
              "deal": s("deal"), "total": total, "zeroMarginOk": spec_zero_ok}
    return header, lines, errs, warns


# ----------------------------------------------------------------------------- BC reads
class QuoteBC(item.BC):
    """The sibling's connection and sign-in, with the reads a quote commit depends on."""

    def path_probe(self):
        out = []
        for what, url in (("customers (API)", f"{self.api}/customers?" + qp(select="number", top=1)),
                          ("items (API)", f"{self.api}/items?" + qp(select="number", top=1)),
                          ("salesQuotes (API)", f"{self.api}/salesQuotes?" + qp(select="number", top=1)),
                          ("unitsOfMeasure (API)", f"{self.api}/unitsOfMeasure?" + qp(select="code", top=1))):
            st, body = self.get(url)
            ok = st == 200 and isinstance(body, dict) and "value" in body
            detail = "PASS" if ok else f"FAIL HTTP {st}: {json.dumps(body)[:160]}"
            hint = "" if ok else explain_error(json.dumps(body), st)
            out.append((what, ok, detail + (f" ({hint})" if hint else "")))
        return out

    def require_path(self):
        probes = self.path_probe()
        for what, ok, detail in probes:
            print(f"[path] {what}: {detail}")
        if not all(ok for _, ok, _ in probes):
            die("path check", "a read this skill depends on failed, so nothing can be checked or committed. "
                "Fix the access (bc-item-entry/references/rep-setup.md names each failure) and run again.")
        return probes

    def customer(self, number):
        st, body = self.get(f"{self.api}/customers?" + qp(f"number eq '{odq(number)}'"))
        if st != 200:
            http_fail("customer lookup", st, body)
        rows = body.get("value") or []
        return rows[0] if rows else None

    def quotes_with_ext_doc(self, ext):
        st, body = self.get(f"{self.api}/salesQuotes?" + qp(f"externalDocumentNumber eq '{odq(ext)}'",
                                                             select="number,status,customerNumber,documentDate"))
        if st != 200:
            http_fail("quote duplicate check", st, body)
        return body.get("value") or []

    def quote(self, qid, expand_lines=False):
        url = f"{self.api}/salesQuotes({qid})" + ("?$expand=salesQuoteLines" if expand_lines else "")
        st, body = self.get(url)
        if st != 200:
            http_fail("quote read-back", st, body)
        return body


# ----------------------------------------------------------------------------- gates
def customer_gate(bc, header):
    """The customer exists and is not blocked. Returns (record, errors)."""
    cust = bc.customer(header["customerNumber"])
    if not cust:
        return None, [f"customer {header['customerNumber']} does not exist in Business Central. Resolve the number "
                      f"with bc_find_customer; this script never creates a customer"]
    blocked = norm(cust.get("blocked")).strip()
    errs = []
    if blocked:
        errs.append(f"customer {header['customerNumber']} ({cust.get('displayName')}) is blocked: {blocked}")
    print(f"[customer] {header['customerNumber']} = {cust.get('displayName')!r}, {cust.get('addressLine1') or '-'}, "
          f"{cust.get('city') or '-'} {cust.get('state') or ''} {cust.get('postalCode') or ''}; "
          f"terms {str(cust.get('paymentTermsId') or '-')[:8]}, ship {str(cust.get('shipmentMethodId') or '-')[:8]}"
          f"{'  BLOCKED ' + blocked if blocked else ''}")
    return cust, errs


def item_gate(bc, lines):
    """Every line's item exists, is Inventory and unblocked. Read-only: nothing is created or patched.
    Returns (cards by number, errors, notes)."""
    cards, errs, notes = {}, [], []
    for ln in lines:
        num = ln["number"]
        if num in cards:
            continue
        rb = bc.item(num)
        if not rb:
            errs.append(f"item {num} is {ITEM_MISSING}")
            continue
        cards[num] = rb
        typ = norm(rb.get("type"))
        if typ != "Inventory":
            errs.append(f"item {num} ({rb.get('displayName')}) is type {typ}, not Inventory")
        if rb.get("blocked"):
            errs.append(f"item {num} ({rb.get('displayName')}) is blocked")
        card_cost = float(rb.get("unitCost") or 0)
        card_price = float(rb.get("unitPrice") or 0)
        print(f"  {num:20} EXISTS  {str(rb.get('displayName'))[:50]!r}  card cost {money(card_cost):>10}  "
              f"card price {money(card_price):>10}  {typ}{'  BLOCKED' if rb.get('blocked') else ''}")
        if abs(card_cost - ln["unitCost"]) > 0.005:
            notes.append(f"line {ln['line']} {num}: card cost {money(card_cost)} differs from the spec's cost "
                         f"{money(ln['unitCost'])} ({'card is 0' if card_cost == 0 else 'the card is not patched here'}; "
                         f"the rep updates the card in BC if wanted)")
    return cards, errs, notes


def dup_gate(bc, header):
    """No sales quote in BC already carries this external document number."""
    hits = bc.quotes_with_ext_doc(header["externalDocumentNumber"])
    if hits:
        return [f"a sales quote already carries external document number {header['externalDocumentNumber']!r}: "
                + ", ".join(f"{q.get('number')} ({norm(q.get('status'))}, {q.get('customerNumber')}, "
                            f"{q.get('documentDate')})" for q in hits)
                + ". The rep decides: quote it as a revision in BC, or give this spec a new external document number"]
    return []


def header_gate(h, cust, header):
    """Read-back of the header against the spec and the customer card. Pure. Returns [(name, ok)]."""
    ship = header["shipTo"]
    return [(f"customer {header['customerNumber']}", h.get("customerNumber") == header["customerNumber"]),
            ("ship-to " + ", ".join(f"{k[6:]}={v!r}" for k, v in ship.items()),
             all(str(h.get(k) or "") == v for k, v in ship.items())),
            ("payment terms = customer card", h.get("paymentTermsId") == cust.get("paymentTermsId")),
            ("shipment method = customer card", h.get("shipmentMethodId") == cust.get("shipmentMethodId")),
            (f"CONTRACT = {header['contract']}", h.get("shortcutDimension1Code") == header["contract"]),
            (f"salesperson = {header['salesperson']}", h.get("salesperson") == header["salesperson"]),
            (f"ext doc {header['externalDocumentNumber']!r}",
             h.get("externalDocumentNumber") == header["externalDocumentNumber"])]


def verify_lines(doc, lines, total):
    """Read-back of the whole quote against the spec. Pure. Returns ([(name, ok)], mismatched line numbers)."""
    got = {l.get("sequence"): l for l in doc.get("salesQuoteLines") or []}
    mism = []
    for ln in lines:
        l = got.get(ln["line"] * 10000)
        ok = bool(l) and l.get("lineObjectNumber") == ln["number"] \
            and abs(float(l.get("unitPrice") or 0) - ln["unitPrice"]) < 0.005 \
            and abs(float(l.get("quantity") or 0) - ln["qty"]) < 0.0001 \
            and l.get("unitOfMeasureCode") == ln["uom"] and l.get("description") == ln["description"]
        if not ok:
            mism.append(ln["line"])
    bc_sum = round(sum(float(l.get("amountExcludingTax") or 0) for l in got.values()), 2)
    hdr_total = float(doc.get("totalAmountExcludingTax") or 0)
    return [(f"{len(lines)} lines in BC", len(got) == len(lines)),
            (f"every line = spec (item, qty, UoM, price, description); mismatches {mism or 'none'}", not mism),
            (f"lines sum {money(bc_sum)} = spec {money(total)}", abs(bc_sum - total) < 0.005),
            (f"header total {money(hdr_total)} = spec {money(total)}", abs(hdr_total - total) < 0.005)], mism


# ----------------------------------------------------------------------------- review sheet
def review_sheet(bc, header, lines, cust, cards, notes, warns, token, spec_path):
    ship = header["shipTo"]
    ship_text = ", ".join(v for v in (ship.get("shipToName"), ship.get("shipToContact"), ship.get("shipToAddressLine1"),
                                      ship.get("shipToAddressLine2"), f"{ship.get('shipToCity', '')} "
                                      f"{ship.get('shipToState', '')} {ship.get('shipToPostCode', '')}".strip(),
                                      ship.get("shipToCountry")) if v)
    rows = [("Deal", header["deal"] or "-"),
            ("Customer", f"{header['customerNumber']} {cust.get('displayName', '')} ({cust.get('city') or '-'}, "
                         f"{cust.get('state') or '-'})"),
            ("Customer card terms / shipment", f"paymentTermsId {cust.get('paymentTermsId') or '-'} / "
                                               f"shipmentMethodId {cust.get('shipmentMethodId') or '-'} "
                                               f"(inherited; the rep compares with the solicitation)"),
            ("External document no.", header["externalDocumentNumber"]),
            ("CONTRACT (dimension 1)", header["contract"]),
            ("Salesperson", header["salesperson"]),
            ("Ship-to (PATCHed, then gated)", ship_text),
            ("Document date", f"{dt.date.today().isoformat()} (today; validUntilDate is BC's, document date + 60)"),
            ("Lines", f"{len(lines)}, lineType Item, location DROPSHIP, sequence line x 10000"),
            ("Total excl. tax", f"{money(header['total'])} (tax is calculated when a person releases the quote in BC)"),
            ("Cost source", header["costSource"]),
            ("Pricing basis", header["pricingBasis"] + ("  [all lines at cost by design: zeroMarginOk on the spec]"
                                                        if header["zeroMarginOk"] else "")),
            ("Prepared by", header["preparedBy"] or "[MISSING - NEEDS INPUT]"),
            ("Checked", dt.datetime.now().isoformat(timespec="seconds")),
            ("Writes as", bc.mode_text),
            ("Connection", f"{bc.conn['environment']} / {bc.company_display}; values from "
                           + ", ".join(sorted({bc.sources[k] for k in item.CONNECTION_KEYS}))),
            ("Approval token", f"`{token}` (changes if the spec file changes)")]
    out = [f"# Quote entry review - {os.path.basename(spec_path)}", "", "| Field | Value |", "|---|---|"]
    out += [f"| {k} | {str(v).replace('|', '/')} |" for k, v in rows]
    out += ["", "The quote is created as a Draft sales quote in Business Central with the header above and the lines "
                "below. Nothing is written until the rep approves this sheet by name. Nothing here releases, "
                "converts or sends it.", "",
            "| # | Item No. | Description | Qty | UoM | Cost | Price | Ext. price | GM% | Card |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for ln in lines:
        card = cards.get(ln["number"], {})
        card_text = (f"cost {money(float(card.get('unitCost') or 0))}, price {money(float(card.get('unitPrice') or 0))}"
                     if card else "-")
        gm = f"{ln['gm']:.1f}" + (" AT COST" if ln["atCost"] else "") if ln["gm"] is not None else "-"
        qty = f"{ln['qty']:g}"
        out.append(f"| {ln['line']} | {ln['number']} | {ln['description'].replace('|', '/')} | {qty} | {ln['uom']} | "
                   f"{money(ln['unitCost'])} | {money(ln['unitPrice'])} | {money(ln['extPrice'])} | {gm} | {card_text} |")
    out.append(f"| | | **Total excl. tax** | | | | | **{money(header['total'])}** | | |")
    if notes:
        out += ["", "Notes from the item gate (not blocking):"] + [f"- {n}" for n in notes]
    if warns:
        out += ["", "Warnings (not blocking):"] + [f"- {w}" for w in warns]
    if bc.mode == "app-only":
        out += ["", "[FLAG: this run is app-only. The quote will show the service principal as creator, not the "
                    "rep. A rep's own quote runs delegated.]"]
    out += ["", "To commit after the rep has read this sheet:", "",
            f"    python3 bc_quote_entry.py commit \"{spec_path}\" --approve {token} --approved-by \"<rep name>\"", ""]
    return "\n".join(out)


# ----------------------------------------------------------------------------- commands
def run_checks(bc, spec):
    bc.require_path()
    uoms = bc.units_of_measure()
    header, lines, errs, warns = validate_spec(spec, uoms)
    if errs:
        print("\n[pre-flight] FAILED, nothing written:")
        for e in errs:
            print("  -", e)
        sys.exit(1)
    print(f"[pre-flight] header and {len(lines)} lines pass the field rules; lines sum to {money(header['total'])} "
          f"excl. tax; CONTRACT {header['contract']}; salesperson {header['salesperson']}")
    cust, cerrs = customer_gate(bc, header)
    if cerrs:
        print("\n[customer gate] FAILED, nothing written:")
        for e in cerrs:
            print("  -", e)
        sys.exit(1)
    print("[item gate] read-only; every line's item must already exist")
    cards, ierrs, notes = item_gate(bc, lines)
    if ierrs:
        print("\n[item gate] FAILED, nothing written:")
        for e in ierrs:
            print("  -", e)
        sys.exit(1)
    derrs = dup_gate(bc, header)
    if derrs:
        print("\n[duplicate gate] FAILED, nothing written:")
        for e in derrs:
            print("  -", e)
        sys.exit(1)
    print(f"[duplicate gate] no sales quote carries ext doc {header['externalDocumentNumber']!r}")
    return header, lines, cust, cards, notes, warns


def cmd_whoami(args):
    bc = QuoteBC(account=args.account)
    probes = bc.path_probe()
    for what, ok, detail in probes:
        print(f"[path] {what}: {detail}")
    if all(ok for _, ok, _ in probes):
        print(f"[whoami] {bc.mode_text}; company {bc.company_display!r}; the reads a quote commit depends on PASS. "
              f"A read PASS does not prove write rights. Next: run check on a spec.")
    else:
        print("[whoami] a read FAILED above; check and commit will refuse until it passes. "
              "bc-item-entry/references/rep-setup.md says what each failure means.")
        sys.exit(1)


def cmd_check(args):
    spec = load_spec(args.spec)
    bc = QuoteBC(account=args.account)
    header, lines, cust, cards, notes, warns = run_checks(bc, spec)
    token = spec_token(args.spec)
    sheet = review_sheet(bc, header, lines, cust, cards, notes, warns, token, args.spec)
    out = os.path.splitext(args.spec)[0] + ".review.md"
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(sheet)
    print("\n" + sheet)
    print(f"[check] review sheet written to {out}")
    print(f"[check] APPROVAL TOKEN {token}. Show the sheet to the rep. Commit only with their name.")


def approval_gate(args, spec):
    """Token and name, before anything touches BC. Returns the approving rep's name."""
    token = spec_token(args.spec)
    if args.approve != token:
        die("approval", f"token {args.approve!r} does not match the spec on disk ({token}). Run check again, "
            f"have the rep read the new sheet, and commit with the new token.")
    who = (args.approved_by or "").strip()
    if len(who) < 3 or who.lower() in ("rep", "me", "user", "claude", "n/a", "na"):
        die("approval", "--approved-by must be the reviewing rep's real name")
    prepared = str(spec.get("preparedBy") or "").strip()
    if not prepared:
        die("approval", "spec has no preparedBy; the rep whose quote this is must be named on the spec")
    if who.lower() != prepared.lower():
        die("approval", f"--approved-by {who!r} is not the rep named on the spec ({prepared!r}). The person who "
            f"reads the sheet is the person named on it; nobody approves on another rep's behalf")
    return who, token


def cmd_commit(args):
    spec = load_spec(args.spec)
    who, token = approval_gate(args, spec)
    bc = QuoteBC(account=args.account)
    if bc.mode == "app-only":
        if os.environ.get("BBS_BC_AUTH", "").strip().lower() != "app-only":
            die("approval", "commit refuses app-only auth unless BBS_BC_AUTH=app-only is set explicitly")
        print(f"[commit] FLAG: app-only run. The quote will show the service principal as creator, not {who}. "
              f"The log records both.")
    elif not any(part.lower() in bc.user.split("@")[0].lower() for part in who.split() if len(part) > 1):
        print(f"[commit] note: approved by {who}, but the sign-in writing is {bc.user}. The log records both; "
              f"this is acceptable only because {who} is in the chat reading the sheet.")
    header, lines, cust, cards, notes, warns = run_checks(bc, spec)
    log_path = os.path.splitext(args.spec)[0] + ".bc-log.jsonl"
    log = open(log_path, "a", encoding="utf-8")
    state = {"qno": None, "qid": None}

    def record(**kw):
        kw.update({"ts": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                   "spec": os.path.basename(args.spec), "token": token, "approvedBy": who,
                   "auth": bc.mode, "signedInAs": bc.user, "quoteNumber": state["qno"]})
        log.write(json.dumps(kw) + "\n"); log.flush()

    def stop(step, msg, **kw):
        record(event="error", step=step, **kw)
        die(step, msg)

    record(event="commit-start", customerNumber=header["customerNumber"], extDoc=header["externalDocumentNumber"],
           contract=header["contract"], lines=[l["number"] for l in lines], total=header["total"])

    # [B] header
    hdr = {"customerNumber": header["customerNumber"], "documentDate": dt.date.today().isoformat(),
           "externalDocumentNumber": header["externalDocumentNumber"],
           "shortcutDimension1Code": header["contract"], "salesperson": header["salesperson"]}
    print(f"\n[commit] approved by {who}; POST salesQuotes {json.dumps(hdr)}")
    st, body = bc.post(f"{bc.api}/salesQuotes", hdr)
    if st != 201:
        hint = explain_error(json.dumps(body), st)
        stop("header POST", f"HTTP {st}: {json.dumps(body)[:400]}" + (f"\n  {hint}" if hint else "")
             + "\n  Nothing was created.", http=st, body=str(body)[:300])
    state["qid"], state["qno"] = body["id"], body["number"]
    qid, qno = state["qid"], state["qno"]
    record(event="header-created", status=norm(body.get("status")))
    print(f"[commit] BC assigned {qno} (Draft). Setting ship-to.")
    cur = bc.quote(qid)
    st, res = bc.patch(f"{bc.api}/salesQuotes({qid})", cur["@odata.etag"], header["shipTo"])
    if st not in (200, 204):
        stop("ship-to PATCH", f"HTTP {st}: {json.dumps(res)[:400]}\n  {qno} exists as an EMPTY DRAFT with no lines "
             f"and the customer's default ship-to. Delete it in the BC UI. Do not re-run commit: the duplicate gate "
             f"will stop on the external document number until the empty draft is gone.", http=st, body=str(res)[:300])
    h = bc.quote(qid)
    print(f"[commit] HEADER READ-BACK {qno}")
    for k in HEADER_READBACK:
        print(f"      {k:24} = {h.get(k)!r}")
    gate = header_gate(h, cust, header)
    for n, ok in gate:
        print(f"      {'PASS' if ok else 'FAIL'}  {n}")
    record(event="header-gate", passed=all(ok for _, ok in gate), failed=[n for n, ok in gate if not ok])
    if not all(ok for _, ok in gate):
        stop("header gate", f"{qno} exists as an EMPTY DRAFT; no lines were added. Delete it in the BC UI, fix the "
             f"spec or the customer card, and run check again. Do not re-run commit against this spec until the "
             f"empty draft is gone.", failed=[n for n, ok in gate if not ok])

    # [C] lines
    print(f"\n[commit] POST {len(lines)} lines to {qno}")
    landed = []
    for ln in lines:
        line = {"documentId": qid, "sequence": ln["line"] * 10000, "lineType": "Item",
                "lineObjectNumber": ln["number"], "description": ln["description"], "quantity": ln["qty"],
                "unitOfMeasureCode": ln["uom"], "unitPrice": ln["unitPrice"], "locationId": DROPSHIP_ID}
        st, body = bc.post(f"{bc.api}/salesQuoteLines", line)
        if st != 201:
            hint = explain_error(json.dumps(body), st)
            stop(f"line {ln['line']} {ln['number']}", f"HTTP {st}: {json.dumps(body)[:400]}"
                 + (f"\n  {hint}" if hint else "")
                 + f"\n  {qno} is a PARTIAL DRAFT: lines that landed {landed or 'none'}. Finish or delete it in the "
                 f"BC UI; do not re-run commit for it.", http=st, body=str(body)[:300], landed=landed)
        landed.append(ln["line"])
        record(event="line-created", line=ln["line"], number=ln["number"], qty=ln["qty"], uom=ln["uom"],
               unitPrice=ln["unitPrice"], unitCost=ln["unitCost"])
        print(f"  {ln['line'] * 10000:>6}  {ln['number']:20} x{ln['qty']:<6g} @ {money(ln['unitPrice']):>10} "
              f"= {money(ln['extPrice']):>11}  {ln['description']}")

    # [D] read-back
    doc = bc.quote(qid, expand_lines=True)
    checks, mism = verify_lines(doc, lines, header["total"])
    print(f"\n[commit] READ-BACK {qno}")
    for n, ok in checks:
        print(f"      {'PASS' if ok else 'FAIL'}  {n}")
    print(f"      INFO  tax {money(float(doc.get('totalTaxAmount') or 0))} (an unreleased quote carries no tax; "
          f"a person releases in BC)")
    if not all(ok for _, ok in checks):
        stop("verification", f"{qno} EXISTS but the read-back does not match the spec (mismatched lines "
             f"{mism or 'none'}). Open it in BC and fix or delete it before it goes anywhere.", mismatched=mism)
    record(event="verified", status=norm(doc.get("status")), total=doc.get("totalAmountExcludingTax"),
           lines=len(doc.get("salesQuoteLines") or []))
    print(f"\nQUOTE CREATED AND VERIFIED: {qno} - {doc.get('customerName')} - ext doc "
          f"{doc.get('externalDocumentNumber')!r} - {money(float(doc.get('totalAmountExcludingTax') or 0))} excl. tax - "
          f"{norm(doc.get('status'))} - approved by {who}. Log: {log_path}")
    print("NEXT: a person reviews the quote in BC, releases it (tax), prints the PDF there and sends it. "
          "Nothing here releases or sends.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    acct = dict(default=None, help="cached sign-in to use when more than one is cached (or BBS_BC_ACCOUNT)")
    w = sub.add_parser("whoami", help="sign in, prove the read path a quote commit needs, print who writes would be attributed to")
    w.add_argument("--account", **acct)
    c = sub.add_parser("check", help="validate the spec and gates; write the review sheet; no writes")
    c.add_argument("spec")
    c.add_argument("--account", **acct)
    m = sub.add_parser("commit", help="create the sales quote after the rep approved the review sheet")
    m.add_argument("spec")
    m.add_argument("--approve", required=True, help="token printed by check")
    m.add_argument("--approved-by", required=True, help="name of the rep who read the review sheet")
    m.add_argument("--account", **acct)
    lo = sub.add_parser("logout", help="remove a cached sign-in (shared with bc-item-entry)")
    lo.add_argument("--account", default=None, help="which cached sign-in to remove")
    lo.add_argument("--all", action="store_true", help="remove every cached sign-in")
    args = ap.parse_args()
    {"whoami": cmd_whoami, "check": cmd_check, "commit": cmd_commit, "logout": item.cmd_logout}[args.cmd](args)


if __name__ == "__main__":
    main()
