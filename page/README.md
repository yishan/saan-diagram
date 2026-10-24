# Landing page

Static HTML and images for Saan Diagram. The page is currently in Chinese; the repository README is available in English and Chinese.

## Local preview

From the repository root:

```bash
python3 scripts/sync_page.py
python3 -m http.server 8768 --directory page
```

Open http://localhost:8768. No package installation or build command is needed.

## Vercel

Connect `yishan/saan-diagram` and use these project settings:

- Root Directory: `page`
- Framework Preset: Other
- Build Command: empty
- Install Command: empty
- Output Directory: `.`
- Production Branch: `main`

The directory name does not add `/page` to the public URL. `index.html` is served at `/`.

## Maintaining examples

Update the skill's `assets/*.yaml` and the corresponding `docs/img/*.png` first, then run `python3 scripts/sync_page.py` (it only copies `docs/img/*.png`; re-render those first with `uv run skills/saan-diagram/scripts/render.py <spec> --all`). It refreshes the 14 embedded specs, preview images, and displayed skill version. Review any surrounding explanatory text when behavior changes.

`examples/accepted.yaml` is a separate fictional example that intentionally records a control bypass. To regenerate its image (needs uv and a local Chrome), run from the repository root:

```bash
uv run skills/saan-diagram/scripts/render.py page/examples/accepted.yaml --all --out out/accepted.html
mv page/examples/accepted.png page/img/accepted.png
```

Confirm both the reported finding and the rendered image before publishing.

## Icons

`favicon.svg` is the source icon: a gray business node connected to a brand-blue system block by a single-bend connector, drawn on a 32-unit grid so the 16 px rendering stays crisp. `favicon.ico` (16, 32, and 48 px) and `apple-touch-icon.png` (180 px, opaque white background without the border) are exported from it. Re-export both after changing the SVG.
