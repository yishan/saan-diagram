# Saan Prototype v0.2 设计规范包实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal：** 让 saan-prototype 读取用户提供的设计规范包，按规范的主题配色、组件名和内容规则生成并检查评审原型；不带规范包时行为与 v0.1 相同。

**Architecture：** 新增 `scripts/design.py` 负责读取和校验 `design.json`；`build.py` 在 manifest 写了 `design` 时改用规范包的主题，并把组件清单交给 runtime；`check.py` 在有规范包时追加 D1—D4。runtime 增加六种通用组件外观、`c.confirm()` 和“组件名”开关。

**Tech Stack：** Python 3.9+ 标准库（unittest），原生 JS（ES5 写法，与现有 runtime 一致），CSS 变量。

**设计依据：** [2026-11-06-saan-prototype-design-profile-design.zh-CN.md](2026-11-06-saan-prototype-design-profile-design.zh-CN.md)。

---

## 开始之前

- **分支。** 从 `feat/saan-prototype` 新建 `feat/saan-prototype-design-profile`。PR #11 合并后，改为基于 `main` 并同步一次。不要把 v0.2 的提交推到 PR #11 的分支上。
- **基线。** 先跑一遍，记下都通过：

```bash
python3 skills/saan-prototype/scripts/check.py --selftest
python3 -m unittest discover -s tests/saan-prototype -v
python3 scripts/check_site.py
node --check skills/saan-prototype/runtime/runtime.js
```

  预期：`SELFTEST PASS`；`Ran 20 tests … OK`；站点检查最后一行 `PASS: prototype demos match a fresh build`。
- **约定。** 所有提示信息用中文，和现有检查器一致。代码不出现 `../../`（`PackageTests` 会查）。真实公司的设计系统不进仓库，示例一律虚构。
- **进度面板。** 本计划超过 5 步，执行时按 `~/.claude/CLAUDE.md` 启用 dashboard-builder，并把 `.dashboard/` 加进 `.git/info/exclude`。

---

### Task 1：示例规范包

**Files：**
- Create: `skills/saan-prototype/assets/design-example/design.json`
- Create: `skills/saan-prototype/assets/design-example/guide.md`

**Step 1：写 `design.json`**

```json
{
  "name": "示例规范",
  "version": "1.0",
  "themes": {
    "light": {"label": "示例浅色", "bg": "#F5F6F8", "surface": "#FFFFFF", "border": "#D5D8DE",
              "text": "#1F2329", "muted": "#5C6370", "accent": "#2F5D9E", "accent_text": "#FFFFFF",
              "danger": "#B42318", "notice": "#8A5A00", "success": "#1A7F37",
              "radius": "4px", "font_size": "14px"}
  },
  "components": {
    "StatusBadge": {"use": "status", "rule": "单据状态统一用它，同时显示颜色、图标和文字"},
    "ActionBar": {"use": "actions", "rule": "不能执行的动作保留，并写明原因"},
    "ChangeConfirm": {"use": "confirm", "rule": "提交、退回、作废前列出每项变化和后果"},
    "Field": {"use": "field", "rule": "查看态显示文字，不用禁用的输入框"},
    "FilterBar": {"use": "filter", "rule": "默认最多 3 个条件，其余收进“更多条件”"},
    "DataTable": {"use": "table", "rule": "一行讲清一个对象，主次信息放在同一格的两行"},
    "PeriodPicker": {"rule": "显示每个月的结账状态，不能选的月份也保留"}
  },
  "content": {
    "forbid": [
      {"text": "您", "message": "称呼用“你”或省略主语"},
      {"text": "！", "message": "不使用感叹号"},
      {"text": "操作失败", "message": "说明缺什么、在哪里改、找谁处理"}
    ],
    "button_forbid": [{"text": "确定", "message": "写明动作和对象，如“提交审批”"}]
  }
}
```

**Step 2：写 `guide.md`**（Agent 读，检查器不读）

```markdown
# 示例规范：版面与交互

虚构的示例，只用于演示规范包格式和测试。

- 每个视图只有一个主按钮，用于当前最主要的动作。
- 新增、编辑和查看单据用完整页面，操作栏放在底部。弹窗只做短任务：确认变化、填写原因、选择引用数据。
- 长表单在一页展开，按业务分组，不把字段藏进多层页签。
- 列表默认最多显示 3 个筛选条件，其余收进“更多条件”。
- 报错说明缺什么、在哪里改、找谁处理。
```

