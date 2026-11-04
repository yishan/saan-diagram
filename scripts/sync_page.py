#!/usr/bin/env python3
"""Refresh both Diagram languages from the shared skill assets and version."""
import html
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / 'page' / 'diagram' / language / 'index.html' for language in ('', 'zh')]
PATTERN = re.compile(
    r'(<details><summary>spec · <code>([^<]+\.yaml)</code></summary><pre><code>)'
    r'.*?(</code></pre></details>)', re.S
)


def main():
    def replace(match):
        source = ROOT / 'skills' / 'saan-diagram' / 'assets' / match[2]
        return match[1] + html.escape(source.read_text(encoding='utf-8'), quote=False) + match[3]

    skill = (ROOT / 'skills' / 'saan-diagram' / 'SKILL.md').read_text(encoding='utf-8')
    match = re.search(r'''^  version: ["']?([\d.]+)["']?$''', skill, re.M)
    if not match:
        raise SystemExit('Diagram skill version not found; pages not changed.')
    version = match[1]
    updates = {}
    for page in PAGES:
        text, count = PATTERN.subn(replace, page.read_text(encoding='utf-8'))
        if count != 15:
            raise SystemExit(f'{page}: expected 15 embedded examples, found {count}; pages not changed.')
        updates[page] = re.sub(r'(?<=Skill · )v[\d.]+|(?<=Saan Diagram )v[\d.]+', f'v{version}', text)
    for page, text in updates.items():
        page.write_text(text, encoding='utf-8')
    for source in (ROOT / 'docs' / 'img').glob('*.png'):
        shutil.copy2(source, ROOT / 'page' / 'diagram' / 'img' / source.name)
    print(f'Synced {count} examples in {len(PAGES)} languages and preview images for v{version}.')


if __name__ == '__main__':
    main()
