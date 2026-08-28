# CA state agency registry

Grainger/Proco account numbers are carried in the institution folder names under
`Customers/State of CA Agencies/All RFQ's by Agency/`. Pricing is per account, so
this table is the difference between a correct quote and a plausible wrong one.

**The folder name is a starting point, not gospel.** A buyer note inside the folder
can name a different account for their specific site — CMD's folder says
`887895101` while Jess Payne at Camp San Luis Obispo buys on `888567361`. When the
folder and the note disagree, the note wins; it came from the buyer.

Refresh this table with `scripts/mine_precedents.py` after a batch of new RFQs.

## CDCR

| Institution | Grainger account |
|---|---|
| CMC — California Men's Colony (San Luis Obispo) | 887895111 |
| CCWF — Central California Women's Facility | 887895136 |
| CTC — Richard A. McGee Correctional Training Center | 887895107 |
| Calipatria State Prison | 887895116 |
| Centinela State Prison | 887895118 |
| SATF — Substance Abuse Treatment Facility | 887895131 |
| SVSP — Salinas Valley State Prison | 887895125 |
| Office of Correctional Safety (OCS) | 887882892 |
| KVSP — Kern Valley State Prison | folder carries no number — check the buyer note |
| CIM — California Institution for Men | check buyer note |
| CCHCS — Correctional Health Care Services | check buyer note |
| MCSP — Mule Creek State Prison | check buyer note |

## Hospitals, homes, and academies

| Institution | Grainger account |
|---|---|
| DSH Patton | 887895141 |
| DSH Metro | 887895142 |
| DSH Napa | 887895143 |
| DSH Atascadero | 887895144 |
| DSH Coalinga | 887895145 |
| VHC Yountville | 887895148 |
| VHC Barstow | 887895149 |
| VHC West LA | 887895151 |
| VHC Lancaster | 887895153 |
| VHC Redding | 887895155 |
| VHC Chula Vista / VHC HQ | no number on folder — check buyer note |
| PDC — Porterville Developmental Center | 887895140 (BC C10110) |
| Cal Fire Academy | 887895159 |
| Cal Fire HQ | 887895160 |
| Cal Fire SHU | 888793132 |
| Cal Fire Atwater TC | check buyer note |
| LA County Fire Dept | 888625138 |

## Departments

| Agency | Grainger account |
|---|---|
| CARB — Air Resources Board | 888161763 |
| CDFA — Food and Agriculture | 888087098 |
| CDFW — Fish & Wildlife | 887895157 |
| CHP (SSU, Southern Division, Tactical Units) | 887895146 |
| CMD — California Military Department | 887895101 (Camp SLO buys on 888567361) |
| Caltrans District 11 — San Diego | 887943233 (BC C10109) |
| Caltrans District 5 | 888139044 |
| DMV Simi Valley (also serves Winnetka) | 887902525 |
| DWR — Water Resources | 887902531 |
| DGS, DOJ (BFS Fresno, BI FEP Commerce), DOR, DTSC, DCA/DOI, DCC, CNRA, CWB | no Proco on file — confirm with the buyer before pricing |

## Contract vehicles seen

- **NASPO ValuePoint 07-25-51-02.3** — CA State Agency MRO. The default for CDCR,
  CalVet, DSH, and most department buys. Sell rule `at_cost`, track VSBAA.
- **CA DGS BPO** — sub-track VSBUE. Different track, same at-cost rule.
- Some buyers issue no solicitation number at all and simply email an item list.
  Reference the BBS quote number on the certs in that case, and say so in the
  cover summary rather than leaving the field blank.

## Buyer notes

Most buyer folders hold a `<Buyer Name>.txt` with title, email, phone, Grainger
Proco, BC customer ID, and previous ship-to addresses. Read it before asking the
rep anything — it usually holds the ship-to that decides freight and the account
that decides price. Some are empty; those buyers are worth a note after the next
order.
