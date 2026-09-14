#!/usr/bin/env python3
"""
Fill a CDCR OBS 4007(B) RFQ Packet-B for Black Box Safety.

Usage:
    python fill_obs_packet.py <blank_packet.pdf> <inputs.json> <output.pdf>

The script:
  1. Loads the hardcoded BBS vendor profile (assets/bbs_vendor_profile.json).
  2. Merges it with the rep / agency / line-item inputs supplied in inputs.json.
  3. Fills every AcroForm field in-process with pypdf.
  4. Adds 4 text annotations for the company-name lines that have no AcroForm
     field (OBS 4007(B) Business Name, Line-Item Worksheet Business Name,
     CalRecycle 74 Contractor/Company Name, STD 204 Section 1 NAME).

Design notes (why it's built this way):
  - The bidder/rep is a *variable* (a different sales rep may sign each time),
    so rep name/title/email/signature come from inputs.json.
  - Jackson Dalton is the DV owner and ALWAYS signs the DVBE owner lines
    (DGS PD 843) and is the STD 204 authorized payee representative, because
    those certifications are tied to ownership, not to whoever quoted the job.
  - Agency-side fields (method of award details the State fills, SCPRS ref,
    PO#, paying-agency block) are left blank on purpose.
  - Signature DATES are filled if provided; if the rep wants to date at the
    moment of signing, they can pass "" and add it by hand.
  - PCRC defaults to "n/a" on the worksheet and "NA"/"NA" on CalRecycle 74
    unless the input overrides it, because BBS resells finished goods and
    rarely certifies a postconsumer percentage. CalRecycle 74 must never be
    left blank (a blank form can disqualify the bid), so we always certify.
"""

import json
import sys
import os

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_profile():
    with open(os.path.join(SKILL_DIR, "assets", "bbs_vendor_profile.json")) as f:
        return json.load(f)


