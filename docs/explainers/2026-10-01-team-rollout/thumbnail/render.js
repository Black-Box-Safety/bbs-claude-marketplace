// Renders thumbnail.html to the two PNGs beside it. Run from any directory:
//   PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers node docs/explainers/2026-10-01-team-rollout/thumbnail/render.js
// Fails loudly if Archivo did not load, rather than shipping a fallback face.
const path = require('path');
let playwright;
try { playwright = require('playwright'); }
catch { playwright = require('/opt/node22/lib/node_modules/playwright'); }

(async () => {
  const dir = __dirname;
  const browser = await playwright.chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1300, height: 1900 }, deviceScaleFactor: 2 });
  // In a sandbox whose egress goes through a TLS-inspecting proxy, Chromium neither uses
  // the proxy nor trusts its CA. Fetch Google Fonts from Node instead (run with
  // NODE_USE_ENV_PROXY=1 and NODE_EXTRA_CA_CERTS set; TLS verification stays on).
  if (process.env.HTTPS_PROXY || process.env.https_proxy) {
    await page.route(/^https:\/\/fonts\.(googleapis|gstatic)\.com\//, async route => {
      const req = route.request();
      const res = await fetch(req.url(), { headers: { 'user-agent': req.headers()['user-agent'] || 'Mozilla/5.0' } });
      const body = Buffer.from(await res.arrayBuffer());
      await route.fulfill({ status: res.status, body,
        headers: { 'content-type': res.headers.get('content-type') || '', 'access-control-allow-origin': '*' } });
    });
  }
  await page.goto('file://' + path.join(dir, 'thumbnail.html'), { waitUntil: 'networkidle' });
  await page.evaluate(() => document.fonts.ready);

  const check = await page.evaluate(async () => {
    await document.fonts.load('800 88px "Archivo"');
    await document.fonts.load('500 40px "Archivo"');
    const loaded = [...document.fonts].filter(f => f.status === 'loaded')
      .map(f => `${f.family} ${f.weight}`);
    const img = document.querySelector('.plate img');
    return {
      archivo800: document.fonts.check('800 88px "Archivo"') && loaded.some(s => s.includes('Archivo') && s.includes('800')),
      archivo500: document.fonts.check('500 40px "Archivo"') && loaded.some(s => s.includes('Archivo') && s.includes('500')),
      loaded,
      logo: { natural: [img.naturalWidth, img.naturalHeight], filter: getComputedStyle(img).filter },
    };
  });
  console.log(JSON.stringify(check, null, 2));
  if (!check.archivo800 || !check.archivo500) {
    await browser.close();
    throw new Error('Archivo did not load; refusing to render with a fallback face.');
  }

  await page.locator('#wide').screenshot({ path: path.join(dir, 'bbs-claude-toolkit-1200x630.png') });
  await page.locator('#square').screenshot({ path: path.join(dir, 'bbs-claude-toolkit-1080x1080.png') });
  await browser.close();
  console.log('rendered');
})();
