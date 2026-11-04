---
name: "saan-mermaid"
description: "Draw diagrams as Mermaid code for Markdown, READMEs, and design docs, and review business processes against an independent control list. Use for Mermaid requests, process reviews, and sequence, state, or Gantt diagrams (流程审查、时序图、状态图、甘特图、用 Mermaid 画)."
metadata:
  author: "Yishan"
  version: "1.1.0"
---

# Saan Mermaid

Write diagrams as Mermaid code, and review business processes against a control list written before the diagram. Reply in the user's language.

The review is the point of this skill. A small blind comparison found no drawing-quality gain from the skill, so do not claim it makes diagrams better.

## Choose the right tool

Use this skill when the diagram will live in Markdown or a code repository, when the user asks for Mermaid, when an existing process needs a control review, or when the diagram is a sequence, state, or Gantt chart.

Use `saan-diagram` instead, if it is available, when any of these apply:

- The diagram is for a report, an external delivery, or a Feishu board.
- Layout precision matters, such as controlled routing or a platform layer diagram with side panels.
- The user needs IDEF0, or an organization chart with data isolation.

If `saan-diagram` is not available, say what Mermaid cannot do and offer the closest version.

## Write the control list first

Do this for any approval, audit, or control process, before drawing or reviewing. Other flows need it only when the source names a control.

Ask for the user's policy or control requirements when they are likely to exist. If the user is not available, extract them from the source. Save them as `controls.txt` (template: `assets/controls.example.txt`):

```text
source: user
control: 财务复核
must_pass: 执行付款 through 财务复核
separate: 提交付款申请 | 审核单据
```

- `source: user` means the user supplied the requirements. `source: document` means you extracted them. Tell the user that a list you extracted is not independent evidence.
- `control` checks that the step appears on a diagram.
- `must_pass` checks that the target cannot be reached without the control.
- `separate` checks that two steps sit in different `swimlane-beta` lanes.
- If a step exists in the source but is skipped or removed by a rule, still list it as a control. Draw it, and show the skip as a path.
- Names must equal a node label (spaces and `<br/>` ignored), so use the source's words. If the diagram words a step differently, add `alias: 财务复核 = 复核付款单` instead of renaming either side. If the source has no controls, write `none: reason`.
- Do not change the list to make a check pass. Change it only if it misread the source, and tell the user.

## Decide what the diagram explains

Ask first whether the diagram explains what exists or how work runs. Architecture nodes are capabilities. Flow nodes are business actions. Do not mix them in one diagram.

| What the user needs | Mermaid type | Declare | Notes |
|---|---|---|---|
| What exists, by stage | `flowchart LR` + `subgraph` | `arch` | Connect stages and external systems only |
| What exists, by layer | `block-beta` | | Beta; no side panels |
| How work runs | `flowchart TB` | `flow` | Nodes are verbs plus objects |
| How work runs, across roles | `swimlane-beta TB` | `flow` or `approval` | Mermaid 11.16+; lanes align, routing is automatic |
| How work runs, across systems | `flowchart TB` + `subgraph` | `overview` | Forward path only |
| Approval or control | `flowchart TB` or `swimlane-beta TB` | `approval` or `audit` | Keep decisions and returns |
| Interactions over time | `sequenceDiagram` | | Use `alt` for failure paths |
| Status changes | `stateDiagram-v2` | | Label each transition with its trigger |
| Entities and cardinality | `erDiagram` | | Conceptual level unless asked for columns |
| Schedule with dependencies | `gantt` | | Use `after`; add `todayMarker off` |
| Milestones | `timeline` | | No variance display |
| Priorities across two dimensions | `quadrantChart` | | Keep labels short |
| Causes behind an outcome | `ishikawa-beta` | | Beta; Mermaid 11.13+ |