def build_field_values(profile, inp):
    """Return the list of {field_id, page, value} dicts for the AcroForm fill."""
    rep = inp_rep = inp.get("rep", {})
    rep_name = rep.get("name", "")
    rep_title = rep.get("title", "Sales Manager")
    rep_email = rep.get("email", "")
    rep_sig = rep.get("signature", rep_name)  # signature text defaults to name

    owner = profile["dvbe_owner"]
    acct = profile["accounting_contact"]

    sol = inp.get("solicitation_number", "")
    release = inp.get("release_date", "")
    due = inp.get("due_date", "")
    sig_date = inp.get("signature_date", "")  # may be "" to hand-date
    delivery_days = str(inp.get("delivery_days_aro", "30"))

    agency = inp.get("agency", {})
    req_name = agency.get("requestor_name", "")
    req_email = agency.get("requestor_email", "")
    req_phone = agency.get("requestor_phone", "")
    ship1 = agency.get("ship_to_line1", "")
    ship2 = agency.get("ship_to_line2", "")
    ship3 = agency.get("ship_to_line3", "")

    items = inp.get("line_items", [])
    desc_short = inp.get("product_summary", "")  # short label for OBS 1000 / CalRec / PD843

    fv = []

    def add(fid, page, value):
        fv.append({"field_id": fid, "page": page, "value": value})

    # ---------- OBS 4007(B) front page (page 2) ----------
    add("OBS RFQ 4007(B) - Release Date", 2, release)
    add("OBS RFQ 4007(B) - Due Date", 2, due)
    add("OBS RFQ 4007(B) - Business Adrees L1", 2, profile["address_line"])
    add("OBS RFQ 4007(B) - Business Address L2", 2, profile["city_state_zip"])
    add("OBS RFQ 4007(B) - Business Contact Person", 2, rep_name)
    add("OBS RFQ 4007(B) - Business Person Title", 2, rep_title)
    add("OBS RFQ 4007(B) - Business Contact Phone#", 2, profile["phone"])
    add("OBS RFQ 4007(B) - Business Contac Persone Email", 2, rep_email)
    add("OBS RFQ 4007(B) - FEIN", 2, profile["fein"])
    add("OBS RFQ 4007(B) - Seller Perm", 2, profile["seller_permit"])
    add("OBS RFQ 4007(B) - SB Checkbox", 2, "/Off")
    add("OBS RFQ 4007(B) - MB Checkbox", 2, "/Off")
    add("OBS RFQ 4007(B) - DVBE Checkbox", 2, "/Yes")
    add("OBS RFQ 4007(B) - SB/MB/DVBE Cert#", 2, profile["dvbe_cert"])
    add("OBS RFQ 4007(B) - Cert Exp", 2, profile["dvbe_cert_exp"])
    add("OBS RFQ 4007(B) - Manufacture Yes Checkbox", 2, "/Off")
    add("OBS RFQ 4007(B) - Manufacturer No Checkbox", 2, "/Yes")
    add("OBS RFQ 4007(B) - SB Sub Preference Yes", 2, "/Off")
    add("OBS RFQ 4007(B) - SB Sub Preference No", 2, "/Yes")
    add("OBS RFQ 4007(B) - Bidder Signature", 2, rep_sig)
    add("OBS RFQ 4007(B) - Bidder Sig Date", 2, sig_date)

    # ---------- OBS 4007(B) additional details (page 3) ----------
    add("OBS RFQ 4007(B) - Deliver Completion Requirement", 3, delivery_days)
    add("OBS RFQ 4007(B) - All or None", 3, "/Yes")
    add("OBS RFQ 4007(B) - Bid Offering Prepid Freight", 3, "/Yes")
    add("OBS RFQ 4007(B) - Requestor Name", 3, req_name)
    add("OBS RFQ 4007(B) - Requestor Email", 3, req_email)
    add("OBS RFQ 4007(B) - Requestor Phone#", 3, req_phone)
    add("OBS RFQ 4007(B) - Shipping Address L1", 3, ship1)
    add("OBS RFQ 4007(B) - Shipping Address L2", 3, ship2)
    add("OBS RFQ 4007(B) - Shipping Address L3", 3, ship3)

    # ---------- Line-Item Cost Worksheet (page 12) ----------
    # The worksheet has 23 rows. A longer quote used to be truncated here, which
    # also dropped the extra lines from the subtotal — the packet came out looking
    # complete with a grand total that undercharged. Refuse instead: a bid is a
    # binding price, so a wrong total is worse than no packet.
    if len(items) > MAX_LINE_ITEMS:
        sys.exit(f"{len(items)} line items, but the OBS worksheet has only "
                 f"{MAX_LINE_ITEMS} rows. Split the quote across separate packets, "
                 f"or consolidate lines and attach the full quote sheet — do not "
                 f"submit a truncated worksheet.")

    subtotal = 0.0
    for idx, item in enumerate(items, start=1):
        ln = str(idx)
        qty = str(item.get("qty", ""))
        unit = item.get("unit", "")
        desc = item.get("description", "")
        part = item.get("part_number", "")
        pcrc = item.get("pcrc", "n/a")
        unit_price = item.get("unit_price", 0.0)
        ext_price = item.get("ext_price")
        try:
            up = float(str(unit_price).replace("$", "").replace(",", ""))
        except (ValueError, TypeError):
            up = 0.0
        try:
            q = float(qty)
        except (ValueError, TypeError):
            q = 0.0
        if ext_price is None:
            ext = up * q
        else:
            ext = float(str(ext_price).replace("$", "").replace(",", ""))
        subtotal += ext

        # Field IDs are not perfectly regular in the source PDF; resolve per-row.
        line_field_map = LINE_FIELD_IDS[idx]
        add(line_field_map["line"], 12, ln)
        add(line_field_map["qty"], 12, qty)
        add(line_field_map["unit"], 12, unit)
        add(line_field_map["desc"], 12, desc)
        add(line_field_map["part"], 12, part)
        add(line_field_map["pcrc"], 12, pcrc)
        add(line_field_map["unit_price"], 12, _money(up))
        add(line_field_map["ext_price"], 12, _money(ext))

    sh = inp.get("shipping_handling", 0.0)
    try:
        sh_val = float(str(sh).replace("$", "").replace(",", ""))
    except (ValueError, TypeError):
        sh_val = 0.0
    total = subtotal + sh_val
    add("OBS Line-Item Cost Wrksht - Subtotal", 12, _money(subtotal))
    add("OBS Line-Item Cost Wrksht - S&H", 12, _money(sh_val))
    add("OBS Line-Item Cost Wrksht - Grand Total", 12, _money(total))

    # ---------- GSPD-05-105 Bidder Declaration (page 13) ----------
    add("GSPD-05-105 Bidder Dec. Written -Certification #", 13, "DVBE")
    add("GSPD-05-105 Bidder Dec. Written -Cert# N/A", 13, "/Off")
    add("GSPD-05-105 Bidder Dec. Written -Sub Yes", 13, "/Off")
    add("GSPD-05-105 Bidder Dec. Written -Sub No", 13, "/Yes")
    add("GSPD-05-105 Bidder Dec. Written - Broker/Agent Yes", 13, "/Off")
    add("GSPD-05-105 Bidder Dec. Written - Broker/Agent No", 13, "/Yes")
    add("GSPD-05-105 Bidder Dec. Written - Eqpt. Rental Yes", 13, "/Off")
    add("GSPD-05-105 Bidder Dec. Written - Eqpt. Rental No", 13, "/Off")
    add("GSPD-05-105 Bidder Dec. Written - Eqpt. Rental N/A", 13, "/Yes")
    add("GSPD-05-105 Bidder Dec. Written - Pg 1 - Pg #", 13, "1")
    add("GSPD-05-105 Bidder Dec. Written - Pg 1 - #of pgs", 13, "1")

    # ---------- Darfur OBS 1500 (page 15) — Option 1, no activities outside US ----------
    add("Darfur OBS 1500 - CompanyVendor Name Printed", 15, profile["short_name"])
    add("Darfur OBS 1500 - Date", 15, sig_date)
    add("Darfur OBS 1500 - By Authorized Signature", 15, rep_sig)

    # ---------- CalRecycle 74 (page 16) ----------
    add("DORRR CalRec 74 - Address", 16,
        f'{profile["address_line"]} {profile["city"]} {profile["state"]} {profile["zip"]}')
    add("DORRR CalRec 74 - Phone_2", 16, profile["phone"])
    add("DORRR CalRec 74 - Item Row1", 16, "1")
    add("DORRR CalRec 74 - Product or Services DescriptionRow1", 16,
        desc_short or (items[0].get("description", "") if items else ""))
    add("DORRR CalRec 74 - 1Percent Postconsumer Recycled Content MaterialRow1", 16,
        inp.get("calrecycle_pcrc", "NA"))
    add("DORRR CalRec 74 - 2SABRC Product Category CodeRow1", 16,
        inp.get("calrecycle_sabrc", "NA"))
    add("DORRR CalRec 74 - Print Name", 16, rep_name)
    add("DORRR CalRec 74 - Signature", 16, rep_sig)
    add("DORRR CalRec 74 - Title", 16, rep_title)
    add("DORRR CalRec 74 - Date", 16, sig_date)

    # ---------- OBS 1000 GenAI (pages 18-19) ----------
    add("OBS 1000 - Business Name", 18, profile["short_name"])
    add("OBS 1000 - Business Telephone Number", 18, profile["phone"])
    add("OBS 1000 - Business Address", 18, profile["address_line"])
    add("OBS 1000 - City", 18, profile["city"])
    add("OBS 1000 - State", 18, profile["state"])
    add("OBS 1000 - Zip Code", 18, profile["zip"])
    add("OBS 1000 - Contract  Description of Purchase", 18, desc_short)
    add("OBS 1000 - Was GenAI used - Yes", 18, "/Off")
    add("OBS 1000 - Was GenAI used - No", 18, "/Yes")
    add("OBS 1000 - Date", 19, sig_date)

    # ---------- DGS PD 843 DVBE Declarations (page 21) ----------
    # Jackson Dalton ALWAYS signs as DV owner — certification is tied to ownership.
    add("DVBE Dec. DGS PD 843 - Name of DVBE", 21, profile["short_name"])
    add("DVBE Dec. DGS PD 843 - DVBE Ref #", 21, profile["dvbe_cert"])
    add("DVBE Dec. DGS PD 843 - Desc", 21, desc_short)
    add("DVBE Dec. DGS PD 843 - DVBE not Broker", 21, "/Yes")
    add("DVBE Dec. DGS PD 843 - DVBE is Broker", 21, "/Off")
    add("DVBE Dec. DGS PD 843 -  Owner/Mngr. Print Nmae 1", 21, owner["name"])
    add("DGS PD 843 - DVBE Owner/ Signature 1", 21, owner["name"])
    add("DVBE Dec. DGS PD 843 - Date Signed 1", 21, sig_date)
    add("DVBE Dec. DGS PD 843 -  Page 1 of #", 21, "1")
    add("DVBE Dec. DGS PD 843 -  Total Pg.#s", 21, "1")

    # ---------- Supplement Vendor Payee Data Record (pages 22-23) ----------
    add("Supplement Vendor Payee Data Rec - Legal Biz Name", 22, profile["legal_name"])
    add("Supplement Vendor Payee Data Rec - FEIN/SSN", 22, profile["fein"])
    add("Supplement Vendor Payee Data Rec - Biz Physical Address", 22, profile["address_line"])
    add("Supplement Vendor Payee Data Rec - Biz Physical Address City", 22, profile["city"])
    add("Supplement Vendor Payee Data Rec - Physical Address State", 22, profile["state"])
    add("Supplement Vendor Payee Data Rec - Physical Address Zip", 22, profile["zip"])
    add("Supplement Vendor Payee Data Rec - RTO Company Name", 22, profile["legal_name"])
    add("Supplement Vendor Payee Data Rec - RTO Company Street / PO Box", 22, profile["address_line"])
    add("Supplement Vendor Payee Data Rec - RTO Company CA", 22, profile["city"])
    add("Supplement Vendor Payee Data Rec - RTO Company State", 22, profile["state"])
    add("Supplement Vendor Payee Data Rec - RTO Company Zip", 22, profile["zip"])
    add("Supplement Vendor Payee Data Rec - Sales Contact Name", 22, rep_name)
    add("Supplement Vendor Payee Data Rec - Sales Contact Title", 22, rep_title)
    add("Supplement Vendor Payee Data Rec - Sales Contact Phone", 22, profile["phone"])
    add("Supplement Vendor Payee Data Rec - Sales Contact Email", 22, rep_email)
    add("Supplement Vendor Payee Data Rec - Accounting Contact Name", 22, acct["name"])
    add("Supplement Vendor Payee Data Rec - Accounting Contact Title", 22, acct["title"])
    add("Supplement Vendor Payee Data Rec - Accounting Contact Phone", 22, acct["phone"])
    add("Supplement Vendor Payee Data Rec - Website Address", 22, profile["website"])
    add("Supplement Vendor Payee Data Rec - Type of Srvc. Checkbox", 22, "/Off")
    add("Supplement Vendor Payee Data Rec - Commodity Checkbox", 22, "/Yes")
    add("Supplement Vendor Payee Data Rec - Type of Product Text", 22, profile["product_type"])
    add("Supplement Vendor Payee Data Rec - DVBE Checkbox", 23, "/Yes")
    add("Supplement Vendor Payee Data Rec - DVBE Cert#", 23, profile["dvbe_cert"])
    add("Supplement Vendor Payee Data Rec - DVBE Cert Exp Date", 23, profile["dvbe_cert_exp"])
    add("Supplement Vendor Payee Data Rec - Type of Recipient - LLC S-Corp", 23, "/Yes")

    # ---------- STD 204 Payee Data Record (page 24) ----------
    # Jackson Dalton is the authorized payee representative (owner).
    add("Payee Data Record STD 204 - BUSINESS MAILING ADDRESS number street apt or suite no See instructions on Page 2", 24, profile["address_line"])
    add("Payee Data Record STD 204 - BUSINESS ADRESS CITY STATE ZIP CODE", 24, profile["city_state_zip"])
    add("Payee Data Record STD 204 - BUSINESS EMAIL ADDRESS", 24, owner["email"])
    add("Payee Data Record STD 204 - Sole Proprietor Checkbox", 24, "/Off")
    add("Payee Data Record STD 204 - Single LLC Checkbox", 24, "/Off")
    add("Payee Data Record STD 204 - Partnership Checkbox", 24, "/Off")
    add("Payee Data Record STD 204 - Estae/Trust Checkbox", 24, "/Off")
    add("Payee Data Record STD 204 - Med Checkbox", 24, "/Off")
    add("Payee Data Record STD 204 - Legal Checkbox", 24, "/Off")
    add("Payee Data Record STD 204 - Exempt Checkbox", 24, "/Off")
    add("Payee Data Record STD 204 - All Others Checkbox", 24, "/Yes")
    add("Payee Data Record STD 204 - CORPORATION see instructions on page 2 MEDICAL eg dentistry chiropractic etc LEGAL eg attorney services EXEMPT eg nonprofit ALL OTHERS", 24, profile["fein"])
    add("Payee Data Record STD 204 - CA Resident", 24, "/Yes")
    add("Payee Data Record STD 204 - CA Non-Resident", 24, "/Off")
    add("Payee Data Record STD 204 - NAME OF AUTHORIZED PAYEE REPRESENTATIVE", 24, owner["name"])
    add("Payee Data Record STD 204 - Auth Rep TITLE", 24, owner["title"])
    add("Payee Data Record STD 204 - Auth Rep EMAIL ADDRESS_2", 24, owner["email"])
    add("Payee Data Record STD 204 - Auth Rep Phone#", 24, profile["phone"])
    add("Payee Data Record STD 204 - Auth Rep Sign Date", 24, sig_date)
    add("Payee Data Record STD 204 - Auth Rep. Signature", 24, owner["name"])

    # Drop empty-string values so we don't write blank-but-present fields
    # needlessly. Checkbox "/Off" values are not empty, so they survive this.
    fv = [f for f in fv if f["value"] != ""]
    return fv


