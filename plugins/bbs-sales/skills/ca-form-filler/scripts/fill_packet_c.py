#!/usr/bin/env python3
"""
Complete a CDCR "Packet C" — OBS 4007(C) Price Request (Fair and Reasonable /
Exempt, e.g. a NASPO LPA order) plus whatever attachments came with it.

Usage:
    python fill_packet_c.py <packet.pdf> <inputs.json> <output.pdf>

STABLE INTERFACE — keep this file's name, location and arguments. The managed
settings allow it by path (the `ca-form-filler/scripts/` rule in
plugins/bbs-foundations/docs/bbs-managed-settings.json); a rename or a new
argument stops matching, and a rep in auto mode is stopped mid-packet. New
inputs go in inputs.json — `attachments` lists any further PDFs the agency sent
separately (Darfur, CalRecycle 74, OBS 1000, PD 843, STD 204 ...).

How it works (ca-form-filler references/packets/obs-4007c.md is the map):
  1. Assemble. Every page of the packet and the attachments is identified by
     its own header text, using the form table in ca-form-rules.md. The run
     reports which Packet C forms are present, where, and which are missing.
  2. Map. Each identified form's fields come from FORM_FIELDS below — IDs read
     off the real blank forms, never guessed. A field the agency's copy has
     renamed is reported as a gap, not hunted for.
  3. Fill and sign through the vetted engine, naspo-quote's fill_ca_forms.py:
     the signer rules, the $ limit (quote_total_incl_tax), each signature's page
     checked against its form, field validation, and the agency's pre-filled
     values kept. This script holds no signing logic of its own.
  4. Merge the filled documents into <output.pdf>, in the order given.

Nothing is written unless every check passed; at or over the limit the packet
is written unsigned with every signature line flagged.
"""
import json
import os
import shutil
import sys
import tempfile

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(SKILL_DIR)))
VENDOR_PROFILE = os.path.join(PLUGIN_ROOT, "references", "vendor_profile.json")
SIGNING_SCRIPTS = os.path.join(PLUGIN_ROOT, "skills", "naspo-quote", "scripts")

# The forms OBS 4007(C)'s own response list asks for, in the order to report them.
# The Line-Item Cost Worksheet has no row: a BBS itemized quote on letterhead is
# allowed in its place ("Line Item Cost Worksheet or Business Letterhead Itemized
# Quote"), and an agency worksheet is reported as unidentified pages to fill by hand.
EXPECTED = ("OBS4007C", "GSPD05105", "Darfur", "CalRecycle74", "OBS1000", "PD843", "STD204")

