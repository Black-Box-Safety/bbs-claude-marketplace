#!/usr/bin/env python3
"""Parse a Grainger priced hot list PDF, then merge live account pricing into data/hotlist.json.

Why this runs in two passes
---------------------------
Pricing an item requires the `grainger_price` MCP tool, and an MCP tool cannot be
called from inside a plain script. So the work splits:

  pass 1 (parse)  read the PDF, write the parsed CSV, and print the batched item
                  lists you paste into `grainger_price`. Save the tool's JSON.
  pass 2 (merge)  feed that JSON back in with --api-results and get hotlist.json.

Pass 1
    python3 price_hotlist.py --pdf source-hotlist-priced.pdf \\
        --account 887895160 --out programs/<project>/data

Pass 2
    python3 price_hotlist.py --pdf source-hotlist-priced.pdf \\
        --account 887895160 --out programs/<project>/data \\
        --api-results prices.json --report

Why the account price matters even though the sheet is "the deal": per-account
discounts differ, and on the reference build the account beat the sheet on 14 of
91 lines. The rep almost certainly promised the lowest price at quote time, so the
piece prints min(sheet, account) and you raise the gap with the rep. --report
prints exactly those lines.
"""

import argparse
import csv
import json
import os
import re
import subprocess
import sys

# The item column of a Grainger sheet: always starts with a digit, then letters
# and digits. Anchored so prose lines cannot masquerade as items.
ITEM_RE = re.compile(r'^([0-9][0-9A-Za-z]{1,7})\s+(\S.*?)\s*(?:\$\s*([\d,]+\.\d{2}))?$')

# A category banner is a short all-caps run. The 4-word document title
# ("CAL FIRE HOTLIST PRODUCTS") is excluded by both the length and the word cap,
# which is why those limits are here rather than being tidied away.
CAT_RE = re.compile(r'^[A-Z0-9][A-Z0-9 /&.\-]{1,23}$')

TERM_RE = re.compile(r'pric\w*\s+(is|are)\s+\w*\s*(good|valid|firm)', re.I)


def die(msg):
    sys.stderr.write('price_hotlist: %s\n' % msg)
    raise SystemExit(2)


def pdf_text(pdf_path):
    """Extract with -layout, because the column positions ARE the data here."""
    if not os.path.exists(pdf_path):
        die('no such PDF: %s' % pdf_path)
    try:
        out = subprocess.run(['pdftotext', '-layout', pdf_path, '-'],
                             capture_output=True)
    except FileNotFoundError:
        die('pdftotext not found. Install poppler (bbs-setup.ps1 on Windows; brew install poppler on macOS).')
    if out.returncode != 0:
        die('pdftotext failed on %s: %s'
            % (pdf_path, out.stderr.decode('utf-8', 'replace').strip()))
    return out.stdout.decode('utf-8', 'replace')


def money(s):
    return float(s.replace(',', ''))


def parse_half(text_half, state, out, unparsed):
    s = text_half.strip()
    if not s:
        return
    m = ITEM_RE.match(s)
    if m and not CAT_RE.match(s):
        item, desc, price = m.group(1), m.group(2).strip(), m.group(3)
        out.append({
            'item': item,
            'sheet_description': desc,
            'category': state['cat'] or '',
            'hotlist_price': ('%.2f' % money(price)) if price else '',
        })
        return
    if CAT_RE.match(s) and len(s.split()) <= 3 and '$' not in s:
        state['cat'] = s
        if s not in state['order']:
            state['order'].append(s)
        return
    unparsed.append(s)


def parse_sheet(text, split_col):
    """Split each line at split_col and read the two columns independently.

    Column position varies by sheet, which is why --split-col exists. If a run
    comes back with far too few rows, dump the pdftotext output and count the
    character offset where the right-hand item numbers begin.
    """
    left = {'cat': None, 'order': []}
    right = {'cat': None, 'order': []}
    rows, unparsed = [], []
    for line in text.split('\n'):
        parse_half(line[:split_col], left, rows, unparsed)
        parse_half(line[split_col:], right, rows, unparsed)
    cats = left['order'] + [c for c in right['order'] if c not in left['order']]
    return rows, cats, unparsed


def write_parsed_csv(rows, path):
    with open(path, 'w', newline='') as f:
        w = csv.DictWriter(
            f, fieldnames=['item', 'sheet_description', 'category', 'hotlist_price'])
        w.writeheader()
        w.writerows(rows)


def print_batches(items, account, batch_size):
    """grainger_price takes at most 48 codes per call, and `account` is required.

    Pricing against the wrong account returns a wrong number that still looks
    valid, so the account is repeated in every printed call rather than left
    implicit.
    """
    print('')
    print('Next step, in the agent session, not in this script:')
    print('call grainger_price once per batch below, then save the combined')
    print('JSON responses to a file and re-run with --api-results <file>.')
    print('')
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        print('grainger_price(account=%r, productCodes=%s)'
              % (account, json.dumps(batch)))
        print('')


