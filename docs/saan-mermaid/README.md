# Saan Mermaid

**English** | [简体中文](README.zh-CN.md)

[Introduction and examples (中文)](https://kits.yishan.app/mermaid/)

Draw diagrams as Mermaid code that stays in your documents, and review business processes against a control list written before the diagram.

The review is what sets this skill apart. A small blind comparison (three scenarios, one run each) found no drawing-quality gain from an earlier version, so treat it as a review tool first.

## When to use it

| Use Saan Mermaid | Use [Saan Diagram](../saan-diagram/README.md) |
|---|---|
| Diagrams kept in Markdown, READMEs, and design documents | Reports, external delivery, and Feishu/Lark whiteboards |
| Sequence, state, and Gantt charts | IDEF0, and organization charts with data isolation |
| Reviewing a process against a control list | Exact layout and routing |

Both skills share the same first question, what exists versus how work runs, and the same role colors. Neither requires the other.

## Installation

```bash
npx skills add yishan/saankits --skill saan-mermaid
```

For manual installation, copy the complete `skills/saan-mermaid/` directory into the target agent's skills directory.

## Dependencies

- Python 3 for `scripts/check_mermaid.py`, standard library only.
- [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) 12 or later for rendering. `swimlane-beta` needs Mermaid 11.16 or later.

## How a review works

1. Write `controls.txt` before drawing, ideally from your policy or control requirements.

   ```text
   source: user
   control: 财务复核
   must_pass: 执行付款 through 财务复核
   separate: 提交付款申请 | 审核单据
   ```

2. Declare the diagram type with `%% saan: arch|flow|overview|approval|audit` above the type line.
3. Render, then check all diagrams of the process together:

   ```bash
   mmdc -i diagram.mmd -o diagram.svg -b white -q
   python3 skills/saan-mermaid/scripts/check_mermaid.py --controls controls.txt diagram.mmd diagram.svg
   ```

| Output | Meaning | What to do |
|---|---|---|
| 必须修改 | Style, syntax, a missing control, or a failed render | Fix the diagram |
| 业务发现 | A structural finding in the process | Report it. Do not delete a line to pass |
| 建议 | Long labels, wide diagrams, too many dotted lines | Follow unless there is a clear reason |
| 已确认 | A finding accepted with `%% accept P1: reason` | Keep the reason, written only after the user confirms |

Each line names the file and line, such as `doc.md:42 [P1]`. A Markdown file is checked block by block.

| Option | Use |
|---|---|
| `--target 11.12` | Flag diagram types and syntax the host's Mermaid version cannot render. Find the version by rendering a block that contains only `info` |
| `--theme saan-dark` | Require a theme. By default the theme is recognized from the frontmatter |
| `--theme-block saan-dark` | Print the frontmatter and role colors for a theme |
| `--json` | Machine-readable output |

Theme files live in `skills/saan-mermaid/assets/themes/`. `saan-light` is the default and `saan-dark` is for dark-only pages. A custom theme is a copy of one of these files; the checker rejects text and role colors below 4.5:1 contrast.

To catch syntax errors as soon as Claude Code writes a file, add `scripts/hook.py` as a `PostToolUse` hook in your settings. It blocks only on problems that stop a diagram from rendering:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{ "type": "command", "command": "python3 <skill-dir>/scripts/hook.py" }]
      }
    ]
  }
}
```

## Rules

| Trigger | Checks |
|---|---|
| `saan: flow` | P2 unreachable step, P3 dead end, P4 decision with one exit |
| `saan: approval` or `audit` | Also AP1 no decision, RT1 approval without a return |
| `saan: overview` | Also OV1 cycle in an overview |
| `saan: arch` | AR1 decision in an architecture diagram |
| `control` | CP1 control not on any diagram |
| `must_pass` | P1 control can be bypassed |
| `separate` | P5 incompatible steps in the same lane |
| `alias: name = label` | Lets a control name match a differently worded node label |
| Same-label nodes | CP4 warns that several nodes share a label and are checked as one step; write node IDs in the list to check them separately |
| `sequenceDiagram` | S3 unclosed block, SQ1 unused participant, SQ2 activation imbalance, SQ3 `;` in message text |
| `gantt` | GT1 unknown `after` ID, GT2 dependency loop, GT3 missing `todayMarker off` |
| `erDiagram` | ER1 entity with no relationship |
| Frontmatter | CL3 theme does not match a theme file, CF1 deprecated `%%{init}%%` |
| SVG input | G1 overlapping nodes, G2 edge label on a node, W1 too wide, R1 render failed |

## Limits

- It checks structure and the list. It does not know whether the business is right, and it finds nothing outside the list.
- A list extracted by the same agent that draws the diagram is weak evidence, so results mark it as not independent.
- Path logic covers flowchart, swimlane, and state diagrams. Sequence, Gantt, and ER diagrams get structural checks only.
- The SVG overlap check reads node and label boxes from Mermaid's output. It does not see crossing lines.
- Each Markdown host ships its own Mermaid version. The examples were rendered with Mermaid CLI 12.2 and have not been tested on GitHub, Feishu, or other hosts.
- `swimlane-beta`, `block-beta`, and `ishikawa-beta` are beta syntax and may not render on older hosts.

## Development and validation

```bash
python skills/saan-mermaid/scripts/check_mermaid.py --selftest
python -m unittest discover -s tests/saan-mermaid -v
```
