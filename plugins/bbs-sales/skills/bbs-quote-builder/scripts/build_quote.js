#!/usr/bin/env node
/*
 * build_quote.js — Black Box Safety Sales Quote generator (SQ-104032 format)
 *
 * Usage:
 *   node build_quote.js <spec.json> <output.docx>
 *
 * Reads a JSON spec describing the quote and emits a .docx on BBS letterhead
 * matching the SQ-104032 template. Convert to PDF separately (see SKILL.md).
 * Runs offline: it never calls Business Central and never writes anywhere but
 * <output.docx>.
 *
 * SPEC SCHEMA (see references/spec-schema.md for full detail):
 * {
 *   "bcQuote": {                                 // what the BC read-back returned
 *     "number": "SQ-104797",                     // the BC sales quote this document is
 *     "customerNumber": "C10171",
 *     "customerName": "U.S. Air Force"
 *   },
 *   "documentDate": "09/28/2026",
 *   "validTo": "10/28/2026",
 *   "shipmentMethod": "FOB Destination",        // optional, default "FOB Destination"
 *   "solicitation": "SCTASK0021599",            // optional; omit to hide the row
 *   "billTo":  ["Customer Name", "Line 2"],
 *   "shipTo":  ["Customer Name", "Street", "City, ST ZIP", "US"],
 *   "pricing": { "method": "margin", "rate": 0.20,     // "margin" | "markup" | "at-cost"
 *                "graingerAtCost": true },             // required with Grainger lines
 *                                                      // unless method is "at-cost"
 *   "taxRate": 0.0875,                          // 0 for pre-tax; omit = pre-tax
 *   "estimatedPricing": false,                  // true adds the "*" estimate footnote
 *   "columns": { "leadTime": true },            // optional Lead Time column
 *   "items": [
 *     { "partNumber": "9828588", "description": "...", "qty": 8, "uom": "Pack", "unitCost": 16.99 },
 *     { "partNumber": "1ZRZ8", "description": "...", "qty": 1, "unitCost": 175.36,
 *       "source": "grainger", "leadTime": "1-3 business days" }
 *   ]
 * }
 *
 * unitCost is the VENDOR COST. The script derives the customer Unit Price:
 *   margin:   sell = cost / (1 - rate)
 *   markup:   sell = cost * (1 + rate)
 *   at-cost:  sell = cost
 * A line with source "grainger" carries the Grainger MCP unitPrice as its cost.
 * Grainger at cost is ruled for CA state schedule / cooperative quotes only, so
 * the spec must say which applies: method "at-cost", or pricing.graingerAtCost
 * true (Grainger lines at cost) / false (Grainger lines follow the method).
 * A spec with Grainger lines that says neither is rejected.
 */

const fs = require('fs');
const path = require('path');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, WidthType, ShadingType, BorderStyle, VerticalAlign,
  ImageRun, Footer
} = require('docx');

const specPath = process.argv[2];
const outPath = process.argv[3];
if (!specPath || !outPath) {
  console.error('Usage: node build_quote.js <spec.json> <output.docx>');
  process.exit(1);
}
const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));