def load_api_rows(path):
    """Accept whatever shape the operator saved.

    A single tool response, a list of responses (one per batch), or a bare list
    of row dicts all work. Being liberal here saves a re-run over a paste detail.
    """
    if not os.path.exists(path):
        die('no such API results file: %s' % path)
    try:
        with open(path) as f:
            blob = json.load(f)
    except ValueError as e:
        die('%s is not valid JSON: %s' % (path, e))
    payloads = blob if isinstance(blob, list) else [blob]
    rows = []
    for p in payloads:
        if isinstance(p, dict) and 'rows' in p:
            rows.extend(p['rows'])
        elif isinstance(p, dict) and 'graingerItem' in p:
            rows.append(p)
        elif isinstance(p, list):
            rows.extend(p)
        else:
            die('unrecognised entry in %s. Expected a grainger_price response '
                'object with a "rows" key, a list of them, or a list of rows.'
                % path)
    by_item = {}
    for r in rows:
        code = r.get('graingerItem')
        if not code:
            continue
        by_item[code.upper()] = r
    if not by_item:
        die('%s contained no priced rows.' % path)
    return by_item


def retarget_image(url, query):
    """Grainger's pictureUrl is a thumbnail by default.

    Re-requesting the same asset with explicit width, height and png-alpha gives
    a transparent product shot that sits on the page's cream background instead
    of a white box. Pass --img-query '' to keep the URL exactly as returned.
    """
    if not url:
        return ''
    if not query:
        return url
    base = url.split('?', 1)[0]
    return base + '?' + query


def merge(rows, api, args):
    items, notes = [], {'account_won': [], 'no_price': [], 'no_api': [],
                        'desc_mismatch': []}
    for r in rows:
        code = r['item'].upper()
        a = api.get(code)
        sheet = money(r['hotlist_price']) if r['hotlist_price'] else None
        acct = a.get('unitPrice') if a else None
        if a is None:
            notes['no_api'].append(code)

        candidates = [p for p in (sheet, acct) if p is not None]
        price = min(candidates) if candidates else None
        if price is None:
            src = ''
            notes['no_price'].append((code, r['sheet_description']))
        elif sheet is not None and acct is not None and acct < sheet:
            src = 'account'
            notes['account_won'].append((code, sheet, acct, sheet - acct))
        elif sheet is not None and price == sheet:
            src = 'sheet'
        else:
            src = 'account'

        api_desc = (a or {}).get('description') or ''
        sheet_desc = r['sheet_description']
        if api_desc and _norm(api_desc) != _norm(sheet_desc):
            notes['desc_mismatch'].append((code, sheet_desc, api_desc))
        desc = api_desc if (args.desc_source == 'api' and api_desc) else sheet_desc

        lst = (a or {}).get('listPrice')
        off = None
        if price is not None and lst:
            off = int(round(100.0 * (1.0 - price / float(lst))))

        items.append({
            'item': code,
            'desc': desc,
            'cat': r['category'],
            'price': price,
            'sheet': sheet,
            'acct': acct,
            'src': src,
            'list': lst,
            'brand': (a or {}).get('brand') or '',
            'img': retarget_image((a or {}).get('pictureUrl') or '', args.img_query),
            'off': off,
        })
    return items, notes


def _norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def report(items, notes, term_lines, unparsed):
    print('')
    print('== report ==')
    print('%d items parsed' % len(items))

    print('')
    print('Lines where the account price beat the sheet (%d).' % len(notes['account_won']))
    print('These are the ones to raise with the rep: the sheet is meant to be the')
    print('best price, so a cheaper account price is a gap in the negotiated sheet.')
    for code, sheet, acct, delta in sorted(notes['account_won'],
                                           key=lambda x: -x[3]):
        print('  %-8s sheet $%8.2f  account $%8.2f  saves $%.2f'
              % (code, sheet, acct, delta))

    print('')
    print('Items with no price at all (%d). Each is a blocker: omit the line or'
          % len(notes['no_price']))
    print('get the price. Do not invent one and do not quietly drop it.')
    for code, desc in notes['no_price']:
        print('  %-8s %s' % (code, desc))

    if notes['no_api']:
        print('')
        print('Items the pricing API did not return (%d). Usually a bad item'
              % len(notes['no_api']))
        print('number on the sheet. Check each by hand before printing it.')
        print('  ' + ', '.join(notes['no_api']))

    if notes['desc_mismatch']:
        print('')
        print('Descriptions where the sheet and the API disagree (%d).'
              % len(notes['desc_mismatch']))
        print('Most are harmless shorthand. Some are the sheet describing a')
        print('different product than the item number actually is, which is why')
        print('this list gets read rather than skimmed. Record real corrections')
        print('in the README under "Data corrections applied".')
        for code, sd, ad in notes['desc_mismatch']:
            print('  %-8s sheet: %s' % (code, sd))
            print('  %-8s api  : %s' % ('', ad))

    if term_lines:
        print('')
        print('Pricing term found in the sheet. Check the date is still in the')
        print('future. An expired or missing term is a blocker to raise, not a')
        print('number to invent.')
        for t in term_lines:
            print('  %s' % t)
    else:
        print('')
        print('No pricing term line found in the sheet. Confirm the term in')
        print('writing with the rep before any piece states one.')

    if unparsed:
        print('')
        print('Lines the parser ignored (%d). Skim for a dropped item row; if you'
              % len(unparsed))
        print('see one, the split column is probably wrong. Try --split-col.')
        for u in unparsed[:20]:
            print('  %s' % u)


