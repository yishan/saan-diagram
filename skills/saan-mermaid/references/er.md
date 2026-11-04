# erDiagram

Header: `erDiagram`. Since 8.0. Example: `assets/examples/er.mmd`.

Saan use: business entities and cardinality, at the conceptual level unless the user asks for columns.

## Syntax

- `合同 ||--o{ 结算单 : 产生` reads "one contract produces zero or more settlements".
- Cardinality markers: `||` exactly one, `|o` zero or one, `}|` one or more, `}o` zero or more. `--` is identifying, `..` is non-identifying.
- Attributes only when asked: `合同 { string 编号 }`.

## Pitfalls

- An entity with no relationship (ER1) usually means a missing link or an entity that belongs in another diagram.
- Do not turn a conceptual model into a physical schema; leave keys and types out unless asked.