**Step 3：确认主题通过对比度检查**

```bash
PYTHONPATH=skills/saan-prototype/scripts python3 -c "import json,contrast;t=json.load(open('skills/saan-prototype/assets/design-example/design.json'))['themes']['light'];print(contrast.problems(t))"
```

预期：`[]`（`success` 的检查在 Task 2 加入，`#1A7F37` 对白色是 5.08:1）。

**Step 4：提交**

```bash
git add skills/saan-prototype/assets/design-example
git commit -m "Add a fictional design profile for saan-prototype"
```

---

### Task 2：`success` 的对比度检查

**Files：**
- Modify: `skills/saan-prototype/scripts/contrast.py`
- Test: `tests/saan-prototype/test_prototype.py`（`ThemeTests`）

**Step 1：写失败的测试**，加在 `ThemeTests` 里：

```python
    def test_optional_success_is_checked_when_present(self):
        t = dict(self.THEMES["neutral"], success="#7FD39A")
        self.assertTrue(any(m.startswith("success 在 surface") for m in mod("contrast").problems(t)))
        self.assertEqual(mod("contrast").problems(dict(self.THEMES["neutral"], success="#1A7F37")), [])
```

**Step 2：运行，确认失败**

```bash
python3 -m unittest discover -s tests/saan-prototype -k success
```

预期：FAIL（目录名带连字符，只能用 `discover`）。

**Step 3：实现。** 在 `PAIRS` 之后加 `OPTIONAL_PAIRS = [("success", "surface", 4.5)]`，并把 `problems()` 的循环改为同时遍历两组（现有的 `if fg in theme and bg in theme` 已经让缺省的可选令牌跳过）：

```python
    for fg, bg, need in PAIRS + OPTIONAL_PAIRS:
```

**Step 4：运行，确认通过**；再跑全部 20 个测试，确认没有回归。

**Step 5：提交**

```bash
git commit -am "Check the optional success color for contrast"
```

---

### Task 3：读取和校验规范包（`design.py`）

**Files：**
- Create: `skills/saan-prototype/scripts/design.py`
- Create: `tests/saan-prototype/test_design.py`

**Step 1：写失败的测试** `tests/saan-prototype/test_design.py`：

```python
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

    def test_missing_file(self):
        with self.assertRaises(ValueError):
            mod("design").load(Path("/nonexistent/design.json"))


if __name__ == "__main__":
    unittest.main()
```

**Step 2：运行，确认失败**

```bash
python3 -m unittest discover -s tests/saan-prototype -p test_design.py -v
```

预期：ERROR，找不到 `design.py`。

**Step 3：实现** `skills/saan-prototype/scripts/design.py`：

```python
"""Load and validate a saan-prototype design profile (design.json)."""
import json
from pathlib import Path

USES = {"status", "actions", "confirm", "field", "filter", "table"}


def load(path):
    """Return the profile as a dict. Raise ValueError with a Chinese message when it is unusable."""
    path = Path(path)
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"找不到设计规范包：{path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"design.json 无法解析：{e}")
    problems = []
    if not isinstance(d.get("name"), str) or not d["name"]:
        problems.append("缺少 name")
    if not isinstance(d.get("themes"), dict) or not d["themes"]:
        problems.append("themes 至少要有一套主题")
    comps = d.get("components", {})
    if not isinstance(comps, dict):
        problems.append("components 必须是对象")
        comps = {}
    for name, c in comps.items():
        use = (c or {}).get("use")
        if use is not None and use not in USES:
            problems.append(f"组件 {name} 的 use '{use}' 不在 {', '.join(sorted(USES))} 中")
    content = d.get("content", {})
    for key in ("forbid", "button_forbid"):
        for i, rule in enumerate(content.get(key, [])):
            if not isinstance(rule, dict) or not rule.get("text"):
                problems.append(f"content.{key}[{i}] 缺少 text")
    if problems:
        raise ValueError("设计规范包有误：" + "；".join(problems))
    d.setdefault("version", "")
    d.setdefault("components", {})
    d.setdefault("content", {})
    return d
```