# Field IDs per form, read off real blanks on 2026-10-01 with inspect_form.py:
# OBS 4007(C) Rev. 03/2025 (uploaded by Parker); OBS 1500 (06/11), OBS 1000 Rev.
# 10/2025 (cdcr.ca.gov); CalRecycle 74 Rev. 01/23 (calrecycle.ca.gov); DGS PD 843
# Rev. 9/2019 and STD 204 Rev. 03/2021 (dgs.ca.gov). Values are keys resolved in
# values(); "@sign" marks the signature field and "@date" its date.
FORM_FIELDS = {
    "OBS4007C": {
        "text": {
            "OBS RFQ 4007(C) - Business Name": "legal_name",
            "OBS RFQ 4007(C) - Business Contact Person": "rep_name",
            "OBS RFQ 4007(C) - Business ContactTitle": "rep_title",
            "OBS RFQ 4007(C) - Business Contact Phone": "phone",
            "OBS RFQ 4007(C) - Business Contact Email": "rep_email",
            "OBS RFQ 4007(C) - Business Address L1": "street",
            "OBS RFQ 4007(C) - Business Address L2": "city_state_zip",
            "OBS RFQ 4007(C) - Federal Employer Identification Number FEIN": "fein",
            "OBS RFQ 4007(C) -  Sellers Permit": "seller_permit",
            "OBS RFQ 4007(C) - SB/MB/DVBE Cert": "dvbe_cert",
            "OBS RFQ 4007(C) - Cert Exp Date": "dvbe_cert_exp",
        },
        # DVBE ticked with the cert; SB and MB never (Parker, 2026-10-01).
        "checks": {
            "OBS RFQ 4007(C) - SB Checkbox": False,
            "OBS RFQ 4007(C) - MB Checkbox": False,
            "OBS RFQ 4007(C) - DVBE Checkbox": True,
            "OBS RFQ 4007 (C) Manufacturer -Yes": False,
            "OBS RFQ 4007 (C) Manufacturer -No": True,
        },
        "sign": ("OBS RFQ 4007C) - Bidder Signature", "OBS RFQ 4007C) - Sig Date", "rep"),
    },
    "Darfur": {
        "text": {"CompanyVendor Name Printed": "legal_name"},
        "sign": ("By Authorized Signature", "Date", "rep"),
    },
    "CalRecycle74": {
        "text": {
            "ContractorCompany Name": "legal_name",
            "Address": "full_address",
            "Phone_2": "phone",
            "Item Row1": "one",
            "Product or Services DescriptionRow1": "product_summary",
            "1Percent Postconsumer Recycled Content MaterialRow1": "calrecycle_pcrc",
            "2SABRC Product Category CodeRow1": "calrecycle_sabrc",
        },
        "signer_fields": {"name": "Print Name", "title": "Title"},
        "sign": ("Signature", "Date", "rep"),
    },
    "OBS1000": {
        "text": {
            "Business Name": "legal_name",
            "Business Telephone Number": "phone",
            "Business Address": "street",
            "City": "city",
            "State": "state",
            "Zip Code": "zip",
            "Contract  Description of Purchase": "product_summary",
        },
        # GenAI is about the product sold, not how the bid was prepared (ca-form-rules.md).
        "radios": {"Is GenAI utilized?": {"index": 1, "on": "No"}},
        "sign": ("Signature", "Date", "rep"),
    },
    "PD843": {
        "text": {
            "DVBEname": "legal_name",
            "DVBErefno": "dvbe_cert",
            "description": "product_summary",
            "DVBEowner1": "owner_name",
            "PageNo": "one",
            "TotalPages": "one",
        },
        "radios": {"I declare that the DVBE is not a broker or agent":
                   {"index": 0, "on": "DVBE#20is#20a#20broker#20or#20agent"}},
        "sign": ("DVBEowner1signature", "DVBEowner1date", "dv_owner"),
    },
    "STD204": {
        "text": {
            "NAME (This is required. Do not leave this line blank. Must match the payee’s "
            "federal tax return)": "legal_name",
            "MAILING ADDRESS (number, street, apt. or suite no.) (See instructions on Page 2)":
                "street",
            "CITY STATE ZIP CODE": "city_state_zip",
            "EMAIL ADDRESS": "owner_email",
            "Federal Employer Identification Number (FEIN)": "fein",
            "NAME OF AUTHORIZED PAYEE REPRESENTATIVE": "owner_name",
            "TITLE": "owner_title",
            "EMAIL ADDRESS_2": "owner_email",
            "TELEPHONE include area code": "phone",
        },
        "checks": {"corpOthers": True, "calRes": True},
        "sign": ("Signature4", "DATE", "dv_owner"),
    },
}


def _signing():
    if SIGNING_SCRIPTS not in sys.path:
        sys.path.insert(0, SIGNING_SCRIPTS)
    import fill_ca_forms
    return fill_ca_forms


def values(vp, inp):
    """Every value FORM_FIELDS names, from the vendor profile and inputs only."""
    ident, addr, contact = vp["business_identity"], vp["address"], vp["contact"]
    cert = vp["certifications"]["sb_dvbe"]
    owner = next(r for r in vp["authorized_representatives"] if r["role"] == "dvbe_owner")
    rep = inp.get("rep") or {}
    csz = f"{addr['city']}, {addr['state']} {addr['zip']}"
    return {
        "legal_name": ident["legal_name"], "fein": ident["fein"],
        "seller_permit": ident["ca_sellers_permit"], "street": addr["mailing_street"],
        "city": addr["city"], "state": addr["state"], "zip": addr["zip"],
        "city_state_zip": csz, "full_address": f"{addr['mailing_street']} {csz}",
        "phone": contact["phone"], "dvbe_cert": cert["osds_ref_number"],
        "dvbe_cert_exp": cert["expiration"], "owner_name": owner["name"],
        "owner_title": owner["title"], "owner_email": owner["email"],
        "rep_name": rep.get("name", ""), "rep_title": rep.get("title", ""),
        "rep_email": rep.get("email", ""), "product_summary": inp.get("product_summary", ""),
        "calrecycle_pcrc": inp.get("calrecycle_pcrc", "NA"),
        "calrecycle_sabrc": inp.get("calrecycle_sabrc", "NA"), "one": "1",
    }


