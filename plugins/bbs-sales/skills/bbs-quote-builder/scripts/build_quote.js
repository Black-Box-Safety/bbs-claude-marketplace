#!/usr/bin/env node
/*
 * build_quote.js — Black Box Safety Sales Quote generator (SQ-104032 format)
 *
 * Usage:
 *   node build_quote.js <spec.json> <output.docx>
 *
 * Reads a JSON spec describing the quote and emits a .docx on BBS letterhead
 * matching the SQ-104032 template. Convert to PDF separately (see SKILL.md).
 *
 * SPEC SCHEMA (see references/spec-schema.md for full detail):
 * {
 *   "quoteNumber": "900003",
 *   "documentDate": "06/04/2026",
 *   "validTo": "07/31/2026",
 *   "shipmentMethod": "FOB Destination",        // optional, default "FOB Destination"
 *   "solicitation": "SCTASK0021599",            // optional; omit to hide the row
 *   "billTo":  ["Customer Name", "Line 2"],
 *   "shipTo":  ["Customer Name", "Street", "City, ST ZIP", "US"],
 *   "pricing": { "method": "margin", "rate": 0.20 },  // method: "margin" | "markup"
 *   "taxRate": 0.0875,                          // 0 for pre-tax; omit = pre-tax
 *   "estimatedPricing": false,                  // true adds the "*" estimate footnote
 *   "items": [
 *     { "partNumber": "9828588", "description": "...", "qty": 8, "uom": "Pack", "unitCost": 16.99 }
 *   ]
 * }
 *
 * unitCost is the VENDOR COST. The script applies the markup/margin to derive
 * the customer Unit Price:
 *   margin:  sell = cost / (1 - rate)
 *   markup:  sell = cost * (1 + rate)
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

// ---- pricing ----
const method = (spec.pricing && spec.pricing.method) || 'margin';
const rate = (spec.pricing && typeof spec.pricing.rate === 'number') ? spec.pricing.rate : 0.20;
const taxRate = typeof spec.taxRate === 'number' ? spec.taxRate : 0;
const estimated = !!spec.estimatedPricing;
const star = estimated ? '*' : '';

function sellPrice(cost) {
  const s = method === 'markup' ? cost * (1 + rate) : cost / (1 - rate);
  return Math.round(s * 100) / 100;
}
const fmt = n => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

let subtotal = 0;
const rows = spec.items.map((it, i) => {
  const sell = sellPrice(it.unitCost);
  const amt = Math.round(sell * it.qty * 100) / 100;
  subtotal += amt;
  return {
    ln: i + 1,
    partNumber: it.partNumber || '—',
    desc: it.description,
    qty: it.qty,
    uom: it.uom || 'Each',
    sell, amt
  };
});
subtotal = Math.round(subtotal * 100) / 100;
const tax = Math.round(subtotal * taxRate * 100) / 100;
const total = Math.round((subtotal + tax) * 100) / 100;

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
      new Paragraph({ spacing: { after: 40 }, children: [new TextRun({ text: "Sales Quote - " + spec.quoteNumber, bold: true, size: 30, color: BLACK })] }),
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
const COL = [450, 1500, 3160, 650, 950, 1150, 1300]; // = 9160
function headCell(text, w, align) {
  return new TableCell({ borders: { top: noBorder, left: noBorder, right: noBorder, bottom: botRule }, width: { size: w, type: WidthType.DXA }, margins: { top: 40, bottom: 60, left: 60, right: 60 }, verticalAlign: VerticalAlign.BOTTOM, children: [new Paragraph({ alignment: align, children: [new TextRun({ text, bold: true, size: 16, color: BLACK })] })] });
}
function bodyCell(text, w, align) {
  return new TableCell({ borders: noBorders, width: { size: w, type: WidthType.DXA }, margins: { top: 50, bottom: 50, left: 60, right: 60 }, verticalAlign: VerticalAlign.TOP, children: [new Paragraph({ alignment: align, children: [new TextRun({ text, size: 15, color: BLACK })] })] });
}
const L = AlignmentType.LEFT, C = AlignmentType.CENTER, R = AlignmentType.RIGHT;
const liHeader = new TableRow({ tableHeader: true, children: [
  headCell("#", COL[0], L), headCell("Part #", COL[1], L), headCell("Description", COL[2], L),
  headCell("Qty", COL[3], C), headCell("UOM", COL[4], C), headCell("Unit Price", COL[5], R), headCell("Amount", COL[6], R),
]});
const liRows = rows.map(r => new TableRow({ children: [
  bodyCell(String(r.ln), COL[0], L), bodyCell(r.partNumber, COL[1], L), bodyCell(r.desc, COL[2], L),
  bodyCell(String(r.qty), COL[3], C), bodyCell(r.uom, COL[4], C),
  bodyCell(fmt(r.sell) + star, COL[5], R), bodyCell(fmt(r.amt) + star, COL[6], R),
]}));
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
  console.log('Pricing: ' + method + ' @ ' + (rate * 100) + '%  |  Subtotal ' + fmt(subtotal) + (taxRate > 0 ? '  Tax ' + fmt(tax) + '  Total ' + fmt(total) : '  (pre-tax)'));
});
