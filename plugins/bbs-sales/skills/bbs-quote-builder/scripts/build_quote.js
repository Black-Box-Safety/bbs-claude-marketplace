#!/usr/bin/env node
/*
 * build_quote.js — Black Box Safety Sales Quote generator, Business Central print layout
 *
 * Matches the layout Business Central prints for BBS sales quotes (reference
 * SQ-104776, CAL FIRE Shasta-Trinity, 08/28/2026; Parker chose this layout on
 * 2026-09-28):
 *   - Logo top-left; "Quote - SQ-######" centered with the company block beneath
 *   - "Bill to Address" / "Ship to Address" columns
 *   - Metadata grid: Document Date / Valid to / Payment Terms | Shipment Method / Solicitation
 *   - Optional note lines under the grid
 *   - Line table: Item No. | Description | Qty | [UOM] | [Country of Origin] | [Lead Time] | Unit Price | Amount
 *   - Totals band: Subtotal | Tax % | Tax Basis | Tax Amount | Total
 *   - Optional footer notes; "Page X / Y" bottom-right
 *
 * Usage:
 *   node build_quote.js <spec.json> <output.docx>
 *
 * Runs offline: it never calls Business Central and never writes anywhere but
 * <output.docx>. Company identity (legal name, address, phone, certification)
 * is read from the bbs-sales plugin's references/vendor_profile.json, never
 * typed here. Full schema: references/spec-schema.md.
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
let docx;
try {
  docx = require('docx');
} catch (err) {
  // Only a missing package gets the install advice; a broken install is a
  // different fault and must surface as itself.
  if (err.code !== 'MODULE_NOT_FOUND' || !/'docx'/.test(err.message)) throw err;
  console.error("The 'docx' package is missing. Windows: run bbs-setup.ps1, then open a new " +
    "window / reopen VS Code. Any OS: run `npm install docx` inside " +
    path.dirname(__dirname) + " once per plugin update.");
  process.exit(1);
}
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, WidthType, ShadingType, BorderStyle, VerticalAlign,
  ImageRun, Footer
} = docx;
const { PageNumber } = docx;

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

// ---- layout-specific validation ----
const CHANNELS = ['california', 'federal', 'none'];
if (!CHANNELS.includes(spec.certChannel)) {
  errors.push('certChannel must be one of ' + CHANNELS.join(' | ') + ' (got ' + JSON.stringify(spec.certChannel) + '). ' +
    'It picks the certification line: california -> DVBE, federal (federal agencies and primes) -> SDVOSB, none -> no line. No default.');
}
// Both live on the BC quote (paymentTermsId, shipmentMethodId). No default: a typed-in
// "Net 30" or "FOB Destination" is a fact that belongs to the system of record.
if (!nonEmptyStr(spec.paymentTerms)) errors.push('"paymentTerms" is missing — look up the BC quote\'s paymentTermsId in paymentTerms; if BC has none, ask the rep.');
if (!nonEmptyStr(spec.shipmentMethod)) errors.push('"shipmentMethod" is missing — look up the BC quote\'s shipmentMethodId in shipmentMethods; if BC has none, ask the rep.');
if (spec.taxBasis !== undefined && !(typeof spec.taxBasis === 'number' && spec.taxBasis >= 0)) {
  errors.push('taxBasis ' + JSON.stringify(spec.taxBasis) + ' is not a number of 0 or more.');
}
for (const k of ['notes', 'footerNotes']) {
  if (spec[k] !== undefined && !strLines(spec[k])) errors.push(k + ', when present, must be a non-empty list of text lines.');
}
const COLS = ['uom', 'countryOfOrigin', 'leadTime'];
const cols = spec.columns || {};
Object.keys(cols).forEach(k => {
  if (!COLS.includes(k)) errors.push('columns.' + k + ' is unknown; columns are ' + COLS.join(', ') + '.');
  else if (typeof cols[k] !== 'boolean') errors.push('columns.' + k + ' must be true or false.');
});
(spec.items || []).forEach((it, i) => {
  // An origin on a federal or prime document is a certification. One without a
  // named source is a guess, and a guess there is a false certification.
  if (it.countryOfOrigin !== undefined && !(nonEmptyStr(it.countryOfOrigin) && nonEmptyStr(it.countryOfOriginSource))) {
    errors.push('items[' + i + '].countryOfOrigin needs a non-empty countryOfOriginSource naming where it is documented ' +
      '(tool result, manufacturer spec sheet, vendor quote). Without one, omit countryOfOrigin — the cell prints blank and is flagged.');
  }
  if (it.leadTime !== undefined && !nonEmptyStr(it.leadTime)) errors.push('items[' + i + '].leadTime, when present, must be text.');
  if (it.uom !== undefined && !nonEmptyStr(it.uom)) errors.push('items[' + i + '].uom, when present, must be text.');
  // No default unit: a pack price printed as "Each" is a plausible wrong number.
  if (cols.uom === true && !nonEmptyStr(it.uom)) errors.push('items[' + i + '].uom is missing and columns.uom is on — give every line its unit from the source; there is no default.');
});

// ---- company identity from vendor_profile.json (never literals) ----
// Resolved from this script's own location (skills/bbs-quote-builder/scripts -> plugin root),
// so it is always the bbs-sales plugin's profile, whichever plugin the session started in.
const pluginRoot = path.join(__dirname, '..', '..', '..');
const profilePath = path.join(pluginRoot, 'references', 'vendor_profile.json');
let vp = null;
try { vp = JSON.parse(fs.readFileSync(profilePath, 'utf8')); } catch (e) {
  errors.push('cannot read the vendor profile at ' + profilePath + ' (' + e.message + '). Company identity comes from there only.');
}
const get = (o, ks) => ks.reduce((a, k) => (a && a[k] !== undefined ? a[k] : undefined), o);
const need = ks => {
  const v = vp && get(vp, ks);
  if (vp && !nonEmptyStr(v)) errors.push('vendor_profile.json has no ' + ks.join('.') + '.');
  return v;
};
const co = {
  name: need(['business_identity', 'legal_name']),
  street: need(['address', 'mailing_street']),
  city: need(['address', 'city']),
  state: need(['address', 'state']),
  zip: need(['address', 'zip']),
  phone: need(['contact', 'phone']),
};
let certLine = null;
const warnings = [];
// "MM/DD/YYYY" or "YYYY-MM-DD" -> Date (UTC midnight), or null.
function parseDate(v) {
  let m = /^(\d{1,2})\/(\d{1,2})\/(\d{4})$/.exec(String(v || '').trim());
  if (m) return new Date(Date.UTC(+m[3], +m[1] - 1, +m[2]));
  m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(v || '').trim());
  if (m) return new Date(Date.UTC(+m[1], +m[2] - 1, +m[3]));
  return null;
}
if (spec.certChannel === 'california') {
  certLine = 'DVBE ' + need(['certifications', 'sb_dvbe', 'osds_ref_number']);
  // Never print a certification that has lapsed on the quote's own date.
  const expRaw = need(['certifications', 'sb_dvbe', 'expiration']);
  const exp = parseDate(expRaw), docDate = parseDate(spec.documentDate);
  if (expRaw && !exp) errors.push('vendor_profile.json certifications.sb_dvbe.expiration "' + expRaw + '" is not a date (MM/DD/YYYY).');
  if (nonEmptyStr(spec.documentDate) && !docDate) errors.push('documentDate "' + spec.documentDate + '" is not MM/DD/YYYY or YYYY-MM-DD, so the DVBE expiry cannot be checked.');
  if (exp && docDate) {
    const days = Math.round((exp - docDate) / 86400000);
    if (days < 0) errors.push('DVBE certification ' + certLine + ' expired ' + expRaw + ', before this quote\'s documentDate ' + spec.documentDate + '. Do not print it; renew or escalate to Parker.');
    else if (days <= 30) warnings.push('DVBE certification expires ' + expRaw + ' — ' + days + ' day(s) after this quote\'s documentDate. Tell the rep.');
  }
}
if (spec.certChannel === 'federal') certLine = need(['certifications', 'federal', 'designation']);

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
const showUom = cols.uom === true;
const showCoo = cols.countryOfOrigin === true;
const showLead = cols.leadTime === true;

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
const money = n => '$' + fmt(n);

const flags = [];
let subtotal = 0;
const rows = spec.items.map((it, i) => {
  const sell = sellPrice(it);
  const amt = r2(sell * it.qty);
  subtotal += amt;
  if (showCoo && it.countryOfOrigin === undefined) {
    flags.push('[FLAG: line ' + (i + 1) + ' (' + (it.partNumber || it.description) + ') has no documented country of origin — ' +
      'printed blank. Get it from a documented source before this goes out; never fill it by inference.]');
  }
  return {
    itemNo: it.partNumber || '—',
    desc: it.description,
    qty: it.qty,
    uom: it.uom || '',
    coo: it.countryOfOrigin || '',
    lead: it.leadTime || '—',
    sell, amt
  };
});
subtotal = r2(subtotal);
const taxBasis = typeof spec.taxBasis === 'number' ? r2(spec.taxBasis) : subtotal;
if (taxBasis > subtotal) {
  console.error('ERROR: taxBasis ' + fmt(taxBasis) + ' is more than the subtotal ' + fmt(subtotal) + '.');
  process.exit(1);
}
const tax = r2(taxBasis * taxRate);
const total = r2(subtotal + tax);
if (spec.taxBasis !== undefined && !(taxRate > 0)) warnings.push('taxBasis given but no tax rate — the basis prints but no tax is charged. Check with the rep.');
warnings.forEach(w => console.error('WARNING: ' + w));
flags.forEach(f => console.error('WARNING: ' + f));

// ---- style ----
const BLACK = '000000';
const noBorder = { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };
const rule = { style: BorderStyle.SINGLE, size: 6, color: '000000' };
const logoBuf = fs.readFileSync(path.join(__dirname, '..', 'assets', 'bbs_logo.png'));
const L = AlignmentType.LEFT, C = AlignmentType.CENTER, R = AlignmentType.RIGHT;
const PAGE_W = 9360; // 12240 page width - 1440 margin each side

function p(text, o = {}) {
  return new Paragraph({
    alignment: o.align || L,
    spacing: { after: o.after || 0, before: o.before || 0 },
    children: [new TextRun({ text, size: o.size || 18, bold: !!o.bold, italics: !!o.italics, color: o.color || BLACK })]
  });
}
function cell(children, o = {}) {
  return new TableCell({
    borders: o.borders || noBorders,
    width: { size: o.w, type: WidthType.DXA },
    margins: o.margins || { top: 0, bottom: 0, left: 0, right: 0 },
    verticalAlign: o.valign || VerticalAlign.TOP,
    children
  });
}

// ---- header: logo left, title + company block centered ----
const companyBlock = [
  p('Quote - ' + quoteNumber, { bold: true, size: 30, align: C, after: 140 }),
  p(co.name, { bold: true, size: 19, align: C, after: 70 }),
  p(co.street, { size: 17, align: C, after: 20 }),
  p(co.city + ', ' + co.state + ' ' + co.zip, { size: 17, align: C, after: 20 }),
  p(co.phone, { size: 17, align: C, after: certLine ? 20 : 0 }),
];
if (certLine) companyBlock.push(p(certLine, { size: 17, bold: true, align: C }));
const headerTable = new Table({
  width: { size: PAGE_W, type: WidthType.DXA }, columnWidths: [2600, 6760], borders: noBorders,
  rows: [new TableRow({ children: [
    cell([new Paragraph({ children: [new ImageRun({ type: 'png', data: logoBuf, transformation: { width: 150, height: 150 } })] })], { w: 2600 }),
    cell(companyBlock, { w: 6760 }),
  ]})],
});

// ---- bill to / ship to ----
function addrCell(label, lines, w) {
  return cell([p(label, { bold: true, size: 18, after: 40 }), ...lines.map(l => p(l, { size: 18, after: 20 }))], { w });
}
const billShipTable = new Table({
  width: { size: PAGE_W, type: WidthType.DXA }, columnWidths: [4680, 4680], borders: noBorders,
  rows: [new TableRow({ children: [addrCell('Bill to Address', spec.billTo, 4680), addrCell('Ship to Address', spec.shipTo, 4680)] })],
});

// ---- metadata grid: left pairs | right pairs ----
const leftMeta = [['Document Date', spec.documentDate], ['Valid to', spec.validTo]];
leftMeta.push(['Payment Terms', spec.paymentTerms]);
const rightMeta = [['Shipment Method', spec.shipmentMethod]];
if (spec.solicitation) rightMeta.push(['Solicitation', spec.solicitation]);
const metaRows = [];
for (let i = 0; i < Math.max(leftMeta.length, rightMeta.length); i++) {
  const lf = leftMeta[i] || ['', ''];
  const rg = rightMeta[i] || ['', ''];
  metaRows.push(new TableRow({ children: [
    cell([p(lf[0], { bold: true, size: 18, after: 30 })], { w: 1900 }),
    cell([p(lf[1], { size: 18, after: 30 })], { w: 2780 }),
    cell([p(rg[0], { bold: true, size: 18, after: 30 })], { w: 1900 }),
    cell([p(rg[1], { size: 18, after: 30 })], { w: 2780 }),
  ]}));
}
const metaTable = new Table({ width: { size: PAGE_W, type: WidthType.DXA }, columnWidths: [1900, 2780, 1900, 2780], borders: noBorders, rows: metaRows });

// ---- line table: optional columns take their width from Description ----
const widths = [], heads = [];
let descW = 4560;
if (showUom) descW -= 700;
if (showCoo) descW -= 1000;
if (showLead) descW -= 1100;
widths.push(1450); heads.push(['Item No.', L]);
widths.push(descW); heads.push(['Description', L]);
widths.push(700); heads.push(['Qty', C]);
if (showUom) { widths.push(700); heads.push(['UOM', C]); }
if (showCoo) { widths.push(1000); heads.push(['Country of Origin', C]); }
if (showLead) { widths.push(1100); heads.push(['Lead Time', C]); }
widths.push(1250); heads.push(['Unit Price', R]);
widths.push(1400); heads.push(['Amount', R]);

function headCell(text, w, align) {
  return new TableCell({
    borders: { top: rule, left: noBorder, right: noBorder, bottom: rule },
    width: { size: w, type: WidthType.DXA }, margins: { top: 70, bottom: 70, left: 60, right: 60 },
    verticalAlign: VerticalAlign.BOTTOM, children: [p(text, { bold: true, size: 17, align })]
  });
}
function bodyCell(text, w, align) {
  return new TableCell({
    borders: noBorders, width: { size: w, type: WidthType.DXA },
    margins: { top: 70, bottom: 70, left: 60, right: 60 }, verticalAlign: VerticalAlign.TOP,
    children: [p(text, { size: 17, align })]
  });
}
const liHeader = new TableRow({ tableHeader: true, children: heads.map((h, i) => headCell(h[0], widths[i], h[1])) });
const liRows = rows.map(r => {
  const vals = [[r.itemNo, L], [r.desc, L], [String(r.qty), C]];
  if (showUom) vals.push([r.uom, C]);
  if (showCoo) vals.push([r.coo, C]);
  if (showLead) vals.push([r.lead, C]);
  vals.push([money(r.sell) + star, R], [money(r.amt) + star, R]);
  return new TableRow({ children: vals.map(([t, a], k) => bodyCell(t, widths[k], a)) });
});
const liTable = new Table({ width: { size: PAGE_W, type: WidthType.DXA }, columnWidths: widths, borders: noBorders, rows: [liHeader, ...liRows] });

// ---- totals band ----
const bandW = [1872, 1872, 1872, 1872, 1872];
function bandCell(text, w, o = {}) {
  return new TableCell({
    borders: { top: o.top ? rule : noBorder, bottom: o.bottom ? rule : noBorder, left: noBorder, right: noBorder },
    width: { size: w, type: WidthType.DXA }, margins: { top: 90, bottom: 90, left: 40, right: 40 },
    children: [p(text, { bold: !!o.bold, size: 19, align: C })]
  });
}
const totalsTable = new Table({
  width: { size: PAGE_W, type: WidthType.DXA }, columnWidths: bandW, borders: noBorders,
  rows: [
    new TableRow({ children: ['Subtotal', 'Tax %', 'Tax Basis', 'Tax Amount', 'Total'].map((t, i) => bandCell(t, bandW[i], { bold: true, top: true })) }),
    new TableRow({ children: [money(subtotal), pct(taxRate) + '%', money(taxBasis), money(tax), money(total)].map((t, i) => bandCell(t, bandW[i], { bottom: true })) }),
  ],
});

const spacer = (h = 120) => new Paragraph({ spacing: { after: h }, children: [new TextRun({ text: '', size: 2 })] });
const footer = new Footer({ children: [
  new Paragraph({ alignment: R, children: [new TextRun({ children: ['Page ', PageNumber.CURRENT, ' / ', PageNumber.TOTAL_PAGES], bold: true, size: 16, color: BLACK })] }),
]});

const children = [headerTable, spacer(200), billShipTable, spacer(220), metaTable];
if (spec.notes) {
  children.push(spacer(120));
  spec.notes.forEach(n => children.push(p(n, { size: 17, after: 40 })));
}
children.push(spacer(200), liTable, spacer(220), totalsTable);
if (estimated) {
  children.push(spacer(160));
  children.push(p('* Estimated unit pricing based on current online retail; pending confirmed vendor quotes. Subject to revision.', { size: 15, italics: true, color: '666666' }));
}
if (spec.footerNotes) {
  children.push(spacer(140));
  spec.footerNotes.forEach(n => children.push(p(n, { size: 15, color: '666666', after: 40 })));
}

const doc = new Document({
  styles: { default: { document: { run: { font: 'Arial', size: 18 } } } },
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
  console.log('Quote ' + quoteNumber + '  |  BC customer ' + bc.customerNumber + ' ' + bc.customerName +
    '  |  Cert line: ' + (certLine || '(none)'));
  console.log('Pricing: ' + basis.join(', ') + '  |  Subtotal ' + fmt(subtotal) + '  Tax ' + fmt(tax) +
    ' (' + pct(taxRate) + '% of ' + fmt(taxBasis) + ')  Total ' + fmt(total) +
    (flags.length ? '  |  ' + flags.length + ' FLAG(s) — see WARNING lines' : ''));
});
