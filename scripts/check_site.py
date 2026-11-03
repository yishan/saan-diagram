#!/usr/bin/env python3
"""Check local navigation, copy sources, and embedded examples without a build step."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from collections import Counter
import html
import re

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'page'


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.ids = []
        self.links = []
        self.copies = []
        self.landmarks = Counter()
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        self.landmarks[tag] += 1
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])
        if tag == 'img':
            assert attrs.get('alt'), f'{self.path}: image without alt text'
        if 'data-copy' in attrs:
            assert attrs.get('aria-label'), f'{self.path}: unnamed copy button'
            self.copies.append(attrs['data-copy'])
            if 'data-copy-prefix' in attrs:
                self.copies.append(attrs['data-copy-prefix'])


def main():
    pages = {p.resolve(): Page(p) for p in SITE.rglob('*.html')}
    for path, page in pages.items():
        assert page.landmarks['main'] == 1, f'{path}: expected one main landmark'
        assert page.landmarks['h1'] == 1, f'{path}: expected one page heading'
        assert len(page.ids) == len(set(page.ids)), f'{path}: duplicate IDs'
        for source in page.copies:
            assert 'code-' + source in page.ids, f'{path}: missing copy source {source}'
        for link in page.links:
            url = urlsplit(link)
            if url.scheme or url.netloc:
                continue
            target = (SITE / unquote(url.path).lstrip('/') if url.path.startswith('/')
                      else path.parent / unquote(url.path)).resolve() if url.path else path
            assert target.is_relative_to(SITE.resolve()), f'{path}: link outside site: {link}'
            if target.is_dir():
                target /= 'index.html'
            assert target.exists(), f'{path}: missing {link}'
            if url.fragment and target in pages:
                assert unquote(url.fragment) in pages[target].ids, f'{path}: missing anchor {link}'
        print('PASS', path.relative_to(SITE))
    diagram = (SITE / 'diagram/index.html').read_text(encoding='utf-8')
    specs = re.findall(r'<details><summary>spec · <code>([^<]+)</code></summary><pre><code>(.*?)</code></pre></details>', diagram, re.S)
    assert len(specs) == 15, 'Expected all 15 Diagram examples'
    for name, source in specs:
        assert html.unescape(source) == (ROOT / 'skills/saan-diagram/assets' / name).read_text(encoding='utf-8'), name
    mermaid = html.unescape((SITE / 'mermaid/index.html').read_text(encoding='utf-8'))
    for source in (ROOT / 'skills/saan-mermaid/assets/examples').glob('*.mmd'):
        body = re.sub(r'\A---\n.*?\n---\n', '', source.read_text(encoding='utf-8'), flags=re.S)
        assert body in mermaid, source.name
    print('PASS: example sources match both skill packages')


if __name__ == '__main__':
    main()
