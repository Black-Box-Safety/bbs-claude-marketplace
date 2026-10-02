# Toolkit share thumbnails

Images to attach to the texts and emails that invite the team to open the BBS Claude Toolkit page.

| File | What it is for |
|---|---|
| `thumbnail.html` | The one source. `#wide` is the 1200 x 630 image, `#square` the 1080 x 1080. Edit here, never the PNGs. |
| `bbs-claude-toolkit-1200x630.png` | Email body and link-preview shape. Rendered at 2x (2400 x 1260). |
| `bbs-claude-toolkit-1080x1080.png` | Square, for text messages. Rendered at 2x (2160 x 2160). |
| `render.js` | Renders both PNGs from `thumbnail.html` with Playwright. |

## Re-render

From the repo root:

```bash
PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers node docs/explainers/2026-10-01-team-rollout/thumbnail/render.js
```

In a cloud session behind the agent proxy, add `NODE_USE_ENV_PROXY=1 NODE_EXTRA_CA_CERTS=/root/.ccr/ca-bundle.crt`.
Chromium there neither uses the proxy nor trusts its CA, so the script fetches Google Fonts
from Node instead, with TLS verification left on. The script checks that Archivo 500 and 800
actually loaded and stops with an error if they did not. It never renders a fallback face.

## Copy used

Every line appears on `../bbs-claude-toolkit.html`:

- Headline: "Claude does the lookups. You make the calls."
- Second line: "Claude drafts. You send."
- Sign-off: "BBS Claude Toolkit" (the page's title)

## Marks and type

- Logo: `plugins/bbs-sales/skills/bbs-quote-builder/assets/bbs_logo.png`, linked by relative
  path rather than copied, on a white plate. It is shown at its native pixel size (78 x 88.5 CSS
  px at 2x), with no filter, crop or recolor.
- No Claude or Anthropic mark. The repo holds no file for one and `ASSETS.md` grants no right
  to one, so "Claude" is set in type.
- Archivo 500 and 800 only. JetBrains Mono is not used, because these images contain no
  commands or placeholders.
