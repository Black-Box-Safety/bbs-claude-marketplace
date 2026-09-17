#!/usr/bin/env python3
"""Render the 1200x630 Open Graph preview card with headless Chrome.

Why Chrome and not an image library
-----------------------------------
The card has to be set in the brand faces (Oswald display, Inter body, JetBrains
Mono for numbers). Compositing it with PIL means either shipping font files or
substituting a face, and a substituted face on a preview card is the tell that
makes the link look like spam. Chrome loads the real webfonts and renders the
same box model the page uses, so the card and the page agree.

Why the card matters at all
---------------------------
The page gets opened from an email. Without og:image the link renders in Outlook
as a bare URL, which reads as a link someone pasted rather than a piece of work.

    python3 make_og.py \\
        --title "H2 2026 contract sheet" \\
        --dek "Shelters, line tools, helmets, batteries, station sanitation." \\
        --tag-items 91 \\
        --vehicle "California MRO Statewide LPA 7-25-51-02.03" \\
        --cert "CA DVBE Cert. 2009473" \\
        --lpa "No solicitation to run" \\
        --photos a.jpg,b.jpg,c.jpg \\
        --logos bbs-logo-white.png \\
        --out web/assets/og-contract-sheet.jpg

Every string you pass is published copy. It goes through brand/CLAIMS.md and
brand/VOICE.md like any other line: no em dashes, sentence case, and no vehicle
number or credential that is not registered in its approved wording.
"""

import argparse
import base64
import mimetypes
import os
import shutil
import subprocess
import sys
import tempfile

CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'

# Brand tokens. These are the page's tokens, repeated here so the card and the
# page cannot drift apart silently.
TOKENS = {
    'crimson': '#9E1B1E',
    'ember': '#C8242C',
    'charcoal': '#14181D',
    'cream': '#F4EFE6',
    'hivis': '#FFC42E',
}

W, H = 1200, 630


def die(msg):
    sys.stderr.write('make_og: %s\n' % msg)
    raise SystemExit(2)


