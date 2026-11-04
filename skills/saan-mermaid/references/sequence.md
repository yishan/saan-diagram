# sequenceDiagram

Header: `sequenceDiagram`. Since 8.0. Example: `assets/examples/sequence.mmd`.

Saan use: interactions over time between systems or people. Use `alt` for failure paths.

## Syntax

- `participant P as 平台` declares an ID with a display name. Declare in reading order.
- Messages: `A->>B: 文字` (request), `B-->>A: 文字` (reply).
- Activation: `A->>+B: 请求` activates B; `B-->>-A: 结果` deactivates B. Or `activate B` / `deactivate B`.
- Blocks: `alt` / `else` / `end`, `opt`, `loop`, `par` / `and`, `critical` / `option`, `break`, `rect`, `box`. Every block ends with `end`.
- `autonumber` numbers the messages; useful when the reply refers to steps.

## Pitfalls

- A block without `end`, or an `else` outside `alt`, breaks rendering (S3).
- Deactivating a participant that is not active is a render error (SQ2).
- `;` in message text acts as a line break (SQ3). Avoid `:` inside the message text too; the first `:` ends the arrow part.
- A declared participant with no messages usually means a missing step (SQ1).