// ---- validation: fail loudly, never guess ----
const errors = [];
if (spec.quoteNumber !== undefined) {
  errors.push('spec has a top-level "quoteNumber". The local 900001 series is retired; the quote number is ' +
    'the Business Central SQ number, carried in "bcQuote" after reading the quote back from BC (SKILL.md step 2).');
}
const bc = spec.bcQuote || {};
if (!spec.bcQuote) {
  errors.push('"bcQuote" is missing. Read the sales quote back from Business Central and copy number, ' +
    'customerNumber and customerName from the result. No SQ number means [MISSING — NEEDS INPUT], not a guess.');
} else {
  if (!/^SQ-\d{6}$/.test(bc.number || '')) {
    errors.push('bcQuote.number "' + (bc.number || '') + '" is not a Business Central SQ number (SQ- plus six digits).');
  }
  if (!bc.customerNumber) errors.push('bcQuote.customerNumber is missing — copy it from the BC read-back.');
  if (!bc.customerName) errors.push('bcQuote.customerName is missing — copy it from the BC read-back.');
}
if (!Array.isArray(spec.items) || spec.items.length === 0) errors.push('"items" is empty or missing.');
const nonEmptyStr = v => typeof v === 'string' && v.trim() !== '';
const strLines = v => Array.isArray(v) && v.length > 0 && v.every(nonEmptyStr);
if (!nonEmptyStr(spec.documentDate)) errors.push('"documentDate" is missing — take it from the BC quote\'s documentDate.');
if (!nonEmptyStr(spec.validTo)) errors.push('"validTo" is missing — take it from the BC quote\'s validUntilDate.');
if (!strLines(spec.billTo)) errors.push('"billTo" must be a non-empty list of text lines. If the BC bill-to address is empty, ask the rep — do not print a name-only block.');
if (!strLines(spec.shipTo)) errors.push('"shipTo" must be a non-empty list of text lines.');
// Tax: a decimal, 0 <= rate < 0.2. A string, a percent (8.75) or a negative would print a
// wrong total that still looks valid.
if (spec.taxRate !== undefined && !(typeof spec.taxRate === 'number' && spec.taxRate >= 0 && spec.taxRate < 0.2)) {
  errors.push('taxRate ' + JSON.stringify(spec.taxRate) + ' is not a decimal between 0 and 0.2 (e.g. 0.0875 for 8.75%). ' +
    'Omit it or use 0 for a pre-tax quote.');
}

const METHODS = ['margin', 'markup', 'at-cost'];
const method = spec.pricing && spec.pricing.method;
const rate = spec.pricing && spec.pricing.rate;
const isGrainger = it => String(it.source || '').toLowerCase() === 'grainger';
const hasGrainger = Array.isArray(spec.items) && spec.items.some(isGrainger);
const gac = spec.pricing && spec.pricing.graingerAtCost;
if (spec.pricing && gac !== undefined && typeof gac !== 'boolean') {
  errors.push('pricing.graingerAtCost must be true or false (got ' + JSON.stringify(gac) + ').');
}
if (hasGrainger && method !== 'at-cost' && typeof gac !== 'boolean') {
  errors.push('Grainger at-cost is ruled for CA state schedules; for this quote\'s channel, state whether ' +
    'Grainger lines are at cost (pricing.graingerAtCost true/false).');
}
const graingerAtCost = method === 'at-cost' || gac === true;
const needsMethod = Array.isArray(spec.items) &&
  spec.items.some(it => !isGrainger(it) || (gac === false));
if (needsMethod) {
  if (!METHODS.includes(method)) {
    errors.push('pricing.method must be one of ' + METHODS.join(' | ') + ' (got ' + JSON.stringify(method) +
      '). Confirm it with the rep; there is no default.');
  } else if (method !== 'at-cost' && !(typeof rate === 'number' && rate >= 0 && rate < 1)) {
    // Also caps markup below 100%, so a percent typed as 20 instead of 0.20 fails here.
    errors.push('pricing.rate must be a decimal from 0 up to (not including) 1 for ' + method + ' (got ' + JSON.stringify(rate) + ').');
  }
}
(spec.items || []).forEach((it, i) => {
  if (!nonEmptyStr(it.description)) errors.push('items[' + i + '].description is missing.');
  if (typeof it.unitCost !== 'number' || !(it.unitCost >= 0)) errors.push('items[' + i + '].unitCost is not a number of 0 or more (discount lines are not supported).');
  if (typeof it.qty !== 'number' || !(it.qty > 0)) errors.push('items[' + i + '].qty is not a positive number.');
  if (it.source !== undefined && !isGrainger(it)) errors.push('items[' + i + '].source "' + it.source + '" is unknown; the only value is "grainger".');
});
if (errors.length) {
  errors.forEach(e => console.error('ERROR: ' + e));
  process.exit(1);
}
const quoteNumber = bc.number;
// The customer on the BC quote should be the one this document is addressed to.
const addrText = [].concat(spec.billTo, spec.shipTo).join(' ').toLowerCase();
if (!addrText.includes(String(bc.customerName).toLowerCase())) {
  console.error('WARNING: BC customer "' + bc.customerName + '" (' + bc.customerNumber + ') appears in neither billTo nor shipTo. ' +
    'Confirm with the rep that ' + quoteNumber + ' is the quote for this customer before sending.');
}