MAX_LINE_ITEMS = 23


def _money(x):
    return "${:,.2f}".format(float(x))


# Line-item field IDs from the source PDF. They are mostly regular but a few
# rows have irregular IDs (the source form was hand-named), so we map explicitly
# for the first 7 rows which cover the typical 1-10 item quote. Rows 8-23 follow
# the regular "L{n}" pattern and are generated below.
LINE_FIELD_IDS = {
    1: {
        "line": "OBS Line-Item Cost Wrksht - Line Itm - L1",
        "qty": "OBS Line-Item Cost Wrksht - QTY L1",
        "unit": "OBS Line-Item Cost Wrksht - Unit L1",
        "desc": "OBS Line-Item Cost Wrksht - Descriptions L1",
        "part": "OBS Line-Item Cost Wrksht - Itm/Part# L1",
        "pcrc": "OBS Line-Item Cost Wrksht - PCRC L1",
        "unit_price": "OBS Line-Item Cost Wrksht - Unit Price L1",
        "ext_price": "OBS Line-Item Cost Wrksht - Ext Price L1",
    },
    2: {
        "line": "OBS Line-Item Cost Wrksht - Line Itm L2",
        "qty": "OBS Line-Item Cost Wrksht - Qty L2",
        "unit": "OBS Line-Item Cost Wrksht - Unit L2",
        "desc": "OBS Line-Item Cost Wrksht - Descriptions L2",
        "part": "OBS Line-Item Cost Wrksht - Itm/Part# L2",
        "pcrc": "OBS Line-Item Cost Wrksht - PCRC L2",
        "unit_price": "OBS Line-Item Cost Wrksht - Unit Price L2",
        "ext_price": "OBS Line-Item Cost Wrksht - Ext Price L2",
    },
    3: {
        "line": "OBS Line-Item Cost Wrksht - Line Itm# L3",
        "qty": "OBS Line-Item Cost Wrksht - QTY L3",
        "unit": "OBS Line-Item Cost Wrksht - Unit L3",
        "desc": "OBS Line-Item Cost Wrksht - Description L3",
        "part": "OBS Line-Item Cost Wrksht - Itm/Part# L3",
        "pcrc": "OBS Line-Item Cost Wrksht - PCRC L3",
        "unit_price": "OBS Line-Item Cost Wrksht - Unit Price L3",
        "ext_price": "OBS Line-Item Cost Wrksht - Ext Price L3",
    },
    4: {
        "line": "OBS Line-Item Cost Wrksht - Line Itm# L4",
        "qty": "OBS Line-Item Cost Wrksht - QTY L4",
        "unit": "OBS Line-Item Cost Wrksht - Unit L4",
        "desc": "OBS Line-Item Cost Wrksht - Description L4",
        "part": "OBS Line-Item Cost Wrksht - Itm/Part# L4",
        "pcrc": "OBS Line-Item Cost Wrksht - PCRC L4",
        "unit_price": "OBS Line-Item Cost Wrksht - Unit Price L4",
        "ext_price": "OBS Line-Item Cost Wrksht - Ext Price L4",
    },
    5: {
        "line": "OBS Line-Item Cost Wrksht - Line Itm# L5",
        "qty": "OBS Line-Item Cost Wrksht - QTY L5",
        "unit": "OBS Line-Item Cost Wrksht - Unit L5",
        "desc": "OBS Line-Item Cost Wrksht - Description L5",
        "part": "OBS Line-Item Cost Wrksht - Itm/Part# L5",
        "pcrc": "OBS Line-Item Cost Wrksht - PCRC L5",
        "unit_price": "OBS Line-Item Cost Wrksht - Unit Price L5",
        "ext_price": "OBS Line-Item Cost Wrksht - Ext Price LOBS Line-Item Cost Wrksht - Ext Price L5",
    },
    6: {
        "line": "OBS Line-Item Cost Wrksht - Line Itm# L6",
        "qty": "OBS Line-Item Cost Wrksht - QTY L6",
        "unit": "OBS Line-Item Cost Wrksht - Unit L6",
        "desc": "OBS Line-Item Cost Wrksht - Description L6",
        "part": "OBS Line-Item Cost Wrksht - Itm/Part# L6",
        "pcrc": "OBS Line-Item Cost Wrksht - PCRC L6",
        "unit_price": "OBS Line-Item Cost Wrksht - Unit Price L6",
        "ext_price": "OBS Line-Item Cost Wrksht L6",
    },
    7: {
        "line": "OBS Line-Item Cost Wrksht - Line Itm# L7",
        "qty": "OBS Line-Item Cost Wrksht - QTY L7",
        "unit": "OBS Line-Item Cost Wrksht - Unit L7",
        "desc": "OBS Line-Item Cost Wrksht - Description L7",
        "part": "OBS Line-Item Cost Wrksht - Itm/Part# L7",
        "pcrc": "OBS Line-Item Cost Wrksht - PCRC L7",
        "unit_price": "OBS Line-Item Cost Wrksht - Unit Price L7",
        "ext_price": "OBS Line-Item Cost Wrksht - Ext Price L7",
    },
}
# Rows 8-23 follow the regular pattern. A couple of ext-price fields are
# irregular in the source (L13, L18, L23 use "OBS Line-Item Cost Wrksht L{n}"),
# so override those after generating the regular pattern.
for _n in range(8, 24):
    LINE_FIELD_IDS[_n] = {
        "line": f"OBS Line-Item Cost Wrksht - Line Itm# L{_n}",
        "qty": f"OBS Line-Item Cost Wrksht - QTY L{_n}",
        "unit": f"OBS Line-Item Cost Wrksht - Unit L{_n}",
        "desc": f"OBS Line-Item Cost Wrksht - Description L{_n}",
        "part": f"OBS Line-Item Cost Wrksht - Itm/Part# L{_n}",
        "pcrc": f"OBS Line-Item Cost Wrksht - PCRC L{_n}",
        "unit_price": f"OBS Line-Item Cost Wrksht - Unit Price L{_n}",
        "ext_price": f"OBS Line-Item Cost Wrksht - Ext Price L{_n}",
    }