**Step 4：运行，确认通过**（3 个测试）。

**Step 5：提交**

```bash
git add skills/saan-prototype/scripts/design.py tests/saan-prototype/test_design.py
git commit -m "Load and validate design profiles"
```

---

### Task 4：打包时使用规范包

**Files：**
- Modify: `skills/saan-prototype/scripts/build.py`（`load()`、`build()`）
- Test: `tests/saan-prototype/test_design.py`

**Step 1：写失败的测试**，加到 `test_design.py`：

```python
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
```

**Step 2：运行，确认失败**（`KeyError: 'design'` 或不抛 BuildError）。

**Step 3：实现。**

在 `build.py` 顶部 `import source_index` 旁边加 `import design  # noqa: E402`。

`load()` 里，`parts` 组装完、`return` 之前：

```python
    parts["design"] = None
    if m.get("design"):
        try:
            parts["design"] = design.load(root / m["design"])
        except ValueError as e:
            raise BuildError(str(e)) from e
```

新增：

```python
def themes_for(parts):
    """Themes a prototype may use: the profile's when it has one, otherwise the bundled set."""
    return parts["design"]["themes"] if parts["design"] else themes()
```

`build()` 里把 `all_themes = themes()` 改成 `all_themes = themes_for(parts)`，默认主题改为：

```python
    theme = theme or m.get("theme") or ("neutral" if not parts["design"] else next(iter(all_themes)))
```

`data` 增加：

```python
            "design": None if not parts["design"] else {
                "name": parts["design"]["name"], "version": parts["design"]["version"],
                "components": {k: {"rule": (v or {}).get("rule", "")} for k, v in parts["design"]["components"].items()}},
```

**Step 4：运行全部测试**（`test_design.py` 和 `test_prototype.py`）。预期全部通过；`test_example_builds_into_one_offline_file` 不受影响。

**Step 5：提交**

```bash
git commit -am "Build with a design profile's themes and components"
```

---

### Task 5：D1—D4 检查

**Files：**
- Modify: `skills/saan-prototype/scripts/check.py`
- Test: `tests/saan-prototype/test_design.py`

**Step 1：写失败的测试**：

```python
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
```

**Step 2：运行，确认失败。**

**Step 3：实现。** 在 `check.py`：

1. 正则，放在现有正则旁：

```python
COMPONENT = re.compile(r"""data-component\s*=\s*\\?["']([^"'\\]+)\\?["']""")
BUTTON = re.compile(r"<button\b[^>]*>([^<]*)</button>")
CONFIRM_TEXT = re.compile(r"""confirm\s*:\s*\{\s*text\s*:\s*["']([^"']*)["']""")
RAW_COLOR = re.compile(r"""(?:color|background|border|fill|stroke|outline)[\w-]*\s*:\s*[^;"'<>]*?(?:#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\()""")
COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.S)
COMMENT_LINE = re.compile(r"(?<![:\\])//.*$", re.M)
```

2. 去注释，保留行号（块注释换成同样数量的换行）：

```python
def strip_comments(src):
    src = COMMENT_BLOCK.sub(lambda m: "\n" * m.group(0).count("\n"), src)
    return COMMENT_LINE.sub("", src)
```

3. 新函数，由 `check_parts()` 在末尾调用 `out += design_checks(p)`（只在 `p.get("design")` 时）：

