# Worked example — CMC metal detectors, 08/27/2026 (quote 900008)

The run this skill was built from. Useful as a shape reference: what the buyer
sent, what got asked, and what shipped back.

## Inbound

Email from Kelly Warnes, HCA Office Technician, California Men's Colony:

> The California Men's Colony is requesting a quotation for the following items:
> - Metal Detectors (15 Total): GARRETT METAL DETECTORS, 8 3/8 in L x 4 in W x
>   1 1/2 in H, Hand-Held Metal Detector - 1ZRZ8|1165900 - Grainger

Attached: OBS RFQ Line-Item Cost Worksheet, CalRecycle 74, DGS PD 843, Darfur
OBS 1500, OBS 1000 GenAI, Bidder Declaration GSPD-05-105. The worksheet's
pre-printed header carried the solicitation: `NASPO: 07-25-51-02.3`.

Buyer folder already held `Kelly Warnes.txt` with the Proco account
(0887895111), BC customer ID, and the ship-to address — read the buyer folder
before asking the rep for anything.

## Pricing

```
grainger_price(productCodes=["1ZRZ8"], account="CMC")
→ unitPrice 175.36, contractReferencePrice 211.28, listPrice 251.00
  discountOffContractReferencePct 17, uom EA, "Typically in Stock"
  account 887895111 · NASPO ValuePoint CA State Agency · sellRule at_cost
```

15 × $175.36 = **$2,630.40**, no markup, no tax, S&H $0.00.

## Quote

> Built 08/27/2026, before the 2026-09-28 ruling that retired the local 900001 series.
> The numbering and pricing fields below are historical: today the number is the
> Business Central SQ number read back per `bbs-quote-builder` step 2, and the spec uses
> `pricing.method "at-cost"` with `source "grainger"` on each line.

`bbs-quote-builder` spec with `pricing.method "markup"`, `rate 0`, `taxRate 0`,
`solicitation "NASPO: 07-25-51-02.3"`. Quote number 900008 — the 900001 series
was at 900007 (KVSP), and the rep confirmed the next number rather than it being
auto-assigned.

## Forms

All six filled via `scripts/fill_ca_forms.py`. Signatures: Parker on CalRecycle
74, Darfur, OBS 1000; Jackson on PD 843 (the DV-owner perjury declaration).

Things that needed a second pass, all caught by rendering the pages:

1. Worksheet line-1 description clipped at 8pt → dropped to 6.5pt and trimmed to
   "Garrett Hand-Held Metal Detector, 8-3/8 x 4 x 1-1/2 in H".
2. PD 843 rendered with **both** Section 2 radios filled — fixed by writing /AS
   per widget (now handled inside the script).
3. `SCno` and `description` on PD 843 clipped → shortened to the bare
   solicitation number and "Hand-held metal detectors, Qty 15 EA".
4. CalRecycle row 1 clipped → "RFQ NASPO 07-25-51-02.3" and a trimmed description.
5. Darfur signature landed on top of the printed caption → `dx: 150, dy: 4`.
6. GSPD `Text1` clipped "DVBE (OSDS Ref. 2009473)" → just `DVBE`.

CalRecycle values were 0% PCRC / SABRC "N/A", matching the 08/04/2026 CMC packet
for the same buyer institution and CalRecycle footnote 3 (electronics).

## Output

`~/bbs_forms/20260827_CMC_MetalDetectors/` — quote, six filled PDFs,
`cover_summary.md` — copied to
`…/CMC - 887895111 - California Men's Colony/Kelly Warnes/metal detectors naspo 8.27.26/FILLED/`.