// ---- pricing ----
const taxRate = spec.taxRate || 0;
const estimated = !!spec.estimatedPricing;
const star = estimated ? '*' : '';
const showLead = !!(spec.columns && spec.columns.leadTime);

// Round to the cent, half up. Plain Math.round(x * 100) rounds 12.42 / 0.80 = 15.525
// down to 15.52, because 15.525 * 100 is 1552.4999999999998 in floating point.
const pct = x => (x * 100).toFixed(2).replace(/\.?0+$/, '');
const r2 = x => Math.round(Number((x * 100).toFixed(6))) / 100;

function sellPrice(it) {
  let s;
  if (method === 'at-cost' || (isGrainger(it) && graingerAtCost)) s = it.unitCost;
  else if (method === 'markup') s = it.unitCost * (1 + rate);
  else s = it.unitCost / (1 - rate);
  return r2(s);
}
const fmt = n => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

let subtotal = 0;
const rows = spec.items.map((it, i) => {
  const sell = sellPrice(it);
  const amt = r2(sell * it.qty);
  subtotal += amt;
  return {
    ln: i + 1,
    partNumber: it.partNumber || '—',
    desc: it.description,
    qty: it.qty,
    uom: it.uom || 'Each',
    lead: it.leadTime || '—',
    sell, amt
  };
});
subtotal = r2(subtotal);
const tax = r2(subtotal * taxRate);
const total = r2(subtotal + tax);

// ---- style constants ----
const BLACK = "000000";
const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const botRule = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
const logoBuf = fs.readFileSync(path.join(__dirname, '..', 'assets', 'bbs_logo.png'));

function plain(text, opts = {}) {
  return new Paragraph({ spacing: { after: opts.after || 0 }, children: [new TextRun({ text, size: opts.size || 16, bold: opts.bold || false, color: BLACK })] });
}

// ---- header: company info + logo ----
const headerTable = new Table({
  width: { size: 9360, type: WidthType.DXA }, columnWidths: [6360, 3000], borders: noBorders,
  rows: [new TableRow({ children: [
    new TableCell({ borders: noBorders, width: { size: 6360, type: WidthType.DXA }, margins: { top: 0, bottom: 0, left: 0, right: 0 }, children: [
      new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "Sales Quote - " + quoteNumber, bold: true, size: 30, color: BLACK })] }),
      plain("Black Box Safety, Inc.", { bold: true, size: 18, after: 20 }),
      plain("1950 Cordell Ct, Suite 103", { size: 16 }),
      plain("El Cajon, CA 92020-0923", { size: 16 }),
      plain("sales@blackboxsafety.com", { size: 16 }),
      plain("(619) 499-7943", { size: 16 }),
      plain("https://blackboxsafety.com/", { size: 16 }),
    ]}),
    new TableCell({ borders: noBorders, width: { size: 3000, type: WidthType.DXA }, verticalAlign: VerticalAlign.TOP, margins: { top: 0, bottom: 0, left: 0, right: 0 }, children: [
      new Paragraph({ alignment: AlignmentType.RIGHT, children: [new ImageRun({ type: "png", data: logoBuf, transformation: { width: 150, height: 170 } })] }),
      new Paragraph({ alignment: AlignmentType.RIGHT, spacing: { before: 80 }, children: [new TextRun({ text: "Page 1 / 1", bold: true, size: 15, color: BLACK })] }),
    ]}),
  ]})],
});

