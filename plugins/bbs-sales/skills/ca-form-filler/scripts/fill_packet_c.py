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

# The same forms bound into CDCR's own Packet C (cover "10/2025 Request For Quote
# (RFQ) Packet – C", OBS 4007(C) Rev. 08/2025 front), where CDCR renamed every
# attachment's fields with a form prefix. Read with inspect_form.py on 2026-11-17
# from a DAPO blank (CDCR (ALL)/DAPO, RFQ of 10/5/2026, 4007(C)-(10-2025).pdf).
# The front page keeps FORM_FIELDS' IDs, so it has no entry here. A form uses this
# map when its signature field is in the document (field_map()). `hand` lists
# values the bound copy has no field for: each is reported for the rep to write in.
BOUND_FORM_FIELDS = {
    "Darfur": {
        # Option #1 (no activities outside the US), as on the standalone form.
        "text": {"OBS RFQ 4007(C) - Business Name - Darfur": "legal_name"},
        "sign": ("Darfur OBS 1500 - By Authorized Signature", "Darfur OBS 1500 - Date", "rep"),
    },
    "CalRecycle74": {
        # Contractor/Company Name is the shared `OBS RFQ 4007(C) - Business Name`
        # (front page and worksheet too), filled by the front page's map.
        "text": {
            "DORRR CalRec 74 - Address": "full_address",
            "DORRR CalRec 74 - Phone_2": "phone",
            "DORRR CalRec 74 - Item Row1": "one",
            "DORRR CalRec 74 - Product or Services DescriptionRow1": "product_summary",
            "DORRR CalRec 74 - 1Percent Postconsumer Recycled Content MaterialRow1":
                "calrecycle_pcrc",
            "DORRR CalRec 74 - 2SABRC Product Category CodeRow1": "calrecycle_sabrc",
        },
        "signer_fields": {"name": "DORRR CalRec 74 - Print Name",
                          "title": "DORRR CalRec 74 - Title"},
        "sign": ("DORRR CalRec 74 - Signature", "DORRR CalRec 74 - Date", "rep"),
    },
    "OBS1000": {
        "text": {
            "OBS 1000 - Business Name": "legal_name",
            "OBS 1000 - Business Telephone Number": "phone",
            "OBS 1000 - Business Address": "street",
            "OBS 1000 - City": "city",
            "OBS 1000 - State": "state",
            "OBS 1000 - Zip Code": "zip",
            "OBS 1000 - Contract  Description of Purchase": "product_summary",
        },
        # The standalone form's "Is GenAI utilized?" radio is two checkboxes here.
        "checks": {"OBS 1000 - Was GenAI used - Yes": False,
                   "OBS 1000 - Was GenAI used - No": True},
        "sign": ("OBS 1000 - Signature", "OBS 1000 - Date", "rep"),
    },
    "PD843": {
        "text": {
            "DVBE Dec. DGS PD 843 - Name of DVBE": "legal_name",
            "DVBE Dec. DGS PD 843 - DVBE Ref #": "dvbe_cert",
            "DVBE Dec. DGS PD 843 - Desc": "product_summary",
            "DVBE Dec. DGS PD 843 -  Owner/Mngr. Print Nmae 1": "owner_name",
            "DVBE Dec. DGS PD 843 -  Page 1 of #": "one",
            "DVBE Dec. DGS PD 843 -  Total Pg.#s": "one",
        },
        # The standalone form's "not a broker or agent" radio is two checkboxes here.
        "checks": {"DVBE Dec. DGS PD 843 - DVBE not Broker": True,
                   "DVBE Dec. DGS PD 843 - DVBE is Broker": False},
        "sign": ("DVBE Dec. DGS PD 843 - DVBE Owner/ Mngr. Signature 1",
                 "DVBE Dec. DGS PD 843 - Date Signed 1", "dv_owner"),
    },
    "STD204": {
        "text": {
            "Payee Data Record STD 204 - BUSINESS NAME": "legal_name",
            "Payee Data Record STD 204 - BUSINESS MAILING ADDRESS number street apt or "
            "suite no See instructions on Page 2": "street",
            "Payee Data Record STD 204 - BUSINESS ADRESS CITY STATE ZIP CODE":
                "city_state_zip",
            "Payee Data Record STD 204 - BUSINESS EMAIL ADDRESS": "owner_email",
            "Payee Data Record STD 204 - NAME OF AUTHORIZED PAYEE REPRESENTATIVE":
                "owner_name",
            "Payee Data Record STD 204 - Auth Rep TITLE": "owner_title",
            "Payee Data Record STD 204 - Auth Rep EMAIL ADDRESS_2": "owner_email",
            "Payee Data Record STD 204 - Auth Rep Phone#": "phone",
        },
        "checks": {"Payee Data Record STD 204 - All Others Checkbox": True,
                   "Payee Data Record STD 204 - CA Resident": True},
        "hand": ["fein"],   # Section 3's FEIN boxes are printed, not a field
        "sign": ("Payee Data Record STD 204 - Auth Rep. Signature",
                 "Payee Data Record STD 204 - Auth Rep Sign Date", "dv_owner"),
    },
}


def field_map(kind, fields):
    """The field map for `kind` in a document whose field names are `fields`.

    The bound Packet C map when its signature field is in the document, else the
    standalone map. A copy matching neither falls through to FORM_FIELDS, and each
    absent ID is reported as a gap, as before.
    """
    bound = BOUND_FORM_FIELDS.get(kind)
    if bound and bound["sign"][0] in fields:
        return bound
    return FORM_FIELDS.get(kind)


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
            fmap = field_map(kind, fields)
            if not fmap:
                continue
            for key in fmap.get("hand", []):
                gaps.append(f"[MISSING — NEEDS INPUT] {kind} in {os.path.basename(path)}: "
                            f"this copy has no field for `{key}` ({vals[key]}); write it in "
                            f"by hand")
            pages = {i for i, k in enumerate(kinds) if k == kind}

            def usable(name, kind=kind, pages=pages):
                where = fields.get(name)
                if not where:
                    gaps.append(f"[MISSING — NEEDS INPUT] {kind} in {os.path.basename(path)}: "
                                f"field {name!r} is not in this copy; fill it by hand or add "
                                f"this revision's ID to FORM_FIELDS")
                    return False
                if not set(where) <= pages:
                    spots = ", ".join(f"p{p + 1} ({kinds[p] or 'unidentified'})"
                                      for p in sorted(set(where)))
                    gaps.append(f"[MISSING — NEEDS INPUT] {kind} in {os.path.basename(path)}: "
                                f"field {name!r} is one field shown on {spots}; left blank "
                                f"for the rep rather than written across forms. Typing it "
                                f"once fills every one of those pages")
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
