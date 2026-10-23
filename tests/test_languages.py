"""Language behavior across all diagram layouts and the public renderer CLI."""
import copy
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/saan-diagram'
sys.path.insert(0, str(SKILL / 'scripts'))
import render as r
from spec_validation import SpecError

CJK = re.compile(r'[\u4e00-\u9fff]')


def english_structure(spec):
    """Synthetic short English labels preserve the 14 fixtures' topology and references."""
    labels = {}

    def convert(value):
        if isinstance(value, dict):
            return {key: convert(item) for key, item in value.items()}
        if isinstance(value, list):
            return [convert(item) for item in value]
        if isinstance(value, str) and CJK.search(value):
            if '.' in value:
                return '.'.join(convert(part) for part in value.split('.'))
            if value not in labels:
                labels[value] = ('AI ' if value.startswith('AI') else '') + f'Item {len(labels) + 1}'
            return labels[value]
        return value

    result = convert(spec)
    result['language'] = 'en'
    return result


class LanguageTests(unittest.TestCase):
    def test_all_fourteen_types_have_english_svg_and_whiteboard_captions(self):
        for name in r.EXAMPLES:
            with self.subTest(example=name):
                d, svg, *_ = r.build_spec(english_structure(r._load_example(name)))
                layout, findings, accepted, verified = r.collect(d)
                self.assertEqual(layout + findings, [])
                text = ''.join(ET.fromstring(svg).itertext())
                wb = d.wb() if hasattr(d, 'wb') else r.to_wb_dsl(d)
                self.assertIsNone(CJK.search(text))
                self.assertIsNone(CJK.search(json.dumps(wb, ensure_ascii=False)))
                self.assertIsNone(CJK.search(' '.join(r.note_lines(accepted, verified, d.t))))

    def test_all_business_rules_keep_english_findings(self):
        r._m_setup()
        covered = set()
        for code, _, make in r.MUTATIONS:
            if code not in r.FINDING_CODES:
                continue
            with self.subTest(code=code):
                d, *_ = r.build_spec(english_structure(make()))
                _, findings, _, _ = r.collect(d)
                messages = [message for actual, message, _ in findings if actual == code]
                self.assertTrue(messages, code)
                self.assertIsNone(CJK.search(' '.join(messages)))
                covered.add(code)
        self.assertEqual(covered, r.FINDING_CODES)

    def test_language_does_not_translate_input_names(self):
        spec = r.load_spec(SKILL / 'assets/en/approval-flow.yaml')
        spec['nodes'][0]['label'] = '甲方 A'
        d, svg, *_ = r.build_spec(spec)
        self.assertIn('甲方 A', svg)
        self.assertIn('Legend', svg)
        self.assertEqual(d.nodes['submit'].label, '甲方 A')

    def test_caption_locale_is_per_diagram_and_does_not_mutate_spec(self):
        sp = r._load_example('1-arch')
        original = copy.deepcopy(sp)
        zh, *_ = r.build_spec(sp)
        self.assertEqual(sp, original)
        sp['language'] = 'en'
        en, *_ = r.build_spec(sp)
        self.assertIn('图例', zh.svg()[0])
        self.assertIn('Legend', en.svg()[0])
        self.assertIn('图例', zh.svg()[0])
        self.assertNotIn('_special', sp)

    def test_english_words_manual_breaks_and_identifiers_are_preserved(self):
        lines = r._wrap_w('Review invoice before payment', 90)
        self.assertEqual(' '.join(lines), 'Review invoice before payment')
        self.assertTrue(all(r.text_w(line) <= 90 for line in lines))
        self.assertEqual(r._wrap_w('First line\nSecond line', 200), ['First line', 'Second line'])
        self.assertEqual(r._wrap_w('CustomerAccountID', 20), ['CustomerAccountID'])
        self.assertEqual(r._vlines('Security policy'), ['Security', 'policy'])
        self.assertEqual(r._chunks('Review invoice', 2), ['Review', 'invoice'])
        self.assertEqual(r._wrap_w('第三方能力', 48), ['第三', '方能力'])

    def test_english_layer_chips_and_rails_fit_their_text(self):
        d, *_ = r.build(SKILL / 'assets/en/platform-layers.yaml')
        for item in d.S.items:
            if item['t'] != 'rect' or not item.get('text'):
                continue
            lines = r._vlines(item['text']) if item['vtext'] else item['text'].split('\n')
            for line in lines:
                self.assertLessEqual(r.text_w(line, item['fs']), item['w'], line)
            self.assertLessEqual(len(lines) * (item['fs'] + 6), item['h'] + 6, lines)

    def test_confirmed_english_finding_keeps_counterexample_and_user_note(self):
        sp = r.load_spec(SKILL / 'assets/en/approval-flow.yaml')
        sp['edges'].append({'from': 'submit', 'to': 'pay', 'kind': 'flow', 'route': 'll', 'offset': 80})
        sp['accept'] = [{'code': 'P1', 'match': 'Release funds', 'note': 'Known exception; remediation pending.'}]
        d, *_ = r.build_spec(sp)
        _, findings, accepted, verified = r.collect(d)
        self.assertEqual(findings, [])
        self.assertEqual(len(accepted), 1)
        notes = ' '.join(r.note_lines(accepted, verified, d.t))
        self.assertIn('Submit request → Release funds', notes)
        self.assertIn('Known exception; remediation pending.', notes)
        self.assertIsNone(CJK.search(notes))

    def test_english_timeline_does_not_infer_completion(self):
        d, svg, *_ = r.build(SKILL / 'assets/en/release-timeline.yaml')
        notes = ' '.join(d.notes)
        self.assertIn('Done: 1', notes)
        self.assertIn('Unknown: 1', notes)
        self.assertIn('Overdue: 1', notes)
        self.assertIn('stroke-dasharray="3,3"', svg)
        self.assertIsNone(CJK.search(''.join(ET.fromstring(svg).itertext())))

    def test_invalid_locale_is_reported_as_spec_error(self):
        sp = r._load_example('1-arch')
        sp['language'] = 'fr'
        with self.assertRaisesRegex(SpecError, 'language'):
            r.build_spec(sp)

    def test_cli_language_override_sets_html_and_result_language(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)
            for locale in ('zh-CN', 'en'):
                command = [sys.executable, str(SKILL / 'scripts/render.py'),
                           str(SKILL / 'assets/en/approval-flow.yaml'), '--language', locale,
                           '--outdir', str(out)]
                result = subprocess.run(command, text=True, capture_output=True)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn(f'lang="{locale}"', (out / 'approval-flow.html').read_text())
                report = json.loads((out / 'approval-flow.result.json').read_text())
                self.assertEqual(report['language'], locale)
                self.assertEqual(report['status'], 'generated')


if __name__ == '__main__':
    unittest.main()
