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


if __name__ == "__main__":
    unittest.main()
