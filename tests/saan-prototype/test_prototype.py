"""Validate the standalone Saan Prototype package: source index, build, check, themes."""
import copy
import importlib.util
import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "saan-prototype"
EXAMPLE = SKILL / "assets" / "example" / "manifest.json"


_CACHE = {}


def mod(name):
    """Import skills/saan-prototype/scripts/<name>.py on first use."""
    if name not in _CACHE:
        sys.path.insert(0, str(SKILL / "scripts"))
        spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / f"{name}.py")
        _CACHE[name] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_CACHE[name])
    return _CACHE[name]


class SourceIndexTests(unittest.TestCase):
    TEXT = "| Q-01 | 期限多长？ | 表单 |\n正文提到 Q-01 和 FR-B01。\n| AC-01 | FR-B01 | 前置 |\n另见 XQ-02 与 Q-031a。\n"

    def test_ids_and_definitions(self):
        idx = mod("source_index").index(self.TEXT, mod("source_index").DEFAULT_PATTERNS)
        self.assertEqual(idx["open"], {"Q-01": "Q-01 | 期限多长？ | 表单"})
        self.assertEqual(idx["acceptance"]["AC-01"], "AC-01 | FR-B01 | 前置")
        self.assertEqual(idx["rule"]["FR-B01"], "正文提到 Q-01 和 FR-B01。")

    def test_ignores_ids_inside_other_tokens(self):
        self.assertNotIn("Q-02", mod("source_index").index(self.TEXT, mod("source_index").DEFAULT_PATTERNS)["open"])

    def test_manifest_can_override_patterns(self):
        p = mod("source_index").patterns({"id_patterns": {"open": r"OPEN-\d+"}})
        self.assertEqual(mod("source_index").index("OPEN-3 和 Q-01", p)["open"], {"OPEN-3": "OPEN-3 和 Q-01"})


class ThemeTests(unittest.TestCase):
    THEMES = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in sorted((SKILL / "themes").glob("*.json"))}

    def test_bundled_themes_pass(self):
        self.assertEqual(sorted(self.THEMES), ["blue", "dark", "neutral"])
        for name, t in self.THEMES.items():
            self.assertEqual(mod("contrast").problems(t), [], name)

    def test_low_contrast_is_reported(self):
        t = dict(self.THEMES["neutral"], text="#C0C4CA")
        self.assertTrue(any(m.startswith("text 在 bg") for m in mod("contrast").problems(t)))

    def test_known_ratio(self):
        self.assertAlmostEqual(mod("contrast").ratio("#000000", "#FFFFFF"), 21.0, places=1)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.out = Path(self.td.name) / "p.html"

    def tearDown(self):
        self.td.cleanup()

    def test_example_builds_into_one_offline_file(self):
        html = mod("build").build(EXAMPLE, self.out).read_text(encoding="utf-8")
        self.assertNotRegex(html, r"""(?:src|href)=["']https?://""")
        self.assertEqual(html.count("<script"), 5)
        self.assertNotIn("/*@", html)
        data = json.loads(re.search(r'<script type="application/json" id="p-data">(.*?)</script>', html, re.S).group(1))
        self.assertEqual(data["defs"]["Q-01"], "Q-01 | 借用期限多长，超期怎么处理？ | 借用表单、提醒")
        self.assertEqual(sorted(data["themes"]), ["blue", "dark", "neutral"])

    def test_closing_script_tag_in_source_is_escaped(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "proto"
            src.mkdir()
            for f in ("manifest.json", "source.md", "rules.js", "scenarios.json", "trace.md"):
                (src / f).write_text((EXAMPLE.parent / f).read_text(encoding="utf-8"), encoding="utf-8")
            (src / "pages").mkdir()
            page = (EXAMPLE.parent / "pages" / "devices.js").read_text(encoding="utf-8")
            (src / "pages" / "devices.js").write_text(page + '\nvar s = "</script>";\n', encoding="utf-8")
            html = mod("build").build(src / "manifest.json", self.out).read_text(encoding="utf-8")
            self.assertIn('"<\\/script>"', html)

    def test_unknown_theme_fails(self):
        with self.assertRaises(mod("build").BuildError):
            mod("build").build(EXAMPLE, self.out, theme="pink")

    def test_cli_reports_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            m = Path(td) / "manifest.json"
            m.write_text(json.dumps({"title": "x", "source": "nope.md", "roles": [{"id": "a"}], "scenarios": "s.json", "pages": ["p.js"]}), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SKILL / "scripts" / "build.py"), str(m)], capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("找不到", r.stderr)


class CheckTests(unittest.TestCase):
    def codes(self, mutate):
        p = mod("build").load(EXAMPLE)
        mutate(p)
        return {c for _, c, _, _ in mod("check").check_parts(p)}

    def test_example_is_clean(self):
        self.assertEqual(mod("check").check(EXAMPLE), [])

    def test_selftest_passes(self):
        r = subprocess.run([sys.executable, str(SKILL / "scripts" / "check.py"), "--selftest"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_open_question_excused_in_trace(self):
        self.assertNotIn("T2", self.codes(lambda p: None))
        self.assertIn("T2", self.codes(lambda p: p.update(trace=p["trace"].replace("不涉及：", ""))))

    def test_exit_codes(self):
        self.assertEqual(mod("check").report([]), 0)
        self.assertEqual(mod("check").report([("finding", "C1", "m", "x")]), 2)
        self.assertEqual(mod("check").report([("finding", "C1", "m", "x"), ("error", "T1", "m", "y")]), 1)


if __name__ == "__main__":
    unittest.main()
