#!/usr/bin/env python3
"""Claude Code PostToolUse hook: block on Mermaid syntax errors right after a .mmd or .md file is written.

Only syntax problems that stop a diagram from rendering are reported here. Style, theme, and control-list
checks stay in check_mermaid.py, which you still run before delivering.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_mermaid as cm  # noqa: E402

SYNTAX = {"S0", "S1", "S2", "S3", "SQ2", "GT1", "GT2"}


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    path = (event.get("tool_input") or {}).get("file_path", "")
    if not path.endswith((".mmd", ".md", ".markdown")) or not Path(path).is_file():
        return 0
    body = Path(path).read_text(encoding="utf-8")
    items = cm.blocks(path, body)
    if path.endswith(".md") and not items:
        return 0
    out = [x for x in cm.review_issues(items) if x["level"] == "error" and x["code"] in SYNTAX]
    if not out:
        return 0
    print(cm.render(out, None), file=sys.stderr)
    print("修好这些 Mermaid 语法问题后再继续。", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
