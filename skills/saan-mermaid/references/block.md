# block-beta

Header: `block-beta` (also `block` in newer releases). Since 10.8 (beta). Example: `assets/examples/arch-by-layer.mmd`.

Saan use: what exists, by layer. No side panels; use `saan-diagram` when they are needed.

## Syntax

- `columns 3` sets the grid width.
- A full-width layer title: `app["应用层"]:3`.
- Blocks fill the row left to right: `a1["合同管理"] a2["结算管理"] a3["经营分析"]`.

## Pitfalls

- The layout is a grid, not a graph; avoid edges between layers unless the source names a dependency.
- Beta syntax may change between releases. Say which version you tested with.