// ---- bill to / ship to ----
function addr(label, lines, width) {
  return new TableCell({ borders: noBorders, width: { size: width, type: WidthType.DXA }, margins: { top: 0, bottom: 0, left: 0, right: 0 }, children: [
    new Paragraph({ spacing: { after: 30 }, children: [new TextRun({ text: label, bold: true, size: 17, color: BLACK })] }),
    ...lines.map(l => new Paragraph({ spacing: { after: 10 }, children: [new TextRun({ text: l, size: 16, color: BLACK })] })),
  ]});
}
const billShipTable = new Table({
  width: { size: 9360, type: WidthType.DXA }, columnWidths: [4680, 4680], borders: noBorders,
  rows: [new TableRow({ children: [addr("Bill to", spec.billTo, 4680), addr("Ship to", spec.shipTo, 4680)] })],
});

// ---- metadata block ----
function lblVal(label, val) {
  return new TableRow({ children: [
    new TableCell({ borders: noBorders, width: { size: 2600, type: WidthType.DXA }, margins: { top: 0, bottom: 0, left: 0, right: 0 }, children: [new Paragraph({ spacing: { after: 10 }, children: [new TextRun({ text: label, bold: true, size: 16, color: BLACK })] })] }),
    new TableCell({ borders: noBorders, width: { size: 6760, type: WidthType.DXA }, margins: { top: 0, bottom: 0, left: 0, right: 0 }, children: [new Paragraph({ spacing: { after: 10 }, children: [new TextRun({ text: val, size: 16, color: BLACK })] })] }),
  ]});
}
const metaRows = [];
if (spec.solicitation) metaRows.push(lblVal("Solicitation", spec.solicitation));
metaRows.push(lblVal("Shipment Method", spec.shipmentMethod || "FOB Destination"));
metaRows.push(lblVal("Document Date", spec.documentDate));
metaRows.push(lblVal("Valid to", spec.validTo));
const shipBlock = new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [2600, 6760], borders: noBorders, rows: metaRows });

// ---- line items ----
// Widths sum to 9160. The optional Lead Time column takes its width from Description.
const LEAD_W = 1100;
const COL = showLead
  ? [450, 1500, 3160 - LEAD_W, 650, 950, LEAD_W, 1150, 1300]
  : [450, 1500, 3160, 650, 950, 1150, 1300];
function headCell(text, w, align) {
  return new TableCell({ borders: { top: noBorder, left: noBorder, right: noBorder, bottom: botRule }, width: { size: w, type: WidthType.DXA }, margins: { top: 40, bottom: 60, left: 60, right: 60 }, verticalAlign: VerticalAlign.BOTTOM, children: [new Paragraph({ alignment: align, children: [new TextRun({ text, bold: true, size: 16, color: BLACK })] })] });
}
function bodyCell(text, w, align) {
  return new TableCell({ borders: noBorders, width: { size: w, type: WidthType.DXA }, margins: { top: 50, bottom: 50, left: 60, right: 60 }, verticalAlign: VerticalAlign.TOP, children: [new Paragraph({ alignment: align, children: [new TextRun({ text, size: 15, color: BLACK })] })] });
}
const L = AlignmentType.LEFT, C = AlignmentType.CENTER, R = AlignmentType.RIGHT;
const heads = [["#", L], ["Part #", L], ["Description", L], ["Qty", C], ["UOM", C]];
if (showLead) heads.push(["Lead Time", C]);
heads.push(["Unit Price", R], ["Amount", R]);
const liHeader = new TableRow({ tableHeader: true, children: heads.map(([t, a], k) => headCell(t, COL[k], a)) });
const liRows = rows.map(r => {
  const vals = [[String(r.ln), L], [r.partNumber, L], [r.desc, L], [String(r.qty), C], [r.uom, C]];
  if (showLead) vals.push([r.lead, C]);
  vals.push([fmt(r.sell) + star, R], [fmt(r.amt) + star, R]);
  return new TableRow({ children: vals.map(([t, a], k) => bodyCell(t, COL[k], a)) });
});
const liTable = new Table({ width: { size: 9160, type: WidthType.DXA }, columnWidths: COL, borders: noBorders, rows: [liHeader, ...liRows] });

