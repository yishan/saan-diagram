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
        raise ValueError(f"找不到设计规范包：{path}") from None
    except OSError as e:
        raise ValueError(f"无法读取设计规范包：{path}") from e
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise ValueError(f"design.json 无法解析：{e}") from e
    if not isinstance(d, dict):
        raise ValueError("设计规范包有误：design.json 顶层必须是对象")
    problems = []
    if not isinstance(d.get("name"), str) or not d["name"]:
        problems.append("缺少 name")
    if "version" in d and not isinstance(d["version"], str):
        problems.append("version 必须是文字")
    if not isinstance(d.get("themes"), dict) or not d["themes"]:
        problems.append("themes 至少要有一套主题")
    else:
        for name, t in d["themes"].items():
            if not isinstance(t, dict):
                problems.append(f"主题 {name} 必须是对象")
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
            if not isinstance(rule, dict) or not isinstance(rule.get("text"), str) or not rule["text"]:
                problems.append(f"content.{key}[{i}] 缺少 text")
            elif "message" in rule and not isinstance(rule["message"], str):
                problems.append(f"content.{key}[{i}] 的 message 必须是文字")
    if problems:
        raise ValueError("设计规范包有误：" + "；".join(problems))
    d.setdefault("version", "")
    d.setdefault("components", {})
    d.setdefault("content", {})
    return d
