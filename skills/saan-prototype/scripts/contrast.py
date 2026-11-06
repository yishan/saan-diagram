"""WCAG 2.x contrast ratios for theme token pairs."""

PAIRS = [("text", "bg", 4.5), ("text", "surface", 4.5), ("muted", "surface", 4.5),
         ("accent_text", "accent", 4.5), ("danger", "surface", 4.5), ("notice", "surface", 4.5),
         ("accent", "surface", 3.0)]
OPTIONAL_PAIRS = [("success", "surface", 4.5)]
REQUIRED = {"label", "bg", "surface", "border", "text", "muted", "accent", "accent_text",
            "danger", "notice", "radius", "font_size"}


def luminance(hex_color):
    h = hex_color.lstrip("#")
    rgb = [int(h[k:k + 2], 16) / 255 for k in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def ratio(a, b):
    la, lb = sorted((luminance(a), luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def problems(theme):
    """Return a list of messages; empty means the theme passes."""
    out = [f"缺少 token：{k}" for k in sorted(REQUIRED - set(theme))]
    for fg, bg, need in PAIRS + OPTIONAL_PAIRS:
        if fg in theme and bg in theme:
            r = ratio(theme[fg], theme[bg])
            if r < need:
                out.append(f"{fg} 在 {bg} 上对比度 {r:.2f}，需 ≥ {need}")
    return out