```python
def design_checks(p):
    out = []
    add = lambda level, code, where, msg: out.append((level, code, where, msg))
    d, m = p["design"], p["manifest"]
    confirmed = m.get("confirmed_text", [])
    files = p["pages"] + [(m.get("rules") or "rules.js", p["rules"])]
    reported = set()
    for rel, src in files:
        lines = strip_comments(src).splitlines()
        for n, line in enumerate(lines, 1):
            where = f"{rel}:{n}"
            for cm in COMPONENT.finditer(line):
                if cm.group(1) not in d["components"]:
                    add("error", "D1", where, f"组件「{cm.group(1)}」不在《{d['name']}》的组件清单中")
            for rule in d["content"].get("forbid", []):
                f = rule["text"]
                if f not in line:
                    continue
                hits = [t for t in confirmed if f in t and t in line]
                rest = line
                for t in hits:
                    rest = rest.replace(t, "")
                for t in hits:
                    if (t, f) not in reported:
                        reported.add((t, f))
                        add("finding", "D2", "manifest.json", f"已确认文案「{t}」含有规范禁用的「{f}」：报告给用户，不要为了通过而改")
                if f in rest:
                    add("error", "D2", where, f"出现规范禁用的「{f}」：{rule.get('message', '')}")
            labels = [b.strip() for b in BUTTON.findall(line)] + [b.strip() for b in CONFIRM_TEXT.findall(line)]
            for rule in d["content"].get("button_forbid", []):
                if rule["text"] in labels:
                    add("error", "D2", where, f"按钮文字只有「{rule['text']}」：{rule.get('message', '')}")
            if RAW_COLOR.search(line):
                add("error", "D4", where, "页面写死了颜色：用 runtime 的类名或主题令牌")
        if rel in dict(p["pages"]) and src.count("p-btn primary") > 1:
            add("note", "D3", rel, f"这个页面的代码里有 {src.count('p-btn primary')} 个主按钮；规范要求每个视图一个，互斥分支可以忽略")
    return out
```

4. B2 用规范包主题：把 `check_parts()` 里的主题来源改成

```python
    theme_set = all_themes if all_themes is not None else B.themes_for(p)
    theme_dir = "design.json themes" if p.get("design") else "themes"
    for name, t in theme_set.items():
        for msg in contrast.problems(t):
            add("error", "B2", f"{theme_dir}/{name}", msg)
```

   注意：现有自测把 `weak` 作为 `all_themes` 传入，行为不变。`B.load()` 对没有 `design` 的 manifest 返回 `parts["design"] = None`，但测试里自己拼的 `p` 可能没有这个键，所以用 `p.get("design")`；`themes_for` 也改成 `parts.get("design")`。

**Step 4：运行全部测试，确认通过。** 再跑 `python3 skills/saan-prototype/scripts/check.py skills/saan-prototype/assets/example/manifest.json`，预期 `通过`。

**Step 5：提交**

```bash
git commit -am "Check pages against a design profile (D1-D4)"
```

---

### Task 6：自测覆盖 D1—D4

**Files：**
- Modify: `skills/saan-prototype/scripts/check.py`（`selftest()`、`ALL_CODES`）

**Step 1：** `ALL_CODES` 加入 `"D1", "D2", "D3", "D4"`。先运行 `check.py --selftest`，预期 FAIL，列出 `没有改坏样例的检查：['D1', 'D2', 'D3', 'D4']`。

**Step 2：实现。** 加：

```python
def _designed():
    p = _example()
    p["design"] = B.design.load(B.SKILL / "assets" / "design-example" / "design.json")
    _page(p, lambda s: s.replace('<span class="p-tag">', '<span class="p-tag" data-component="StatusBadge">'))
    return p


DESIGN_MUTATIONS = [
    ("D1", "用了规范之外的组件名", lambda p: _page(p, lambda s: s + '\nvar x = \'<div data-component="Foo"></div>\';\n')),
    ("D2", "文案用了规范禁用的字", lambda p: _page(p, lambda s: s + '\nc.flash("请您稍后再试");\n')),
    ("D3", "一个页面两个主按钮", lambda p: _page(p, lambda s: s + '\nvar b = \'<button class="p-btn primary">再借</button>\';\n')),
    ("D4", "页面写死颜色", lambda p: _page(p, lambda s: s + '\nvar t = \'<p style="color: #ff0000">x</p>\';\n')),
]
```

`selftest()` 里，在 `MUTATIONS` 循环之后：先断言 `check_parts(_designed())` 为空（否则 `FAIL 带规范包的示例本身应当通过`），再对 `DESIGN_MUTATIONS` 用同样的 DETECTED/MISSED 打印和计数。

**Step 3：运行**

```bash
python3 skills/saan-prototype/scripts/check.py --selftest
```

预期：每行 `DETECTED`，最后 `SELFTEST PASS`。

**Step 4：提交**

```bash
git commit -am "Selftest the design profile checks"
```

---

### Task 7：runtime 的通用组件和组件名开关