def find_chrome(explicit):
    candidates = [
        explicit,
        os.environ.get('CHROME'),
        CHROME,
        shutil.which('google-chrome'),
        shutil.which('google-chrome-stable'),
        shutil.which('chromium'),
        shutil.which('chromium-browser'),
        shutil.which('chrome'),
        shutil.which('chrome.exe'),
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
        os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
        os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    die('Google Chrome not found. Install Chrome (bbs-setup.ps1 installs it on '
        'Windows), or pass --chrome with the path to a Chrome or Chromium binary. '
        'Headless Chrome is what loads the brand webfonts, so there is no fallback '
        'renderer here.')


def data_uri(path):
    """Inline every image.

    Chrome headless loading file:// subresources from a temp directory is fragile
    across versions, and a silently missing photo produces a card that looks
    deliberate and is wrong. Inlining fails loudly instead.
    """
    if not os.path.exists(path):
        die('image not found: %s' % path)
    mime = mimetypes.guess_type(path)[0] or 'image/png'
    with open(path, 'rb') as f:
        return 'data:%s;base64,%s' % (mime, base64.b64encode(f.read()).decode())


def split_list(s):
    return [p.strip() for p in (s or '').split(',') if p.strip()]


def esc(s):
    return (str(s or '').replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;').replace('"', '&quot;'))


def build_html(args):
    photos = [data_uri(p) for p in split_list(args.photos)]
    logos = [data_uri(p) for p in split_list(args.logos)]

    collage = ''.join(
        '<div class="ph" style="background-image:url(%s)"></div>' % u
        for u in photos)
    logo_row = ''.join('<img class="lg" src="%s" alt="">' % u for u in logos)

    chips = []
    if args.tag_items:
        chips.append('<span class="chip num">%s line items</span>'
                     % esc(args.tag_items))
    if args.vehicle:
        chips.append('<span class="chip">%s</span>' % esc(args.vehicle))
    if args.cert:
        chips.append('<span class="chip cert">%s</span>' % esc(args.cert))
    if args.lpa:
        chips.append('<span class="chip">%s</span>' % esc(args.lpa))

    return """<!doctype html>
<html><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@600;700&display=swap" rel="stylesheet">
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{width:%(W)dpx;height:%(H)dpx;overflow:hidden}
  body{background:%(charcoal)s;color:%(cream)s;
       font-family:Inter,system-ui,sans-serif;position:relative}
  .collage{position:absolute;inset:0;display:grid;
           grid-template-columns:repeat(%(ncol)d,1fr)}
  .ph{background-size:cover;background-position:center;filter:saturate(.85)}
  .wash{position:absolute;inset:0;
        background:linear-gradient(103deg,%(charcoal)s 0%%,rgba(20,24,29,.94) 46%%,
                   rgba(158,27,30,.82) 100%%)}
  .edge{position:absolute;left:0;top:0;bottom:0;width:14px;background:%(crimson)s}
  .rule{position:absolute;left:0;right:0;bottom:0;height:8px;background:%(hivis)s}
  .body{position:absolute;inset:0;padding:64px 72px 72px 86px;
        display:flex;flex-direction:column;justify-content:space-between}
  .top{display:flex;align-items:center;gap:26px}
  .lg{height:38px;width:auto;object-fit:contain}
  h1{font-family:Oswald,Impact,sans-serif;font-weight:600;font-size:66px;
     line-height:1.02;letter-spacing:.4px;max-width:15ch}
  .dek{margin-top:18px;font-size:25px;line-height:1.38;max-width:30ch;
       color:rgba(244,239,230,.9)}
  .chips{display:flex;flex-wrap:wrap;gap:12px}
  .chip{font-size:17px;font-weight:600;letter-spacing:.2px;padding:10px 16px;
        border-radius:4px;background:rgba(244,239,230,.12);
        border:1px solid rgba(244,239,230,.24)}
  .chip.num{font-family:'JetBrains Mono',ui-monospace,monospace;
            background:%(ember)s;border-color:%(ember)s;color:#fff}
  .chip.cert{background:%(cream)s;color:%(charcoal)s;border-color:%(cream)s}
</style></head>
<body>
  <div class="collage">%(collage)s</div>
  <div class="wash"></div><div class="edge"></div><div class="rule"></div>
  <div class="body">
    <div class="top">%(logos)s</div>
    <div>
      <h1>%(title)s</h1>
      <p class="dek">%(dek)s</p>
    </div>
    <div class="chips">%(chips)s</div>
  </div>
</body></html>""" % {
        'W': W, 'H': H, 'ncol': max(1, len(photos)),
        'collage': collage, 'logos': logo_row,
        'title': esc(args.title), 'dek': esc(args.dek),
        'chips': ''.join(chips), **TOKENS}


def render(chrome, html_path, png_path):
    """--virtual-time-budget holds the render open until the webfonts land.

    Without it Chrome screenshots the first paint and the card ships in the
    fallback face, which is exactly the failure this script exists to avoid.
    """
    cmd = [chrome, '--headless=new', '--disable-gpu', '--hide-scrollbars',
           '--force-device-scale-factor=1',
           '--window-size=%d,%d' % (W, H),
           '--screenshot=%s' % png_path,
           '--virtual-time-budget=8000',
           'file://' + html_path]
    proc = subprocess.run(cmd, capture_output=True)
    if not os.path.exists(png_path) or os.path.getsize(png_path) == 0:
        die('Chrome produced no screenshot.\n%s'
            % proc.stderr.decode('utf-8', 'replace').strip()[:2000])


def to_jpeg(png_path, out_path, quality):
    """JPEG at 82 because the card is photographic and PNG at this size runs
    past what some mail clients will fetch before giving up on the preview."""
    if shutil.which('sips') is None:
        die('sips not found. It ships with macOS. On another platform, convert '
            '%s to JPEG yourself.' % png_path)
    proc = subprocess.run(
        ['sips', '-s', 'format', 'jpeg', '-s', 'formatOptions', str(quality),
         png_path, '--out', out_path], capture_output=True)
    if proc.returncode != 0 or not os.path.exists(out_path):
        die('sips failed to convert the screenshot: %s'
            % proc.stderr.decode('utf-8', 'replace').strip())


def main():
    p = argparse.ArgumentParser(
        description='Render a 1200x630 Open Graph preview card in the brand '
                    'typefaces using headless Chrome.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='Every string passed here is published copy and is subject to '
               'brand/CLAIMS.md and brand/VOICE.md.')
    p.add_argument('--title', required=True,
                   help='card headline. Sentence case, no em dashes.')
    p.add_argument('--dek', default='',
                   help='one supporting line under the headline.')
    p.add_argument('--tag-items', default='',
                   help='item count for the numeric chip, e.g. 91. Printed as '
                        '"<n> line items".')
    p.add_argument('--vehicle', default='',
                   help='contract vehicle, in its approved CLAIMS.md wording.')
    p.add_argument('--cert', default='',
                   help='credential, in its approved CLAIMS.md wording.')
    p.add_argument('--lpa', default='',
                   help='one short supporting chip, e.g. the no-solicitation line.')
    p.add_argument('--photos', default='',
                   help='comma separated image paths for the background collage. '
                        'Manufacturer lifestyle shots only. Never an agency photo '
                        'and never uniforms, patches or badges.')
    p.add_argument('--logos', default='',
                   help='comma separated image paths for the top-left lockup. '
                        'Every third-party mark needs a row in '
                        'brand/assets/ASSETS.md before it ships.')
    p.add_argument('--out', required=True, help='output .jpg path.')
    p.add_argument('--quality', type=int, default=82,
                   help='JPEG quality passed to sips (default: 82).')
    p.add_argument('--chrome', default='',
                   help='path to a Chrome or Chromium binary if it is not at %s'
                        % CHROME)
    p.add_argument('--keep-html', action='store_true',
                   help='keep the temporary HTML and print its path, for tuning '
                        'the layout in a real browser.')
    args = p.parse_args()

    chrome = find_chrome(args.chrome)
    out_dir = os.path.dirname(os.path.abspath(args.out))
    if not os.path.isdir(out_dir):
        die('output directory does not exist: %s' % out_dir)

    html = build_html(args)
    tmp = tempfile.mkdtemp(prefix='bbs-og-')
    html_path = os.path.join(tmp, 'card.html')
    png_path = os.path.join(tmp, 'card.png')
    with open(html_path, 'w') as f:
        f.write(html)

    render(chrome, html_path, png_path)
    to_jpeg(png_path, args.out, args.quality)
    print('wrote %s (%d bytes, %dx%d)'
          % (args.out, os.path.getsize(args.out), W, H))
    if args.keep_html:
        print('layout source kept at %s' % html_path)
    else:
        shutil.rmtree(tmp, ignore_errors=True)
    print('Now point og:image at the deployed URL of this file and check the '
          'preview in the client people will actually open, not in a validator.')


if __name__ == '__main__':
    main()