def survey(paths, fcf, fitz):
    """[(path, [kind per page or None], {field: [page indexes]})] for each document."""
    table = fcf.load_form_table()
    out = []
    for path in paths:
        doc = fitz.open(path)
        kinds, fields = [], {}
        for pno, page in enumerate(doc):
            hits = fcf.classify_page(page.get_text(), table)
            kinds.append(hits[0] if len(hits) == 1 else None)
            for w in (page.widgets() or []):
                fields.setdefault(w.field_name, []).append(pno)
        doc.close()
        out.append((path, kinds, fields))
    return out


def build_spec(docs, vp, inp, staging):
    """The fill_ca_forms spec for these documents, and the gap report."""
    vals = values(vp, inp)
    gaps, forms = [], []
    for n, (path, kinds, fields) in enumerate(docs):
        present = sorted({k for k in kinds if k}, key=lambda k: list(FORM_FIELDS).index(k)
                         if k in FORM_FIELDS else 99)
        entry = {"src": os.path.abspath(path), "out": f"part-{n:02d}.pdf",
                 "text": {}, "checks": {}, "radios": {}, "sign": {}}
        if len(present) == 1 and all(k in (present[0], None) for k in kinds):
            entry["form"] = present[0]
        else:
            entry["form"] = "packet"
        signer_fields = {}
        for kind in present:
            fmap = FORM_FIELDS.get(kind)
            if not fmap:
                continue
            pages = {i for i, k in enumerate(kinds) if k == kind}

            def usable(name, kind=kind, pages=pages):
                where = fields.get(name)
                if not where:
                    gaps.append(f"[MISSING — NEEDS INPUT] {kind} in {os.path.basename(path)}: "
                                f"field {name!r} is not in this copy; fill it by hand or add "
                                f"this revision's ID to FORM_FIELDS")
                    return False
                if not set(where) <= pages:
                    gaps.append(f"[MISSING — NEEDS INPUT] {kind} in {os.path.basename(path)}: "
                                f"field {name!r} also appears on another form's page; left "
                                f"for the rep rather than written to both")
                    return False
                return True

            for name, key in fmap.get("text", {}).items():
                if not usable(name):
                    continue
                if str(vals[key]).strip():
                    entry["text"][name] = vals[key]
                else:
                    gaps.append(f"[MISSING — NEEDS INPUT] {kind} in {os.path.basename(path)}: "
                                f"{name!r} needs `{key}`, which the inputs do not give; "
                                f"left blank")
            for name, on in fmap.get("checks", {}).items():
                if usable(name):
                    entry["checks"][name] = on
            for name, choice in fmap.get("radios", {}).items():
                if usable(name):
                    entry["radios"][name] = choice
            for k, name in fmap.get("signer_fields", {}).items():
                if usable(name):
                    signer_fields[k] = name
            sfield, dfield, line = fmap["sign"]
            if usable(sfield):
                who = "jackson" if line == "dv_owner" else _signer_who(vp, inp)
                if who:
                    # Owner lines are always marked; on a bound packet every line is,
                    # and fill_ca_forms checks the mark against the page.
                    sig = {"who": who}
                    if entry["form"] == "packet" or line == "dv_owner":
                        sig["line"] = line
                    if dfield in fields and usable(dfield):
                        sig["date"] = dfield
                    entry["sign"][sfield] = sig
                else:
                    gaps.append(f"⚑ SIGNATURE REQUIRED — {kind} in {os.path.basename(path)}: "
                                f"the named signer is not one of the six delegates; sign and "
                                f"date by hand")
        if signer_fields:
            entry["signer_fields"] = signer_fields
        if inp.get("replace_prefilled"):
            entry["replace_prefilled"] = inp["replace_prefilled"]
        for key in ("text", "checks", "radios", "sign"):
            if not entry[key]:
                entry.pop(key)
        forms.append(entry)
    spec = {"src_dir": "/", "out_dir": staging, "master_root": inp.get("master_root") or None,
            "signer": inp.get("signer") or {}, "forms": forms,
            "quote_total_incl_tax": inp.get("quote_total_incl_tax"),
            "quote_ref": inp.get("quote_ref", ""),
            "signature_date": inp.get("signature_date", "")}
    return spec, gaps