// ---- totals ----
function totalRow(label, val, opts = {}) {
  return new TableRow({ children: [
    new TableCell({ borders: noBorders, width: { size: 6010, type: WidthType.DXA }, children: [new Paragraph({ children: [new TextRun({ text: "", size: 2 })] })] }),
    new TableCell({ borders: noBorders, width: { size: 2050, type: WidthType.DXA }, margins: { top: 30, bottom: 30, left: 80, right: 80 }, children: [new Paragraph({ alignment: R, children: [new TextRun({ text: label, bold: opts.bold || false, size: 16, color: BLACK })] })] }),
    new TableCell({ borders: opts.rule ? { top: botRule, left: noBorder, right: noBorder, bottom: noBorder } : noBorders, width: { size: 1300, type: WidthType.DXA }, margins: { top: 30, bottom: 30, left: 80, right: 80 }, children: [new Paragraph({ alignment: R, children: [new TextRun({ text: val, bold: opts.bold || false, size: 16, color: BLACK })] })] }),
  ]});
}
const totalsRows = [];
if (taxRate > 0) {
  totalsRows.push(totalRow("Subtotal", fmt(subtotal), { bold: true, rule: true }));
  totalsRows.push(totalRow("Sales Tax (" + (taxRate * 100).toFixed(2).replace(/\.?0+$/, '') + "%)", fmt(tax)));
  totalsRows.push(totalRow("Total $ Incl. Tax", "$" + fmt(total), { bold: true, rule: true }));
} else {
  totalsRows.push(totalRow("Subtotal", fmt(subtotal), { bold: true, rule: true }));
  totalsRows.push(totalRow("Total $ (Pre-Tax)", "$" + fmt(subtotal), { bold: true, rule: true }));
}
const totalsTable = new Table({ width: { size: 9360, type: WidthType.DXA }, columnWidths: [6010, 2050, 1300], borders: noBorders, rows: totalsRows });

const spacer = (h = 120) => new Paragraph({ spacing: { after: h }, children: [new TextRun({ text: "", size: 2 })] });

const footer = new Footer({ children: [
  new Paragraph({ alignment: AlignmentType.CENTER, border: { top: { style: BorderStyle.SINGLE, size: 4, color: "999999", space: 4 } }, children: [new TextRun({ text: "Black Box Safety, Inc.  |  1950 Cordell Ct, Suite 103, El Cajon, CA 92020  |  (619) 499-7943  |  sales@blackboxsafety.com", size: 13, color: "666666" })] }),
]});

const children = [headerTable, spacer(160), billShipTable, spacer(160), shipBlock, spacer(200), liTable, spacer(60), totalsTable];
if (estimated) {
  children.push(spacer(160));
  children.push(new Paragraph({ children: [new TextRun({ text: "* Estimated unit pricing based on current online retail; pending confirmed vendor quotes. Subject to revision.", size: 14, italics: true, color: "666666" })] }));
}
children.push(new Paragraph({ spacing: { before: 40 }, children: [new TextRun({ text: "Quote valid through date shown. Pricing subject to product availability. Reference quote number on any resulting order.", size: 14, color: "666666" })] }));

const doc = new Document({
  styles: { default: { document: { run: { font: "Arial", size: 16 } } } },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1080, right: 1440, bottom: 1080, left: 1440 } } },
    footers: { default: footer },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log('Created ' + outPath);
  const nG = graingerAtCost ? spec.items.filter(isGrainger).length : 0;
  const nGm = spec.items.filter(isGrainger).length - nG;
  const basis = [];
  const byMethod = method === 'at-cost' ? 'at cost' : method + ' @ ' + pct(rate) + '%';
  if (nG) basis.push(nG + ' Grainger line(s) at cost');
  if (nGm) basis.push(nGm + ' Grainger line(s) ' + byMethod + ' (graingerAtCost false)');
  const nOther = spec.items.length - nG - nGm;
  if (nOther) basis.push(nOther + ' other line(s) ' + byMethod);
  console.log('Quote ' + quoteNumber + '  |  BC customer ' + bc.customerNumber + ' ' + bc.customerName);
  console.log('Pricing: ' + basis.join(', ') + '  |  Subtotal ' + fmt(subtotal) + (taxRate > 0 ? '  Tax ' + fmt(tax) + '  Total ' + fmt(total) : '  (pre-tax)'));
});