LINE_FIELD_IDS[13]["ext_price"] = "OBS Line-Item Cost Wrksht L13"
LINE_FIELD_IDS[18]["ext_price"] = "OBS Line-Item Cost wrksht L18"
LINE_FIELD_IDS[23]["ext_price"] = "OBS Line-Item Cost Wrksht L23"


# Text annotations for the 4 company-name lines that have NO AcroForm field.
# Coordinates are in PyMuPDF space (origin top-left), verified against the
# Rev. 08/2025 packet. (page is 0-based here.)
ANNOTATIONS = [
    # OBS 4007(B) front page Business Name line
    {"page": 1, "x": 155, "y": 223, "key": "legal_name"},
    # Line-Item Worksheet "BUSINESS NAME:" header
    {"page": 11, "x": 105, "y": 101, "key": "short_name"},
    # CalRecycle 74 "Contractor/Company Name"
    {"page": 15, "x": 145, "y": 296, "key": "short_name"},
    # STD 204 Section 1 NAME line
    {"page": 23, "x": 22, "y": 97, "key": "legal_name"},
]


def _resolve(obj):
    """Follow an indirect reference, if that's what this is."""
    return obj.get_object() if hasattr(obj, "get_object") else obj


def _qualified_field_name(obj):
    """Fully-qualified AcroForm name for a widget, e.g. "parent.child"."""
    parts = []
    seen = set()
    while obj is not None and id(obj) not in seen:
        seen.add(id(obj))
        title = obj.get("/T")
        if title is not None:
            parts.append(str(title))
        parent = obj.get("/Parent")
        obj = _resolve(parent) if parent is not None else None
    return ".".join(reversed(parts)) if parts else None