`assets/examples/` holds tested files for these types, with the theme included. `references/` has one note per type (`flowchart.md`, `swimlane.md`, `sequence.md`, `state.md`, `er.md`, `gantt.md`, `timeline.md`, `quadrant.md`, `block.md`, `ishikawa.md`) with the version it needs and its pitfalls. Read the matching example and note before writing unfamiliar syntax. Use vertical layouts by default. Use `LR` only for a chain of about five nodes. If a paragraph explains it clearly, do not draw it. If the target host runs an older Mermaid, replace `swimlane-beta` with `flowchart` + `subgraph` and say that lanes will not align.

## Declare the diagram

Put `%% saan: arch|flow|overview|approval|audit` directly above the type line of every `flowchart` and `swimlane-beta`. Add `%% verify start: id` or `%% verify end: id` only if detection gets them wrong.

## Drawing rules

- Draw only what the source supports. Mark assumptions outside the diagram and do not invent systems or steps.
- Do not fill a gap in the source. If it does not say what happens on rejection, leave the branch undrawn and report the gap.
- Show preconditions and effects on the diagram, such as what becomes locked or allowed. Put any constraint that does not fit in the reply.
- Add a decision node only where the process really branches.
- An overview shows the forward path only. Approval and audit flows must keep decisions and returns, because removing them hides control risk.
- Do not add internal role lanes unless handoffs are the point of the diagram.
- Use solid lines by default. Reserve dotted lines for returns or optional paths.
- Keep one flowchart to about 15 nodes. Split larger ones into an overview plus detail diagrams.
- Keep node labels short. Put function lists in the surrounding text.

## Colors mean roles

Use the `saan-light` theme. Put this frontmatter at the top of every diagram, including charts that ignore some of the values:

```text
---
config:
  theme: base
  look: classic
  themeVariables:
    fontFamily: "PingFang SC, Microsoft YaHei, Noto Sans CJK SC, sans-serif"
    primaryColor: "#E3E5EA"
    primaryTextColor: "#1F2329"
    primaryBorderColor: "#E3E5EA"
    secondaryColor: "#E9ECF1"
    tertiaryColor: "#F5F6F8"
    lineColor: "#4E5563"
    textColor: "#1F2329"
    clusterBkg: "#F5F6F8"
    clusterBorder: "#D5D8DE"
    edgeLabelBackground: "#FFFFFF"
    dropShadow: "none"
    cScale0: "#E3E5EA"
    cScale1: "#E2EBFF"
    cScale2: "#E9ECF1"
    cScale3: "#F5F6F8"
  quadrantChart:
    pointTextPadding: 14
---
```

The theme files are `assets/themes/saan-light.json` and `assets/themes/saan-dark.json`. Print a ready block with `python3 <skill-dir>/scripts/check_mermaid.py --theme-block saan-dark`. Use `saan-dark` only when the page is dark and has no light mode. Use another theme only when the user asks for one: copy `saan-light.json`, change the values, and pass it with `--theme`. The checker rejects text and role colors below 4.5:1 contrast.

Business nodes use the default gray. Decisions are shown by shape. For anything else, define only the roles the diagram uses:

```text
classDef core fill:#E2EBFF,stroke:#2B5FD8,color:#1F2329
classDef hub fill:#D0D3D9,stroke:#D0D3D9,color:#1F2329
classDef system fill:#2B5FD8,stroke:#2B5FD8,color:#FFFFFF
classDef external fill:#8FB0FF,stroke:#8FB0FF,color:#1F2329
classDef ai fill:#FDEBD8,stroke:#F5C99B,color:#1F2329
```

Use `core` on at most three nodes. Do not use other class names, other colors, `style`, or `linkStyle`. The colors match `saan-diagram`, and the dark theme has its own role colors (`--theme-block saan-dark`). Do not add `%%{init}%%` directives; put settings in the frontmatter.

## Syntax that commonly breaks

- Quote labels that contain punctuation or brackets: `A["合同(草稿)"]`.
- Use ASCII IDs for nodes and show Chinese in the label: `apply[提交申请]`.
- Do not use lowercase `end` as a node ID.
- Set `direction TB` inside a `subgraph` when its nodes should stack.
- Use `<br/>` for a line break in flowchart labels.
- Avoid `:` and `;` in sequence message text.