**Files：**
- Modify: `skills/saan-prototype/runtime/runtime.css`
- Modify: `skills/saan-prototype/runtime/runtime.js`
- Test: `tests/saan-prototype/test_design.py`（打包产物里能找到新接口）

**Step 1：写失败的测试**：

```python
class RuntimeTests(unittest.TestCase):
    def test_runtime_has_design_features(self):
        js = (SKILL / "runtime" / "runtime.js").read_text(encoding="utf-8")
        css = (SKILL / "runtime" / "runtime.css").read_text(encoding="utf-8")
        for name in ("confirm: function", "data-disabled-reason", "data-component", 'data-bar="components"', "data-p-close"):
            self.assertIn(name, js)
        for cls in (".p-status", ".p-reason", ".p-filter", ".p-cell-sub", ".p-changes", ".p-effects", "data-changed-from", ".p-badge.component"):
            self.assertIn(cls, css)
```

**Step 2：运行，确认失败。**

**Step 3：CSS**，追加到 `runtime.css` 末尾：

```css
/* design profile components */
.p-status { display: inline-flex; align-items: center; gap: 4px; padding: 0 8px; border: 1px solid currentColor; border-radius: 999px; font-size: .85em; color: var(--muted); }
.p-status::before { content: "•"; }
.p-status[data-tone="success"] { color: var(--success, var(--text)); }
.p-status[data-tone="success"]::before { content: "✓"; }
.p-status[data-tone="notice"] { color: var(--notice); }
.p-status[data-tone="notice"]::before { content: "!"; }
.p-status[data-tone="danger"] { color: var(--danger); }
.p-status[data-tone="danger"]::before { content: "×"; }
.p-reason { display: inline-block; margin-left: 8px; color: var(--muted); font-size: .9em; }
.p-field.read > div { padding: 6px 0; }
.p-field[data-changed-from]::after { content: "原值：" attr(data-changed-from); color: var(--notice); font-size: .85em; }
.p-filter { margin: 8px 0; }
.p-filter > summary { cursor: pointer; color: var(--muted); }
.p-count { display: inline-block; min-width: 18px; padding: 0 5px; border-radius: 999px; background: var(--accent); color: var(--accent_text); font-size: 11px; text-align: center; }
.p-cell-sub { display: block; color: var(--muted); font-size: .85em; }
.p-changes th { width: 30%; }
.p-effects { margin: 12px 0; padding-left: 20px; }
.p-badge.component { color: var(--accent); }
body:not(.p-components-on) .p-badge.component { display: none; }
```

**Step 4：JS。** 在 `runtime.js`：

1. 状态 `S` 加 `components: false`。
2. `applyTheme()` 里先移除可选令牌，避免切到没有它的主题时残留：

```js
    ["success"].forEach(function (k) { if (!(k in t)) document.documentElement.style.removeProperty("--" + k); });
```

3. 新函数（放在 `attrs()` 之后）：

```js
  function confirmHtml(opt, name) {
    var data = opt.data || {};
    var dattrs = Object.keys(data).map(function (k) { return " data-" + esc(k) + '="' + esc(data[k]) + '"'; }).join("");
    var changes = (opt.changes || []).map(function (ch) {
      return "<tr><th>" + esc(ch.label) + "</th><td>" + esc(ch.from) + '</td><td aria-hidden="true">→</td><td>' + esc(ch.to) + "</td></tr>";
    }).join("");
    var effects = (opt.effects || []).map(function (ef) {
      ef = typeof ef === "string" ? { text: ef } : ef;
      return "<li" + (ef.open ? ' class="p-pending p-review-only"' : "") + attrs(ef) + ">" + esc(ef.text) + "</li>";
    }).join("");
    var btn = opt.confirm || { text: "确认" };
    return '<form class="p-confirm" data-action="' + esc(name) + '"' + dattrs + ">" +
      '<h2 class="p-h"' + attrs(opt) + ">" + esc(opt.title) + "</h2>" + (opt.body || "") +
      (changes ? '<table class="p-table p-changes"><tbody>' + changes + "</tbody></table>" : "") +
      (effects ? '<ul class="p-effects">' + effects + "</ul>" : "") +
      '<div class="p-row"><button class="p-btn ' + (opt.danger ? "danger" : "primary") + '"' + attrs(btn) + ">" + esc(btn.text) + "</button>" +
      '<button type="button" class="p-btn" data-p-close>返回</button></div></form>';
  }
```

