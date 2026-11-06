"""Design profiles for saan-prototype: loading, build, and the D checks."""
import copy
import importlib.util
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "skills" / "saan-prototype"
EXAMPLE = SKILL / "assets" / "example" / "manifest.json"
PROFILE = SKILL / "assets" / "design-example" / "design.json"
_CACHE = {}


def mod(name):
    if name not in _CACHE:
        sys.path.insert(0, str(SKILL / "scripts"))
        spec = importlib.util.spec_from_file_location(name, SKILL / "scripts" / f"{name}.py")
        _CACHE[name] = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_CACHE[name])
    return _CACHE[name]


def write_profile(dirpath, mutate=None):
    d = json.loads(PROFILE.read_text(encoding="utf-8"))
    if mutate:
        mutate(d)
    p = Path(dirpath) / "design.json"
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    return p


class LoadTests(unittest.TestCase):
    def test_example_profile_loads(self):
        d = mod("design").load(PROFILE)
        self.assertEqual(d["name"], "示例规范")
        self.assertEqual(list(d["themes"]), ["light"])
        self.assertEqual(d["components"]["StatusBadge"]["use"], "status")

    def test_structure_errors(self):
        cases = [
            (lambda d: d.pop("name"), "name"),
            (lambda d: d.update(themes={}), "themes"),
            (lambda d: d["components"]["StatusBadge"].update(use="badge"), "badge"),
            (lambda d: d["content"]["forbid"].append({"message": "x"}), "text"),
        ]
        for mutate, word in cases:
            with tempfile.TemporaryDirectory() as td, self.subTest(word=word):
                with self.assertRaises(ValueError) as e:
                    mod("design").load(write_profile(td, mutate))
                self.assertIn(word, str(e.exception))

    def test_malformed_shapes(self):
        base = json.loads(PROFILE.read_text(encoding="utf-8"))
        cases = [
            ([], "顶层必须是对象"),
            (dict(base, content=[]), "content 必须是对象"),
            (dict(base, components={"X": "s"}), "组件 X 必须是对象"),
            (dict(base, content={"forbid": "x"}), "content.forbid 必须是数组"),
        ]
        for data, word in cases:
            with tempfile.TemporaryDirectory() as td, self.subTest(word=word):
                p = Path(td) / "design.json"
                p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                with self.assertRaises(ValueError) as e:
                    mod("design").load(p)
                self.assertIn(word, str(e.exception))

    def test_missing_file(self):
        with self.assertRaises(ValueError):
            mod("design").load(Path("/nonexistent/design.json"))


if __name__ == "__main__":
    unittest.main()
