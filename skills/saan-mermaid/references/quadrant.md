# quadrantChart

Header: `quadrantChart`. Since 10.2. Example: `assets/examples/quadrant.mmd`.

Saan use: priorities across two dimensions.

## Syntax

- `x-axis 低投入 --> 高投入`, `y-axis 低价值 --> 高价值`.
- `quadrant-1` is top right, then counterclockwise: 2 top left, 3 bottom left, 4 bottom right.
- Points: `经营预警: [0.3, 0.8]`, both values between 0 and 1.

## Pitfalls

- Long point labels overlap. Keep them to a few characters.
- The Saan frontmatter already sets `quadrantChart.pointTextPadding`; do not add `%%{init}%%` (CF1).