def _inherited(obj, key):
    """Look up an inheritable field attribute (/FT, /Opt) up the parent chain."""
    seen = set()
    while obj is not None and id(obj) not in seen:
        seen.add(id(obj))
        if key in obj:
            return _resolve(obj[key])
        parent = obj.get("/Parent")
        obj = _resolve(parent) if parent is not None else None
    return None


def describe_fields(reader):
    """Describe every AcroForm field: type, pages holding a widget, on-states.

    Read off the widgets rather than taken on trust from the field dictionary:
    /FT is inheritable, and a checkbox's "checked" value is spelled out only in
    its appearance dictionary. A revised packet that spells the checked state
    "/1" instead of "/Yes" is exactly what this has to catch.
    """
    specs = {}
    for page_no, page in enumerate(reader.pages, start=1):
        for annot in page.get("/Annots") or []:
            obj = _resolve(annot)
            name = _qualified_field_name(obj)
            if not name:
                continue
            spec = specs.setdefault(
                name, {"type": None, "pages": set(), "on_states": set()})
            spec["pages"].add(page_no)
            ftype = _inherited(obj, "/FT")
            if ftype is not None:
                spec["type"] = str(ftype)
            if spec["type"] != "/Btn":
                # Only a button's /AP /N is a state dictionary. On a text field
                # it is the appearance stream itself, whose keys (/BBox, /Filter,
                # ...) are not states.
                continue
            appearances = _resolve((_resolve(obj.get("/AP")) or {}).get("/N"))
            if hasattr(appearances, "keys"):
                spec["on_states"].update(
                    str(state) for state in appearances.keys() if str(state) != "/Off")
    return specs


