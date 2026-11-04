# stateDiagram-v2

Header: `stateDiagram-v2`. Since 8.0. Example: `assets/examples/state.mmd`.

Saan use: lifecycle of one business object, such as a contract or a payment order.

## Syntax

- `[*] --> 草稿` marks the start; `已归档 --> [*]` marks an end.
- Label every transition with its trigger: `草稿 --> 审批中: 提交`.
- `direction LR` on the second line for short lifecycles.

## Pitfalls

- A state that cannot be reached from `[*]` (P2) or that can never reach an end (P3) is usually a gap in the source.
- Keep one object per diagram. Two objects' states mixed together read as one lifecycle.
