# swimlane-beta

Header: `swimlane-beta TB` or `LR`. Since 11.16 (beta). Example: `assets/examples/flow-swimlane.mmd`.

Saan use: flows where handoffs between roles matter, and any control list with `separate:` checks. Only `swimlane-beta` lanes count as roles for P5.

## Syntax

- Each top-level `subgraph id[角色]` … `end` is a lane. Nodes declared inside belong to that lane.
- Edges use flowchart syntax and are routed automatically; lanes stay aligned.

## Pitfalls

- Declare each node inside its lane before using it in an edge. A node first used outside any lane has no role, and P5 reports it as unconfirmed.
- Hosts older than 11.16 fail to render it. Check with `--target`, or fall back to `flowchart` + `subgraph` and say that lanes will not align.
- Nested subgraphs inside a lane do not create new roles; the outermost lane wins.
