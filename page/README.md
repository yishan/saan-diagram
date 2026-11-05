# Site

Static pages for the collection, currently in Chinese, published at [kits.yishan.app](https://kits.yishan.app/):

| Path | Source | Content |
|---|---|---|
| `/` | `index.html` | Saan Kits overview |
| `/diagram/` | `diagram/` | Saan Diagram introduction and gallery |
| `/mermaid/` | `mermaid/` | Saan Mermaid introduction and examples |
| `/prototype/` | `prototype/` | Saan Prototype introduction and live example |
| `/prototype/zh/` | `prototype/zh/index.html` | Explicit Chinese Prototype introduction |

The overview page forwards old `/#anchor` links to `/diagram/#anchor`. Each new skill gets its own second-level directory and a row on the overview page.

## Local preview

From the repository root:

```bash
python3 scripts/sync_page.py
python3 -m http.server 8768 --directory page
```

Open http://localhost:8768. No package installation or build command is needed.

Run `python3 scripts/check_site.py` before publishing. It checks local links and anchors, image alt text, copy targets, and embedded examples against the skill sources. CI runs the same check.

`site.css` shares navigation, headings, and copy controls. `site.js` copies each `data-copy` source and its optional `data-copy-prefix` (the Mermaid theme). If clipboard access fails, it selects the same complete text in a read-only field. Without JavaScript, commands, examples, and links remain available; copy buttons stay hidden.

## Vercel

Connect `yishan/saankits` and use these project settings:

- Root Directory: `page`
- Framework Preset: Other
- Build Command: empty
- Install Command: empty
- Output Directory: `.`
- Production Branch: `main`

Bind `kits.yishan.app` to this project. In Cloudflare, use a DNS-only CNAME for `kits` with the target recommended by Vercel. The collection uses `/`, Saan Diagram uses `/diagram/`, and Saan Mermaid uses `/mermaid/`.

The directory name does not add `/page` to the public URL. `index.html` is served at `/`. `vercel.json` keeps trailing slashes so that relative image paths on second-level pages resolve.

## Maintaining Saan Diagram examples

Update the skill's `assets/*.yaml` and the corresponding `docs/img/*.png` first, then run `python3 scripts/sync_page.py` (it only copies `docs/img/*.png`; re-render those first with `uv run skills/saan-diagram/scripts/render.py <spec> --all`). It refreshes the 15 embedded specs, preview images, and displayed skill version. Review any surrounding explanatory text when behavior changes.

`diagram/examples/accepted.yaml` is a separate fictional example that intentionally records a control bypass. To regenerate its image (needs uv and a local Chrome), run from the repository root:

```bash
uv run skills/saan-diagram/scripts/render.py page/diagram/examples/accepted.yaml --all --out out/accepted.html
mv page/diagram/examples/accepted.png page/diagram/img/accepted.png
```

Confirm both the reported finding and the rendered image before publishing.

## Maintaining Saan Mermaid examples

`mermaid/index.html` embeds each file in `skills/saan-mermaid/assets/examples/`. After changing one, update the embedded code and `mermaid/img/`. `tests/saan-mermaid` fails if the page and an example differ.

## Maintaining the Saan Prototype example

`prototype/example.html` is the bundled example from `skills/saan-prototype/assets/example/`, shown in an iframe on both introductions. After changing the example or the runtime, rebuild it from the repository root:

```bash
python3 skills/saan-prototype/scripts/build.py skills/saan-prototype/assets/example/manifest.json -o page/prototype/example.html
```

`check_site.py` skips it as a site page and fails if it differs from a fresh build.

## Icons

Each page has its own icon family, sharing a white rounded tile, neutral gray nodes, and the `#3370FF` brand accent:

| Page | SVG source | Symbol |
|---|---|---|
| Saan Kits | `favicon.svg` | Four modules forming a toolkit |
| Saan Diagram | `diagram/favicon.svg` | A business node connected to a system block |
| Saan Mermaid | `mermaid/favicon.svg` | A decision node branching into two outcomes |

Each directory also contains `favicon.ico` (16, 32, and 48 px) and `apple-touch-icon.png` (180 px, opaque white background without the border). Keep these exports in sync with their SVG source. Each page references its own local icons; `/favicon.ico` is the collection's default fallback.
