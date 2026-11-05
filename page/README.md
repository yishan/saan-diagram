# Site

Static pages for the collection, published at [kits.yishan.app](https://kits.yishan.app/). All seven pages include English and Chinese, selected from browser preferences on first visit.

| Path | Source | Content |
|---|---|---|
| `/` | `index.html` | Saan Kits overview |
| `/zh/` | `zh/index.html` | Explicit Chinese overview |
| `/diagram/` | `diagram/` | Saan Diagram introduction and gallery |
| `/diagram/zh/` | `diagram/zh/index.html` | Explicit Chinese Diagram introduction |
| `/mermaid/` | `mermaid/` | Saan Mermaid introduction and examples |
| `/mermaid/zh/` | `mermaid/zh/index.html` | Explicit Chinese Mermaid introduction |
| `/discovery/` | `discovery/index.html` | Saan Discovery automatic language entry (English HTML fallback) |
| `/discovery/zh/` | `discovery/zh/index.html` | Explicit Chinese introduction |
| `/prd-writing/` | `prd-writing/index.html` | PRD Writing automatic language entry (English HTML fallback) |
| `/prd-writing/zh/` | `prd-writing/zh/index.html` | Explicit Chinese introduction |
| `/prototype/` | `prototype/` | Saan Prototype introduction and live example |
| `/prototype/zh/` | `prototype/zh/index.html` | Explicit Chinese Prototype introduction |
| `/inquiry/` | `inquiry/index.html` | Inquiry introduction (local addition) |
| `/inquiry/zh/` | `inquiry/zh/index.html` | Explicit Chinese Inquiry introduction |

The overview page forwards old `/#anchor` links to `/diagram/#anchor`, except its own `#collection-install` section. Each new skill gets its own second-level directory and a row on the overview page. Keep the localized skill count in sync with that list. Skill text aligns with the main heading; decorative circles and a connecting line sit in the left gutter.

## Local preview

From the repository root:

```bash
python3 scripts/sync_page.py
python3 -m http.server 8768 --directory page
```

Open http://localhost:8768. No package installation or build command is needed.

Run `python3 scripts/check_site.py` before publishing. It checks local links and anchors, image alt text, copy targets, and embedded examples against the skill sources. CI runs the same check.

`site.css` shares navigation, headings, and copy controls. `site.js` copies each `data-copy` source and its optional `data-copy-prefix` (the Mermaid theme). If clipboard access fails, it selects the same complete text in a read-only field. Without JavaScript, commands, examples, and links remain available; copy buttons stay hidden.

Copy feedback follows the rendered page's `lang` attribute. Each bilingual introduction keeps complete English and Chinese HTML documents and shares its own CSS. `site-preferences.js` runs before styles: an explicit `?lang=en|zh` choice takes precedence; otherwise the main entry uses the saved language and then the first supported browser language (Chinese or English, with English fallback). A direct `/zh/` URL remains Chinese. Language links preserve the query and section anchor and remember manual choices. Without JavaScript, both documents and ordinary language links remain usable.

Two icon buttons at the top right open language and appearance dropdowns. The appearance icon reflects the selected system, light, or dark mode. Menus mark the current choice, close on selection, outside click, focus leaving, or Escape, and support Tab and arrow-key navigation. Escape returns focus to the trigger. Language selection uses native `details` and links, so it remains usable without JavaScript; the appearance picker stays hidden in that case.

Initial appearance follows `prefers-color-scheme`; a manual light/dark/system choice is saved for the site. System mode follows live OS changes. The shared script also applies that preference when navigating to existing pages. Storage denial does not block language switching or the current page's theme control. Page preferences do not change the skill's output-language rule.

## Vercel

Connect `yishan/saankits` and use these project settings:

- Root Directory: `page`
- Framework Preset: Other
- Build Command: empty
- Install Command: empty
- Output Directory: `.`
- Production Branch: `main`

Bind `kits.yishan.app` to this project. In Cloudflare, use a DNS-only CNAME for `kits` with the target recommended by Vercel. The collection uses `/`, Saan Diagram uses `/diagram/`, Saan Mermaid uses `/mermaid/`, and Saan Discovery uses `/discovery/` with Chinese at `/discovery/zh/`.

The directory name does not add `/page` to the public URL. `index.html` is served at `/`. `vercel.json` keeps trailing slashes so that relative image paths on second-level pages resolve.

## Maintaining Saan Diagram examples

Update the skill's `assets/*.yaml` and the corresponding `docs/img/*.png` first, then run `python3 scripts/sync_page.py` (it only copies `docs/img/*.png`; re-render those first with `uv run skills/saan-diagram/scripts/render.py <spec> --all`). It refreshes the 15 embedded specs in both languages, shared preview images, and the version from Diagram's `SKILL.md`. Review any surrounding explanatory text when behavior changes.

`diagram/examples/accepted.yaml` is a separate fictional example that intentionally records a control bypass. To regenerate its image (needs uv and a local Chrome), run from the repository root:

```bash
uv run skills/saan-diagram/scripts/render.py page/diagram/examples/accepted.yaml --all --out out/accepted.html
mv page/diagram/examples/accepted.png page/diagram/img/accepted.png
```

Confirm both the reported finding and the rendered image before publishing.

## Maintaining Saan Mermaid examples

`mermaid/index.html` and `mermaid/zh/index.html` embed each file in `skills/saan-mermaid/assets/examples/`. After changing one, update both pages and `mermaid/img/`. `check_site.py` checks both languages against the sources; `tests/saan-mermaid` also checks the main page.

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
