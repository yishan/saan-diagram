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
    if not isinstance(d, dict):
        raise ValueError("设计规范包有误：design.json 顶层必须是对象")
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
        if not isinstance(c, dict):
            problems.append(f"组件 {name} 必须是对象")
            continue
        use = c.get("use")
        if use is not None and use not in USES:
            problems.append(f"组件 {name} 的 use '{use}' 不在 {', '.join(sorted(USES))} 中")
    content = d.get("content", {})
    if not isinstance(content, dict):
        problems.append("content 必须是对象")
        content = {}
    for key in ("forbid", "button_forbid"):
        rules = content.get(key, [])
        if not isinstance(rules, list):
            problems.append(f"content.{key} 必须是数组")
            continue
        for i, rule in enumerate(rules):
            if not isinstance(rule, dict) or not rule.get("text"):
                problems.append(f"content.{key}[{i}] 缺少 text")
    if problems:
        raise ValueError("设计规范包有误：" + "；".join(problems))
    d.setdefault("version", "")
    d.setdefault("components", {})
    d.setdefault("content", {})
    return d
