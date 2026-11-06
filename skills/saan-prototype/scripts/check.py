#!/usr/bin/env python3
"""Check a prototype source directory against its source specification.

    python3 scripts/check.py path/to/prototype/manifest.json
    python3 scripts/check.py --selftest

Exit 0: clean. Exit 1: must fix (必须修改). Exit 2: only business findings (业务发现),
which are reported to the user and must not be "fixed" just to pass.
"""
import argparse
import copy
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as B  # noqa: E402
import contrast  # noqa: E402
import source_index  # noqa: E402

ATTR = re.compile(r"""data-(proposal|open|rule)\s*=\s*\\?["']([^"'\\]*)\\?["']""")
FLASH = re.compile(r"""\b(proposal|open|rule)\s*[:=]\s*["']([^"']+)["']""")      # { open: "Q-1" } or x.open = "Q-1"
VARIABLE = re.compile(r"""\b(proposal|open|rule)\s*[:=]\s*(?!["'\s])([A-Za-z_$][\w.$\[\]]*)""")  # { rule: why.rule }
EXTERNAL = re.compile(r"""(?:src|href)\s*=\s*\\?["']https?://|url\(\s*["']?https?://|\bfetch\s*\(|XMLHttpRequest|\bimport\s*\(""")
COMPONENT = re.compile(r"""data-component\s*=\s*\\?["']([^"'\\]+)\\?["']""")
COMPONENT_KEY = re.compile(r"""\bcomponent\s*:\s*["']([^"']+)["']""")  # c.confirm({component: "X"})
BUTTON = re.compile(r"<button\b[^>]*>(.*?)</button>")
TAG = re.compile(r"<[^>]+>")
CLASS_ATTR = re.compile(r"""\bclass\s*=\s*\\?["']([^"'\\]*)\\?["']""")
CONFIRM_TEXT = re.compile(r"""confirm\s*:\s*\{\s*text\s*:\s*["']([^"']*)["']""")
RAW_COLOR = re.compile(r"""(?:color|background|border|fill|stroke|outline)[\w-]*\s*:\s*[^;"'<>]*?(?:#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\()""")
COMMENT_BLOCK = re.compile(r"/\*.*?\*/", re.S)
COMMENT_LINE = re.compile(r"(?:^|(?<=[\s;]))(?<!:)//.*$", re.M)
KIND_OF_ATTR = {"open": "open", "rule": "rule"}
LEVELS = {"error": "必须修改", "finding": "业务发现", "note": "提示"}