def resolve_value(name, spec, value):
    """Return (value_to_write, note, error) for one field.

    Buttons are resolved against the states the packet actually declares, so
    the intent ("check the DVBE box") survives a revision that renames the
    checked state. Anything unresolvable is an error, never a silent skip: an
    unchecked DVBE box on a DVBE bid is a disqualification.
    """
    ftype = spec["type"]
    value = str(value)

    if ftype == "/Btn":
        if value == "/Off":
            return "/Off", None, None
        on_states = sorted(spec["on_states"])
        if not on_states:
            return None, None, (
                f"ERROR: `{name}` is a button field with no on-state in its "
                f"appearance dictionary, so it cannot be checked")
        if value in on_states:
            return value, None, None
        if len(on_states) > 1:
            return None, None, (
                f"ERROR: `{name}` is a button with several on-states "
                f"{on_states}; the script asked for \"{value}\". It is probably "
                f"a radio group now and needs an explicit choice")
        return on_states[0], (
            f"NOTE: `{name}` is checked as \"{on_states[0]}\", not \"{value}\" — "
            f"this packet revision spells the checked state differently"), None

    if ftype == "/Ch":
        options = spec.get("options")
        if options and value not in options:
            return None, None, (
                f"ERROR: invalid value \"{value}\" for choice field `{name}`. "
                f"Valid values are: {sorted(options)}")

    return value, None, None