def main():
    p = argparse.ArgumentParser(
        description='Parse a Grainger priced hot list PDF and merge live account '
                    'pricing into hotlist.json.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Run once without --api-results to get the parsed CSV and the '
               'grainger_price batches. Run again with --api-results to write '
               'hotlist.json.')
    p.add_argument('--pdf', required=True,
                   help='the PRICED sheet. If it has no dollar signs in it, you '
                        'have the unpriced twin; ask the rep for the priced file.')
    p.add_argument('--account', required=True,
                   help='Grainger account number or facility name to price '
                        'against, e.g. 887895160 or "CAL FIRE Headquarters". '
                        'Per-account discounts differ, so the wrong account '
                        'returns a wrong price that still looks valid.')
    p.add_argument('--out', required=True,
                   help='project data directory. Receives hotlist_official.csv '
                        'and, on the merge pass, hotlist.json.')
    p.add_argument('--api-results',
                   help='JSON saved from the grainger_price calls printed by the '
                        'first pass. Triggers the merge and writes hotlist.json.')
    p.add_argument('--split-col', type=int, default=76,
                   help='character column where the right-hand product column '
                        'begins in pdftotext -layout output (default: 76). '
                        'Column position varies by sheet.')
    p.add_argument('--batch-size', type=int, default=48,
                   help='item numbers per grainger_price call (default and '
                        'maximum: 48).')
    p.add_argument('--desc-source', choices=['api', 'sheet'], default='api',
                   help='which description to print (default: api). Sheet '
                        'descriptions are shorthand typed by a human; API '
                        'descriptions are correct and read better on a page.')
    p.add_argument('--img-query', default='wid=800&hei=800&fmt=png-alpha',
                   help='query string appended to the API pictureUrl. The '
                        'default asks for a large transparent PNG instead of the '
                        'default thumbnail. Pass an empty string to keep the URL '
                        'as returned.')
    p.add_argument('--report', action='store_true',
                   help='print the lines where the account beat the sheet, the '
                        'items with no price, and the description mismatches.')
    args = p.parse_args()

    if args.batch_size < 1 or args.batch_size > 48:
        die('--batch-size must be between 1 and 48 (the API caps at 48).')
    if not os.path.isdir(args.out):
        die('--out is not a directory: %s' % args.out)

    text = pdf_text(args.pdf)
    if '$' not in text:
        die('%s contains no dollar amounts. This looks like the unpriced twin '
            'of the sheet. Ask the rep for the priced file before going further.'
            % args.pdf)

    rows, cats, unparsed = parse_sheet(text, args.split_col)
    if not rows:
        die('parsed 0 items. Check --split-col against the pdftotext -layout '
            'output: pdftotext -layout %s - | head -40' % args.pdf)

    # Read the term off whole lines, not the split halves: a centred footer
    # straddles the column split and would otherwise be truncated mid-date.
    term_lines = [l.strip() for l in text.split('\n') if TERM_RE.search(l)]

    csv_path = os.path.join(args.out, 'hotlist_official.csv')
    write_parsed_csv(rows, csv_path)
    priced = sum(1 for r in rows if r['hotlist_price'])
    print('parsed %d items in %d categories (%d with a sheet price)'
          % (len(rows), len(cats), priced))
    print('categories: %s' % ', '.join(cats))
    print('wrote %s' % csv_path)

    if not args.api_results:
        print_batches([r['item'] for r in rows], args.account, args.batch_size)
        if args.report:
            print('')
            print('== report (parse only) ==')
            for code, desc in [(r['item'], r['sheet_description'])
                               for r in rows if not r['hotlist_price']]:
                print('  no sheet price: %-8s %s' % (code, desc))
            for t in term_lines:
                print('  pricing term: %s' % t)
        return

    api = load_api_rows(args.api_results)
    items, notes = merge(rows, api, args)
    json_path = os.path.join(args.out, 'hotlist.json')
    with open(json_path, 'w') as f:
        json.dump(items, f, indent=1)
        f.write('\n')
    print('wrote %s (%d items, account price used on %d lines)'
          % (json_path, len(items), len(notes['account_won'])))
    if args.report:
        report(items, notes, term_lines, unparsed)


if __name__ == '__main__':
    main()