def statuses(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "status" and isinstance(v, str):
                yield v
            else:
                yield from statuses(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from statuses(v)


def annotations(pages):
    """Yield (file, line, kind, id) for every annotation written in page code."""
    for rel, src in pages:
        for n, line in enumerate(src.splitlines(), 1):
            for rx in (ATTR, FLASH):
                for m in rx.finditer(line):
                    for i in m.group(2).split():
                        yield rel, n, m.group(1), i
            for m in VARIABLE.finditer(line):
                yield rel, n, m.group(1), "${" + m.group(2) + "}"


def strip_comments(src):
    src = COMMENT_BLOCK.sub(lambda m: "\n" * m.group(0).count("\n"), src)
    return COMMENT_LINE.sub("", src)


def _with_message(text, rule):
    msg = rule.get("message", "")
    return f"{text}：{msg}" if msg else text


def primary_buttons(src):
    """Count class attributes that carry both p-btn and primary, ignoring comments."""
    return sum(1 for c in CLASS_ATTR.findall(strip_comments(src)) if {"p-btn", "primary"} <= set(c.split()))


def design_checks(p):
    out = []
    add = lambda level, code, where, msg: out.append((level, code, where, msg))
    d, m = p["design"], p["manifest"]
    confirmed = m.get("confirmed_text", [])
    files = p["pages"] + [(m.get("rules") or "rules.js", p["rules"])]
    reported = {}
    for rel, src in files:
        lines = strip_comments(src).splitlines()
        for n, line in enumerate(lines, 1):
            where = f"{rel}:{n}"
            for cm in list(COMPONENT.finditer(line)) + list(COMPONENT_KEY.finditer(line)):
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
                    reported.setdefault((t, f), where)
                if f in rest:
                    add("error", "D2", where, _with_message(f"出现规范禁用的「{f}」", rule))
            labels = [TAG.sub("", b).strip() for b in BUTTON.findall(line)] + [b.strip() for b in CONFIRM_TEXT.findall(line)]
            for rule in d["content"].get("button_forbid", []):
                if rule["text"] not in labels:
                    continue
                if rule["text"] in confirmed:
                    reported.setdefault((rule["text"], rule["text"]), where)
                else:
                    add("error", "D2", where, _with_message(f"按钮文字只有「{rule['text']}」", rule))
            if RAW_COLOR.search(line):
                add("error", "D4", where, "页面写死了颜色：用 runtime 的类名或主题令牌")
        if rel in dict(p["pages"]):
            primaries = primary_buttons(src)
            if primaries > 1:
                add("note", "D3", rel, f"这个页面的代码里有 {primaries} 个主按钮；规范要求每个视图一个，互斥分支可以忽略")
    for (t, f), first in reported.items():
        add("finding", "D2", "manifest.json",
            f"已确认文案「{t}」含有规范禁用的「{f}」：报告给用户，不要为了通过而改（首次出现在 {first}）")
    return out


def check_parts(p, all_themes=None):
    """Return [(level, code, location, message)] for loaded prototype parts."""
    out = []
    add = lambda level, code, where, msg: out.append((level, code, where, msg))
    m = p["manifest"]
    idx = source_index.index(p["source"], source_index.patterns(m))
    known = source_index.all_ids(idx)
    used = {"open": set()}

    for rel, n, kind, i in annotations(p["pages"]):
        where = f"{rel}:{n}"
        if "${" in i or "+" in i:
            add("note", "N2", where, f"标注编号 '{i}' 是运行时才确定的，无法核对；能写死的编号请写死")
            continue
        if i not in known:
            add("error", "T1", where, f"data-{kind}='{i}' 在来源中找不到")
            continue
        want = KIND_OF_ATTR.get(kind)
        if want and i not in idx.get(want, {}):
            add("error", "T3", where, f"data-{kind} 只能用{ {'open': '待确认事项', 'rule': '规则'}[kind] }编号，'{i}' 不是")
        if kind == "open":
            used["open"].add(i)

    trace = p["trace"]
    for q in sorted(idx.get("open", {})):
        excused = any(q in line and re.search(r"不涉及|not covered", line, re.I) for line in trace.splitlines())
        if q not in used["open"] and not excused:
            add("error", "T2", m.get("trace") or "trace.md", f"待确认事项 {q} 既没有在原型里标出，也没有在追溯表中写明「不涉及」及原因")

    role_ids = {r.get("id") for r in m["roles"]}
    seen = set()
    covered = set()
    for s in p["scenarios"]:
        sid = s.get("id", "?")
        if sid in seen:
            add("error", "S4", m["scenarios"], f"场景 id '{sid}' 重复")
        seen.add(sid)
        for a in s.get("acceptance") or []:
            if a not in idx.get("acceptance", {}):
                add("error", "S1", m["scenarios"], f"场景 '{sid}' 引用的验收编号 {a} 在来源中找不到")
            covered.add(a)
        if s.get("role") and s["role"] not in role_ids:
            add("error", "S3", m["scenarios"], f"场景 '{sid}' 的角色 '{s['role']}' 不在 manifest.roles 中")
        for st in sorted(set(statuses(s.get("data")))):
            if st not in m.get("states", []):
                add("error", "C2", m["scenarios"], f"场景 '{sid}' 用了状态「{st}」，不在 manifest.states 中：原型不能新增状态")
    missing = sorted(set(idx.get("acceptance", {})) - covered)
    if missing:
        add("note", "N1", m["scenarios"], f"未覆盖的验收场景：{'、'.join(missing)}。不能在界面上演示的，在追溯表中说明")

    for st in m.get("states", []):
        if st not in p["source"]:
            add("finding", "C1", "manifest.json", f"状态「{st}」在来源中没有出现：确认来源是否定义了它")
    shown = "\n".join([src for _, src in p["pages"]] + [p["rules"], json.dumps(p["scenarios"], ensure_ascii=False)])
    for t in m.get("confirmed_text", []):
        if t not in p["source"]:
            add("finding", "W2", "manifest.json", f"已确认文案「{t}」在来源中没有出现：不要把建议文案列为已确认")
        if t not in shown:
            add("error", "W1", "manifest.json", f"已确认文案「{t}」没有在页面、规则或场景数据中原样出现")

    for rel, src in p["pages"] + [(m.get("rules") or "rules.js", p["rules"])]:
        for n, line in enumerate(src.splitlines(), 1):
            if EXTERNAL.search(line):
                add("error", "B1", f"{rel}:{n}", "原型不能请求外部资源或网络：资源要内联，数据写进场景")
    theme_set = all_themes if all_themes is not None else B.themes_for(p)
    for name, t in theme_set.items():
        where = f"design.json themes/{name}" if p.get("design") else f"themes/{name}.json"
        for msg in contrast.problems(t):
            add("error", "B2", where, msg)
    if p.get("design"):
        out += design_checks(p)
    return out


def check(manifest_path):
    try:
        parts = B.load(manifest_path)
    except (B.BuildError, json.JSONDecodeError) as e:
        return [("error", "M1", str(manifest_path), str(e))]
    return check_parts(parts)


def report(items):
    for level, code, where, msg in sorted(items, key=lambda x: ["error", "finding", "note"].index(x[0])):
        print(f"{LEVELS[level]} {where} [{code}] {msg}")
    if not items:
        print("通过")
    if any(x[0] == "error" for x in items):
        return 1
    return 2 if any(x[0] == "finding" for x in items) else 0


# ---------- selftest: every check must fire on a deliberately broken example ----------

def _example():
    return B.load(B.SKILL / "assets" / "example" / "manifest.json")


def _page(p, fn):
    p["pages"] = [(rel, fn(src)) for rel, src in p["pages"]]


MUTATIONS = [
    ("T1", "标注了来源中没有的编号", lambda p: _page(p, lambda s: s.replace('data-rule="FR-B01"', 'data-rule="FR-B99"'))),
    ("T2", "待确认事项既没标出也没说明", lambda p: p.update(trace=p["trace"].replace("Q-02", "Q-0x"))),
    ("T3", "data-open 用了规则编号", lambda p: _page(p, lambda s: s.replace('data-open="Q-01"', 'data-open="FR-B01"'))),
    ("S1", "场景引用不存在的验收编号", lambda p: p["scenarios"][0].update(acceptance=["AC-99"])),
    ("S3", "场景角色未声明", lambda p: p["scenarios"][0].update(role="admin")),
    ("S4", "场景 id 重复", lambda p: p["scenarios"][1].update(id=p["scenarios"][0]["id"])),
    ("C2", "场景数据里新增了状态", lambda p: p["scenarios"][0]["data"]["devices"][0].update(status="维修中")),
    ("C1", "manifest 声明了来源中没有的状态", lambda p: p["manifest"]["states"].append("报废")),
    ("W1", "已确认文案没在页面出现", lambda p: p["manifest"]["confirmed_text"].append("待确认事项")),
    ("W2", "把建议文案列为已确认", lambda p: p["manifest"]["confirmed_text"].append("借用成功啦")),
    ("B1", "页面请求外部资源", lambda p: _page(p, lambda s: s + '\nfetch("https://example.com/api");\n')),
    ("N1", "验收场景未覆盖", lambda p: p.update(scenarios=p["scenarios"][:1])),
    ("N2", "动态拼出的标注编号", lambda p: _page(p, lambda s: s.replace('data-open="Q-01"', 'data-open="${q}"'))),
]


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
THEME_MUTATION = ("B2", "主题文字对比度不足")
ALL_CODES = {"T1", "T2", "T3", "S1", "S3", "S4", "C1", "C2", "W1", "W2", "B1", "B2", "N1", "N2", "M1", "D1", "D2", "D3", "D4"}


def selftest():
    bad = 0
    base = _example()
    clean = check_parts(base)
    if clean:
        print(f"  FAIL  示例本身应当通过：{clean}")
        bad += 1
    covered = set()
    for code, what, fn in MUTATIONS:
        p = copy.deepcopy(base)
        fn(p)
        got = {c for _, c, _, _ in check_parts(p)}
        hit = code in got
        covered |= {code} if hit else set()
        bad += not hit
        print(f"  {'DETECTED' if hit else 'MISSED  '}  {code:<3} {what}" + ("" if hit else f"（实际：{sorted(got)}）"))
    designed = _designed()
    clean = check_parts(designed)
    if clean:
        print(f"  FAIL  带规范包的示例本身应当通过：{clean}")
        bad += 1
    for code, what, fn in DESIGN_MUTATIONS:
        p = copy.deepcopy(designed)
        fn(p)
        got = {c for _, c, _, _ in check_parts(p)}
        hit = code in got
        covered |= {code} if hit else set()
        bad += not hit
        print(f"  {'DETECTED' if hit else 'MISSED  '}  {code:<3} {what}" + ("" if hit else f"（实际：{sorted(got)}）"))
    weak = {"x": dict(B.themes()["neutral"], text="#B0B4BA")}
    if any(c == "B2" for _, c, _, _ in check_parts(copy.deepcopy(base), weak)):
        covered.add("B2")
        print(f"  DETECTED  B2  {THEME_MUTATION[1]}")
    else:
        bad += 1
        print(f"  MISSED    B2  {THEME_MUTATION[1]}")
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "manifest.json").write_text('{"title": "x"}', encoding="utf-8")
        if any(c == "M1" for _, c, _, _ in check(Path(td) / "manifest.json")):
            covered.add("M1")
            print("  DETECTED  M1  manifest 缺字段")
        else:
            bad += 1
            print("  MISSED    M1  manifest 缺字段")
    left = sorted(ALL_CODES - covered)
    if left:
        bad += len(left)
        print(f"  没有改坏样例的检查：{left}")
    print("SELFTEST PASS" if not bad else f"SELFTEST FAIL：{bad} 处")
    return 1 if bad else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Check a saan-prototype source directory")
    ap.add_argument("manifest", nargs="?")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if not a.manifest:
        ap.error("需要 manifest.json 路径，或 --selftest")
    return report(check(a.manifest))


if __name__ == "__main__":
    sys.exit(main())
