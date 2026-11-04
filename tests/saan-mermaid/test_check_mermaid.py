"""Validate the standalone Saan Mermaid package and its checker."""
import html
import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "saan-mermaid"
SCRIPT = SKILL / "scripts" / "check_mermaid.py"
spec = importlib.util.spec_from_file_location("check_mermaid", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


def codes(findings):
    return sorted({code for code, _ in findings})


class PackageTests(unittest.TestCase):
    def test_frontmatter_name_matches_directory(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertRegex(text, r'\A---\nname: "saan-mermaid"\ndescription: ".+"')

    def test_referenced_files_exist(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for rel in re.findall(r"`((?:scripts|assets)/[^`]+)`", text):
            self.assertTrue((SKILL / rel).exists(), rel)

    def test_every_reference_note_is_listed(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        for path in (SKILL / "references").glob("*.md"):
            self.assertIn(f"`{path.name}`", text, path.name)

    def test_skill_theme_blocks_match_theme_file(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        light = checker.load_theme("saan-light")
        self.assertIn(checker.theme_block(light), text)
        self.assertIn(checker.classdef_block(light), text)

    def test_page_theme_block_matches_theme_file(self):
        page = html.unescape((ROOT / "page" / "mermaid" / "index.html").read_text(encoding="utf-8"))
        self.assertIn(checker.theme_block(checker.load_theme("saan-light")).rstrip("\n"), page)

    def test_themes_meet_contrast(self):
        for theme in checker.all_themes():
            self.assertEqual(checker.theme_problems(theme), [], theme["name"])


class CheckerTests(unittest.TestCase):
    def test_selftest_passes(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "--selftest"], capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_examples_are_clean(self):
        examples = sorted((SKILL / "assets" / "examples").glob("*.mmd"))
        self.assertEqual(len(examples), 12)
        for path in examples:
            errors, findings, warnings, _ = checker.review([path.read_text(encoding="utf-8")], "source: document\nnone: example\n")
            self.assertEqual((errors, findings, warnings), ([], [], []), path.name)

    def test_control_list_finds_real_gaps(self):
        text = (ROOT / "tests" / "saan-mermaid" / "payment-with-gaps.mmd").read_text(encoding="utf-8")
        controls = (SKILL / "assets" / "controls.example.txt").read_text(encoding="utf-8")
        errors, findings, _, _ = checker.review([text], controls)
        self.assertTrue(any("[CP1]" in error for error in errors))
        self.assertEqual(codes(findings), ["P1", "P5", "RT1"])

    def test_page_embeds_current_examples(self):
        page = html.unescape((ROOT / "page" / "mermaid" / "index.html").read_text(encoding="utf-8"))
        for path in (SKILL / "assets" / "examples").glob("*.mmd"):
            body = re.sub(r"\A---\n.*?\n---\n", "", path.read_text(encoding="utf-8"), flags=re.S)
            self.assertIn(body, page, path.name)

    def test_markdown_file_is_checked_block_by_block(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "good.md"
            bad = Path(tmp) / "bad.md"
            empty = Path(tmp) / "empty.md"
            good.write_text("# 文档\n\n```mermaid\n" + checker.FLOW + "  a[甲] --> b[乙]\n```\n", encoding="utf-8")
            bad.write_text("# 文档\n\n```mermaid\n" + checker.FLOW + "  a[甲] --> end\n```\n", encoding="utf-8")
            empty.write_text("# 只有文字\n", encoding="utf-8")
            run = lambda path: subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(run(good).returncode, 0, run(good).stdout)
            self.assertIn("[S2]", run(bad).stdout)
            self.assertEqual(run(bad).returncode, 1)
            self.assertIn("[R2]", run(empty).stdout)
            self.assertEqual(run(empty).returncode, 1)

    def test_json_output_has_locations(self):
        import json
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.mmd"
            path.write_text(checker.FLOW + "  a[甲] --> end\n", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "--json", str(path)], capture_output=True, text=True, encoding="utf-8")
            data = json.loads(result.stdout)
            self.assertFalse(data["ok"])
            hit = [x for x in data["issues"] if x["code"] == "S2"]
            self.assertEqual(hit[0]["file"], str(path))
            self.assertEqual(hit[0]["line"], checker.FLOW.count("\n") + 1)

    def test_target_flags_new_types(self):
        text = (SKILL / "assets" / "examples" / "flow-swimlane.mmd").read_text(encoding="utf-8")
        self.assertTrue(any("[V2]" in e for e in checker.review([text], "source: document\nnone: example\n", target="11.12")[0]))
        self.assertEqual(checker.review([text], "source: document\nnone: example\n", target="12.1")[0], [])

    def test_hook_blocks_only_on_syntax_errors(self):
        import json
        import tempfile
        hook = SKILL / "scripts" / "hook.py"
        with tempfile.TemporaryDirectory() as tmp:
            broken = Path(tmp) / "broken.md"
            styled = Path(tmp) / "plain.md"
            broken.write_text("```mermaid\nflowchart TB\n  a --> end\n```\n", encoding="utf-8")
            styled.write_text("```mermaid\nflowchart TB\n  a --> b\n  style a fill:#f00\n```\n", encoding="utf-8")
            run = lambda p: subprocess.run([sys.executable, str(hook)], input=json.dumps({"tool_input": {"file_path": str(p)}}),
                                           capture_output=True, text=True, encoding="utf-8")
            result = run(broken)
            self.assertEqual(result.returncode, 2)
            self.assertIn("broken.md:3 [S2]", result.stderr)
            self.assertEqual(run(styled).returncode, 0)

    def test_svg_width_is_read(self):
        self.assertEqual(checker.svg_width('<svg viewBox="4 4 1800.5 200">'), 1800.5)


if __name__ == "__main__":
    unittest.main()
