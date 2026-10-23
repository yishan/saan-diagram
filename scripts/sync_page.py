#!/usr/bin/env python3
"""Refresh the landing page's embedded examples, images, and skill version."""
import html
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / 'page' / 'index.html'
PATTERN = re.compile(
    r'(<details><summary>spec · <code>([^<]+\.yaml)</code></summary><pre><code>)'
    r'.*?(</code></pre></details>)', re.S
)


def main():
    def replace(match):
        source = ROOT / 'skills' / 'saan-diagram' / 'assets' / match[2]
        return match[1] + html.escape(source.read_text(encoding='utf-8'), quote=False) + match[3]

    text, count = PATTERN.subn(replace, PAGE.read_text(encoding='utf-8'))
    if count != 14:
        raise SystemExit(f'Expected 14 embedded examples, found {count}; page not changed.')
    version = json.loads((ROOT / '.claude-plugin' / 'plugin.json').read_text())['version']
    text = re.sub(r'(?<=Skill · )v[\d.]+|(?<=Saan Diagram )v[\d.]+', f'v{version}', text)
    PAGE.write_text(text, encoding='utf-8')
    for source in (ROOT / 'docs' / 'img').glob('*.png'):
        shutil.copy2(source, ROOT / 'page' / 'img' / source.name)
    print(f'Synced {count} examples and preview images for v{version}.')


if __name__ == '__main__':
    main()