4. `ctx()` 返回的对象加：`confirm: function (opt, name) { S.dialog = confirmHtml(opt, name); },`
5. `bar()`：把 `'<span class="p-tag-review">评审原型 · 示例数据为虚构</span>'` 改为

```js
      '<span class="p-tag-review">评审原型 · 示例数据为虚构' +
      (D.design ? " · 按《" + esc(D.design.name) + (D.design.version ? " " + esc(D.design.version) : "") + "》" : "") + "</span>" +
```

   并在“标注”复选框那一行之后插入：

```js
      (D.design ? '<label><input type="checkbox" data-bar="components"' + (S.components ? " checked" : "") + "> 组件名</label>" : "") +
```

6. `decorate(root)` 末尾加：

```js
    root.querySelectorAll("[data-disabled-reason]").forEach(function (el) {
      if (el.__reason) return;
      el.__reason = true;
      var s = document.createElement("span");
      s.className = "p-reason";
      s.textContent = el.getAttribute("data-disabled-reason");
      el.insertAdjacentElement("afterend", s);
    });
    if (D.design) root.querySelectorAll("[data-component]").forEach(function (el) {
      if (el.__comp) return;
      el.__comp = true;
      var name = el.getAttribute("data-component"), def = D.design.components[name];
      var b = document.createElement("span");
      b.className = "p-badge component";
      b.textContent = name;
      b.title = "组件 · " + name + "\n" + (def ? def.rule || "" : "规范中没有该组件");
      if (/^(TABLE|THEAD|TBODY|TR|UL|OL|SELECT|INPUT|TEXTAREA)$/.test(el.tagName)) el.insertAdjacentElement("beforebegin", b);
      else el.appendChild(b);
    });
```

7. `render()` 里 `classList.toggle("p-review-off", …)` 之后加 `document.body.classList.toggle("p-components-on", S.components);`
8. 点击处理里，`[data-go]` 判断之前加：

```js
    if (e.target.closest("[data-p-close]")) { S.dialog = null; S.flash = null; return render(); }
```

9. `change` 处理里加 `if (k === "components") S.components = e.target.checked;`

**Step 5：检查**

```bash
node --check skills/saan-prototype/runtime/runtime.js
python3 -m unittest discover -s tests/saan-prototype -v
```

预期：语法通过，全部测试通过。

**Step 6：提交**

```bash
git commit -am "Add design profile components and a component name toggle to the runtime"
```

---

### Task 8：浏览器验证 runtime

**Files：**
- 临时目录，不提交。

**Step 1：做一个临时的带规范包原型。** 用 Task 4 的 `designed_copy` 同样的方法复制示例到 `/tmp/sp-design/prototype`，在 `pages/devices.js` 里临时加：

- 状态列改成 `<span class="p-status" data-tone="success" data-component="StatusBadge">`；
- 一个 `<button class="p-btn" disabled data-disabled-reason="设备已借出，归还后可借" data-component="ActionBar">借用</button>`；
- 一个 `<div class="p-field read" data-changed-from="可借" data-component="Field"><span>状态</span><div>已借出</div></div>`；
- 一个 `<details class="p-filter" data-component="FilterBar"><summary>更多条件 <span class="p-count">1</span></summary>…</details>`；
- 一个按钮 `data-action="askReturn"`，动作里调用 `c.confirm({title: "归还这台设备？", proposal: "FR-R01", changes: [{label: "状态", from: "已借出", to: "可借"}], effects: ["释放借用", {text: "归还后是否通知下一位待定", open: "Q-01"}], confirm: {text: "确认归还", proposal: "FR-R01"}, data: {id: d.id}}, "return")`。

**Step 2：打包并在应用内浏览器打开**

```bash
python3 skills/saan-prototype/scripts/build.py /tmp/sp-design/prototype/manifest.json -o /tmp/sp-design/prototype.html
```

逐项确认，并截图存档到 `/tmp/sp-design/`：