def _signer_who(vp, inp):
    """The `who` for the named signer, if they are a delegate; else None.

    fill_ca_forms checks the signer again (domain, name and email together); this
    only picks the key, so a non-delegate's lines get no `sign` entry at all.
    """
    signer = inp.get("signer") or {}
    email = str(signer.get("email", "")).strip().lower()
    name = " ".join(str(signer.get("name", "")).split()).lower()
    reps = {r["role"]: r for r in vp["authorized_representatives"]}
    for role in vp["signature_delegation"]["delegates"]:
        r = reps.get(role) or {}
        addrs = {r.get("email", "").lower(), *[a.lower() for a in r.get("aliases") or []]}
        if email in addrs and name == " ".join(r.get("name", "").split()).lower():
            return role
    return None


def report(docs):
    lines, found = ["Packet C assembly:"], {}
    for path, kinds, _f in docs:
        for pno, k in enumerate(kinds):
            if k:
                found.setdefault(k, []).append(f"{os.path.basename(path)} p{pno + 1}")
        odd = [str(p + 1) for p, k in enumerate(kinds) if k is None]
        if odd:
            lines.append(f"  {os.path.basename(path)}: pages {', '.join(odd)} not identified "
                         f"(worksheet, instructions or an unlisted form) — check by eye")
    for k in EXPECTED:
        lines.append(f"  {k:<13} " + (", ".join(found[k]) if k in found else
                                       "MISSING — attach the agency's copy or a blank"))
    return lines


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    packet, inputs_path, output_pdf = sys.argv[1:4]
    try:
        import fitz
    except ImportError:
        sys.exit("pymupdf required: python -m pip install pymupdf "
                 "(Mac: python3 -m pip install --user pymupdf, or use a venv)")
    fcf = _signing()
    fcf.fitz = fitz
    with open(inputs_path, encoding="utf-8") as fh:
        inp = json.load(fh)
    with open(VENDOR_PROFILE, encoding="utf-8") as fh:
        vp = json.load(fh)
    paths = [packet] + list(inp.get("attachments") or [])
    for p in paths:
        if not os.path.isfile(p):
            sys.exit(f"ERROR: {p} not found. Nothing written.")

    docs = survey(paths, fcf, fitz)
    print("\n".join(report(docs)))
    if not any("OBS4007C" in kinds for _p, kinds, _f in docs):
        sys.exit("STOP: no OBS 4007(C) page found — this is not a Packet C. Run "
                 "packet_profile.py --recognize-pdf and follow what it says. Nothing written.")

    staging = tempfile.mkdtemp(prefix="packet-c-")
    try:
        spec, gaps = build_spec(docs, vp, inp, staging)
        try:
            sigs, ctx = fcf.prepare(spec)
        except fcf.SignatureMissing as e:
            hint = ("\nThe named signer's PNG is not in MASTER/Signatures/ yet: have the rep "
                    "name a delegate whose PNG is on file, or add theirs (ADMIN-RUNBOOK §3b)."
                    if "signature_image" in str(e) else "")
            sys.exit(f"STOP: {e}{hint}")
        kept, unapplied = [], []
        for form in spec["forms"]:
            try:
                _out, missed, form_kept = fcf.fill_form(form, sigs, "/", staging,
                                                        spec.get("master_root"), ctx)
            except fcf.SignatureMissing as e:
                sys.exit(f"STOP: {e}")
            unapplied += missed
            kept += form_kept
        if unapplied:
            sys.exit("STOP: " + "\n".join(unapplied) + "\nNothing written.")
        merged = fitz.open()
        for form in spec["forms"]:
            part = fitz.open(os.path.join(staging, form["out"]))
            merged.insert_pdf(part)
            part.close()
        tmp = os.path.join(staging, "merged.pdf")
        merged.save(tmp)
        merged.close()
        os.makedirs(os.path.dirname(os.path.abspath(output_pdf)), exist_ok=True)
        shutil.move(tmp, output_pdf)
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    print(f"\nPacket written to: {output_pdf}")
    stamped = sum(len(f.get("sign") or {}) for f in spec["forms"])
    print(f"Signatures stamped: {stamped}"
          + ("" if not ctx["withheld"] else " — SIGNATURES WITHHELD, the packet is UNSIGNED"))
    for line in kept + gaps + ctx["withheld"]:
        print(line)
    print("\nRender every page and look at it before sending (verify_script in the "
          "profile). A person sends; nothing here transmits anything.")


if __name__ == "__main__":
    main()
