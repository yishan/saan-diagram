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
            (dict(base, themes={"light": "x"}), "主题 light 必须是对象"),
            (dict(base, content={"forbid": [{"text": 5}]}), "content.forbid[0] 缺少 text"),
            (dict(base, content={"button_forbid": [{"text": "确定", "message": 5}]}),
             "content.button_forbid[0] 的 message 必须是文字"),
            (dict(base, version=1), "version 必须是文字"),
        ]
        for data, word in cases:
            with tempfile.TemporaryDirectory() as td, self.subTest(word=word):
                p = Path(td) / "design.json"
                p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                with self.assertRaises(ValueError) as e:
                    mod("design").load(p)
                self.assertIn(word, str(e.exception))

    def test_missing_file(self):
        with self.assertRaises(ValueError) as e:
            mod("design").load(Path("/nonexistent/design.json"))
        self.assertIn("找不到", str(e.exception))

    def test_read_errors(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "design.json"
            p.write_bytes(b"\xff\xfe{")
            with self.assertRaises(ValueError) as e:
                mod("design").load(p)
            self.assertIn("无法解析", str(e.exception))
            with self.assertRaises(ValueError) as e:
                mod("design").load(Path(td))
            self.assertIn("无法读取", str(e.exception))


def designed_copy(td, mutate_profile=None):
    """Copy the example to td/prototype with the profile at prototype/design/design.json."""
    dst = Path(td) / "prototype"
    shutil.copytree(EXAMPLE.parent, dst)
    (dst / "design").mkdir()
    write_profile(dst / "design", mutate_profile)
    m = json.loads((dst / "manifest.json").read_text(encoding="utf-8"))
    m["design"] = "design/design.json"
    m.pop("theme", None)
    (dst / "manifest.json").write_text(json.dumps(m, ensure_ascii=False), encoding="utf-8")
    return dst / "manifest.json"


def payload(html):
    return json.loads(re.search(r'<script type="application/json" id="p-data">(.*?)</script>', html, re.S).group(1))


class BuildTests(unittest.TestCase):
    def test_profile_themes_replace_bundled_ones(self):
        with tempfile.TemporaryDirectory() as td:
            data = payload(mod("build").build(designed_copy(td)).read_text(encoding="utf-8"))
        self.assertEqual(list(data["themes"]), ["light"])
        self.assertEqual(data["theme"], "light")
        self.assertEqual(data["design"]["name"], "示例规范")
        self.assertEqual(data["design"]["components"]["StatusBadge"]["rule"], "单据状态统一用它，同时显示颜色、图标和文字")

    def test_without_profile_design_is_null(self):
        with tempfile.TemporaryDirectory() as td:
            data = payload(mod("build").build(EXAMPLE, Path(td) / "p.html").read_text(encoding="utf-8"))
        self.assertIsNone(data["design"])
        self.assertEqual(sorted(data["themes"]), ["blue", "dark", "neutral"])

    def test_unknown_theme_with_profile_fails(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(mod("build").BuildError):
                mod("build").build(designed_copy(td), theme="neutral")

    def test_bad_profile_is_a_build_error(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(mod("build").BuildError):
                mod("build").build(designed_copy(td, lambda d: d.update(themes={})))


def designed_parts(page_suffix=""):
    """Example parts with the profile attached and a StatusBadge on the status tag."""
    p = mod("build").load(EXAMPLE)
    p["design"] = mod("design").load(PROFILE)
    p["pages"] = [(rel, src.replace('<span class="p-tag">', '<span class="p-tag" data-component="StatusBadge">') + page_suffix)
                  for rel, src in p["pages"]]
    return p


def found(p):
    return {(lvl, c) for lvl, c, _, _ in mod("check").check_parts(p)}


class CheckTests(unittest.TestCase):
    def test_designed_example_is_clean(self):
        self.assertEqual(mod("check").check_parts(designed_parts()), [])

    def test_unknown_component(self):
        self.assertIn(("error", "D1"), found(designed_parts('\nvar x = \'<div data-component="Foo"></div>\';\n')))

    def test_forbidden_text(self):
        self.assertIn(("error", "D2"), found(designed_parts('\nc.flash("请您稍后再试");\n')))

    def test_forbidden_text_in_comment_is_ignored(self):
        self.assertNotIn(("error", "D2"), found(designed_parts("\n// 不写“您”\n/* 也不写感叹号！ */\n")))

    def test_confirmed_wording_is_a_finding(self):
        p = designed_parts('\nc.flash("借用成功！");\n')
        p["source"] += "\n已确认提示：借用成功！\n"
        p["manifest"]["confirmed_text"].append("借用成功！")
        got = found(p)
        self.assertIn(("finding", "D2"), got)
        self.assertNotIn(("error", "D2"), got)

    def test_button_text_must_match_exactly(self):
        self.assertIn(("error", "D2"), found(designed_parts('\nvar b = \'<button class="p-btn">确定</button>\';\n')))
        self.assertNotIn(("error", "D2"), found(designed_parts('\nvar b = \'<button class="p-btn">确定人选</button>\';\n')))
        self.assertIn(("error", "D2"), found(designed_parts('\nc.confirm({title: "x", confirm: {text: "确定"}}, "go");\n')))

    def test_two_primary_buttons_is_a_note(self):
        self.assertIn(("note", "D3"), found(designed_parts('\nvar b = \'<button class="p-btn primary">另一个</button>\';\n')))

    def test_raw_color(self):
        self.assertIn(("error", "D4"), found(designed_parts('\nvar s = \'<p style="color: #ff0000">x</p>\';\n')))
        self.assertNotIn(("error", "D4"), found(designed_parts('\nvar s = \'<a href="#add">x</a>\';\n')))

    def test_profile_themes_are_contrast_checked(self):
        p = designed_parts()
        p["design"]["themes"]["light"]["success"] = "#7FD39A"
        self.assertIn(("error", "B2"), found(p))

    def test_no_profile_no_design_checks(self):
        p = mod("build").load(EXAMPLE)
        p["pages"] = [(rel, src + '\nc.flash("请您稍后再试！");\n') for rel, src in p["pages"]]
        self.assertFalse({c for _, c in found(p)} & {"D1", "D2", "D3", "D4"})

    def test_missing_profile_is_m1(self):
        with tempfile.TemporaryDirectory() as td:
            mp = designed_copy(td)
            (mp.parent / "design" / "design.json").unlink()
            self.assertIn("M1", {c for _, c, _, _ in mod("check").check(mp)})


if __name__ == "__main__":
    unittest.main()
