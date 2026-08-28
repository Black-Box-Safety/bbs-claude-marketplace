#!/usr/bin/env python3
"""Build web/index.html from web/template.html and data/hotlist.json.

Fills {{ROWS}}, {{CARDS}}, {{NAV}}, {{COUNT}}, and {{DATA}}.
Row contract: every item row carries data-item="ITEM" so the page script can
attach an Add button at runtime, and data-cat="<slug>" so the accordion script
can tie the row to its category. Columns are sku, description, thumbnail,
list, price, off. Category header rows (tr.cat) are emitted with colspan="6";
the script bumps them to 7 when it injects the Add column.
"""
import json
import os
import html

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(ROOT, '..', 'data', 'hotlist.json')
TEMPLATE_PATH = os.path.join(ROOT, 'template.html')
OUT_PATH = os.path.join(ROOT, 'index.html')

CAT_ORDER = ['FIRE TOOLS', 'PPE', 'BATTERIES', 'JAN/SAN', 'FLEET', 'MISC']
CAT_NOTE = {
    'FIRE TOOLS': 'Shelters, hand tools, handles',
    'PPE': 'Head, eye, hand, hearing',
    'BATTERIES': 'Radio and headlamp cells',
    'JAN/SAN': 'Station and camp sanitation',
    'FLEET': 'Apparatus wash and service',
    'MISC': 'Camp, marking, and light',
}
# Ordered by CAL FIRE purchase volume in the SCPRS Grainger-direct record, FY24 to FY26:
# fire shelters, laundry detergent, toilet paper, batteries, fire hoods, goggles,
# paper towels, hydration, helmets, dish detergent, hand tools, rations.
HERO = ['8FA83', '9AN11', '818G62', '10F284', '38W365', '784H63',
        '36Y133', '2U229', '9DTE3', '13W831', '794KD9', '11Z396']


# brand string -> approved mark file in web/assets (case-insensitive contains match).
# APPROVED VENDOR, CONDOR, TOUGH GUY and WESTWARD are Grainger private-label brands,
# so they carry the Grainger mark. Longest/most specific keys come first.
BRAND_LOGOS = [
    ('APPROVED VENDOR', 'grainger.png'),
    ('TOUGH GUY', 'grainger.png'),
    ('WESTWARD', 'grainger.png'),
    ('CONDOR', 'grainger.png'),
    ('GRAINGER', 'grainger.png'),
    ('ABILITY ONE', 'brand-abilityone.png'),
    ('ANCHOR INDUSTRIES', 'brand-anchor.png'),
    ('ARMOR ALL', 'brand-armorall.png'),
    ('BLUE MAGIC', 'brand-bluemagic.png'),
    ('BULLARD', 'brand-bullard.png'),
    ('CAMELBAK', 'brand-camelbak.png'),
    ('CLOROX', 'brand-clorox.png'),
    ('CORONA', 'brand-corona.png'),
    ('COUNCIL TOOL', 'brand-counciltool.png'),
    ('DEWALT', 'brand-dewalt.png'),
    ('DIVERSEY', 'brand-diversey.png'),
    ('DIXIE', 'brand-dixie.png'),
    ('EASY OFF', 'brand-easyoff.png'),
    ('ENERGIZER', 'brand-energizer.png'),
    ('FIRE-DEX', 'brand-firedex.png'),
    ('FIRST AID ONLY', 'brand-firstaidonly.png'),
    ('FINISH', 'brand-finish.png'),
    ('FRESHWAVE', 'brand-freshwave.png'),
    ('GEORGIA-PACIFIC', 'brand-gp.png'),
    ('GOJO', 'brand-gojo.png'),
    ('GUNK', 'brand-gunk.png'),
    ('HONEYWELL', 'brand-honeywell.png'),
    ('IGLOO', 'brand-igloo.png'),
    ('IMPACT', 'brand-impact.png'),
    ('KIMBERLY', 'brand-kimberly.png'),
    ('MEAL KIT SUPPLY', 'brand-mealkit.png'),
    ('MILWAUKEE', 'brand-milwaukee.png'),
    ('NICHOLSON', 'brand-nicholson.png'),
    ('PRIME GUARD', 'brand-primeguard.png'),
    ('PROCELL', 'brand-procell.png'),
    ('R & R TEXTILE', 'brand-rrtextile.png'),
    ('RUBBERMAID', 'brand-rubbermaid.png'),
    ('SANITAIRE', 'brand-sanitaire.png'),
    ('SCOTT', 'brand-kimberly.png'),
    ('SEYMOUR', 'brand-seymour.png'),
    ('SIMPLE GREEN', 'brand-simplegreen.png'),
    ('SNAPLIGHT', 'brand-snaplight.png'),
    ('STREAMLIGHT', 'brand-streamlight.png'),
    ('TIDE', 'brand-tide.png'),
    ('TURTLE WAX', 'brand-turtlewax.png'),
    ('VP SMALL ENGINE FUELS', 'brand-vpracing.png'),
    ('WINDEX', 'brand-windex.png'),
    ('3M', 'brand-3m.png'),
    ('ESS', 'brand-ess.png'),
]


def brand_logo(brand):
    b = (brand or '').upper()
    for key, fname in BRAND_LOGOS:
        if key in b:
            return fname
    return None


def _png_size(path):
    """Width and height from a PNG IHDR, no third-party imaging library."""
    import struct
    with open(path, 'rb') as f:
        head = f.read(24)
    return struct.unpack('>II', head[16:24])