1. 评审栏有“组件名”开关，默认关；打开后各组件显示组件名角标；关闭“标注”不影响组件名开关。
2. 状态显示“✓ 已借出”，颜色来自 `success`。
3. 不可用的按钮旁边直接显示原因，点击无反应。
4. 只读字段下显示“原值：可借”。
5. 确认框列出变化和后果；待定后果在关闭标注后隐藏；“返回”关闭对话框不改数据；“确认归还”执行 `return` 动作。
6. 浏览器控制台没有错误。

**Step 3：不带规范包回归。** 打包 `assets/example`，确认评审栏没有“组件名”开关，三套内置主题可切换，控制台无错误。

---

### Task 9：Agent 说明

**Files：**
- Create: `skills/saan-prototype/references/design-profile.md`
- Create: `skills/saan-prototype/patterns/components.md`
- Modify: `skills/saan-prototype/SKILL.md`
- Test: `PackageTests.test_referenced_files_exist`（已有）

**Step 1：写 `references/design-profile.md`**（英文，和其他 references 一致），内容：

1. 什么时候用：用户提到设计系统、规范、组件库，或给了目录；没提到时不问，交付时说明可以指定。
2. 格式：`design.json` 各字段（照设计文档第 3 节），`guide.md` 的作用。`use` 的六个取值链接到 `patterns/components.md`。
3. 复制：把 `design.json` 和 `guide.md` 复制到 `prototype/design/`，manifest 写 `"design": "design/design.json"`，删掉 `theme` 或改为规范包里的主题名。
4. 搭页面：先按 `components` 选组件，每个用到的区块写 `data-component`；规范没有对应组件时用基础样式，并在 `trace.md` 的“页面—组件”表里写“外观近似”。
5. 冲突：规范和来源冲突时以来源为准，冲突写进 `trace.md`。规范要求的确认步骤如果来源没有，确认框标为建议。
6. 只有文档、没有 `design.json` 时：Agent 可以起草，文件开头写明“草稿，待确认”，先给用户确认再用。
7. D 类检查的含义，以及 D2 业务发现不能改已确认文案。

**Step 2：写 `patterns/components.md`**（英文），按设计文档第 4 节的表，每个 `use` 一段写法示例，其中 `confirm` 用 room-booking 管理员取消的写法：

```js
Proto.action("askCancel", function (c, a) {
  c.confirm({
    title: "取消这条预约？", proposal: "FR-M04",
    body: '<label class="p-field"><span>取消原因 *</span><textarea name="reason"></textarea></label>',
    changes: [{label: "状态", from: "有效", to: "已取消"}],
    effects: ["释放该时段的占用", {text: "预约人能否看到取消原因待定", open: "Q-08"}],
    confirm: {text: "确认取消", proposal: "FR-M04"}, danger: true, data: {id: a.id}
  }, "cancel");
});
```

并写明：`confirm.text` 必须写；`c.confirm` 只改变呈现，执行仍由动作调用规则函数；来源没有确认步骤时 `title` 带 `proposal`。

**Step 3：改 `SKILL.md`。**

- frontmatter `version` 改为 `"0.2.0"`；description 末尾的触发词加入“设计规范、组件库”。
- “Read the source first” 之后加一节 **Design profile**（3—4 句）：有规范包时读 [design profile](references/design-profile.md)，复制到 `prototype/design/`，按 `components` 选组件并写 `data-component`，按 `guide.md` 排版；没有时用内置主题。
- Build 第 4 步的 “Choose layouts from `patterns/`” 一句，加上 “and, with a design profile, the components in [patterns/components.md](patterns/components.md)”。
- 第 6 步 `trace.md` 加 “with a design profile, a page-to-component table”。
- Package and check：说明 D1—D4，D2 的业务发现照 业务发现 处理。
- Deliver：有规范包时报告使用的规范和用到的组件。

**Step 4：运行**

```bash
python3 -m unittest discover -s tests/saan-prototype -v
```

预期：`test_referenced_files_exist` 等全部通过。

**Step 5：提交**

```bash
git add skills/saan-prototype
git commit -m "Document design profiles for the agent"
```

---

### Task 10：重新打包已记录的产出

**Files：**
- Modify: `page/prototype/example.html`
- 不修改：`tests/**/results/**` 里的记录（它们是 v0.1 的历史产出，只做回归渲染，不覆盖）

**Step 1：重建站点演示**

