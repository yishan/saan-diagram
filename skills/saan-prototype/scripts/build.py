#!/usr/bin/env python3
"""Bundle a prototype source directory into one self-contained HTML file.

    python3 scripts/build.py path/to/prototype/manifest.json [-o out.html] [--theme NAME]
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))
import design  # noqa: E402
import source_index  # noqa: E402

REQUIRED = ("title", "source", "roles", "scenarios", "pages")


class BuildError(Exception):
    pass


def themes():
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((SKILL / "themes").glob("*.json"))}


def load(manifest_path):
    """Read the manifest and every file it names. Returns a dict of loaded parts."""
    mp = Path(manifest_path).resolve()
    root = mp.parent
    m = json.loads(mp.read_text(encoding="utf-8"))
    missing = [k for k in REQUIRED if not m.get(k)]
    if missing:
        raise BuildError(f"manifest 缺少字段：{', '.join(missing)}")
    read = lambda rel: (root / rel).read_text(encoding="utf-8")
    try:
        parts = {
            "manifest": m, "root": root,
            "source": read(m["source"]),
            "rules": read(m["rules"]) if m.get("rules") else "",
            "scenarios": json.loads(read(m["scenarios"])),
            "pages": [(rel, read(rel)) for rel in m["pages"]],
            "trace": read(m["trace"]) if m.get("trace") else "",
        }
    except FileNotFoundError as e:
        raise BuildError(f"找不到 manifest 引用的文件：{e.filename}") from e
    if not parts["scenarios"]:
        raise BuildError("scenarios 至少要有一个场景")
    parts["design"] = None
    if m.get("design"):
        try:
            parts["design"] = design.load(root / m["design"])
        except ValueError as e:
            raise BuildError(str(e)) from e
    return parts


def themes_for(parts):
    """Themes a prototype may use: the profile's when it has one, otherwise the bundled set."""
    return parts["design"]["themes"] if parts.get("design") else themes()


def script_safe(text):
    return text.replace("</script", "<\\/script").replace("<!--", "<\\!--")


def json_safe(text):
    """Escape serialized JSON for a <script> element. Every '<' is inside a string, and \\u003c stays valid JSON."""
    return text.replace("<", "\\u003c")


def build(manifest_path, out=None, theme=None):
    parts = load(manifest_path)
    m = parts["manifest"]
    all_themes = themes_for(parts)
    theme = theme or m.get("theme") or ("neutral" if not parts["design"] else next(iter(all_themes)))
    if theme not in all_themes:
        raise BuildError(f"未知主题 '{theme}'，可选：{', '.join(all_themes)}")
    idx = source_index.index(parts["source"], source_index.patterns(m))
    defs = {i: d for ids in idx.values() for i, d in ids.items()}
    data = {"title": m["title"], "language": m.get("language", "zh-CN"), "timezone": m.get("timezone", "Asia/Shanghai"),
            "roles": m["roles"], "states": m.get("states", []), "theme": theme, "themes": all_themes,
            "scenarios": parts["scenarios"], "defs": defs,
            "design": None if not parts["design"] else {
                "name": parts["design"]["name"], "version": parts["design"]["version"],
                "components": {k: {"rule": v.get("rule", "")} for k, v in parts["design"]["components"].items()}}}
    rt = SKILL / "runtime"
    html = (rt / "shell.html").read_text(encoding="utf-8")
    html = html.replace("@LANG@", m.get("language", "zh-CN")).replace("@TITLE@", m["title"])
    html = html.replace("/*@CSS@*/", (rt / "runtime.css").read_text(encoding="utf-8"))
    html = html.replace("/*@DATA@*/", json_safe(json.dumps(data, ensure_ascii=False)))
    html = html.replace("/*@RUNTIME@*/", script_safe((rt / "runtime.js").read_text(encoding="utf-8")))
    html = html.replace("/*@RULES@*/", script_safe(parts["rules"]))
    html = html.replace("/*@PAGES@*/", "\n".join(f"/* {rel} */\n{script_safe(src)}" for rel, src in parts["pages"]))
    out = Path(out) if out else parts["root"].parent / "prototype.html"
    out.write_text(html, encoding="utf-8")
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description="Bundle a saan-prototype source directory into one HTML file")
    ap.add_argument("manifest")
    ap.add_argument("-o", "--out")
    ap.add_argument("--theme")
    a = ap.parse_args(argv)
    try:
        out = build(a.manifest, a.out, a.theme)
    except (BuildError, json.JSONDecodeError) as e:
        print(f"构建失败：{e}", file=sys.stderr)
        return 1
    print(f"已生成 {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