## When the layout tangles

- Reorder the node declarations first; Mermaid places nodes in the order it first sees them.
- Use `a ~~~ b` to keep two nodes next to each other without drawing a line.
- Add spacing in the frontmatter only for this diagram: `flowchart:` with `nodeSpacing: 50` and `rankSpacing: 60` under `config:`.
- If the host registers the ELK layout, `layout: elk` under `config:` routes dense graphs better. Most Markdown hosts do not; check before relying on it.
- Stop after two rounds that do not reduce crossings or overlaps. Split the diagram, or recommend `saan-diagram` if the user needs exact placement.

## Check before delivering

The checker is `scripts/check_mermaid.py` in this skill's directory, and needs only Python 3. Render, then check all diagrams of the same process in one command:

```bash
mmdc -i diagram.mmd -o diagram.svg -b white -q
mmdc -i diagram.mmd -o diagram.png -b white -s 2 -q
python3 <skill-dir>/scripts/check_mermaid.py --controls controls.txt diagram.mmd diagram.svg
```

When the diagrams live in a Markdown file, pass the `.md` file itself. The script checks each fenced `mermaid` block. Each line of output names the file and line, such as `doc.md:42 [P1]`. Add `--json` when another tool reads the result.

When you know where the diagram will be shown, pass that host's Mermaid version with `--target 11.12`. The script then flags diagram types and syntax the host cannot render. To find a host's version, render a block that contains only `info`. Without `--target`, say which version you tested with.

Look at the PNG. If `mmdc` is missing, install `@mermaid-js/mermaid-cli`, version 12 or later. If it cannot be installed, tell the user the diagram is unrendered.

Handle the script output this way:

- **必须修改:** Fix the diagram until these lines are gone.
- **业务发现:** Tell the user. Do not delete a line, change the control list, or move a node just to pass. Fix the diagram only if the source shows it was drawn wrong.
- **`%% accept P1: reason`:** Add this only after the user confirms the finding is real and must stay. Do not write it on your own.
- **建议:** Follow these unless there is a clear reason not to.

The script checks structure and the control list. It checks path logic for flowchart, swimlane, and state diagrams, block and activation balance for sequence diagrams, dependencies for Gantt charts, and orphan entities for ER diagrams. With an SVG it also flags overlapping nodes and edge labels that sit on nodes. It does not know whether the business itself is right. A clean result means no listed problem was found, not that the process is correct.

To catch syntax errors as soon as a file is written, the user can add `scripts/hook.py` as a Claude Code `PostToolUse` hook for `Write|Edit|MultiEdit`. It reports only problems that stop a diagram from rendering. Suggest it, but do not edit the user's settings yourself.

Then check the image:

1. Every label is readable, and nothing overlaps.
2. The main path reads in one direction, without crossing lines that can be avoided.
3. Every node and connection comes from the source or a stated assumption.

If the image fails 1 or 2, follow "When the layout tangles".

Each Markdown host ships its own Mermaid version, so beta types may not render on GitHub, in a wiki, or in another host. For portable documents, prefer stable types, and say which version you tested with. Do not claim a diagram renders on a host you have not tested.

## Review an existing process

When the user brings an existing process, do not redraw it to match your reading. Transcribe it as it is, add the declaration and the control list, run the script, and report what it found. Do not add nodes or lines to make it pass.

## Deliver

Keep the reply short, and in this order:

1. **Diagrams:** Name the files, or edit them into the file the user named. Paste a fenced `mermaid` block only when there is one diagram and no file target. Do not repeat the frontmatter for other diagrams in the reply.
2. **Needs confirmation:** Business findings, source gaps, and contradictions, each pointing to a node or source line. State whether the control list came from the user or from the source.
3. **Assumptions and limits:** Only ones that change how the diagram reads.

Do not narrate your process or explain the script. Mention a check only when it found something or could not run. Add a PNG or SVG only when the user asks for an image or the target cannot render Mermaid.