def fill_acroform(blank_pdf, field_values, output_pdf):
    """Fill the packet's AcroForm fields.

    Done in-process rather than by shelling out to the managed pdf skill:
    this skill ships to reps' machines through the marketplace plugin, where
    /mnt/skills/public/pdf does not exist. The validation below stands in for
    what that script used to catch — every field is checked against the packet
    in hand before anything is written.
    """
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(blank_pdf)
    if reader.is_encrypted:
        # decrypt() reports failure by return value, not by raising.
        try:
            opened = reader.decrypt("")
        except Exception:
            opened = False
        if not opened:
            sys.exit(f"{blank_pdf} is password-protected. Save an unlocked copy of "
                     f"the blank packet and run again.")
    known = reader.get_fields() or {}
    specs = describe_fields(reader)

    errors = []
    notes = []
    by_page = {}
    for fv in field_values:
        name, page, raw = fv["field_id"], fv["page"], fv["value"]
        if name not in known:
            errors.append(f"ERROR: `{name}` is not a valid field ID")
            continue
        spec = specs.get(name)
        if spec is None or not spec["pages"]:
            errors.append(f"ERROR: `{name}` exists in the form but has no widget on "
                          f"any page, so nothing would be written to it")
            continue
        if page not in spec["pages"]:
            errors.append(f"ERROR: Incorrect page number for `{name}` (got {page}, "
                          f"expected {sorted(spec['pages'])})")
            continue
        value, note, err = resolve_value(name, spec, raw)
        if err:
            errors.append(err)
            continue
        if note:
            notes.append(note)
        by_page.setdefault(page, {})[name] = value

    if errors:
        print("\n".join(errors))
        print(f"\n{len(errors)} field(s) could not be filled. The packet revision has "
              f"probably changed — run `--inspect` on the blank packet and reconcile "
              f"LINE_FIELD_IDS / the add() calls. See references/field_map.md.")
        sys.exit(1)
    if notes:
        print("\n".join(notes))

    writer = PdfWriter(clone_from=reader)
    for page_no, values in by_page.items():
        writer.update_page_form_field_values(
            writer.pages[page_no - 1], values, auto_regenerate=False)
    writer.set_need_appearances_writer(True)
    with open(output_pdf, "wb") as f:
        writer.write(f)