```bash
python3 skills/saan-prototype/scripts/build.py skills/saan-prototype/assets/example/manifest.json -o page/prototype/example.html
python3 scripts/check_site.py
```

预期：最后一行 `PASS: prototype demos match a fresh build`。

**Step 2：回归渲染。** 把四个已记录的验证原型（`tests/e2e/room-booking/results/2026-11-05/05-prototype`、`…/2026-11-05-rerun/05-prototype`、`tests/saan-prototype/results/2026-11-05/no-prd`、`…/2026-11-05-rerun/no-prd`）用新 runtime 打包到 `/tmp/sp-regress/`，在应用内浏览器逐个场景、逐个导航页渲染，记录脚本错误数。预期 0。

**Step 3：提交**

```bash
git add page/prototype/example.html
git commit -m "Rebuild the prototype demo with the v0.2 runtime"
```

---

### Task 11：全新上下文验证

**Files：**
- Create: `tests/saan-prototype/review-criteria-design.md`（先写先提交）
- Create: `tests/saan-prototype/results/<日期>-design/`（运行产出）
- Create: `docs/saan-prototype/validation-design.zh-CN.md`

**Step 1：先写评审标准并提交**，再开始运行。标准：

| 编号 | 标准 |
|---|---|
| D-P1 | 只用了规范包里的组件名；角标和页面区块一致 |
| D-P2 | 没有因为规范而增加来源以外的步骤；规范要求而来源没有的确认框标为建议 |
| D-P3 | 规范和来源的冲突写进了 `trace.md` |
| D-P4 | D2 业务发现如实报告，已确认文案没有被改 |
| D-P5 | v0.1 的标准 P1—P6 仍然通过 |
| D-P6 | 交付说明写了使用的规范和用到的组件 |

```bash
git add tests/saan-prototype/review-criteria-design.md
git commit -m "Write review criteria for the design profile run before generating"
```

**Step 2：运行。** 在隔离目录准备：技能副本（`skills/saan-prototype/`）、room-booking 的 PRD、示例规范包。用全新上下文的子代理执行，提示只包括“用 saan-prototype 根据 prd.md 做评审原型，设计规范包在 design-example/”。子代理看不到评审标准。

**Step 3：评审。** 在应用内浏览器按标准逐项操作，结果和发现的问题写进 `validation-design.zh-CN.md`（格式照 `validation.zh-CN.md`）。发现的问题修复后，记录哪些重跑了、哪些只做了回归。

**Step 4：提交产出和记录。**

---

### Task 12：使用说明、站点与版本

**Files：**
- Modify: `docs/saan-prototype/README.md`、`README.zh-CN.md`
- Modify: `page/prototype/index.html`、`page/prototype/zh/index.html`
- Modify: `.claude-plugin/plugin.json`

**Step 1：使用说明。** 在“How to use it / 怎么用”之后加一节“Design profiles / 设计规范包”：用途、目录格式（简表）、怎么指定、D1—D4 加进检查表、局限（只外观接近；`guide.md` 的规则靠人工看）。

**Step 2：站点。** 版本标签改为 `v0.2.0`；在“Patterns, themes, and a checker / 页面范式、主题和检查工具”表加一行“设计规范包”。改完 CSS 时更新 `?v=` 为文件 sha256 前 10 位。运行 `python3 scripts/check_site.py`。

**Step 3：插件版本。** `.claude-plugin/plugin.json` 的 `version` 升一个次版本。

**Step 4：全套检查**（与 CI 一致，3.9 和 3.12 各跑一次，有 `uv` 时用 `uv run --python 3.9`）：

```bash
python3 skills/saan-prototype/scripts/check.py --selftest
python3 -m unittest discover -s tests -v
python3 scripts/check_site.py
node --check skills/saan-prototype/runtime/runtime.js
```

**Step 5：提交。** 打标签 `saan-prototype/v0.2.0`、推送和开 PR 都等用户明确要求再做。

---

## 完成标准

- 不带规范包：现有 20 个测试、自测、站点检查全部通过，示例检查结果为 `通过`。
- 带规范包：`test_design.py` 全部通过，自测覆盖 D1—D4，浏览器验证 6 项通过。
- 全新上下文运行按 D-P1—D-P6 评审，结果如实记录，包括没通过的项。
