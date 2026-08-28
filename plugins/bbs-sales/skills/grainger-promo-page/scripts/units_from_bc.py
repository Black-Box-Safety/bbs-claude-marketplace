#!/usr/bin/env python3
"""Turn Business Central customer records into data/units.json for the unit picker.

Why the unit picker exists
--------------------------
The quote form asks for a delivery address. Agency buyers abandon forms when they
have to type one, and a typed address is also the field they get wrong. BC already
holds every ship-to the agency has ever used, so the picker offers those and
autofills the address. That is the whole reason this script exists.

Why it runs in two passes
-------------------------
`bc_query_entity` is an MCP tool and a plain script cannot call it. So:

  pass 1  run with no --input. It prints the exact call to make.
  pass 2  save the tool's JSON, then re-run with --input <file> --out data/units.json

    python3 units_from_bc.py --agency "CAL FIRE"
    python3 units_from_bc.py --agency "CAL FIRE" --input bc.json \\
        --out programs/<project>/data/units.json

Output shape, which is what web/build.py reads:

    [{"n": "Butte Unit", "a": "176 Nelson Ave, Oroville, CA 95965"}, ...]

`n` is the unit name with the agency prefix stripped, because the page prints
"CAL FIRE " itself and the picker should not read "CAL FIRE CAL FIRE Butte Unit".
"""

import argparse
import json
import os
import re
import sys

SELECT = 'number,displayName,addressLine1,addressLine2,city,state,postalCode'


def die(msg):
    sys.stderr.write('units_from_bc: %s\n' % msg)
    raise SystemExit(2)


def print_call(agency, top):
    """BC text search is case sensitive, so the agency string must match the

    casing actually stored on the customer records. If the call comes back empty,
    try bc_find_customer first to see how the name is really spelled.
    """
    print('Run this in the agent session, then save the JSON response:')
    print('')
    print('bc_query_entity(')
    print('    entitySet="customers",')
    print('    filter="startswith(displayName,\'%s\')",' % agency)
    print('    select="%s",' % SELECT)
    print('    orderby="displayName",')
    print('    top=%d,' % top)
    print(')')
    print('')
    print('Notes worth knowing before you read the result:')
    print('  Business Central text matching is CASE SENSITIVE. "cal fire" returns')
    print('  nothing. If this comes back empty, resolve the real spelling with')
    print('  bc_find_customer and re-run with that exact string.')
    print('  The call returns at most 200 records and reports has_more and')
    print('  next_skip. If has_more is true, page with skip=<next_skip> and')
    print('  concatenate the responses into one JSON list before feeding it back.')
    print('')
    print('Then: %s --agency %r --input <saved.json> --out <project>/data/units.json'
          % (os.path.basename(sys.argv[0]), agency))


def load_records(path):
    """Accept a raw tool response, a list of responses, or a bare list of records."""
    if not os.path.exists(path):
        die('no such input file: %s' % path)
    try:
        with open(path) as f:
            blob = json.load(f)
    except ValueError as e:
        die('%s is not valid JSON: %s' % (path, e))
    payloads = blob if isinstance(blob, list) else [blob]
    recs = []
    for p in payloads:
        if isinstance(p, dict):
            for key in ('value', 'records', 'rows', 'data'):
                if isinstance(p.get(key), list):
                    recs.extend(p[key])
                    break
            else:
                if 'displayName' in p:
                    recs.append(p)
                else:
                    die('unrecognised object in %s. Expected a bc_query_entity '
                        'response with a "value" list, or a list of customer '
                        'records.' % path)
        elif isinstance(p, list):
            recs.extend(p)
        else:
            die('unrecognised entry in %s.' % path)
    if not recs:
        die('%s contained no customer records.' % path)
    return recs


def one_line_address(rec):
    """Street, optional suite, then city, state ZIP.

    Kept on one line because the picker writes it straight into a single form
    field and into the printed quote header.
    """
    street = (rec.get('addressLine1') or '').strip()
    suite = (rec.get('addressLine2') or '').strip()
    city = (rec.get('city') or '').strip()
    state = (rec.get('state') or '').strip()
    zipc = (rec.get('postalCode') or '').strip()
    head = ', '.join([p for p in (street, suite) if p])
    tail = ' '.join([p for p in (state, zipc) if p])
    tail = ', '.join([p for p in (city, tail) if p])
    return ', '.join([p for p in (head, tail) if p])


def strip_prefix(name, agency):
    """Remove the agency prefix and any separator left behind by it."""
    n = (name or '').strip()
    if agency and n.upper().startswith(agency.upper()):
        n = n[len(agency):]
    n = re.sub(r'^[\s,:/\-]+', '', n)
    return n.strip() or (name or '').strip()


def build(recs, agency):
    units, skipped, seen = [], [], set()
    for r in recs:
        if not (r.get('addressLine1') or '').strip():
            # No street address means the picker would autofill nothing, which is
            # worse than not offering the unit at all.
            skipped.append(r.get('displayName') or r.get('number') or '?')
            continue
        name = strip_prefix(r.get('displayName'), agency)
        key = (name, one_line_address(r))
        if key in seen:
            continue
        seen.add(key)
        units.append({'n': name, 'a': one_line_address(r)})
    units.sort(key=lambda u: u['n'].lower())
    return units, skipped


def main():
    p = argparse.ArgumentParser(
        description='Print the Business Central query for an agency\'s ship-to '
                    'addresses, then turn its JSON response into data/units.json.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Run with no --input to get the call. Run again with --input to '
               'write units.json.')
    p.add_argument('--agency', required=True,
                   help='customer name prefix as stored in Business Central, '
                        'e.g. "CAL FIRE". Matching is case sensitive.')
    p.add_argument('--input',
                   help='JSON saved from the bc_query_entity call printed by the '
                        'first pass.')
    p.add_argument('--out',
                   help='path to write units.json. Required with --input.')
    p.add_argument('--top', type=int, default=200,
                   help='page size for the printed query, 1 to 200 (default: 200).')
    args = p.parse_args()

    if args.top < 1 or args.top > 200:
        die('--top must be between 1 and 200 (Business Central caps at 200).')

    if not args.input:
        print_call(args.agency, args.top)
        return

    if not args.out:
        die('--out is required with --input.')
    out_dir = os.path.dirname(os.path.abspath(args.out))
    if not os.path.isdir(out_dir):
        die('output directory does not exist: %s' % out_dir)

    recs = load_records(args.input)
    units, skipped = build(recs, args.agency)
    if not units:
        die('every record was missing addressLine1, so there is nothing to pick '
            'from. Check the query selected the address fields.')
    with open(args.out, 'w') as f:
        f.write('[\n')
        f.write(',\n'.join(json.dumps(u, separators=(',', ':')) for u in units))
        f.write('\n]\n')
    print('wrote %s (%d units)' % (args.out, len(units)))
    if skipped:
        print('skipped %d records with no street address: %s'
              % (len(skipped), ', '.join(skipped[:12])))
        print('If a unit you need is on that list, its BC record needs the '
              'address filled in rather than the address being typed here.')


if __name__ == '__main__':
    main()