def add_annotations(pdf_path, profile):
    import fitz
    doc = fitz.open(pdf_path)
    for a in ANNOTATIONS:
        page = doc[a["page"]]
        page.insert_text((a["x"], a["y"]), profile[a["key"]],
                         fontname="helv", fontsize=9, color=(0, 0, 0))
    tmp = pdf_path + ".annot.pdf"
    doc.save(tmp)
    doc.close()
    os.replace(tmp, pdf_path)


def inspect(blank_pdf):
    """Print every field with its type, page and on-states.

    The diagnostic lives beside the filler, and reads the packet exactly the
    way the filler does, so the two can never disagree about what it contains.
    """
    from pypdf import PdfReader

    reader = PdfReader(blank_pdf)
    specs = describe_fields(reader)
    rows = sorted(specs.items(), key=lambda kv: (min(kv[1]["pages"]), kv[0]))
    print(f"{len(rows)} fields in {blank_pdf}\n")
    print(f"{'PAGE':<6}{'TYPE':<8}{'ON-STATES':<22}NAME")
    for name, spec in rows:
        pages = ",".join(str(p) for p in sorted(spec["pages"]))
        states = ",".join(sorted(spec["on_states"])) or "-"
        print(f"{pages:<6}{(spec['type'] or '?'):<8}{states:<22}{name}")


def require_dependencies():
    """Fail before touching the packet, not halfway through writing it."""
    missing = []
    for module, package in (("pypdf", "pypdf"), ("fitz", "pymupdf")):
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    if missing:
        sys.exit(f"missing dependencies: {' '.join(missing)}\n"
                 f"install with: pip install {' '.join(missing)}")


USAGE = ("Usage: python fill_obs_packet.py <blank_packet.pdf> <inputs.json> <output.pdf>\n"
         "       python fill_obs_packet.py --inspect <blank_packet.pdf>")


def main():
    require_dependencies()

    if len(sys.argv) == 3 and sys.argv[1] == "--inspect":
        inspect(sys.argv[2])
        return
    if len(sys.argv) != 4:
        print(USAGE)
        sys.exit(1)
    blank_pdf, inputs_path, output_pdf = sys.argv[1], sys.argv[2], sys.argv[3]

    profile = load_profile()
    with open(inputs_path) as f:
        inp = json.load(f)

    field_values = build_field_values(profile, inp)

    # Fill and annotate a scratch copy, then move it into place, so a failure
    # part-way through never leaves a half-filled packet looking finished.
    partial = output_pdf + ".partial"
    try:
        fill_acroform(blank_pdf, field_values, partial)
        add_annotations(partial, profile)
        os.replace(partial, output_pdf)
    finally:
        if os.path.exists(partial):
            os.remove(partial)

    print(f"Filled packet written to: {output_pdf}")
    print(f"Fields written: {len(field_values)}")


if __name__ == "__main__":
    main()
