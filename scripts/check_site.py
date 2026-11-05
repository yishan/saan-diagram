#!/usr/bin/env python3
"""Check local navigation, copy sources, and embedded examples without a build step."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from collections import Counter
import html
import importlib.util
import re
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'page'
# Built prototypes are shown in an iframe; they are checked against a fresh build, not as site pages.
DEMOS = {'prototype/example.html': 'skills/saan-prototype/assets/example/manifest.json'}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.ids = []
        self.links = []
        self.copies = []
        self.landmarks = Counter()
        self.language = None
        self.alternates = {}
        self.language_choices = []
        self.theme_choices = []
        self.feed(path.read_text(encoding='utf-8'))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'html':
            self.language = attrs.get('lang')
        if tag == 'link' and attrs.get('rel') == 'alternate':
            self.alternates[attrs.get('hreflang')] = attrs['href']
        if 'data-language' in attrs:
            self.language_choices.append(attrs['data-language'])
        if 'data-theme-choice' in attrs:
            assert attrs.get('aria-label'), f'{self.path}: unnamed appearance button'
            self.theme_choices.append(attrs['data-theme-choice'])
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
    pages = {p.resolve(): Page(p) for p in SITE.rglob('*.html') if p.relative_to(SITE).as_posix() not in DEMOS}
    for path, page in pages.items():
        assert page.landmarks['main'] == 1, f'{path}: expected one main landmark'
        assert page.landmarks['h1'] == 1, f'{path}: expected one page heading'
        assert len(page.ids) == len(set(page.ids)), f'{path}: duplicate IDs'
        assert page.language in ('en', 'zh-CN'), f'{path}: unsupported page language'
        assert set(page.alternates) == {'en', 'zh-CN'}, f'{path}: missing language alternate'
        assert sorted(page.language_choices) == ['en', 'zh'], f'{path}: missing language switch'
        assert sorted(page.theme_choices) == ['dark', 'light', 'system'], f'{path}: missing appearance choice'
        for language, href in page.alternates.items():
            other = pages[(path.parent / href / 'index.html').resolve()]
            assert other.language == language, f'{path}: incorrect language alternate {href}'
            assert set(other.ids) == set(page.ids), f'{path}: language switch would lose an anchor'
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
    for language in ('', 'zh'):
        diagram = (SITE / 'diagram' / language / 'index.html').read_text(encoding='utf-8')
        specs = re.findall(r'<details><summary>(?:spec|Diagram source|图示源文件) · <code>([^<]+)</code></summary><pre><code>(.*?)</code></pre></details>', diagram, re.S)
        assert len(specs) == 15, f'{language}: expected all 15 Diagram examples'
        for name, source in specs:
            assert html.unescape(source) == (ROOT / 'skills/saan-diagram/assets' / name).read_text(encoding='utf-8'), name
        mermaid = html.unescape((SITE / 'mermaid' / language / 'index.html').read_text(encoding='utf-8'))
        for source in (ROOT / 'skills/saan-mermaid/assets/examples').glob('*.mmd'):
            body = re.sub(r'\A---\n.*?\n---\n', '', source.read_text(encoding='utf-8'), flags=re.S)
            assert body in mermaid, source.name
    print('PASS: English and Chinese example sources match both skill packages')
    spec = importlib.util.spec_from_file_location('prototype_build', ROOT / 'skills/saan-prototype/scripts/build.py')
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    with tempfile.TemporaryDirectory() as td:
        for demo, manifest in DEMOS.items():
            fresh = build.build(ROOT / manifest, Path(td) / 'demo.html').read_bytes()
            assert (SITE / demo).read_bytes() == fresh, f'{demo}: rebuild with skills/saan-prototype/scripts/build.py {manifest}'
    print('PASS: prototype demos match a fresh build')


if __name__ == '__main__':
    main()