def chip_class(fname):
    """Near-square marks read as a smear at 15px, so they get a taller box."""
    try:
        w, h = _png_size(os.path.join(ROOT, 'assets', fname))
    except Exception:
        return 'brchip'
    return 'brchip sq' if h and (w / float(h)) < 2.0 else 'brchip'


def slug(cat):
    return cat.lower().replace('/', '-').replace(' ', '-')


def money(n):
    return '${:,.2f}'.format(n)


def esc(s):
    return html.escape(str(s or ''), quote=True)


def row(it, cat_slug):
    price = it.get('price')
    if price is None:
        l = '<td class="l"></td>'
        p = '<td class="p"><span class="na">on request</span></td>'
        o = '<td class="o"><span class="off na">n/a</span></td>'
    else:
        lst = it.get('list')
        l = '<td class="l">' + ('<s>%s</s>' % money(lst) if lst else '') + '</td>'
        p = '<td class="p">%s</td>' % money(price)
        off = it.get('off')
        o = ('<td class="o"><span class="off">%d%%</span></td>' % off) if off \
            else '<td class="o"><span class="off na">n/a</span></td>'
    img = it.get('img')
    if img:
        im = ('<td class="im"><span class="thumb">'
              '<img loading="lazy" src="%s" alt=""></span></td>' % esc(img))
    else:
        im = '<td class="im"></td>'
    logo = brand_logo(it.get('brand'))
    if logo:
        br = ('<span class="br">%s<span class="%s">'
              '<img loading="lazy" src="assets/%s" alt=""></span></span>'
              % (esc(it.get('brand')), chip_class(logo), logo))
    else:
        br = '<span class="br">%s</span>' % esc(it.get('brand'))
    return ('<tr data-item="%s" data-cat="%s"><td class="sku">%s</td>'
            '<td class="d"><span class="dn">%s</span>%s</td>'
            '%s%s%s%s</tr>' % (esc(it['item']), esc(cat_slug), esc(it['item']),
                               esc(it['desc']), br, im, l, p, o))


def build_rows(items):
    out = []
    for cat in CAT_ORDER:
        group = [x for x in items if x['cat'] == cat]
        group.sort(key=lambda x: (x.get('price') is None, -(x.get('price') or 0)))
        out.append('<tr class="cat" id="%s"><th colspan="6">'
                   '<span class="catname">%s</span>'
                   '<span class="catnote">%s</span>'
                   '<span class="catcount">%d items</span></th></tr>'
                   % (slug(cat), esc(cat), esc(CAT_NOTE[cat]), len(group)))
        out.extend(row(it, slug(cat)) for it in group)
    return ''.join(out)


def build_units():
    import json as _j
    data = _j.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'units.json')))
    opts = ''.join('<option value="CAL FIRE %s"></option>' % esc(u['n']) for u in data)
    m = {('CAL FIRE ' + u['n']): u['a'] for u in data}
    return opts, ('<script type="application/json" id="units-data">%s</script>'
                  % _j.dumps(m).replace('</', '<\\/'))


def build_cards(items):
    by = {x['item']: x for x in items}
    out = []
    for code in HERO:
        it = by[code]
        out.append('<article class="card">'
                   '<div class="ph"><img loading="lazy" src="%s" alt="%s"></div>'
                   '<div class="cb"><span class="cbrand">%s</span><h3>%s</h3>'
                   '<div class="cp"><span class="cnum">%s</span>'
                   '<span class="cwas">list %s</span></div>'
                   '<span class="csku">Grainger item %s</span>'
                   '<button type="button" class="cardadd" data-item="%s">'
                   'Add to quote</button></div></article>'
                   % (esc(it.get('img')), esc(it['desc']), esc(it.get('brand')),
                      esc(it['desc']), money(it['price']), money(it['list']),
                      esc(code), esc(code)))
    return ''.join(out)


def build_nav():
    return ''.join('<a href="#%s">%s</a>' % (slug(c), esc(c)) for c in CAT_ORDER)


def build_data(items):
    compact = [{'item': x['item'], 'desc': x['desc'],
                'brand': x.get('brand') or '', 'price': x.get('price'),
                'uom': x.get('uom') or 'EA', 'uomQty': x.get('uomQty') or 1}
               for x in items]
    # keep the JSON safe inside a <script> element
    return json.dumps(compact, separators=(',', ':')).replace('</', '<\\/')


def main():
    with open(DATA_PATH) as f:
        items = json.load(f)
    with open(TEMPLATE_PATH) as f:
        tpl = f.read()
    out = (tpl.replace('{{ROWS}}', build_rows(items))
              .replace('{{CARDS}}', build_cards(items))
              .replace('{{UNITS}}', build_units()[0])
              .replace('</body>', build_units()[1] + '</body>')
              .replace('{{NAV}}', build_nav())
              .replace('{{COUNT}}', str(len(items)))
              .replace('{{DATA}}', build_data(items)))
    for marker in ('{{ROWS}}', '{{CARDS}}', '{{NAV}}', '{{COUNT}}', '{{DATA}}'):
        assert marker not in out, 'unfilled placeholder ' + marker
    with open(OUT_PATH, 'w') as f:
        f.write(out)
    print('wrote %s (%d bytes, %d items)' % (OUT_PATH, len(out), len(items)))


if __name__ == '__main__':
    main()
