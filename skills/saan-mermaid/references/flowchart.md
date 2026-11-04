# flowchart

Header: `flowchart TB` (or `LR` for a chain of about five nodes). Since 9.0; `graph` works from 8.0. Example: `assets/examples/flow-approval.mmd`, `flow-overview.mmd`, `arch-by-stage.mmd`.

Saan use: business flows (`%% saan: flow|approval|audit|overview`) and stage architecture (`%% saan: arch`). Declare the kind on the line above the header.

## Syntax to prefer

- Node: `apply[提交申请]`, decision: `check{审核单据}`. ASCII IDs, Chinese labels.
- New shapes (11.3+): `check@{ shape: diamond, label: "审核单据" }`. The checker treats `diamond`, `decision`, `diam`, and `question` as decisions. Use the classic forms when the host may be older.
- Edge label: `a -->|通过| b`. Dotted return: `fix -.-> apply`.
- Edge IDs (11.5+): `a e1@--> b`, then `e1@{ animate: true }`. Not needed for Saan diagrams.
- Group: `subgraph fin[财务部门]` … `end`; add `direction TB` inside when its nodes should stack.
- Invisible link to fix order: `a ~~~ b`. It does not count as a path in the checks.

## Pitfalls

- `end` as a node ID breaks parsing (S2). `End` or `finish` is fine.
- Parentheses, brackets, or colons in a label need quotes: `a["合同(草稿)"]` (S1).
- `style` and `linkStyle` are not allowed; use role classes (CL2).
- More than about 15 nodes reads badly (N1). Split into an overview plus details.
- A decision with one exit (P4) or an approval with no return (RT1) usually means the source is incomplete. Report it; do not invent the branch.
- Mermaid 12 lays flowcharts out with the `neo` look by default. The Saan frontmatter pins `look: classic` so v11 and v12 hosts match.
