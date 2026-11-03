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

    def test_svg_width_is_read(self):
        self.assertEqual(checker.svg_width('<svg viewBox="4 4 1800.5 200">'), 1800.5)


if __name__ == "__main__":
    unittest.main()
