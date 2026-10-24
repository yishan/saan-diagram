#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = ["PyYAML==6.0.3"]
# ///
"""saan-diagram renderer v1.3.0 (stages | layers | er | org | fishbone | timeline | quadrant | idef0): YAML spec -> HTML / SVG / PNG / Feishu whiteboard DSL.

Usage (uv reads the inline dependencies above; no venv needed):
  uv run render.py spec.yaml [-o out.html] [--svg out.svg] [--png out.png]
                    [--wb out.wb.json] [--brand "#3370FF"] [--titlebar plain|outline|gray|brand|dark]
                    [--orient horizontal|vertical] [--lint]

The spec says WHAT is on the diagram (columns, groups, nodes, edges, overlays,
paths) on a lane/row grid. This script owns HOW it looks: geometry on a 4px
grid, orthogonal routing, type ramp, tokens, legend - and the lint rules.
Never hand-place pixel coordinates in a spec.
"""
import argparse, html, json, math, sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover
    sys.exit("需要 PyYAML：用 uv run scripts/render.py … 运行，或先 pip install -r requirements.txt")

from spec_validation import SpecError, load_spec, validate_spec
from i18n import tr, join_labels

# ---------------------------------------------------------------- tokens
# Semantic roles (never inline hex elsewhere). Neutrals are fixed; everything that
# carries colour is derived from ONE brand (VI) colour so a diagram matches the
# user's identity: 内部系统 = 主色，外部服务 = 主色提亮，核心底色 = 主色浅调（全图 ≤3 处）。
DEFAULT_BRAND = "#3370FF"   # 飞书蓝
PRESETS = {"gray": DEFAULT_BRAND, "blue": "#1456F0"}   # backward-compatible `theme:` names
NEUTRAL = {
    "paper": "#FFFFFF", "rule": "#E4E6EB", "ink": "#1F2329", "muted": "#4E5969", "soft": "#646A73",
    "node": "#F2F3F5", "hub": "#DEE0E3", "node_text": "#1F2329", "frame": "#BBBFC4",
    "header": "#1F2329", "meta": "#7B7FF5", "ai_fill": "#FDEBD8", "ai_stroke": "#F5C99B",
}
TITLEBARS = ("plain", "outline", "gray", "brand", "dark")


def _rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        raise ValueError(h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _hex(rgb):
    return "#" + "".join(f"{max(0, min(255, round(v))):02X}" for v in rgb)


def mix(a, b, t):
    """t=0 → a, t=1 → b."""
    A, B = _rgb(a), _rgb(b)
    return _hex([A[i] + (B[i] - A[i]) * t for i in range(3)])


def _lum(h):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def on(bg, ink=NEUTRAL["ink"]):
    """Text colour for a filled shape: white unless ink reads better."""
    return "#FFFFFF" if contrast(bg, "#FFFFFF") >= contrast(bg, ink) else ink


def make_theme(brand=None, titlebar="plain"):
    brand = brand or DEFAULT_BRAND
    try:
        _rgb(brand)
    except ValueError:
        raise SpecError(f"brand 颜色 '{brand}' 无效，请用 #RRGGBB")
    if titlebar not in TITLEBARS:
        raise SpecError(f"titlebar '{titlebar}' 无效，可选 {TITLEBARS}")
    t = dict(NEUTRAL)
    sys_ext = mix(brand, "#FFFFFF", 0.45)
    t.update({
        "accent": brand, "accent_tint": mix(brand, "#FFFFFF", 0.86), "accent_zone": mix(brand, "#FFFFFF", 0.94),
        "sys_int": brand, "sys_int_text": on(brand),
        "sys_ext": sys_ext, "sys_ext_text": on(sys_ext),
    })
    bar = {"plain": t["paper"], "outline": t["paper"], "gray": "#EDEEF0", "brand": brand, "dark": "#2B2F36"}[titlebar]
    # plain（默认）：白底无边框，只有标题文字；outline：白底 + 中性灰 1px 线框；其余为实心底色，边框与底色同色
    edge = t["frame"] if titlebar == "outline" else bar
    t.update({"titlebar": bar, "titletext": on(bar), "titleedge": edge})
    return t
FONT = "'PingFang SC','Microsoft YaHei','Noto Sans CJK SC','Noto Sans SC',system-ui,sans-serif"
MONO = "'Geist Mono','SF Mono',Menlo,Consolas,ui-monospace,monospace"

# 4px grid: every structural size below divides by 4
CW, RH = 112, 48          # lane width, row height
NW, NH, NH_SUB = 88, 28, 40
DW, DH = 112, 44          # decision diamond
SYS_W, SYS_H = 88, 36     # system: rounded rect (rx 8), brand-filled
COL_PAD = 16
TOP_TITLE, TOP_HEAD = 48, 48
HEAD_W = 112              # vertical orientation: stage header strip on the left
MIN_END = 24              # arrowhead segment ≥ 24px: head + visible stroke (rule 7)
MIN_SEG = 12              # every other segment ≥ 12px
BODY_PAD = 24
CORNER = 8                # elbow radius (connector rule 1)
FAN = 12                  # min gap between attach points (rule 4)
LABEL_GAP = 6             # label mask ↔ stroke (rule 2)
FS = 12                   # CJK floor: never smaller (cut words, not type)
MAX_CORE = 3
MAX_EDGE_LABEL = 8        # wide chars

NODE_KINDS = {"module", "hub", "optional", "decision", "system", "external", "ai", "label", "doc", "store"}
PROCESS_KINDS = {"module", "hub", "decision", "optional", "ai"}   # DFD: things that transform data
EDGE_KINDS = {"flow", "data", "return", "bidir", "meta"}


def esc(s):
    return html.escape(str(s), quote=True)


def is_wide(c):
    return ord(c) > 0x2E80


def text_w(s, size=FS):
    """Per-character budget: wide/full-width = 1em, other = .6em (sans)."""
    return sum(size if is_wide(c) else size * 0.6 for c in str(s))


def wide_len(s):
    return sum(1 if is_wide(c) else 0.5 for c in str(s))


def up4(v):
    return int(math.ceil(v / 4.0) * 4)




# ---------------------------------------------------------------- model
class Box:
    def __init__(self, id, label, kind, x, y, w, h, **kw):
        self.id, self.label, self.kind = id, label, kind
        self.x, self.y, self.w, self.h = x, y, w, h
        self.core = False
        self.sub = None
        self.__dict__.update(kw)

    @property
    def cx(self): return self.x + self.w / 2

    @property
    def cy(self): return self.y + self.h / 2

    @property
    def r(self): return self.x + self.w

    @property
    def b(self): return self.y + self.h


ROUTE_FLIP = {"h": "v", "v": "h", "hvh": "vhv", "vhv": "hvh", "hv": "vh", "vh": "hv",
              "ll": "tt", "tt": "ll", "rr": "bb", "bb": "rr", "auto": "auto"}


def special_info(spec):
    """重点能力（special）：用浅橙色标出"这张图想让人特别注意的一类能力"，AI 只是其中一种用法。
    kind: special 与旧写法 kind: ai 等价（内部统一为 ai）。spec 顶层 special: {label, prefix} 给它命名；
    返回 (图例名称, 标签必须的前缀或 None)。结果缓存在 spec['_special']，可重复调用。"""
    if "_special" in spec:
        return spec["_special"]
    seen = set()

    def walk(o):
        if isinstance(o, dict):
            k = o.get("kind")
            if k in ("ai", "special"):
                seen.add(k)
                o["kind"] = "ai"
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(spec)
    cfg = spec.get("special") or {}
    if isinstance(cfg, str):
        cfg = {"label": cfg}
    if cfg.get("label"):
        res = (str(cfg["label"]), cfg.get("prefix"))
    elif "ai" in seen and "special" not in seen:      # 旧 spec：kind: ai → 图例"AI 能力"，标签以 AI 开头
        res = (tr(spec, 'AI 能力'), "AI")
    else:
        res = (tr(spec, '重点能力'), cfg.get("prefix"))
    spec["_special"] = res
    return res


class Diagram:
    def __init__(self, spec, theme=None, brand=None, titlebar=None, orient=None):
        self.spec = spec
        preset = PRESETS.get(theme or spec.get("theme") or "gray", DEFAULT_BRAND)
        self.t = make_theme(brand or spec.get("brand") or preset,
                            titlebar or spec.get("titlebar") or "plain")
        self.t["language"] = spec.get("language", "zh-CN")
        self.t["special_label"], self.t["special_prefix"] = special_info(spec)
        self.vertical = (orient or spec.get("orientation") or "horizontal") == "vertical"
        self.nodes, self.containers, self.edges = {}, {}, []
        self.by_label = {}
        self.warnings = []
        self._layout_columns()
        self._layout_groups()
        self._layout_nodes()
        self._layout_paths()
        self._collect_edges()
        self._align_nodes()
        self._finish_extent()

    # -- stages: columns (horizontal) or bands stacked top→bottom (vertical).
    # A spec never changes between orientations: `lane` always runs along the
    # stage's width, `row` always runs across stages.
    def _layout_columns(self):
        cols = self.spec.get("columns") or []
        if not cols:
            raise SpecError("spec.columns 不能为空：先定义阶段列")
        # Columns are always the layout grid; they are DRAWN as lanes only when the lane itself
        # carries meaning (roles, lifecycle stages, departments, value / non-value).
        sp = self.spec
        paths_only = not sp.get("nodes") and not (sp.get("groups") or sp.get("containers"))
        single_flow = paths_only and len((sp.get("paths") or {}).get("rows") or []) <= 1
        auto = not (sp.get("profile") == "dfd" or single_flow)
        self.show_lanes = bool(sp.get("swimlane", auto))
        self.show_header = self.show_lanes and any(c.get("label") for c in cols)
        self.cols = {}
        if not self.vertical:
            s = BODY_PAD
            for c in cols:
                lanes = int(c.get("lanes", 2))
                size = lanes * CW + 2 * COL_PAD
                self.cols[c["id"]] = {"s": s, "size": size, "label": c.get("label", ""), "lanes": lanes}
                s += size
            self.width = s + BODY_PAD
            self.top = TOP_TITLE + (TOP_HEAD if self.show_header else 0) + 16
            self.left = BODY_PAD
        else:
            s = TOP_TITLE
            for c in cols:
                lanes = int(c.get("lanes", 2))
                size = lanes * RH + 2 * COL_PAD
                self.cols[c["id"]] = {"s": s, "size": size, "label": c.get("label", ""), "lanes": lanes}
                s += size
            self.body_end = s
            self.left = BODY_PAD + (HEAD_W if self.show_header else 0) + 16
            self.top = TOP_TITLE

    def _finish_extent(self):
        if self.vertical:
            right = max([b.r for b in self.nodes.values()] + [c.r for c in self.containers.values()]
                        + [self.left + 4 * CW])
            self.width = up4(right + 16 + BODY_PAD)

    def row_pos(self, row):
        """Cross-stage coordinate of a row value (y when horizontal, x when vertical)."""
        return (self.left + row * CW) if self.vertical else (self.top + row * RH)

    def lane_pos(self, col, lane):
        """Along-stage coordinate of col:lane (x when horizontal, y when vertical)."""
        if col not in self.cols:
            raise SpecError(f"未知列 '{col}'，可选：{list(self.cols)}")
        c = self.cols[col]
        return c["s"] + COL_PAD + lane * (RH if self.vertical else CW)

    def cell(self, col, lane, row):
        """Top-left of a CW×RH cell."""
        if self.vertical:
            return self.row_pos(row), self.lane_pos(col, lane)
        return self.lane_pos(col, lane), self.row_pos(row)

    def _register(self, box):
        if box.id in self.nodes:
            raise SpecError(f"重复的节点 id：{box.id}")
        self.nodes[box.id] = box
        if not getattr(box, "path", None):  # 路径视图节点只能用 id 引用
            self.by_label.setdefault(box.label, []).append(box.id)

    def _make_node(self, nid, label, kind, col, lane, row, sub=None, **kw):
        if kind not in NODE_KINDS:
            raise SpecError(f"节点 '{label}' 的 kind '{kind}' 无效，可选 {sorted(NODE_KINDS)}")
        x0, y0 = self.cell(col, lane, row)
        if kind in ("system", "external"):
            w = max(SYS_W, up4(text_w(label) + 28))
            h = SYS_H + (8 if sub else 0)
            return Box(nid, label, kind, x0 + (CW - w) / 2, y0 + (RH - h) / 2, w, h, col=col, sub=sub, **kw)
        if kind == "decision":
            w = max(DW, up4(text_w(label) * 1.6 + 16))
            return Box(nid, label, kind, x0 + (CW - w) / 2, y0 + (RH - DH) / 2, w, DH, col=col, sub=sub, **kw)
        h = NH_SUB if sub else NH
        w = max(NW, up4(text_w(label) + 24), up4(len(sub or "") * 9 * 0.62 + 16))
        if w > CW - 8:  # long label spans lanes (anchored on its first lane)
            span = math.ceil((w + 8) / CW)
            return Box(nid, label, kind, x0 + (span * CW - w) / 2, y0 + (RH - h) / 2, w, h, col=col, sub=sub, **kw)
        return Box(nid, label, kind, x0 + (CW - w) / 2, y0 + (RH - h) / 2, w, h, col=col, sub=sub, **kw)

    # -- groups: a grid of items; frame / core tint are opt-in
    def _layout_groups(self):
        groups = list(self.spec.get("groups") or []) + list(self.spec.get("containers") or [])
        for c in groups:
            cid = c["id"]
            gcols = int(c.get("grid", 1))
            step = float(c.get("row_step", 1))   # >1 opens vertical room for arrows inside the group
            col, lane, row = c["col"], float(c.get("lane", 0)), float(c.get("row", 0))
            members, mains = [], []
            for i, it in enumerate(c.get("items") or []):
                if it in (None, "", "-"):
                    continue
                if isinstance(it, str):
                    it = {"label": it}
                label = it["label"]
                nid = it.get("id") or f"{cid}.{label}"
                kind = it.get("kind", "hub" if it.get("main") else "module")
                rr, ll = divmod(i, gcols)
                box = self._make_node(nid, label, kind, col, lane + ll, row + rr * step, sub=it.get("sub"),
                                      container=cid, main=bool(it.get("main")), core=bool(it.get("core")),
                                      control=it.get("control"), risk=it.get("risk"), actor=it.get("actor"))
                if kind in ("system", "external"):
                    self.warnings.append(f"[R3] 系统节点 '{label}' 被放进分组 '{cid}'：系统节点应在分组外，用点线接入")
                self._register(box)
                members.append(box)
                if box.main:
                    mains.append(box.id)
            if not members:
                raise SpecError(f"分组 '{cid}' 没有 items")
            pad = 8
            x = min(b.x for b in members) - pad
            y = min(b.y for b in members) - pad
            r = max(b.r for b in members) + pad
            bt = max(b.b for b in members) + pad
            self.containers[cid] = Box(cid, c.get("label", ""), "container", x, y, r - x, bt - y,
                                       members=[m.id for m in members], mains=mains, col=col,
                                       ctype=c.get("type", "set"), frame=bool(c.get("frame", False)),
                                       core=bool(c.get("core", False)))
            if not mains and c.get("type", "set") == "process":
                self.warnings.append(f"[R1] 流程分组 '{cid}' 没有标记 main 主线节点")

    # -- free nodes
    def _layout_nodes(self):
        for n in self.spec.get("nodes") or []:
            label = n["label"]
            kind = n.get("kind", "module")
            if kind == "system":
                own = n.get("owner")
                if own not in ("internal", "external"):
                    raise SpecError(f"系统节点 '{label}' 必须声明 owner: internal|external（R4）")
                kind = "system" if own == "internal" else "external"
            box = self._make_node(n.get("id") or label, label, kind, n["col"],
                                  float(n.get("lane", 0)), float(n.get("row", 0)), sub=n.get("sub"),
                                  container=None, main=False, core=bool(n.get("core")),
                                  control=n.get("control"), risk=n.get("risk"), actor=n.get("actor"))
            self._register(box)

    # -- paths: 路径对比视图 / 单条主流程视图（可选）
    def _layout_paths(self):
        P = self.spec.get("paths")
        self.path_band = None
        self.path_edges = []
        if not P:
            return
        start = float(P.get("row", 0))
        if self.nodes:  # only draw a divider when an architecture view sits above
            self.path_band = start
        ek = P.get("edge_kind", "data")
        r = start
        for p in P.get("rows") or []:
            name = p.get("name", f"row{r}")
            tag_col = p.get("tag_col", P.get("tag_col"))
            if tag_col:
                self._register(self._make_node(f"{name}#tag", name, "hub", tag_col,
                                               float(p.get("tag_lane", P.get("tag_lane", 0))), r,
                                               container=None, main=False, path=name, path_tag=True))
            prev = None
            for s in p.get("steps") or []:
                if isinstance(s, str):
                    raise SpecError(f"路径 '{name}' 的步骤需写成 {{label, col, lane}}")
                sid = f"{name}.{s.get('id', s['label'])}"
                box = self._make_node(sid, s["label"], s.get("kind", "module"), s["col"],
                                      float(s.get("lane", 0)), r + float(s.get("drow", 0)), sub=s.get("sub"),
                                      container=None, main=False, path=name, core=bool(s.get("core")),
                                      control=s.get("control"), risk=s.get("risk"), actor=s.get("actor"))
                self._register(box)
                if prev and not s.get("break"):
                    self.path_edges.append({"from": prev, "to": sid, "kind": p.get("edge_kind", ek),
                                            "label": s.get("in_label"), "path_step": True})
                prev = sid
            r += float(p.get("height", 1)) + 0.4
        self.path_edges += list(P.get("edges") or [])

    # -- edges
    def resolve(self, ref, ctx=""):
        if ref in self.nodes or ref in self.containers:
            return self.nodes.get(ref) or self.containers[ref]
        ids = self.by_label.get(ref, [])
        if len(ids) == 1:
            return self.nodes[ids[0]]
        if len(ids) > 1:
            raise SpecError(f"{ctx} 引用 '{ref}' 有歧义，请用 id：{ids}")
        raise SpecError(f"{ctx} 引用了不存在的节点 '{ref}'")

    def _collect_edges(self):
        for e in list(self.spec.get("edges") or []) + self.path_edges:
            kind = e.get("kind", "flow")
            if kind not in EDGE_KINDS:
                raise SpecError(f"连线 {e} 的 kind 无效，可选 {sorted(EDGE_KINDS)}")
            a = self.resolve(e["from"], "edge.from")
            b = self.resolve(e["to"], "edge.to")
            if kind == "meta" and not e.get("label"):
                self.warnings.append(f"[E3] 元关系连线 {a.label}→{b.label} 必须带标签")
            self.edges.append({**e, "kind": kind, "a": a, "b": b})

    # ------------------------------------------------------------ alignment
    def _free(self, n):
        """Free-standing node the aligner may nudge (not a group member, path step or container)."""
        return isinstance(n, Box) and n.id in self.nodes and n.kind != "label" \
            and not getattr(n, "container", None) and not getattr(n, "path", None)

    def _fits(self, n, x, y):
        """n moved to (x, y) stays in its stage and clear of every other node and visible group."""
        c = self.cols.get(getattr(n, "col", None))
        if c:
            lo, hi = (y, y + n.h) if self.vertical else (x, x + n.w)
            if lo < c["s"] + 2 or hi > c["s"] + c["size"] - 2:
                return False
        if (x < self.left - 0.5) if self.vertical else (y < self.top - 0.5):
            return False
        box = (x, y, x + n.w, y + n.h)
        for o in self.nodes.values():
            if o is not n and _overlap_rect(box, (o.x - 8, o.y - 8, o.r + 8, o.b + 8), 0):
                return False
        for c in self.containers.values():
            if (c.frame or c.core) and n.id not in c.members and _overlap_rect(box, (c.x - 4, c.y - 4, c.r + 4, c.b + 4), 0):
                return False
        return True

    def _align_nodes(self):
        """Rule 8: line up directly connected nodes that are slightly off (≤ half a lane / row),
        so the auto-routed edge between them runs straight instead of bending twice."""
        if self.spec.get("align") is False:
            return
        locked = {"x": set(), "y": set()}
        for e in self.edges:
            if e.get("route", "auto") != "auto" or any(e.get(k) is not None for k in ("mid_x", "mid_row", "port_a", "port_b")):
                continue
            a, b = e["a"], e["b"]
            gap_x = max(b.x - a.r, a.x - b.r)
            gap_y = max(b.y - a.b, a.y - b.b)
            dx, dy = b.cx - a.cx, b.cy - a.cy
            if gap_y > 0 and 0.5 < abs(dx) <= CW / 2:
                axis = "x"
            elif gap_x > 0 and 0.5 < abs(dy) <= RH / 2:
                axis = "y"
            else:
                continue
            for n, other in ((b, a), (a, b)):
                if not self._free(n) or n.id in locked[axis]:
                    continue
                nx = other.cx - n.w / 2 if axis == "x" else n.x
                ny = other.cy - n.h / 2 if axis == "y" else n.y
                if self._fits(n, nx, ny):
                    n.x, n.y = nx, ny
                    locked[axis] |= {n.id, other.id}
                    break

    # ------------------------------------------------------------ routing
    def _l_clear(self, a, b, mode):
        """Single-bend route a→b (hv / vh) with room for the arrow and no node in the way."""
        right, down = b.cx > a.cx, b.cy > a.cy
        if mode == "hv":
            p1 = (a.r if right else a.x, a.cy)
            p2 = (b.cx, b.y if down else b.b)
            room = ((p2[0] - p1[0]) if right else (p1[0] - p2[0]), (p2[1] - p1[1]) if down else (p1[1] - p2[1]))
        else:
            p1 = (a.cx, a.b if down else a.y)
            p2 = (b.x if right else b.r, b.cy)
            room = ((p2[1] - p1[1]) if down else (p1[1] - p2[1]), (p2[0] - p1[0]) if right else (p1[0] - p2[0]))
        if room[0] < MIN_SEG or room[1] < MIN_END:
            return False
        corner = (p2[0], p1[1]) if mode == "hv" else (p1[0], p2[1])
        skip = {a.id, b.id} | set(getattr(a, "members", None) or []) | set(getattr(b, "members", None) or [])
        return not any(_hit(seg, n) for n in self.nodes.values() if n.id not in skip and n.kind != "label"
                       for seg in ((p1, corner), (corner, p2)))

    def _mids(self, e):
        """Physical (mx, my) overrides from spec-level mid_x ("col:lane") / mid_row."""
        mx = my = None
        v = e.get("mid_x")
        if v is not None:
            if isinstance(v, str):
                c, l = v.split(":")
                along = self.lane_pos(c, float(l))
            else:
                along = float(v)
            if self.vertical:
                my = along
            else:
                mx = along
        if e.get("mid_row") is not None:
            cross = self.row_pos(float(e["mid_row"]))
            if self.vertical:
                mx = cross
            else:
                my = cross
        return mx, my

    @staticmethod
    def _mid(p, q, given):
        """Elbow coordinate between p and q; when free, keep the arrow end ≥ MIN_END."""
        if given is not None:
            return given
        m = (p + q) / 2
        span = abs(q - p)
        if span >= MIN_END + MIN_SEG and abs(q - m) < MIN_END:
            m = q - MIN_END if q > p else q + MIN_END
        return m

    def route(self, e):
        a, b = e["a"], e["b"]
        mode = e.get("route", "auto")
        if self.vertical:
            if mode not in ROUTE_FLIP:
                raise SpecError(f"未知 route '{mode}'，可选 auto|h|v|hvh|vhv|hv|vh|ll|rr|bb|tt")
            mode = ROUTE_FLIP[mode]
        gmx, gmy = self._mids(e)
        if mode == "auto":
            gap_x = max(b.x - a.r, a.x - b.r)
            gap_y = max(b.y - a.b, a.y - b.b)
            if gap_x > 0 and abs(a.cy - b.cy) < 3:
                mode = "h"
            elif gap_y > 0 and abs(a.cx - b.cx) < 3:
                mode = "v"
            else:
                # Prefer one bend over two: diagonal neighbours get an L when its path is clear.
                horiz = gap_x > 0 and (gap_x >= gap_y or gap_y <= 0)
                ls = ("hv", "vh") if horiz else ("vh", "hv")
                free = gmx is None and gmy is None and gap_x > 0 and gap_y > 0
                ok = [m for m in ls if free and self._l_clear(a, b, m)]
                # An L that lands on a side another edge already uses would run beside it; take the other L first.
                used = getattr(self, "_used_sides", set())
                right, down = b.cx > a.cx, b.cy > a.cy
                sides = {"hv": ("R" if right else "L", "T" if down else "B"),
                         "vh": ("B" if down else "T", "L" if right else "R")}
                ok.sort(key=lambda m: (a.id, sides[m][0]) in used or (b.id, sides[m][1]) in used)
                mode = ok[0] if ok else ("hvh" if horiz else "vhv")
        if mode in ("h", "hvh"):
            right = b.cx > a.cx
            p1 = (a.r if right else a.x, a.cy)
            p2 = (b.x if right else b.r, b.cy)
            if mode == "h":
                return [p1, (p2[0], p1[1])], ("R" if right else "L", "L" if right else "R")
            mx = self._mid(p1[0], p2[0], gmx)
            return [p1, (mx, p1[1]), (mx, p2[1]), p2], ("R" if right else "L", "L" if right else "R")
        if mode in ("v", "vhv"):
            down = b.cy > a.cy
            p1 = (a.cx, a.b if down else a.y)
            p2 = (b.cx, b.y if down else b.b)
            if mode == "v":
                return [p1, (p1[0], p2[1])], ("B" if down else "T", "T" if down else "B")
            my = self._mid(p1[1], p2[1], gmy)
            return [p1, (p1[0], my), (p2[0], my), p2], ("B" if down else "T", "T" if down else "B")
        if mode == "hv":
            right, down = b.cx > a.cx, b.cy > a.cy
            p1 = (a.r if right else a.x, a.cy)
            p2 = (b.cx, b.y if down else b.b)
            return [p1, (p2[0], p1[1]), p2], ("R" if right else "L", "T" if down else "B")
        if mode == "vh":
            right, down = b.cx > a.cx, b.cy > a.cy
            p1 = (a.cx, a.b if down else a.y)
            p2 = (b.x if right else b.r, b.cy)
            return [p1, (p1[0], p2[1]), p2], ("B" if down else "T", "L" if right else "R")
        if mode in ("ll", "rr"):
            left = mode == "ll"
            p1 = (a.x if left else a.r, a.cy)
            p2 = (b.x if left else b.r, b.cy)
            off = float(e.get("offset", 16))
            x = min(p1[0], p2[0]) - off if left else max(p1[0], p2[0]) + off
            if gmx is not None:
                x = gmx
            s = "L" if left else "R"
            return [p1, (x, p1[1]), (x, p2[1]), p2], (s, s)
        if mode in ("bb", "tt"):
            bot = mode == "bb"
            p1 = (a.cx, a.b if bot else a.y)
            p2 = (b.cx, b.b if bot else b.y)
            if gmy is not None:
                y = gmy
            else:
                off = float(e.get("offset", 16))
                y = max(p1[1], p2[1]) + off if bot else min(p1[1], p2[1]) - off
            s = "B" if bot else "T"
            return [p1, (p1[0], y), (p2[0], y), p2], (s, s)
        raise SpecError(f"未知 route '{mode}'，可选 auto|h|v|hvh|vhv|hv|vh|ll|rr|bb|tt")

    def all_routes(self):
        if getattr(self, "_routes", None) is not None:
            return self._routes
        # Explicit routes first, so auto edges know which box sides are already taken.
        self._used_sides = set()
        routed = {}
        order = sorted(range(len(self.edges)), key=lambda i: self.edges[i].get("route", "auto") == "auto")
        for i in order:
            pts, sides = routed[i] = self.route(self.edges[i])
            self._used_sides |= {(self.edges[i]["a"].id, sides[0]), (self.edges[i]["b"].id, sides[1])}
        out = []
        for i, e in enumerate(self.edges):
            pts, sides = routed[i]
            for key, idx, nb, side in (("port_a", 0, 1, sides[0]), ("port_b", -1, -2, sides[1])):
                off = e.get(key)
                if off:
                    x, y = pts[idx]
                    if side in ("T", "B"):
                        pts[idx] = (x + off, y)
                        if pts[nb][0] == x: pts[nb] = (x + off, pts[nb][1])
                    else:
                        pts[idx] = (x, y + off)
                        if pts[nb][1] == y: pts[nb] = (pts[nb][0], y + off)
            out.append((e, pts, sides))
        # rule 4: fan attach points that share one edge of one box
        groups = {}
        for i, (e, pts, sides) in enumerate(out):
            if not e.get("bus") and not e.get("port_a"):
                groups.setdefault((e["a"].id, sides[0]), []).append((i, 0))
            if not e.get("port_b"):
                groups.setdefault((e["b"].id, sides[1]), []).append((i, -1))
        for (nid, side), lst in groups.items():
            if len(lst) < 2:
                continue
            box = self.nodes.get(nid) or self.containers.get(nid)
            horiz = side in ("T", "B")
            span = box.w if horiz else box.h
            step = min(FAN, span / (len(lst) + 1))

            def far(item):
                i, end = item
                q = out[i][1][-1] if end == 0 else out[i][1][0]
                return q[0] if horiz else q[1]
            lst.sort(key=far)
            n = len(lst)
            for k, (i, end) in enumerate(lst):
                off = (k - (n - 1) / 2) * step
                pts = out[i][1]
                idx = 0 if end == 0 else len(pts) - 1
                nb = 1 if end == 0 else len(pts) - 2
                x, y = pts[idx]
                if horiz:
                    pts[idx] = (x + off, y)
                    if pts[nb][0] == x: pts[nb] = (x + off, pts[nb][1])
                else:
                    pts[idx] = (x, y + off)
                    if pts[nb][1] == y: pts[nb] = (pts[nb][0], y + off)
        self._routes = out
        return out

    # ------------------------------------------------------------ labels
    def label_box(self, label, pts, at="longest"):
        """Rule 2: the mask sits BESIDE its stroke with a 6px gap, never on it."""
        if at in ("start", "end") or isinstance(at, int):
            i = 0 if at == "start" else (len(pts) - 2 if at == "end" else at)
        else:
            i, bl = 0, -1
            for k in range(len(pts) - 1):
                l = math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1])
                if l > bl:
                    i, bl = k, l
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        w, h = up4(text_w(label) + 8), 16
        if abs(y0 - y1) < 0.5:  # horizontal → above the line
            mx = (x0 + x1) / 2
            return mx - w / 2, y0 - LABEL_GAP - h, w, h, i
        my = (y0 + y1) / 2      # vertical → to the right of the line
        return x0 + LABEL_GAP, my - h / 2, w, h, i

    def bounds(self):
        content_bottom = max([b.b for b in self.nodes.values()] + [c.b for c in self.containers.values()])
        if self.vertical:
            content_bottom = max(content_bottom, self.body_end - 24)
        legend_y = content_bottom + 40
        extra = self.legend_layout(legend_y)[1] + 22 * len(self.notes())
        return legend_y, legend_y + 56 + extra

    def chrome(self, legend_y):
        """Stage frames, header boxes, header rule and path divider for either orientation."""
        W = self.width
        body_bottom = legend_y - 16
        stages = []
        for c in (self.cols.values() if self.show_lanes else []):
            if self.vertical:
                frame = (BODY_PAD, c["s"], W - 2 * BODY_PAD, c["size"])
                head = (BODY_PAD, c["s"], HEAD_W, c["size"])
            else:
                frame = (c["s"], TOP_TITLE, c["size"], body_bottom - TOP_TITLE)
                head = (c["s"], TOP_TITLE, c["size"], TOP_HEAD)
            stages.append((frame, head, c["label"]))
        rule = None
        if self.show_header:
            rule = ((BODY_PAD + HEAD_W, TOP_TITLE, BODY_PAD + HEAD_W, body_bottom) if self.vertical
                    else (BODY_PAD, TOP_TITLE + TOP_HEAD, W - BODY_PAD, TOP_TITLE + TOP_HEAD))
        divider = None
        if self.path_band is not None:
            p = self.row_pos(self.path_band) - 16
            if self.vertical:
                divider = ((p, TOP_TITLE, p, body_bottom), (p + 8, TOP_TITLE + 16))
            else:
                divider = ((BODY_PAD, p, W - BODY_PAD, p), (BODY_PAD + 12, p + 20))
        return stages, rule, divider

    # ------------------------------------------------------------ svg
    def svg(self, slug="biz"):
        t = self.t
        routes = self.all_routes()
        legend_y, H = self.bounds()
        W = self.width
        o = []
        A = o.append
        title = self.spec.get("title", tr(self.t, '业务架构'))
        A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" '
          f'role="img" xml:lang="{esc(t.get("language", "zh-CN"))}" aria-labelledby="{slug}-title {slug}-desc" font-family="{FONT}">')
        A(f'<title id="{slug}-title">{esc(title)}</title><desc id="{slug}-desc">{esc(self.spec.get("desc", title))}</desc>')
        A('<defs>')
        for k, col in (("flow", t["ink"]), ("data", t["muted"]), ("meta", t["meta"]), ("accent", t["accent"])):
            A(f'<marker id="{slug}-m-{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
              f'orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{col}" stroke-width="1.6" '
              f'stroke-linejoin="round"/></marker>')
        A('</defs>')
        A(f'<rect width="{W}" height="{H}" fill="{t["paper"]}"/>')
        edge = f' stroke="{t["titleedge"]}"' if t["titleedge"] != t["titlebar"] else ""
        A(f'<rect x="{BODY_PAD+0.5}" y="0.5" width="{W-2*BODY_PAD-1}" height="{TOP_TITLE-1}" fill="{t["titlebar"]}"{edge}/>')
        A(f'<text x="{W/2}" y="{TOP_TITLE/2+5}" text-anchor="middle" fill="{t["titletext"]}" font-size="16" font-weight="600">{esc(title)}</text>')
        stages, rule, divider = self.chrome(legend_y)
        for (fx, fy, fw, fh), (hx, hy, hw, hh), label in stages:
            A(f'<rect x="{fx}" y="{fy}" width="{fw}" height="{fh}" fill="none" stroke="{t["rule"]}"/>')
            if self.show_header:
                A(f'<text x="{hx+hw/2}" y="{hy+hh/2+5}" text-anchor="middle" fill="{t["header"]}" font-size="14" font-weight="600">{esc(label)}</text>')
        if rule:
            A(f'<line x1="{rule[0]}" y1="{rule[1]}" x2="{rule[2]}" y2="{rule[3]}" stroke="{t["rule"]}"/>')
        if divider:
            (x1, y1, x2, y2), (lx, ly) = divider
            A(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{t["rule"]}"/>')
            lbl = (self.spec.get("paths") or {}).get("label")
            if lbl:
                A(f'<text x="{lx}" y="{ly}" fill="{t["soft"]}" font-size="12" font-weight="500">{esc(lbl)}</text>')
        # groups: only core tint and/or frame are visible; plain groups are pure layout
        for c in self.containers.values():
            if not (c.frame or c.core):
                continue
            fill = t["accent_zone"] if c.core else "none"
            stroke = (t["accent"] if c.core else t["frame"]) if c.frame else "none"
            A(f'<rect x="{c.x:.1f}" y="{c.y:.1f}" width="{c.w:.1f}" height="{c.h:.1f}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="1"/>')
        for ov in self.spec.get("overlays") or []:
            self._overlay(A, ov)
        # edges behind nodes
        labels = []
        for e, pts, _ in routes:
            col, width, dash, mk = self.edge_style(e)
            attrs = f'fill="none" stroke="{col}" stroke-width="{width}"'
            if dash:
                attrs += f' stroke-dasharray="{dash}"'
            if not e.get("no_arrow"):
                attrs += f' marker-end="url(#{slug}-m-{mk})"'
            if e["kind"] == "bidir":
                attrs += f' marker-start="url(#{slug}-m-{mk})"'
            A(f'<path d="{self._path_d(pts)}" {attrs}/>')
            if e.get("label"):
                at = e.get("label_at", "end" if e.get("bus") else "longest")
                x, y, w, h, _ = self.label_box(e["label"], pts, at)
                lc = t["meta"] if e["kind"] == "meta" else (t["accent"] if e.get("emphasis") else t["soft"])
                labels.append((x, y, w, h, e["label"], lc))
        for x, y, w, h, s, lc in labels:  # rule 6: masks before nodes
            A(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{h}" fill="{t["paper"]}"/>')
            A(f'<text x="{x+w/2:.1f}" y="{y+12:.1f}" text-anchor="middle" fill="{lc}" font-size="{FS}" font-weight="500">{esc(s)}</text>')
        for n in self.nodes.values():
            self._node(A, n)
        self._legend(A, legend_y, W, slug)
        A('</svg>')
        return "\n".join(o), W, H

    def edge_style(self, e):
        t, k = self.t, e["kind"]
        if e.get("emphasis"):
            return t["accent"], 2, ("" if k == "flow" else "2,3"), "accent"
        if k == "flow":
            return t["ink"], 1.5, "", "flow"
        if k == "meta":
            return t["meta"], 1.2, "5,4", "meta"
        return t["muted"], 1.2, "2,3", "data"

    def _path_d(self, pts):
        d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
        for i in range(1, len(pts) - 1):
            (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
            l1, l2 = math.hypot(x1 - x0, y1 - y0), math.hypot(x2 - x1, y2 - y1)
            r = min(CORNER, l1 / 2, l2 / 2)
            if r < 0.5:
                d += f" L{x1:.1f},{y1:.1f}"
                continue
            ax, ay = x1 - (x1 - x0) / l1 * r, y1 - (y1 - y0) / l1 * r
            bx, by = x1 + (x2 - x1) / l2 * r, y1 + (y2 - y1) / l2 * r
            d += f" L{ax:.1f},{ay:.1f} Q{x1:.1f},{y1:.1f} {bx:.1f},{by:.1f}"
        return d + f" L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"

    def node_style(self, n):
        t = self.t
        fill = {"module": t["node"], "hub": t["hub"], "optional": t["paper"], "decision": t["paper"],
                "ai": t["ai_fill"], "label": "none", "doc": t["paper"], "store": t["paper"]}[n.kind]
        stroke, dash, weight = None, None, 600 if n.kind == "hub" else 400
        if n.kind == "optional":
            stroke, dash = t["frame"], "4,3"
        if n.kind == "decision":
            stroke = t["ink"]
        if n.kind == "ai":
            stroke = t["ai_stroke"]
        if n.kind in ("doc", "store"):
            stroke = t["muted"]
        if n.core:
            fill, stroke, weight = t["accent_tint"], t["accent"], 600
        return fill, stroke, dash, weight

    def sys_style(self, n):
        t = self.t
        if n.kind == "system":
            return t["sys_int"], t["sys_int_text"]
        return t["sys_ext"], t["sys_ext_text"]

    def _node(self, A, n):
        t = self.t
        if n.kind in ("system", "external"):
            fill, tc = self.sys_style(n)
            A(f'<rect x="{n.x:.1f}" y="{n.y:.1f}" width="{n.w:.1f}" height="{n.h:.1f}" rx="8" fill="{fill}"/>')
            ty = n.cy + 4 - (6 if n.sub else 0)
            A(f'<text x="{n.cx:.1f}" y="{ty:.1f}" text-anchor="middle" fill="{tc}" font-size="{FS}" font-weight="500">{esc(n.label)}</text>')
            if n.sub:
                A(f'<text x="{n.cx:.1f}" y="{ty+13:.1f}" text-anchor="middle" fill="{tc}" fill-opacity=".8" font-size="9" font-family="{MONO}">{esc(n.sub)}</text>')
            return
        if n.kind == "label":
            A(f'<text x="{n.cx:.1f}" y="{n.cy+4:.1f}" text-anchor="middle" fill="{t["soft"]}" font-size="{FS}">{esc(n.label)}</text>')
            return
        fill, stroke, dash, weight = self.node_style(n)
        sa = f' stroke="{stroke}" stroke-width="1"' if stroke else ""
        if dash:
            sa += f' stroke-dasharray="{dash}"'
        if n.kind == "decision":
            pts = f"{n.cx},{n.y} {n.r},{n.cy} {n.cx},{n.b} {n.x},{n.cy}"
            A(f'<polygon points="{pts}" fill="{fill}"{sa}/>')
        elif n.kind == "doc":     # 单据 / 文档：底边波浪
            w4, yb = n.w / 4, n.b - 4
            d = (f"M{n.x:.1f},{n.y:.1f} H{n.r:.1f} V{yb:.1f} "
                 f"Q{n.r - w4:.1f},{yb + 8:.1f} {n.cx:.1f},{yb:.1f} T{n.x:.1f},{yb:.1f} Z")
            A(f'<path d="{d}" fill="{fill}"{sa}/>')
        elif n.kind == "store":   # 数据存储（Gane-Sarson）：右侧开口 + 左侧编号格
            A(f'<rect x="{n.x:.1f}" y="{n.y:.1f}" width="{n.w:.1f}" height="{n.h:.1f}" fill="{fill}"/>')
            A(f'<path d="M{n.r:.1f},{n.y:.1f} H{n.x:.1f} V{n.b:.1f} H{n.r:.1f}" fill="none" stroke="{stroke}"/>')
            if n.sub:
                A(f'<line x1="{n.x + 28:.1f}" y1="{n.y:.1f}" x2="{n.x + 28:.1f}" y2="{n.b:.1f}" stroke="{stroke}"/>')
                A(f'<text x="{n.x + 14:.1f}" y="{n.cy + 3:.1f}" text-anchor="middle" fill="{t["soft"]}" font-size="9" font-family="{MONO}">{esc(n.sub)}</text>')
            A(f'<text x="{n.cx + (14 if n.sub else 0):.1f}" y="{n.cy + 4:.1f}" text-anchor="middle" fill="{t["node_text"]}" font-size="{FS}" font-weight="{weight}">{esc(n.label)}</text>')
            self._badge(A, n)
            return
        else:
            A(f'<rect x="{n.x:.1f}" y="{n.y:.1f}" width="{n.w:.1f}" height="{n.h:.1f}" rx="4" fill="{fill}"{sa}/>')
        ty = n.cy + 4 - (6 if n.sub else 0)
        A(f'<text x="{n.cx:.1f}" y="{ty:.1f}" text-anchor="middle" fill="{t["node_text"]}" font-size="{FS}" font-weight="{weight}">{esc(n.label)}</text>')
        if n.sub:
            A(f'<text x="{n.cx:.1f}" y="{ty+13:.1f}" text-anchor="middle" fill="{t["soft"]}" font-size="9" font-family="{MONO}">{esc(n.sub)}</text>')
        self._badge(A, n)

    def _badge(self, A, n):
        """Audit control point: dark tag on the node's top-right corner (K1, K2 …)."""
        if not getattr(n, "control", None):
            return
        bw = up4(len(str(n.control)) * 6 + 10)
        A(f'<rect x="{n.r - bw + 6:.1f}" y="{n.y - 8:.1f}" width="{bw}" height="16" rx="8" fill="{self.t["ink"]}"/>')
        A(f'<text x="{n.r - bw / 2 + 6:.1f}" y="{n.y + 3.5:.1f}" text-anchor="middle" fill="#FFFFFF" font-size="9" font-weight="600" font-family="{MONO}">{esc(n.control)}</text>')

    def controls(self):
        return [(n.control, n.label, getattr(n, "risk", None) or "") for n in self.nodes.values()
                if getattr(n, "control", None)]

    def notes(self):
        """Lines printed under the legend: control matrix (audit) and value ratio (opportunity)."""
        out = [tr(self.t, '{0}  {1}：{2}', c, lab.rstrip('？?'), risk or tr(self.t, '（未写风险）')) for c, lab, risk in self.controls()]
        vals = {cid: c.get("value") for cid, c in ((c["id"], c) for c in self.spec.get("columns") or [])}
        if any(v is not None for v in vals.values()):
            nodes = [n for n in self.nodes.values() if n.kind not in ("system", "external", "label")]
            va = sum(1 for n in nodes if vals.get(n.col) is True)
            nva = sum(1 for n in nodes if vals.get(n.col) is False)
            if va + nva:
                out.insert(0, tr(self.t, '增值环节 {0} 个 · 非增值环节 {1} 个（占 {2}%）', va, nva, nva * 100 // (va + nva)))
        return [line for note in out for line in _wrap_w(note, self.width - 2 * BODY_PAD - 64)]

    def _wrap(self, s, k):
        s = str(s)
        if any(c.isascii() and c.isalpha() for c in s):
            return _wrap_w(s, k * FS)
        if "\n" in s:
            return s.split("\n")
        if len(s) <= 3:
            return [s]
        n = max(2, math.ceil(len(s) / k))
        base, extra = divmod(len(s), n)
        out, i = [], 0
        for j in range(n):
            ln = base + (1 if j >= n - extra else 0)
            out.append(s[i:i + ln]); i += ln
        return out

    def overlay_rect(self, ov):
        targets = ov.get("targets") or []
        boxes = []
        for ref in targets:
            if ref in self.containers:
                c = self.containers[ref]
                boxes.append(Box("_", "", "_", c.x + 4, c.y + 4, c.w - 8, c.h - 8))
            else:
                boxes.append(self.resolve(ref, "overlay.targets"))
        if not boxes:
            raise SpecError(f"overlay '{ov.get('label')}' 没有 targets")
        whole = all(r in self.containers for r in targets)
        pad, grow = (0, 24) if whole else (8, 16)
        top = ov.get("title_pos") == "top"
        x = min(b.x for b in boxes) - pad
        y = min(b.y for b in boxes) - pad - (grow if top else 0)
        r = max(b.r for b in boxes) + pad
        bt = max(b.b for b in boxes) + pad + (0 if top else grow)
        return x, y, r, bt, top

    def _overlay(self, A, ov):
        t = self.t
        x, y, r, bt, top = self.overlay_rect(ov)
        kind = ov.get("kind", "ai")
        if kind == "ai":
            A(f'<rect x="{x:.1f}" y="{y:.1f}" width="{r-x:.1f}" height="{bt-y:.1f}" rx="4" fill="{t["ai_fill"]}"/>')
            col = t["ink"]
        else:  # scope: dashed outline, no fill (二期范围 / 试点单位 …)
            A(f'<rect x="{x:.1f}" y="{y:.1f}" width="{r-x:.1f}" height="{bt-y:.1f}" rx="4" fill="none" stroke="{t["soft"]}" stroke-dasharray="4,3"/>')
            col = t["soft"]
        label = ov.get("label", "")
        if top:
            A(f'<text x="{(x+r)/2:.1f}" y="{y+13:.1f}" text-anchor="middle" fill="{col}" font-size="{FS}" font-weight="500">{esc(label)}</text>')
        else:
            A(f'<text x="{r-8:.1f}" y="{bt-4:.1f}" text-anchor="end" fill="{col}" font-size="{FS}" font-weight="500">{esc(label)}</text>')

    def legend_items(self):
        t = self.t
        used_n = {n.kind for n in self.nodes.values()}
        used_e = {e["kind"] for e in self.edges}
        ovk = {ov.get("kind", "ai") for ov in self.spec.get("overlays") or []}
        it = []
        if "hub" in used_n: it.append(("rect", t["hub"], None, tr(self.t, '主线节点')))
        dfd = self.spec.get("profile") == "dfd"
        if "module" in used_n: it.append(("rect", t["node"], None, tr(self.t, '处理过程') if dfd else tr(self.t, '功能模块')))
        if any(n.core for n in self.nodes.values()) or any(c.core for c in self.containers.values()):
            it.append(("rect", t["accent_tint"], t["accent"], tr(self.t, '核心业务')))
        if "decision" in used_n: it.append(("diamond", t["paper"], t["ink"], tr(self.t, '判断')))
        if "optional" in used_n: it.append(("rect", t["paper"], t["frame"], tr(self.t, '可选环节')))
        if any(c.frame for c in self.containers.values()): it.append(("rect", "none", t["frame"], tr(self.t, '业务域')))
        if "system" in used_n: it.append(("sys", t["sys_int"], None, tr(self.t, '内部系统')))
        if "external" in used_n: it.append(("sys", t["sys_ext"], None, tr(self.t, '外部实体') if dfd else tr(self.t, '外部服务')))
        if "flow" in used_e: it.append(("line", "flow", None, tr(self.t, '业务主流程')))
        if used_e & {"data", "return", "bidir"}: it.append(("line", "data", None, tr(self.t, '数据 / 集成 / 推送')))
        if "meta" in used_e: it.append(("line", "meta", None, tr(self.t, '配置 / 委托关系')))
        if any(e.get("emphasis") for e in self.edges): it.append(("line", "accent", None, tr(self.t, '关键路径')))
        if "ai" in ovk or "ai" in used_n: it.append(("rect", t["ai_fill"], None, t["special_label"]))
        if "scope" in ovk: it.append(("rect", "none", t["soft"], tr(self.t, '范围标注')))
        if "doc" in used_n: it.append(("rect", t["paper"], t["muted"], tr(self.t, '单据 / 文档')))
        if "store" in used_n: it.append(("rect", t["paper"], t["muted"], tr(self.t, '数据存储')))
        if self.controls(): it.append(("rect", t["ink"], None, tr(self.t, '控制点')))
        return it

    def legend_layout(self, y0):
        """Place legend items left→right, wrapping to a new 28px line at the page edge."""
        x0 = BODY_PAD + 8 + 48
        x, y, out = x0, y0, []
        for kind, c, s, label in self.legend_items():
            sw = 40 if kind == "line" else 36
            w = sw + text_w(label) + 24
            if x + w - 24 > self.width - BODY_PAD and x > x0:
                x, y = x0, y + 28
            out.append((kind, c, s, label, x, y))
            x += w
        return out, y - y0

    def _legend(self, A, y, W, slug):
        t = self.t
        A(f'<line x1="{BODY_PAD}" x2="{W-BODY_PAD}" y1="{y-16}" y2="{y-16}" stroke="{t["rule"]}"/>')
        A(f'<text x="{BODY_PAD + 8}" y="{y+14}" fill="{t["soft"]}" font-size="{FS}" font-weight="600">{esc(tr(t, "图例"))}</text>')
        for kind, c, s, label, x, y in self.legend_layout(y)[0]:
            if kind == "rect":
                sa = f' stroke="{s}"' if s else ""
                A(f'<rect x="{x}" y="{y+2}" width="28" height="16" rx="4" fill="{c}"{sa}/>'); x += 36
            elif kind == "diamond":
                A(f'<polygon points="{x+14},{y+1} {x+28},{y+10} {x+14},{y+19} {x},{y+10}" fill="{c}" stroke="{s}"/>'); x += 36
            elif kind == "sys":
                A(f'<rect x="{x}" y="{y+1}" width="28" height="18" rx="6" fill="{c}"/>'); x += 36
            else:
                col = {"flow": t["ink"], "data": t["muted"], "meta": t["meta"], "accent": t["accent"]}[c]
                dash = {"flow": "", "data": ' stroke-dasharray="2,3"', "meta": ' stroke-dasharray="5,4"', "accent": ""}[c]
                A(f'<path d="M{x},{y+10} L{x+30},{y+10}" stroke="{col}" stroke-width="1.5" fill="none"{dash} marker-end="url(#{slug}-m-{c})"/>'); x += 40
            A(f'<text x="{x}" y="{y+14}" fill="{t["ink"]}" font-size="{FS}">{esc(label)}</text>')
        ny = y + 44
        for k, line in enumerate(self.notes()):
            A(f'<text x="{BODY_PAD + 56}" y="{ny + k * 22}" fill="{t["muted"]}" font-size="{FS}">{esc(line)}</text>')


# ---------------------------------------------------------------- feishu whiteboard DSL
ANCHOR = {"T": "top", "B": "bottom", "L": "left", "R": "right"}


def to_wb_dsl(d, route_mode="fixed"):
    """Feishu whiteboard DSL (version 2). Shapes carry their own text and
    connectors are BOUND to node ids, so the board stays editable (move a box:
    its label and lines follow)."""
    t = d.t
    routes = d.all_routes()
    legend_y, _ = d.bounds()
    W = d.width
    N = []
    uid = iter(range(10 ** 6))

    def rid(p):
        return f"{p}_{next(uid)}"

    def rect(x, y, w, h, **kw):
        n = {"type": "rect", "x": round(x), "y": round(y), "width": round(w), "height": round(h)}
        n.update({k: v for k, v in kw.items() if v is not None})
        n.setdefault("id", rid("r"))
        return n

    def text(x, y, w, h, s, fs=FS, color=None, align="center"):
        return {"type": "text", "id": rid("t"), "x": round(x), "y": round(y), "width": round(w), "height": round(h),
                "text": s, "fontSize": fs, "textColor": color or t["ink"], "textAlign": align, "verticalAlign": "middle"}

    N.append(rect(BODY_PAD, 0, W - 2 * BODY_PAD, TOP_TITLE, id="titlebar", fillColor=t["titlebar"], borderColor=t["titleedge"],
                  borderWidth=1 if t["titleedge"] != t["titlebar"] else 0, text=d.spec.get("title", tr(t, '业务架构')), fontSize=16, textColor=t["titletext"]))
    stages, rule, divider = d.chrome(legend_y)
    for k, ((fx, fy, fw, fh), (hx, hy, hw, hh), label) in enumerate(stages):
        N.append(rect(fx, fy, fw, fh, id=f"stage_{k}", fillColor=t["paper"], borderColor=t["rule"], borderWidth=1))
        if d.show_header:
            N.append(text(hx + 2, hy + 1, hw - 4, hh - 2, label, 14, t["header"]))

    def hline(x1, y1, x2, y2):
        if abs(y1 - y2) < 0.5:
            return rect(x1, y1, x2 - x1, 1, fillColor=t["rule"], borderColor=t["rule"], borderWidth=0)
        return rect(x1, y1, 1, y2 - y1, fillColor=t["rule"], borderColor=t["rule"], borderWidth=0)
    if rule:
        N.append(hline(*rule))
    if divider:
        N.append(hline(*divider[0]))
        lbl = (d.spec.get("paths") or {}).get("label")
        if lbl:
            lx, ly = divider[1]
            N.append(text(lx - 4, ly - 16, 120, 24, lbl, FS, t["soft"], "left"))
    ids = {}
    for c in d.containers.values():
        if c.frame or c.core:
            ids[c.id] = f"box_{c.id}"
            fill = t["accent_zone"] if c.core else t["paper"]
            border = (t["accent"] if c.core else t["frame"]) if c.frame else fill
            N.append(rect(c.x, c.y, c.w, c.h, id=ids[c.id], fillColor=fill, borderColor=border,
                          borderWidth=1 if c.frame else 0, borderRadius=8))
    for ov in d.spec.get("overlays") or []:
        x, y, r, bt, top = d.overlay_rect(ov)
        if ov.get("kind", "ai") == "ai":
            N.append(rect(x, y, r - x, bt - y, fillColor=t["ai_fill"], borderColor=t["ai_fill"], borderWidth=0, borderRadius=4))
            col = t["ink"]
        else:
            N.append(rect(x, y, r - x, bt - y, fillColor=t["paper"], opacity=0, borderColor=t["soft"],
                          borderWidth=1, borderDash="dashed", borderRadius=4))
            col = t["soft"]
        lab = ov.get("label", "")
        if top:
            N.append(text(x, y, r - x, 16, lab, FS, col))
        else:
            N.append(text(x, bt - 18, r - x - 8, 16, lab, FS, col, "right"))
    for n in d.nodes.values():
        nid = "n_" + str(len(ids))
        ids[n.id] = nid
        if n.kind in ("system", "external"):
            fill, tc = d.sys_style(n)
            N.append({"type": "rect", "id": nid, "x": round(n.x), "y": round(n.y), "width": round(n.w), "height": round(n.h),
                      "fillColor": fill, "borderColor": fill, "borderWidth": 0, "borderRadius": 8,
                      "text": n.label + ("\n" + n.sub if n.sub else ""), "fontSize": FS, "textColor": tc})
            continue
        if n.kind == "label":
            N.append(text(n.x, n.y, n.w, n.h, n.label, FS, t["soft"]))
            continue
        fill, stroke, dash, _ = d.node_style(n)
        lab = n.label + ("\n" + n.sub if n.sub else "")
        if n.kind == "store" and n.sub:
            lab = f"{n.sub} | {n.label}"
        if getattr(n, "control", None):
            N.append(rect(n.r - 26, n.y - 8, 32, 16, fillColor=t["ink"], borderColor=t["ink"], borderWidth=0,
                          borderRadius=8, text=str(n.control), fontSize=9, textColor="#FFFFFF"))
        N.append({"type": "diamond" if n.kind == "decision" else "rect", "id": nid,
                  "x": round(n.x), "y": round(n.y), "width": round(n.w), "height": round(n.h),
                  "fillColor": fill, "borderColor": stroke or fill, "borderWidth": 1 if stroke else 0,
                  **({"borderDash": "dashed"} if dash else {}), **({} if n.kind == "decision" else {"borderRadius": 4}),
                  "text": lab, "fontSize": FS, "textColor": t["node_text"]})
    # legend
    lx = BODY_PAD + 8
    N.append(rect(BODY_PAD, legend_y - 16, W - 2 * BODY_PAD, 1, fillColor=t["rule"], borderColor=t["rule"], borderWidth=0))
    N.append(text(lx, legend_y, 40, 20, tr(t, '图例'), FS, t["soft"], "left"))
    for kind, c, s, label, lx, legend_y in d.legend_layout(legend_y)[0]:
        if kind in ("rect", "diamond", "sys"):
            N.append({"type": "diamond" if kind == "diamond" else "rect", "id": rid("lg"), "x": lx, "y": legend_y + 2,
                      "width": 28, "height": 16, "fillColor": t["paper"] if c == "none" else c,
                      "borderColor": s or c, "borderWidth": 1 if s else 0,
                      **({"borderRadius": 6} if kind == "sys" else {})}); lx += 36
        else:
            col = {"flow": t["ink"], "data": t["muted"], "meta": t["meta"], "accent": t["accent"]}[c]
            style = {"flow": "solid", "data": "dotted", "meta": "dashed", "accent": "solid"}[c]
            N.append({"type": "connector", "id": rid("c"), "connector": {
                "from": {"x": lx, "y": legend_y + 10}, "to": {"x": lx + 30, "y": legend_y + 10},
                "lineShape": "straight", "lineColor": col, "lineWidth": 2, "lineStyle": style, "endArrow": "arrow"}})
            lx += 40
        N.append(text(lx, legend_y, text_w(label) + 8, 20, label, FS, t["ink"], "left"))
    for k, line in enumerate(d.notes()):
        N.append(text(BODY_PAD + 56, legend_y + 30 + k * 22, max(200, text_w(line) + 16), 20, line, FS, t["muted"], "left"))
    # bound connectors
    for e, pts, sides in routes:
        col, width, dash, _ = d.edge_style(e)
        conn = {"from": ids[e["a"].id], "to": ids[e["b"].id],
                "fromAnchor": ANCHOR[sides[0]], "toAnchor": ANCHOR[sides[1]],
                # 2-point runs stay straight; the engine's auto-avoid would otherwise detour them
                "lineShape": "straight" if (len(pts) == 2 and route_mode == "fixed") else "polyline",
                "lineColor": col, "lineWidth": 2 if width >= 1.5 else 1,
                "lineStyle": {"": "solid", "2,3": "dotted", "5,4": "dashed"}[dash],
                "startArrow": "arrow" if e["kind"] == "bidir" else "none",
                "endArrow": "none" if e.get("no_arrow") else "arrow"}
        if route_mode == "fixed" and len(pts) > 2:
            conn["waypoints"] = [{"x": round(x), "y": round(y)} for x, y in pts[1:-1]]
        if e.get("label"):
            conn["label"] = e["label"]
            at = e.get("label_at", "end" if e.get("bus") else "longest")
            _, _, _, _, seg = d.label_box(e["label"], pts, at)
            segs = [math.hypot(pts[i + 1][0] - pts[i][0], pts[i + 1][1] - pts[i][1]) for i in range(len(pts) - 1)]
            run = sum(segs[:seg]) + segs[seg] / 2
            conn["labelPosition"] = round(min(max(run / (sum(segs) or 1), 0.05), 0.95), 3)
        N.append({"type": "connector", "id": rid("c"), "connector": conn})
    return {"version": 2, "nodes": N}


# ---------------------------------------------------------------- lint
def _hit(seg, box, inset=2):
    (x0, y0), (x1, y1) = seg
    lx, hx, ly, hy = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)
    return lx < box.r - inset and hx > box.x + inset and ly < box.b - inset and hy > box.y + inset


def _overlap_rect(a, b, m=1):
    return a[0] < b[2] - m and b[0] < a[2] - m and a[1] < b[3] - m and b[1] < a[3] - m


def _bends(pts):
    """Direction changes along an orthogonal polyline (zero-length segments ignored)."""
    pts = [p for i, p in enumerate(pts) if i == 0 or abs(p[0] - pts[i - 1][0]) > .5 or abs(p[1] - pts[i - 1][1]) > .5]
    dirs = [abs(p[1] - q[1]) < .5 for p, q in zip(pts, pts[1:])]
    return sum(1 for u, v in zip(dirs, dirs[1:]) if u != v)


def lint(d):
    """Return [(code, message)]; any finding blocks delivery."""
    out = [(w[1:3], w) for w in d.warnings]
    nodes = list(d.nodes.values())
    routes = d.all_routes()
    # G1 node overlap
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            if _overlap_rect((a.x, a.y, a.r, a.b), (b.x, b.y, b.r, b.b)):
                out.append(("G1", f"[G1] 节点重叠：'{a.label}' 与 '{b.label}'，调整 lane/row"))
    # G2 transit behind a non-endpoint node (connector rule 5)
    for e, pts, _ in routes:
        ends = {e["a"].id, e["b"].id}
        skip = set()
        for end in ("a", "b"):
            if getattr(e[end], "kind", "") == "container":
                skip |= set(e[end].members)
        for n in nodes:
            if n.id in ends or n.id in skip or n.kind == "label":
                continue
            if any(_hit((pts[k], pts[k + 1]), n) for k in range(len(pts) - 1)):
                out.append(("G2", f"[G2] 连线 {e['a'].label}→{e['b'].label} 穿过非端点节点 '{n.label}'：改 route/mid_x/mid_row/port_a"))
    # G3 stacked parallel connectors (rule 3): two edges sharing a stroke for >8px
    segs = []
    for ei, (e, pts, _) in enumerate(routes):
        for k in range(len(pts) - 1):
            segs.append((ei, e, pts[k], pts[k + 1]))
    seen = set()
    for i in range(len(segs)):
        ei, e1, a0, a1 = segs[i]
        for j in range(i + 1, len(segs)):
            ej, e2, b0, b1 = segs[j]
            if ei == ej or (ei, ej) in seen:
                continue
            if e1.get("bus") and e2.get("bus") and e1["a"].id == e2["a"].id:
                continue
            hz = abs(a0[1] - a1[1]) < .5 and abs(b0[1] - b1[1]) < .5 and abs(a0[1] - b0[1]) < 4
            vt = abs(a0[0] - a1[0]) < .5 and abs(b0[0] - b1[0]) < .5 and abs(a0[0] - b0[0]) < 4
            if hz:
                ov = min(max(a0[0], a1[0]), max(b0[0], b1[0])) - max(min(a0[0], a1[0]), min(b0[0], b1[0]))
            elif vt:
                ov = min(max(a0[1], a1[1]), max(b0[1], b1[1])) - max(min(a0[1], a1[1]), min(b0[1], b1[1]))
            else:
                continue
            if ov > 8:
                seen.add((ei, ej))
                out.append(("G3", f"[G3] 连线 {e1['a'].label}→{e1['b'].label} 与 {e2['a'].label}→{e2['b'].label} 叠在同一条线上：错开 ≥12px（mid_x/mid_row/port_a）"))
    # A1 arrow room (rule 7): the arrowhead segment needs ≥ MIN_END, every other segment ≥ MIN_SEG
    for e, pts, _ in routes:
        segs = [math.hypot(pts[k + 1][0] - pts[k][0], pts[k + 1][1] - pts[k][1]) for k in range(len(pts) - 1)]
        need = [MIN_SEG] * len(segs)
        if not e.get("no_arrow"):
            need[-1] = MIN_END
        if e["kind"] == "bidir":
            need[0] = MIN_END
        if len(segs) == 1:
            need = [MIN_END + (MIN_SEG if e["kind"] == "bidir" else 0)]
        bad = [k for k, (l, m) in enumerate(zip(segs, need)) if l < m - 0.5]
        if bad:
            k = bad[0]
            out.append(("A1", f"[A1] 连线 {e['a'].label}→{e['b'].label} 第 {k+1} 段只有 {segs[k]:.0f}px（需 ≥{need[k]}px），箭头/线段显示不全：拉开 row/lane 间距，或调 mid_x/mid_row"))
    # G5 auto-routed edges bend at most once (rule 8); loops and explicit routes are the author's call
    for e, pts, _ in routes:
        if e.get("route", "auto") != "auto" or e.get("mid_x") is not None or e.get("mid_row") is not None:
            continue
        n = _bends(pts)
        if n >= 2:
            out.append(("G5", f"[G5] 连线 {e['a'].label}→{e['b'].label} 折了 {n} 次：把两端放到同一 lane（上下相接）或同一 row（左右相接），"
                              f"或错开成能一折走通的位置（route: hv / vh）；确需绕行时显式写 route"))
    # G4 visible groups must not overlap each other
    vis = [c for c in d.containers.values() if c.frame or c.core]
    for i, a in enumerate(vis):
        for b in vis[i + 1:]:
            inside = (a.x <= b.x and a.y <= b.y and a.r >= b.r and a.b >= b.b) or \
                     (b.x <= a.x and b.y <= a.y and b.r >= a.r and b.b >= a.b)
            if not inside and _overlap_rect((a.x, a.y, a.r, a.b), (b.x, b.y, b.r, b.b)):
                out.append(("G4", f"[G4] 分组 '{a.id}' 与 '{b.id}' 的框/底色相互交叠：拉开 lane/row 或取消其中一个 frame"))
    # L1/L2 edge labels: short, and never on top of a node (rule 6)
    for e, pts, _ in routes:
        if not e.get("label"):
            continue
        if wide_len(e["label"]) > MAX_EDGE_LABEL:
            out.append(("L1", f"[L1] 连线标签 '{e['label']}' 超过 {MAX_EDGE_LABEL} 个字：精简措辞"))
        x, y, w, h, _ = d.label_box(e["label"], pts, e.get("label_at", "end" if e.get("bus") else "longest"))
        for n in nodes:
            if n.kind != "label" and _overlap_rect((x, y, x + w, y + h), (n.x, n.y, n.r, n.b)):
                out.append(("L2", f"[L2] 连线标签 '{e['label']}' 压住了节点 '{n.label}'：换 label_at 或调整走线"))
                break
    # L3 two edge labels must not collide with each other
    boxes = []
    for e, pts, _ in routes:
        if e.get("label"):
            x, y, w, h, _ = d.label_box(e["label"], pts, e.get("label_at", "end" if e.get("bus") else "longest"))
            boxes.append((e, (x, y, x + w, y + h)))
    for i in range(len(boxes)):
        for j in range(i + 1, len(boxes)):
            if _overlap_rect(boxes[i][1], boxes[j][1]):
                out.append(("L3", f"[L3] 连线标签 '{boxes[i][0]['label']}' 与 '{boxes[j][0]['label']}' 互相重叠：换 label_at、拉开间距，或删掉可由布局看出的标签"))
    # T1 node names: cut words, never shrink type; S1 sublabels are Latin technical values only
    for n in nodes:
        if wide_len(n.label) > 10:
            out.append(("T1", f"[T1] 节点名 '{n.label}' 过长：精简到 10 个字以内（不缩字号）"))
        if n.sub and any(is_wide(c) for c in n.sub):
            out.append(("S1", f"[S1] 副标签 '{n.sub}' 含中文：副标签只写端口/协议/技术栈等拉丁字符值"))
    # B1 a plain group is invisible - nothing may point at it
    for e in d.edges:
        for end in ("a", "b"):
            c = e[end]
            if getattr(c, "kind", "") == "container" and not (c.frame or c.core):
                out.append(("B1", f"[B1] 连线 {e['a'].label}→{e['b'].label} 的端点是无框分组 '{c.id}'：改连其主线节点，或给分组加 frame"))
    # R1 cross-group main flow must hang on a main node
    for e in d.edges:
        for end in ("a", "b"):
            n = e[end]
            cid = getattr(n, "container", None)
            other = e["b" if end == "a" else "a"]
            if not cid or getattr(other, "container", None) == cid or other.id == cid:
                continue
            c = d.containers[cid]
            if c.mains and not n.main and c.ctype == "process" and e["kind"] == "flow":
                out.append(("R1", f"[R1] 主流程 {e['a'].label}→{e['b'].label} 挂在分组 '{cid}' 的非主线节点 '{n.label}' 上"))
    # F1 accent budget: core tint is a signal only while it is rare
    core = [n.label for n in nodes if n.core] + [c.id for c in d.containers.values() if c.core]
    if len(core) > MAX_CORE:
        out.append(("F1", f"[F1] 核心业务底色用了 {len(core)} 处（{'、'.join(core)}），上限 {MAX_CORE}：只留真正的核心"))
    # R5 重点能力命名：声明了 special.prefix（旧写法 kind: ai 默认为 "AI"）时，标签必须以它开头
    sl, pre = d.t["special_label"], d.t["special_prefix"]
    if pre:
        for ov in d.spec.get("overlays") or []:
            if ov.get("kind", "ai") == "ai" and not str(ov.get("label", "")).startswith(pre):
                out.append(("R5", f"[R5] {sl}叠加层标签 '{ov.get('label')}' 必须以 '{pre}' 开头"))
        for n in nodes:
            if n.kind == "ai" and not n.label.startswith(pre):
                out.append(("R5", f"[R5] {sl}节点 '{n.label}' 必须以 '{pre}' 开头"))
    # R6 path rows move forward through stages
    order = {c: i for i, c in enumerate(d.cols)}
    for p in (d.spec.get("paths") or {}).get("rows") or []:
        last = -1
        for s_ in p.get("steps") or []:
            if s_.get("break"):
                last = -1
            k = order.get(s_["col"], 0)
            if k < last:
                out.append(("R6", f"[R6] 路径 '{p.get('name')}' 的步骤 '{s_['label']}' 回到了更早的阶段列"))
            last = k
    # profile rules
    profile = d.spec.get("profile")
    if profile == "dfd":
        ins, outs = {}, {}
        for e in d.edges:
            a, b = e["a"], e["b"]
            outs[a.id] = outs.get(a.id, 0) + 1
            ins[b.id] = ins.get(b.id, 0) + 1
            if a.kind not in PROCESS_KINDS and b.kind not in PROCESS_KINDS:
                out.append(("DF1", tr(d.t, '[DF1] 数据流 {0}→{1} 两端都不是处理过程：数据只能经过处理才能流转（存储/外部实体之间不能直连）', a.label, b.label)))
        for n in nodes:
            if n.kind in PROCESS_KINDS and n.kind != "decision":
                if ins.get(n.id) and not outs.get(n.id):
                    out.append(("DF2", tr(d.t, "[DF2] 处理 '{0}' 只有输入没有输出（黑洞）：补上它产出的数据", n.label)))
                if outs.get(n.id) and not ins.get(n.id):
                    out.append(("DF2", tr(d.t, "[DF2] 处理 '{0}' 只有输出没有输入（奇迹）：补上它依赖的数据", n.label)))
            if n.kind == "store" and not (ins.get(n.id) and outs.get(n.id)):
                out.append(("DF3", tr(d.t, "[DF3] 数据存储 '{0}' 缺少{1}：没人写或没人读的存储要么多余，要么漏画了流程", n.label, tr(d.t, '写入') if not ins.get(n.id) else tr(d.t, '读取'))))
    for c, lab, risk in d.controls():
        if not risk:
            out.append(("AU1", tr(d.t, '[AU1] 控制点 {0}（{1}）没有写 risk：每个控制点都要说明它防的是什么风险', c, lab)))
    if profile == "audit":
        linked = {e["a"].id for e in d.edges} | {e["b"].id for e in d.edges}
        for n in nodes:
            if n.kind == "doc" and n.id not in linked:
                out.append(("AU2", tr(d.t, "[AU2] 单据 '{0}' 没有连线：审计流程里每张单据都要说明谁产生、流向谁", n.label)))
        if not d.controls():
            out.append(("AU1", tr(d.t, '[AU1] profile: audit 但没有标任何控制点：用 control: K1 + risk 标出关键控制')))
    # D1 density
    for cid, c in d.cols.items():
        cnt = sum(1 for n in nodes if n.col == cid and not getattr(n, "path", None))
        if cnt > c["lanes"] * 12:
            out.append(("D1", f"[D1] 列 '{c['label']}' 有 {cnt} 个节点，超出密度预算，拆成全景 + 子图"))
    return out


# ================================================================ scene primitives
# Layer and ER diagrams are drawn as a flat list of primitives so the SVG writer
# and the Feishu whiteboard writer stay in lockstep (one geometry, two outputs).
class Scene:
    def __init__(self):
        self.items = []

    def rect(self, x, y, w, h, fill="none", stroke=None, rx=4, dash=None, text=None, fs=FS, weight=400,
             color=None, vtext=False, id=None, sw=1, z=0, shape="rect"):
        self.items.append({"t": "rect", "x": x, "y": y, "w": w, "h": h, "fill": fill, "stroke": stroke, "rx": rx,
                           "dash": dash, "text": text, "fs": fs, "weight": weight, "color": color, "vtext": vtext,
                           "id": id, "sw": sw, "z": z, "shape": shape})

    def text(self, x, y, w, h, s, fs=FS, weight=400, color=None, align="center", mono=False, mask=None, z=2):
        self.items.append({"t": "text", "x": x, "y": y, "w": w, "h": h, "s": s, "fs": fs, "weight": weight,
                           "color": color, "align": align, "mono": mono, "mask": mask, "z": z})

    def conn(self, pts, color, width=1.5, dash="", start=False, end=True, a=None, b=None, sides=None, z=1, glyph=None,
             label=None, label_color=None):
        self.items.append({"t": "conn", "pts": pts, "color": color, "width": width, "dash": dash, "start": start,
                           "end": end, "a": a, "b": b, "sides": sides, "z": z, "glyph": glyph,
                           "label": label, "label_color": label_color})

    def poly(self, pts, fill, z=2):
        self.items.append({"t": "poly", "pts": pts, "fill": fill, "z": z})


def _vlines(s):
    """Vertical CJK text: one character per line; runs of Latin stay together."""
    out, buf = [], ""
    for c in str(s):
        if is_wide(c):
            if buf.strip():
                out.append(buf.strip())
            buf = ""
            out.append(c)
        elif c.isspace():
            if buf.strip():
                out.append(buf.strip())
            buf = ""
        else:
            buf += c
    if buf.strip():
        out.append(buf.strip())
    return out


def _wrap_w(s, width, size=FS):
    """Wrap at Latin word boundaries or CJK characters, preserving explicit lines."""
    import re
    out = []
    for paragraph in str(s).split("\n"):
        cur = ""
        for token in re.findall(r"[\u2e80-\uffff]|[^\s\u2e80-\uffff]+|[ \t]+", paragraph):
            if not token.strip():
                if cur:
                    cur += " "
                continue
            if cur.strip() and text_w(cur + token, size) > width:
                out.append(cur.rstrip())
                cur = token
            else:
                cur += token
        out.append(cur.rstrip())
    # Preserve balanced two-line CJK labels while keeping Latin words intact.
    if len(out) == 2 and "\n" not in str(s) and not any(c.isascii() and c.isalpha() for c in str(s)):
        tokens = list(str(s))
        candidates = []
        for i in range(1, len(tokens)):
            lines = ["".join(tokens[:i]).strip(), "".join(tokens[i:]).strip()]
            longest = max(text_w(line, size) for line in lines)
            if longest <= width:
                candidates.append((longest, i, lines))
        if candidates:
            out = min(candidates)[2]
    return out or [""]


def _chunks(s, k):
    s = str(s)
    if any(c.isascii() and c.isalpha() for c in s):
        return _wrap_w(s, k * FS)
    return [s[i:i + k] for i in range(0, len(s), k)] or [""]


def scene_svg(scene, W, H, t, title, desc, slug):
    o = []
    A = o.append
    A(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}" '
      f'role="img" xml:lang="{esc(t.get("language", "zh-CN"))}" aria-labelledby="{slug}-title {slug}-desc" font-family="{FONT}">')
    A(f'<title id="{slug}-title">{esc(title)}</title><desc id="{slug}-desc">{esc(desc)}</desc>')
    A('<defs>')
    cols = sorted({i["color"] for i in scene.items if i["t"] == "conn"})
    for k, col in enumerate(cols):
        A(f'<marker id="{slug}-mk{k}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
          f'orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="{col}" stroke-width="1.6" '
          f'stroke-linejoin="round"/></marker>')
    A('</defs>')
    A(f'<rect width="{W}" height="{H}" fill="{t["paper"]}"/>')
    order = sorted(range(len(scene.items)), key=lambda i: (scene.items[i]["z"], i))
    for i in order:
        it = scene.items[i]
        if it["t"] == "rect":
            sa = f' stroke="{it["stroke"]}" stroke-width="{it["sw"]}"' if it["stroke"] else ""
            if it["dash"]:
                sa += f' stroke-dasharray="{it["dash"]}"'
            if it.get("shape") == "diamond":
                x, y, w, h = it["x"], it["y"], it["w"], it["h"]
                A(f'<polygon points="{x + w / 2:.1f},{y:.1f} {x + w:.1f},{y + h / 2:.1f} {x + w / 2:.1f},{y + h:.1f} '
                  f'{x:.1f},{y + h / 2:.1f}" fill="{it["fill"]}"{sa}/>')
            else:
                A(f'<rect x="{it["x"]:.1f}" y="{it["y"]:.1f}" width="{it["w"]:.1f}" height="{it["h"]:.1f}" '
                  f'rx="{it["rx"]}" fill="{it["fill"]}"{sa}/>')
            if it["text"]:
                lines = _vlines(it["text"]) if it["vtext"] else str(it["text"]).split("\n")
                lh = it["fs"] + (6 if it["vtext"] else 4)
                y0 = it["y"] + it["h"] / 2 - (len(lines) - 1) * lh / 2 + it["fs"] * 0.36
                for k, ln in enumerate(lines):
                    A(f'<text x="{it["x"] + it["w"] / 2:.1f}" y="{y0 + k * lh:.1f}" text-anchor="middle" '
                      f'fill="{it["color"] or t["ink"]}" font-size="{it["fs"]}" font-weight="{it["weight"]}">{esc(ln)}</text>')
        elif it["t"] == "text":
            if it["mask"]:
                A(f'<rect x="{it["x"]:.1f}" y="{it["y"]:.1f}" width="{it["w"]:.1f}" height="{it["h"]:.1f}" fill="{it["mask"]}"/>')
            anchor = {"center": "middle", "left": "start", "right": "end"}[it["align"]]
            x = {"center": it["x"] + it["w"] / 2, "left": it["x"], "right": it["x"] + it["w"]}[it["align"]]
            lines = str(it["s"]).split("\n")
            lh = it["fs"] + 6
            y0 = it["y"] + it["h"] / 2 - (len(lines) - 1) * lh / 2 + it["fs"] * 0.36
            fam = f' font-family="{MONO}"' if it["mono"] else ""
            for k, ln in enumerate(lines):
                A(f'<text x="{x:.1f}" y="{y0 + k * lh:.1f}" text-anchor="{anchor}" fill="{it["color"] or t["ink"]}" '
                  f'font-size="{it["fs"]}" font-weight="{it["weight"]}"{fam}>{esc(ln)}</text>')
        elif it["t"] == "conn":
            k = cols.index(it["color"])
            attrs = f'fill="none" stroke="{it["color"]}" stroke-width="{it["width"]}"'
            if it["dash"]:
                attrs += f' stroke-dasharray="{it["dash"]}"'
            if it["end"]:
                attrs += f' marker-end="url(#{slug}-mk{k})"'
            if it["start"]:
                attrs += f' marker-start="url(#{slug}-mk{k})"'
            A(f'<path d="{_round_path(it["pts"])}" {attrs}/>')
            if it.get("label"):   # label rides on the connector: beside its longest segment, masked
                pts = it["pts"]
                k = max(range(len(pts) - 1), key=lambda j: math.hypot(pts[j + 1][0] - pts[j][0], pts[j + 1][1] - pts[j][1]))
                (x0, y0), (x1, y1) = pts[k], pts[k + 1]
                lw = up4(text_w(it["label"]) + 8)
                lx, ly = ((x0 + x1) / 2 - lw / 2, y0 - LABEL_GAP - 16) if abs(y0 - y1) < 0.5 else (x0 + LABEL_GAP, (y0 + y1) / 2 - 8)
                A(f'<rect x="{lx:.1f}" y="{ly:.1f}" width="{lw}" height="16" fill="{t["paper"]}"/>')
                A(f'<text x="{lx + lw / 2:.1f}" y="{ly + 12:.1f}" text-anchor="middle" fill="{it.get("label_color") or it["color"]}" '
                  f'font-size="{FS}" font-weight="500">{esc(it["label"])}</text>')
        elif it["t"] == "poly":
            pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in it["pts"])
            A(f'<polygon points="{pts}" fill="{it["fill"]}"/>')
    A('</svg>')
    return "\n".join(o)


def _round_path(pts):
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        l1, l2 = math.hypot(x1 - x0, y1 - y0), math.hypot(x2 - x1, y2 - y1)
        r = min(CORNER, l1 / 2, l2 / 2)
        if r < 0.5:
            d += f" L{x1:.1f},{y1:.1f}"
            continue
        ax, ay = x1 - (x1 - x0) / l1 * r, y1 - (y1 - y0) / l1 * r
        bx, by = x1 + (x2 - x1) / l2 * r, y1 + (y2 - y1) / l2 * r
        d += f" L{ax:.1f},{ay:.1f} Q{x1:.1f},{y1:.1f} {bx:.1f},{by:.1f}"
    return d + f" L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"


def scene_wb(scene, t):
    """Feishu whiteboard DSL v2 from a scene: shapes keep their text, connectors bind to shape ids."""
    N, uid = [], iter(range(10 ** 6))
    shapes = {i["id"]: (i["x"], i["y"], i["w"], i["h"]) for i in scene.items if i["t"] == "rect" and i.get("id")}
    order = sorted(range(len(scene.items)), key=lambda i: (scene.items[i]["z"], i))
    for i in order:
        it = scene.items[i]
        if it["t"] == "rect":
            n = {"type": it.get("shape") or "rect", "id": it["id"] or f"r_{next(uid)}", "x": round(it["x"]), "y": round(it["y"]),
                 "width": round(it["w"]), "height": round(it["h"]),
                 "fillColor": t["paper"] if it["fill"] == "none" else it["fill"],
                 "borderColor": it["stroke"] or (t["paper"] if it["fill"] == "none" else it["fill"]),
                 "borderWidth": it["sw"] if it["stroke"] else 0, "borderRadius": it["rx"]}
            if n["type"] == "diamond":
                n.pop("borderRadius")
            if it["fill"] == "none":
                n["opacity"] = 0 if not it["stroke"] else n.get("opacity", 1)
            if it["dash"]:
                n["borderDash"] = "dashed"
            if it["text"]:
                n.update({"text": "\n".join(_vlines(it["text"])) if it["vtext"] else str(it["text"]),
                          "fontSize": it["fs"], "textColor": it["color"] or t["ink"]})
            N.append(n)
        elif it["t"] == "text":
            N.append({"type": "text", "id": f"t_{next(uid)}", "x": round(it["x"]), "y": round(it["y"]),
                      "width": round(max(it["w"], 16)), "height": round(it["h"]), "text": str(it["s"]),
                      "fontSize": it["fs"], "textColor": it["color"] or t["ink"], "textAlign": it["align"],
                      "verticalAlign": "middle"})
        elif it["t"] == "conn" and it.get("glyph"):   # tiny chevron → a text glyph on the board
            xs, ys = [p[0] for p in it["pts"]], [p[1] for p in it["pts"]]
            N.append({"type": "text", "id": f"g_{next(uid)}", "x": round(min(xs) - 6), "y": round(min(ys) - 4),
                      "width": 16, "height": 16, "text": it["glyph"], "fontSize": 14, "textColor": it["color"],
                      "textAlign": "center", "verticalAlign": "middle"})
        elif it["t"] == "conn":
            pts = it["pts"]
            c = {"lineShape": "straight" if len(pts) == 2 else "polyline", "lineColor": it["color"],
                 "lineWidth": 2 if it["width"] >= 1.5 else 1,
                 "lineStyle": "solid" if not it["dash"] else ("dotted" if it["dash"] == "2,3" else "dashed"),
                 "startArrow": "arrow" if it["start"] else "none", "endArrow": "arrow" if it["end"] else "none"}
            def mid_of(sid, side):
                r = shapes.get(sid)
                if not r:
                    return None
                x, y, w, h = r
                return {"T": (x + w / 2, y), "B": (x + w / 2, y + h), "L": (x, y + h / 2), "R": (x + w, y + h / 2)}[side]
            bind = False
            if it["a"] and it["b"] and len(pts) == 2:   # the board snaps bound ends to edge midpoints: bind only if we sit there
                ma, mb = mid_of(it["a"], it["sides"][0]), mid_of(it["b"], it["sides"][1])
                bind = bool(ma and mb and math.dist(ma, pts[0]) < 1.5 and math.dist(mb, pts[-1]) < 1.5)
            if bind:
                c.update({"from": it["a"], "to": it["b"],
                          "fromAnchor": ANCHOR[it["sides"][0]], "toAnchor": ANCHOR[it["sides"][1]]})
            else:
                c.update({"from": {"x": round(pts[0][0]), "y": round(pts[0][1])},
                          "to": {"x": round(pts[-1][0]), "y": round(pts[-1][1])}})
            if len(pts) > 2:   # free polylines: the board drops the end legs unless every vertex is a waypoint
                wp = pts[1:-1] if bind else pts
                c["waypoints"] = [{"x": round(x), "y": round(y)} for x, y in wp]
            if it.get("label"):
                c["label"], c["labelPosition"] = it["label"], 0.5
            N.append({"type": "connector", "id": f"c_{next(uid)}", "connector": c})
        elif it["t"] == "poly":   # stage arrow → a short bold connector with an arrowhead
            xs, ys = [p[0] for p in it["pts"]], [p[1] for p in it["pts"]]
            cy = (min(ys) + max(ys)) / 2
            N.append({"type": "connector", "id": f"a_{next(uid)}", "connector": {
                "from": {"x": round(min(xs) - 6), "y": round(cy)}, "to": {"x": round(max(xs) + 2), "y": round(cy)},
                "lineShape": "straight", "lineColor": it["fill"], "lineWidth": 2, "lineStyle": "solid",
                "startArrow": "none", "endArrow": "arrow"}})
    return {"version": 2, "nodes": N}


def _theme_from(spec, theme, brand, titlebar):
    preset = PRESETS.get(theme or spec.get("theme") or "gray", DEFAULT_BRAND)
    t = make_theme(brand or spec.get("brand") or preset, titlebar or spec.get("titlebar") or "plain")
    t["language"] = spec.get("language", "zh-CN")
    t["special_label"], t["special_prefix"] = special_info(spec)
    return t


def _titlebar(S, t, W, title):
    edge = t.get("titleedge", t["titlebar"])
    S.rect(BODY_PAD + 0.5, 0.5, W - 2 * BODY_PAD - 1, TOP_TITLE - 1, fill=t["titlebar"],
           stroke=edge if edge != t["titlebar"] else None, rx=0, text=title, fs=16, weight=600,
           color=t["titletext"], id="titlebar")


def _legend_row(S, t, items, x0, y, W):
    """items: (kind, label). Wraps to a second line when it runs out of width."""
    S.rect(BODY_PAD, y - 16, W - 2 * BODY_PAD, 1, fill=t["rule"], rx=0)
    S.text(x0, y, 40, 20, tr(t, '图例'), FS, 600, t["soft"], "left")
    x, line = x0 + 48, 0
    for kind, label in items:
        need = 40 + text_w(label) + 24
        if x + need > W - BODY_PAD and x > x0 + 48:
            x, line = x0 + 48, line + 1
        yy = y + line * 32
        sw = {} if kind.startswith("tag:") else {"core": (t["accent_tint"], t["accent"]), "sys": (t["sys_int"], None), "ext": (t["sys_ext"], None),
              "ai": (t["ai_fill"], t["ai_stroke"]), "more": (t["paper"], t["frame"]), "chip": (t["node"], None),
              "panel": (t["paper"], t["rule"]), "pk": (t["paper"], t["rule"])}.get(kind)
        if kind.startswith("tag:"):
            S.rect(x, yy + 3, 26, 14, fill=t["paper"], stroke=t["muted"], rx=2, text=kind[4:], fs=9, weight=600,
                   color=t["muted"], z=2)
            x += 34
        elif kind == "flow":
            S.poly([(x, yy + 4), (x + 12, yy + 10), (x, yy + 16)], t["ink"])
            x += 20
        elif kind == "rel":
            S.conn([(x, yy + 10), (x + 30, yy + 10)], t["muted"], 1.2, end=False)
            S.text(x - 2, yy - 2, 10, 12, "1", 10, 500, t["muted"], "left", mono=True)
            S.text(x + 24, yy - 2, 10, 12, "N", 10, 500, t["muted"], "left", mono=True)
            x += 40
        else:
            S.rect(x, yy + 2, 28, 16, fill=sw[0], stroke=sw[1], rx=4, dash="4,3" if kind == "more" else None)
            x += 36
        S.text(x, yy, text_w(label) + 8, 20, label, FS, 400, t["ink"], "left")
        x += text_w(label) + 24
    return line


# ================================================================ 分层架构图 (layout: layers)
RAIL_W = 40          # cross-cutting rail (安全保障 / 法规) width
LBL_W = 72           # layer name column
LPAD = 12            # inner padding of a layer band / panel
GAP = 12             # gap between blocks
ITEM_H, ITEM_GAP = 32, 8
TAB_H = 32
STEP_W = 40          # capability-chain step chip (2 字一行)
STEP_GAP = 16
STAGE_GAP = 32
MAX_LAYERS = 6
MAX_BLOCK_ITEMS = 12
MORE = ("……", "...", "…", "⋯⋯")


class LayersDiagram:
    """Layer stack + side integration columns + cross-cutting rails (集团平台总体架构)."""
    vertical = False

    def __init__(self, spec, theme=None, brand=None, titlebar=None, orient=None):
        self.spec = spec
        self.t = _theme_from(spec, theme, brand, titlebar)
        self.S = Scene()
        self.findings = []
        self.rects = {}       # id -> (x, y, w, h)  for links
        self.cores = []
        self.used = set()
        self.layout()

    # ---------------------------------------------------------------- helpers
    def _f(self, code, msg):
        self.findings.append((code, f"[{code}] {msg}"))

    @staticmethod
    def _items(raw):
        out = []
        for it in raw or []:
            if isinstance(it, str):
                it = {"label": it}
            out.append(it)
        return out

    def _chip(self, x, y, w, h, it, base="chip", vtext=False):
        t = self.t
        label = it["label"]
        kind = it.get("kind") or base
        if label in MORE:
            kind = "more"
        if it.get("core"):
            kind = "core"
            self.cores.append(label)
        style = {
            "chip": (t["node"], None, t["node_text"], 400, None),
            "white": (t["paper"], t["rule"], t["node_text"], 400, None),
            "internal": (t["sys_int"], None, t["sys_int_text"], 500, None),
            "external": (t["sys_ext"], None, t["sys_ext_text"], 500, None),
            "core": (t["accent_tint"], t["accent"], t["node_text"], 600, None),
            "ai": (t["paper"], t["ai_stroke"], t["node_text"], 400, None),
            "more": (t["paper"], t["frame"], t["soft"], 400, "4,3"),
        }[kind]
        self.used.add({"internal": "sys", "external": "ext", "core": "core", "more": "more"}.get(kind, "x"))
        fill, stroke, color, weight, dash = style
        self.S.rect(x, y, w, h, fill=fill, stroke=stroke, rx=8 if kind in ("internal", "external") else 4,
                    dash=dash, text=label, fs=FS, weight=weight, color=color, vtext=vtext, z=2,
                    id=it.get("id"))
        if not vtext and label not in MORE and text_w(label) + 16 > w:
            self._f("T1", f"条目 '{label}' 放不下（宽 {w:.0f}px）：精简措辞，或减少该块的 cols / 加大 w（不缩字号）")
        if vtext and len(_vlines(label)) * (FS + 6) + 12 > h:
            self._f("V1", f"竖排条目 '{label}' 放不下（高 {h:.0f}px）：精简措辞或减少条目")

    def _panel(self, x, y, w, h, title=None, kind=None, core=False, pid=None, title_h=36):
        t = self.t
        if kind == "ai":
            fill, stroke = mix(t["ai_fill"], "#FFFFFF", 0.5), t["ai_stroke"]
            self.used.add("ai")
            pre = t.get("special_prefix")
            if pre and title and not str(title).startswith(pre):
                self._f("R5", f"{t['special_label']}区块标题 '{title}' 必须以 '{pre}' 开头")
        elif core:
            fill, stroke = t["accent_zone"], t["accent"]
            self.cores.append(title or pid)
            self.used.add("core")
        else:
            fill, stroke = t["paper"], t["rule"]
        self.S.rect(x, y, w, h, fill=fill, stroke=stroke, rx=8, z=1, id=pid)
        if title:
            self.S.text(x + 8, y + 8, w - 16, title_h - 12, title, 14, 600,
                        t["accent"] if core else t["header"], "center")
        if pid:
            self.rects[pid] = (x, y, w, h)

    # ---------------------------------------------------------------- layout
    def layout(self):
        sp, t, S = self.spec, self.t, self.S
        layers = sp.get("layers") or []
        if not layers:
            raise SpecError("layout: layers 需要 layers 列表（自上而下：展示层 → 设施层）")
        if len(layers) > MAX_LAYERS:
            self._f("D2", f"分层数 {len(layers)} 超过 {MAX_LAYERS}：合并相近层，或拆成总图 + 分层子图")
        W = int(sp.get("width", 1600))
        rails = sp.get("rails") or {}
        side = sp.get("side") or []
        links = sp.get("links") or []
        rail_labels = []
        for rail in rails.values():
            rail_labels += rail if isinstance(rail, list) else (rail.get("items") or [rail.get("label", "")])
        self.rail_w = max([RAIL_W] + [up4(text_w(word) + 16) for label in rail_labels for word in _vlines(label)])
        self.label_w = max([LBL_W] + [up4(text_w(layer.get("label", layer["id"]), 14) + 24) for layer in layers]) if sp.get("language") == "en" else LBL_W

        # horizontal tracks: [left rail] [layer names] [main] [side columns…] [right rail]
        x = BODY_PAD
        if rails.get("left"):
            self.rail_l = x
            x += self.rail_w + GAP
        self.x_lbl = x
        x += self.label_w + GAP
        x_main = x
        xr = W - BODY_PAD
        if rails.get("right"):
            xr -= self.rail_w
            self.rail_r = xr
            xr -= GAP
        # column index: main = 0, side i = i + 1; a link between neighbours widens their gap
        owner = {}
        for li in layers:
            owner[li["id"]] = 0
            for b in li.get("blocks") or []:
                if b.get("id"):
                    owner[b["id"]] = 0
        for i, c in enumerate(side):
            owner[c["id"]] = i + 1
            for s_ in c.get("sections") or []:
                if s_.get("id"):
                    owner[s_["id"]] = i + 1
        linked = set()
        for l_ in links:
            a, b = owner.get(l_["from"]), owner.get(l_["to"])
            if a is None or b is None:
                raise SpecError(f"links 引用了不存在的 id：{l_}")
            linked.add((min(a, b), max(a, b)))
        side_x = []
        for i in range(len(side) - 1, -1, -1):
            w = int(side[i].get("w", 112))
            side_x.insert(0, (xr - w, w))
            xr -= w + (56 if (i, i + 1) in linked else 16)
        main_w = xr - x_main
        if main_w < 480:
            raise SpecError(f"主体宽度只剩 {main_w}px：加大 width 或收窄 side 列")

        # vertical: layers stacked under the title bar
        y = TOP_TITLE + 16
        self.layer_y = {}
        for L in layers:
            h = self._layer(L, x_main, y, main_w)
            self.layer_y[L["id"]] = (y, h)
            S.rect(self.x_lbl, y, self.label_w, h, fill=t["node"], rx=8, text=L.get("label", L["id"]), fs=14, weight=600,
                   color=t["header"], vtext=h < 64 and False, z=0)
            y += h + GAP
        y_top, y_bot = TOP_TITLE + 16, y - GAP

        for i, c in enumerate(side):
            self._side(c, side_x[i][0], side_x[i][1], y_top, y_bot)
        if rails.get("left"):
            self._rail(rails["left"], self.rail_l, y_top, y_bot)
        if rails.get("right"):
            self._rail(rails["right"], self.rail_r, y_top, y_bot)
        for l_ in links:
            self._link(l_)

        _titlebar(S, t, W, sp.get("title", tr(self.t, '总体架构')))
        legend = []
        if "core" in self.used: legend.append(("core", tr(self.t, '核心业务')))
        if "sys" in self.used: legend.append(("sys", tr(self.t, '内部系统')))
        if "ext" in self.used: legend.append(("ext", tr(self.t, '外部系统')))
        if "ai" in self.used: legend.append(("ai", self.t["special_label"]))
        if "flow" in self.used: legend.append(("flow", tr(self.t, '流程推进')))
        if "more" in self.used: legend.append(("more", tr(self.t, '可扩展')))
        H = y_bot + 24
        if legend:
            ly = y_bot + 40
            extra = _legend_row(S, t, legend, BODY_PAD + 8, ly, W)
            H = ly + 40 + extra * 32
        self.W, self.H = W, H
        if len(self.cores) > MAX_CORE:
            self._f("F1", f"核心底色用了 {len(self.cores)} 处（{'、'.join(map(str, self.cores))}），上限 {MAX_CORE}")

    def _layer(self, L, x, y, w):
        """Lay one band; returns its height. Blocks share the width by weight `w`."""
        t, S = self.t, self.S
        blocks = L.get("blocks") or []
        if not blocks:
            raise SpecError(f"层 '{L['id']}' 没有 blocks")
        inner = w - 2 * LPAD
        tot = sum(float(b.get("w", 1)) for b in blocks)
        avail = inner - GAP * (len(blocks) - 1)
        widths = [avail * float(b.get("w", 1)) / tot for b in blocks]
        plans = [self._plan_block(b, bw) for b, bw in zip(blocks, widths)]
        h_in = max(p["h"] for p in plans)
        H = h_in + 2 * LPAD
        S.rect(x, y, w, H, fill="#F7F8FA", rx=8, z=0, id=f"layer_{L['id']}")
        self.rects[L["id"]] = (x, y, w, H)
        bx = x + LPAD
        for b, bw, p in zip(blocks, widths, plans):
            self._draw_block(b, bx, y + LPAD, bw, h_in, p)
            bx += bw + GAP
        return H

    def _plan_block(self, b, bw):
        items = self._items(b.get("items"))
        if len(items) > MAX_BLOCK_ITEMS:
            self._f("D1", f"区块 '{b.get('title') or b.get('tab')}' 有 {len(items)} 个条目，上限 {MAX_BLOCK_ITEMS}：拆分或只留代表项 + ……")
        head = (TAB_H + 8 if b.get("tab") else 0) + (36 if b.get("title") else LPAD)
        if b.get("stages"):
            mx = max(len(_chunks(it["label"], int(b.get("step_wrap", 2)))) for st in b["stages"] for it in self._items(st.get("steps")))
            chip_h = max(64, up4(mx * (FS + 6) + 16))
            return {"h": head + 32 + chip_h + 2 * LPAD, "chip_h": chip_h, "head": head}
        if not items:
            return {"h": head + LPAD, "head": head, "cols": 1, "rows": 0, "items": []}
        inner = bw - 2 * LPAD
        cols = int(b.get("cols") or max(1, min(len(items), int((inner + ITEM_GAP) // (112 + ITEM_GAP)))))
        rows = math.ceil(len(items) / cols)
        return {"h": head + rows * ITEM_H + (rows - 1) * ITEM_GAP + LPAD, "head": head, "cols": cols, "rows": rows,
                "items": items}

    def _draw_block(self, b, x, y, w, h, p):
        t, S = self.t, self.S
        bid = b.get("id")
        py = y
        if b.get("tab"):
            core = bool(b.get("core"))
            S.rect(x, y, w, TAB_H, fill=t["accent_tint"] if core else t["hub"], stroke=t["accent"] if core else None,
                   rx=6, text=b["tab"], fs=14, weight=600, color=t["accent"] if core else t["header"], z=1)
            py = y + TAB_H + 8
        self._panel(x, py, w, y + h - py, b.get("title"), b.get("kind"), bool(b.get("core")), bid)
        if bid:
            self.rects[bid] = (x, y, w, h)
        top = y + p["head"]
        if b.get("stages"):
            self._chain(b, x + LPAD, top, w - 2 * LPAD, p["chip_h"])
            return
        cols = p["cols"]
        iw = (w - 2 * LPAD - (cols - 1) * ITEM_GAP) / cols
        base = "ai" if b.get("kind") == "ai" else "chip"
        for k, it in enumerate(p["items"]):
            r, c = divmod(k, cols)
            self._chip(x + LPAD + c * (iw + ITEM_GAP), top + r * (ITEM_H + ITEM_GAP), iw, ITEM_H, it, base)

    def _chain(self, b, x, y, w, chip_h):
        """Capability chain: stages (sub-panels) of narrow step chips, ▶ between stages."""
        t, S = self.t, self.S
        stages = b["stages"]
        wrap = int(b.get("step_wrap", 2))
        labels = [it["label"] for st in stages for it in self._items(st.get("steps"))]
        step_w = max([STEP_W] + [up4(text_w(line) + 16) for label in labels for line in _chunks(label, wrap)])
        nat = [len(st.get("steps") or []) * step_w + (len(st.get("steps") or []) - 1) * STEP_GAP + 2 * LPAD
               for st in stages]
        for st, nw in zip(stages, nat):
            if text_w(st.get("title", "")) + 2 * LPAD > nw:
                nat[stages.index(st)] = up4(text_w(st.get("title", "")) + 2 * LPAD)
        need = sum(nat) + STAGE_GAP * (len(stages) - 1)
        if need > w:
            self._f("W1", f"能力链 '{b.get('title')}' 需要 {need:.0f}px，只有 {w:.0f}px：减少步骤、合并阶段或加大该层宽度")
        extra = max(0, w - need) / len(stages)
        sx = x
        self.used.add("flow")
        for i, (st, nw) in enumerate(zip(stages, nat)):
            sw = nw + extra
            core = bool(st.get("core"))
            if core:
                self.cores.append(st.get("title"))
                self.used.add("core")
            S.rect(sx, y, sw, chip_h + 40 + LPAD, fill=t["accent_zone"] if core else "#F7F8FA",
                   stroke=t["accent"] if core else None, rx=8, z=1, id=st.get("id"))
            S.text(sx, y + 6, sw, 24, st.get("title", ""), 14, 600, t["accent"] if core else t["header"])
            steps = self._items(st.get("steps"))
            n = len(steps)
            gap = (sw - 2 * LPAD - n * step_w) / max(1, n - 1) if n > 1 else 0
            cx = sx + (sw - step_w) / 2 if n == 1 else sx + LPAD
            for k, s_ in enumerate(steps):
                lab = s_["label"]
                S.rect(cx, y + 36, step_w, chip_h, fill=t["paper"], stroke=t["rule"], rx=4,
                       text="\n".join(_chunks(lab, wrap)), fs=FS, color=t["node_text"], z=2)
                if k < n - 1:   # small chevron between steps
                    mx, my = cx + step_w + gap / 2, y + 36 + chip_h / 2
                    S.conn([(mx - 4, my - 4), (mx, my), (mx - 4, my + 4)], t["frame"], 1.2, end=False, z=2, glyph="›")
                cx += step_w + gap
            if i < len(stages) - 1:  # stage arrow
                ax, ay = sx + sw + STAGE_GAP / 2, y + 36 + chip_h / 2
                S.poly([(ax - 6, ay - 8), (ax + 6, ay), (ax - 6, ay + 8)], t["ink"])
            sx += sw + STAGE_GAP

    def _side(self, c, x, w, y0, y1):
        t, S = self.t, self.S
        secs = c.get("sections") or []
        if not secs:
            raise SpecError(f"side 列 '{c['id']}' 没有 sections")
        spans = []
        if all(s_.get("span") for s_ in secs):
            for s_ in secs:
                a, b = s_["span"]
                if a not in self.layer_y or b not in self.layer_y:
                    raise SpecError(f"side '{c['id']}' 的 span 引用了不存在的层：{s_['span']}")
                ya = self.layer_y[a][0]
                yb = self.layer_y[b][0] + self.layer_y[b][1]
                spans.append((ya, yb - ya))
        else:   # stack, sharing leftover height by item count
            need = []
            for s_ in secs:
                its = self._items(s_.get("items"))
                need.append(36 + max(1, len(its)) * (ITEM_H + ITEM_GAP) + LPAD)
            left = (y1 - y0) - sum(need) - GAP * (len(secs) - 1)
            if left < 0:
                self._f("V1", f"side 列 '{c['id']}' 内容放不下（差 {-left:.0f}px）：减少条目或给 sections 加 span")
            yy = y0
            for nd in need:
                h = nd + max(0, left) / len(secs)
                spans.append((yy, h))
                yy += h + GAP
        self.rects[c["id"]] = (x, y0, w, y1 - y0)
        for s_, (sy, sh) in zip(secs, spans):
            its = self._items(s_.get("items"))
            sid = s_.get("id")
            kind = s_.get("kind")
            if not its:   # a single labelled box (e.g. 第三方 AI 能力)
                self._panel(x, sy, w, sh, None, kind, bool(s_.get("core")), sid)
                S.text(x, sy, w, sh, "\n".join(_wrap_w(s_.get("title", ""), w - 20, 14)), 14, 600, t["header"])
                continue
            self._panel(x, sy, w, sh, s_.get("title"), kind, bool(s_.get("core")), sid)
            base = {"internal": "internal", "external": "external"}.get(s_.get("owner"), "white")
            if s_.get("vertical"):
                n = len(its)
                top, bot = sy + 36, sy + sh - LPAD
                ih = (bot - top - (n - 1) * GAP) / n
                for k, it in enumerate(its):
                    self._chip(x + LPAD, top + k * (ih + GAP), w - 2 * LPAD, ih, it, "white", vtext=True)
            else:   # stack centred in the space under the title, gap 8..16
                n = len(its)
                room = sh - 36 - LPAD
                g = min(16, max(ITEM_GAP, (room - n * ITEM_H) / max(1, n - 1))) if n > 1 else 0
                top = sy + 36 + max(0, (room - n * ITEM_H - (n - 1) * g) / 2)
                for k, it in enumerate(its):
                    self._chip(x + LPAD, top + k * (ITEM_H + g), w - 2 * LPAD, ITEM_H, it, base)
                if 36 + len(its) * (ITEM_H + ITEM_GAP) + LPAD > sh + 1:
                    self._f("V1", f"side 区块 '{s_.get('title')}' 条目放不下：减少条目或调整 span")

    def _rail(self, r, x, y0, y1):
        """Cross-cutting rail: one segment per concern, vertical text (diagram-design: vertical strip)."""
        t, S = self.t, self.S
        items = r if isinstance(r, list) else (r.get("items") or [p.strip() for p in str(r.get("label", "")).split("/")])
        items = [i for i in items if i]
        need = [len(_vlines(i)) * (FS + 6) + 24 for i in items]
        free = (y1 - y0) - sum(need) - 4 * (len(items) - 1)
        if free < 0:
            self._f("V1", f"侧栏 '{' / '.join(items)}' 竖排放不下（差 {-free:.0f}px）：精简措辞或减少条目")
        yy = y0
        for i, (it, nd) in enumerate(zip(items, need)):
            h = nd + max(0, free) / len(items)
            S.rect(x, yy, self.rail_w, h, fill=t["node"] if i % 2 == 0 else "#F7F8FA", rx=8, text=it, fs=FS, weight=500,
                   color=t["muted"], vtext=True, z=0)
            yy += h + 4

    def _link(self, l_):
        t, S = self.t, self.S
        a, b = self.rects.get(l_["from"]), self.rects.get(l_["to"])
        if not a or not b:
            raise SpecError(f"links 端点必须是层、带 id 的区块、side 列或 section：{l_}")
        if a[0] > b[0]:
            a, b = b, a
        top, bot = max(a[1], b[1]), min(a[1] + a[3], b[1] + b[3])
        if bot - top < 16 or b[0] - (a[0] + a[2]) < 40:
            self._f("K1", f"连线 {l_['from']}↔{l_['to']} 两端没有水平相对的部分或间距不足 40px")
            return
        yc = (top + bot) / 2
        kind = l_.get("kind", "bidir")
        col = t["accent"] if l_.get("emphasis") else (t["ink"] if kind == "flow" else t["muted"])
        x1, x2 = a[0] + a[2] + 2, b[0] - 2
        S.conn([(x1, yc), (x2, yc)], col, 2 if l_.get("emphasis") else 1.5, "" if kind == "flow" else "2,3",
               start=kind == "bidir", end=True, z=3, label=l_.get("label"))

    # ---------------------------------------------------------------- outputs
    def svg(self, slug="biz"):
        sp = self.spec
        return scene_svg(self.S, self.W, self.H, self.t, sp.get("title", tr(self.t, '总体架构')), sp.get("desc", sp.get("title", "")),
                         slug), self.W, self.H

    def wb(self, route_mode="fixed"):
        return scene_wb(self.S, self.t)

    def lint(self):
        return list(self.findings)

    def stats(self):
        n = sum(1 for i in self.S.items if i["t"] == "rect" and i["text"])
        return f"{n} 元素"


# ================================================================ 实体关系图 (layout: er)
ENT_W = 176
ENT_HEAD = 32
FIELD_H = 20
ER_COL_GAP, ER_ROW_GAP = 104, 72
MAX_ENTITIES = 8
MAX_FIELDS = 8


class ERDiagram:
    """Conceptual / logical data model: entities with key fields, relations carry cardinality at both ends."""
    vertical = False

    def __init__(self, spec, theme=None, brand=None, titlebar=None, orient=None):
        self.spec = spec
        self.t = _theme_from(spec, theme, brand, titlebar)
        self.S = Scene()
        self.findings = []
        self.layout()

    def _f(self, code, msg):
        self.findings.append((code, f"[{code}] {msg}"))

    def layout(self):
        sp, t, S = self.spec, self.t, self.S
        ents = sp.get("entities") or []
        if not ents:
            raise SpecError("layout: er 需要 entities")
        if len(ents) > MAX_ENTITIES:
            self._f("D2", f"实体 {len(ents)} 个，超过 {MAX_ENTITIES}：按业务域拆成多张图，跨图实体用虚线框引用")
        ew = int(sp.get("entity_w", ENT_W))
        # row heights from content
        rows = {}
        for e in ents:
            fields = e.get("fields") or []
            if len(fields) > MAX_FIELDS:
                self._f("F2", f"实体 '{e['label']}' 列了 {len(fields)} 个字段，上限 {MAX_FIELDS}：只留主键、外键和讲故事需要的字段")
            e["_h"] = ENT_HEAD + 8 + max(1, len(fields)) * FIELD_H + 8
            r = int(math.floor(float(e.get("row", 0))))
            rows[r] = max(rows.get(r, 0), e["_h"])
        ry, y = {}, TOP_TITLE + 40
        for r in sorted(rows):
            ry[r] = y
            y += rows[r] + ER_ROW_GAP
        self.box = {}
        cores = []
        for e in ents:
            x = BODY_PAD + 24 + float(e.get("col", 0)) * (ew + ER_COL_GAP)
            r = int(math.floor(float(e.get("row", 0))))
            yy = ry[r] + (float(e.get("row", 0)) - r) * (rows[r] + ER_ROW_GAP)
            self.box[e["id"]] = Box(e["id"], e["label"], "entity", x, yy, ew, e["_h"])
            if e.get("core"):
                cores.append(e["label"])
        if len(cores) > 2:
            self._f("F1", f"焦点实体 {len(cores)} 个（{'、'.join(cores)}）：只标聚合根，最多 2 个")
        boxes = list(self.box.values())
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                if _overlap_rect((a.x - 16, a.y - 16, a.r + 16, a.b + 16), (b.x, b.y, b.r, b.b)):
                    self._f("G1", f"实体 '{a.label}' 与 '{b.label}' 重叠或太近：调整 col/row")
        W = max(b.r for b in boxes) + BODY_PAD + 24
        groups = sp.get("groups") or []
        for g in groups:   # bounded context (dashed)
            mem = [self.box[m] for m in g.get("members") or [] if m in self.box]
            if not mem:
                continue
            gx, gy = min(m.x for m in mem) - 20, min(m.y for m in mem) - 36
            gr, gb = max(m.r for m in mem) + 20, max(m.b for m in mem) + 20
            S.rect(gx, gy, gr - gx, gb - gy, fill="#FAFAFB", stroke=t["frame"], rx=8, dash="4,4", z=0)
            S.text(gx + 12, gy + 6, gr - gx - 24, 20, g.get("label", ""), FS, 600, t["soft"], "left")
        for e in ents:
            self._entity(e, self.box[e["id"]])
        self._relations(sp.get("relations") or [])
        bottom = max(b.b for b in boxes)
        _titlebar(S, t, W, sp.get("title", tr(self.t, '数据模型')))
        ly = bottom + 48
        legend = [("tag:PK", tr(self.t, '主键')), ("tag:FK", tr(self.t, '外键')), ("rel", tr(self.t, '两端标基数'))]
        if cores:
            legend.insert(0, ("core", tr(self.t, '聚合根')))
        extra = _legend_row(S, t, legend, BODY_PAD + 8, ly, W)
        self.W, self.H = W, ly + 40 + extra * 32

    def _entity(self, e, b):
        t, S = self.t, self.S
        core = bool(e.get("core"))
        S.rect(b.x, b.y, b.w, b.h, fill=t["paper"], stroke=t["accent"] if core else t["frame"], rx=6, z=1, id=f"ent_{e['id']}")
        S.rect(b.x + 1, b.y + 1, b.w - 2, ENT_HEAD - 1, fill=t["accent_tint"] if core else t["hub"], rx=5,
               text=e["label"], fs=14 if wide_len(e["label"]) <= 9 else FS, weight=600,
               color=t["accent"] if core else t["header"], z=2)
        S.rect(b.x + 1, b.y + ENT_HEAD, b.w - 2, 1, fill=t["rule"], rx=0, z=2)
        if wide_len(e["label"]) > 10:
            self._f("T1", f"实体名 '{e['label']}' 过长：精简到 10 个字以内")
        y = b.y + ENT_HEAD + 8
        for f in e.get("fields") or []:
            f = str(f)
            tag = None
            if f.startswith("#"):
                tag, f = "PK", f[1:].strip()
            elif f.startswith(("→", "->")):
                tag, f = "FK", f.lstrip("→->").strip()
            S.text(b.x + 12, y, b.w - 52, FIELD_H, f, FS, 600 if tag == "PK" else 400, t["ink"], "left")
            if tag:
                S.rect(b.r - 36, y + 3, 26, 14, fill=t["paper"], stroke=t["frame"] if tag == "FK" else t["muted"], rx=2,
                       text=tag, fs=9, weight=600, color=t["muted"], z=2)
            if text_w(f) + 52 > b.w:
                self._f("T1", f"字段 '{f}' 放不下：精简或加大 entity_w")
            y += FIELD_H

    def _relations(self, rels):
        t, S = self.t, self.S
        plan = []
        for r in rels:
            a, b = self.box.get(r["from"]), self.box.get(r["to"])
            if not a or not b:
                raise SpecError(f"relations 引用了不存在的实体：{r}")
            card = r.get("card")
            if not card or len(card) != 2:
                self._f("C1", tr(self.t, "关系 {0}—{1} 两端都要标基数，例如 card: ['1', 'N']", a.label, b.label))
                card = ["", ""]
            gap_x = max(b.x - a.r, a.x - b.r)
            gap_y = max(b.y - a.b, a.y - b.b)
            if gap_x >= gap_y:
                sa, sb = ("R", "L") if b.cx > a.cx else ("L", "R")
            else:
                sa, sb = ("B", "T") if b.cy > a.cy else ("T", "B")
            plan.append([r, a, b, sa, sb, card])
        # fan attach points per (entity, side): spread evenly, ordered by the far end
        slots = {}
        for i, (r, a, b, sa, sb, _) in enumerate(plan):
            slots.setdefault((a.id, sa), []).append((i, 0, b))
            slots.setdefault((b.id, sb), []).append((i, 1, a))
        ends = {}
        for (eid, side), lst in slots.items():
            box = self.box[eid]
            horiz = side in ("T", "B")
            lst.sort(key=lambda it: it[2].cx if horiz else it[2].cy)
            n = len(lst)
            for k, (i, end, _) in enumerate(lst):
                if horiz:
                    span = box.w
                    p = box.x + span * (k + 1) / (n + 1)
                    ends[(i, end)] = (p, box.y if side == "T" else box.b)
                else:
                    top = box.y + ENT_HEAD
                    span = box.h - ENT_HEAD
                    p = top + span * (k + 1) / (n + 1)
                    ends[(i, end)] = (box.x if side == "L" else box.r, p)
        for i, (r, a, b, sa, sb, card) in enumerate(plan):
            p1, p2 = ends[(i, 0)], ends[(i, 1)]
            if sa in ("L", "R"):
                if abs(p1[1] - p2[1]) < 0.5:
                    pts = [p1, p2]
                else:  # snap straight when both ends can share a y
                    lo, hi = max(a.y + ENT_HEAD, b.y + ENT_HEAD), min(a.b, b.b)
                    if hi - lo > 16 and len(slots[(a.id, sa)]) == 1 and len(slots[(b.id, sb)]) == 1:
                        yc = (lo + hi) / 2
                        p1, p2 = (p1[0], yc), (p2[0], yc)
                        pts = [p1, p2]
                    else:
                        mx = (p1[0] + p2[0]) / 2
                        pts = [p1, (mx, p1[1]), (mx, p2[1]), p2]
            else:
                if abs(p1[0] - p2[0]) < 0.5:
                    pts = [p1, p2]
                else:
                    my = (p1[1] + p2[1]) / 2
                    pts = [p1, (p1[0], my), (p2[0], my), p2]
            S.conn(pts, t["muted"], 1.2, end=False, a=f"ent_{a.id}", b=f"ent_{b.id}", sides=(sa, sb), z=1)
            for (pt, nxt, c) in ((pts[0], pts[1], card[0]), (pts[-1], pts[-2], card[1])):
                if not c:
                    continue
                dx, dy = nxt[0] - pt[0], nxt[1] - pt[1]
                ln = math.hypot(dx, dy) or 1
                ux, uy = dx / ln, dy / ln
                cw = text_w(c, 11) + 4
                if abs(uy) < 0.5:   # horizontal: above the line
                    cx = pt[0] + ux * 12 + (0 if ux > 0 else -cw)
                    S.text(cx, pt[1] - 18, cw, 14, c, 11, 600, t["ink"], "left", mono=True, z=3)
                else:               # vertical: right of the line
                    cy = pt[1] + uy * 12 + (0 if uy > 0 else -14)
                    S.text(pt[0] + 5, cy, cw, 14, c, 11, 600, t["ink"], "left", mono=True, z=3)
            if r.get("label"):
                if wide_len(r["label"]) > MAX_EDGE_LABEL:
                    self._f("L1", f"关系标签 '{r['label']}' 超过 {MAX_EDGE_LABEL} 字")
                k = max(range(len(pts) - 1), key=lambda j: math.hypot(pts[j + 1][0] - pts[j][0], pts[j + 1][1] - pts[j][1]))
                (x0, y0), (x1, y1) = pts[k], pts[k + 1]
                lw = up4(text_w(r["label"]) + 8)
                if abs(y0 - y1) < 0.5:
                    lx, ly = (x0 + x1) / 2 - lw / 2, y0 + LABEL_GAP
                else:
                    lx, ly = x0 + LABEL_GAP, (y0 + y1) / 2 - 8
                S.text(lx, ly, lw, 16, r["label"], FS, 500, t["soft"], mask=t["paper"], z=3)
            # G2: relation through a third entity
            for bx in self.box.values():
                if bx.id in (a.id, b.id):
                    continue
                if any(_hit((pts[k], pts[k + 1]), bx) for k in range(len(pts) - 1)):
                    self._f("G2", f"关系 {a.label}—{b.label} 穿过了实体 '{bx.label}'：调整 col/row")

    def svg(self, slug="biz"):
        sp = self.spec
        return scene_svg(self.S, self.W, self.H, self.t, sp.get("title", tr(self.t, '数据模型')), sp.get("desc", sp.get("title", "")),
                         slug), self.W, self.H

    def wb(self, route_mode="fixed"):
        return scene_wb(self.S, self.t)

    def lint(self):
        return list(self.findings)

    def stats(self):
        return f"{len(self.box)} 实体"


# ================================================================ 组织架构 + 数据隔离 (layout: org)
ORG_W, ORG_H, ORG_HSUB = 120, 36, 48
ORG_PITCH = 128            # level-to-level distance (top to top)
ORG_GAP = 16               # sibling gap inside one data scope
ORG_STACK = 3              # more leaf children than this → stacked list under the parent
SCOPE_PAD, SCOPE_STEP, SCOPE_LABEL = 12, 14, 24   # labels sit inside the frame bottom: tree lines enter from the top
MAX_ORG_DEPTH, MAX_ORG_NODES = 4, 24
GRANT_KINDS = {"read": "只读", "write": "读写", "delegate": "委托"}


class OrgDiagram:
    """Org tree with data-isolation scopes (nested = outer sees inner) and cross-scope grants."""
    vertical = False

    def __init__(self, spec, theme=None, brand=None, titlebar=None, orient=None):
        self.spec = spec
        self.t = _theme_from(spec, theme, brand, titlebar)
        self.S = Scene()
        self.findings = []
        self.layout()

    def _f(self, code, msg):
        self.findings.append((code, f"[{code}] {msg}"))

    def _desc(self, nid):
        out, stack = set(), [nid]
        while stack:
            k = stack.pop()
            out.add(k)
            stack += self.n[k]["children"]
        return out

    # ---------------------------------------------------------------- model
    def _model(self):
        sp = self.spec
        self.n = {}

        def walk(o, parent, depth):
            nid = o.get("id") or o["label"]
            if nid in self.n:
                raise SpecError(f"组织 id 重复：{nid}")
            self.n[nid] = {"id": nid, "label": o["label"], "kind": o.get("kind", "unit"), "sub": o.get("sub"),
                           "core": bool(o.get("core")), "stack": o.get("stack"), "parent": parent,
                           "depth": depth, "children": []}
            for c in o.get("children") or []:
                self.n[nid]["children"].append(walk(c, nid, depth + 1))
            return nid
        self.roots = [walk(r, None, 0) for r in sp.get("orgs") or []]
        if not self.roots:
            raise SpecError("layout: org 需要 orgs（组织树）")
        depth = max(v["depth"] for v in self.n.values()) + 1
        if depth > MAX_ORG_DEPTH or len(self.n) > MAX_ORG_NODES:
            self._f("D2", f"组织树 {depth} 层 / {len(self.n)} 个单元，上限 {MAX_ORG_DEPTH} 层 / {MAX_ORG_NODES} 个：拆成集团总图 + 子公司分图")
        # scopes → covered node sets
        self.scopes = []
        for i, s in enumerate(sp.get("scopes") or []):
            cover = set()
            for m in s.get("members") or []:
                if m not in self.n:
                    raise SpecError(f"数据域 '{s.get('label')}' 引用了不存在的组织：{m}")
                cover |= self._desc(m) if s.get("subtree", True) else {m}
            for x in s.get("exclude") or []:
                if x not in self.n:
                    raise SpecError(f"数据域 '{s.get('label')}' 的 exclude 引用了不存在的组织：{x}")
                cover -= self._desc(x)
            self.scopes.append({"id": s.get("id") or f"scope{i}", "label": s.get("label", ""),
                                "kind": s.get("kind", "isolated"), "cover": cover})
        sc = self.scopes
        for i, a in enumerate(sc):
            for b in sc[i + 1:]:
                if a["cover"] & b["cover"] and not (a["cover"] <= b["cover"] or b["cover"] <= a["cover"]):
                    self._f("O1", tr(self.t, "数据域 '{0}' 与 '{1}' 交叉：一个组织只能有一个直属数据域，域之间只能嵌套或并列", a['label'], b['label']))
        self.scope_of = {}
        for nid in self.n:
            cands = [s for s in sc if nid in s["cover"]]
            if cands:
                self.scope_of[nid] = min(cands, key=lambda s: len(s["cover"]))["id"]
        self.by_id = {s["id"]: s for s in sc}

        def inner(s):
            kids = [o for o in sc if o is not s and o["cover"] < s["cover"]]
            return 0 if not kids else 1 + max(inner(o) for o in kids)
        for s in sc:
            s["nest"] = inner(s)
        self.max_nest = max([s["nest"] for s in sc] + [0])
        # siblings: those staying inside the parent's scope first, then by scope, so scopes stay contiguous
        order = {s["id"]: i for i, s in enumerate(sc)}
        for v in self.n.values():
            pscope = self.scope_of.get(v["id"])
            pcover = self.by_id[pscope]["cover"] if pscope else set()

            def key(k):
                return (0 if k in pcover else 1, order.get(self.scope_of.get(k), -1))
            v["children"].sort(key=key)

    # ---------------------------------------------------------------- geometry
    def _size(self, v):
        v["w"] = max(ORG_W, up4(text_w(v["label"]) + 28))
        v["h"] = ORG_HSUB if v["sub"] else ORG_H
        if wide_len(v["label"]) > 9:
            self._f("T1", f"组织名 '{v['label']}' 过长：用简称（≤9 字），全称放 sub 或备注")

    def _stacked(self, v):
        kids = v["children"]
        if v["stack"] is False or not kids or any(self.n[k]["children"] for k in kids):
            return False
        return bool(v["stack"]) or len(kids) > ORG_STACK

    def _gap(self, a, b):
        if self.scope_of.get(a) == self.scope_of.get(b):
            return ORG_GAP
        return 2 * (SCOPE_PAD + SCOPE_STEP * self.max_nest) + 24

    def _width(self, nid):
        v = self.n[nid]
        kids = v["children"]
        if not kids:
            return v["w"]
        if self._stacked(v):
            return max(v["w"], 24 + max(self.n[k]["w"] for k in kids))
        tot = sum(self._width(k) for k in kids) + sum(self._gap(kids[i], kids[i + 1]) for i in range(len(kids) - 1))
        return max(v["w"], tot)

    def _place(self, nid, x0, top):
        v = self.n[nid]
        W = self._width(nid)
        v["y"] = top + v["depth"] * ORG_PITCH
        kids = v["children"]
        if self._stacked(v):
            v["x"] = x0
            y = v["y"] + v["h"] + 20
            for k in kids:
                c = self.n[k]
                c["x"], c["y"], c["stacked"] = x0 + 24, y, True
                y += c["h"] + 10
            return
        v["x"] = x0 + (W - v["w"]) / 2
        cx = x0 + (W - self._width_kids(kids)) / 2 if kids else x0
        for i, k in enumerate(kids):
            self._place(k, cx, top)
            cx += self._width(k) + (self._gap(k, kids[i + 1]) if i + 1 < len(kids) else 0)

    def _width_kids(self, kids):
        return sum(self._width(k) for k in kids) + sum(self._gap(kids[i], kids[i + 1]) for i in range(len(kids) - 1))

    def _box(self, nid):
        v = self.n[nid]
        return v["x"], v["y"], v["x"] + v["w"], v["y"] + v["h"]

    # ---------------------------------------------------------------- layout
    def layout(self):
        sp, t, S = self.spec, self.t, self.S
        self._model()
        for v in self.n.values():
            self._size(v)
        top = TOP_TITLE + 24 + SCOPE_PAD + SCOPE_STEP * self.max_nest
        x = BODY_PAD + 16 + SCOPE_PAD + SCOPE_STEP * self.max_nest
        for i, r in enumerate(self.roots):
            self._place(r, x, top)
            x += self._width(r) + (self._gap(r, self.roots[i + 1]) if i + 1 < len(self.roots) else 0)
        right = max(v["x"] + v["w"] for v in self.n.values())
        bottom = max(v["y"] + v["h"] for v in self.n.values())
        pad_all = SCOPE_PAD + SCOPE_STEP * self.max_nest
        W = up4(max(right + pad_all + 16 + BODY_PAD, 720))
        self.used = set()

        # data scopes (outer first so inner frames paint on top)
        frames = {}
        for s in sorted(self.scopes, key=lambda s: -len(s["cover"])):
            if not s["cover"]:
                continue
            bx = [self._box(k) for k in s["cover"]]
            pad = SCOPE_PAD + SCOPE_STEP * s["nest"]
            fx, fy = min(b[0] for b in bx) - pad, min(b[1] for b in bx) - pad
            fr, fb = max(b[2] for b in bx) + pad, max(b[3] for b in bx) + SCOPE_PAD + SCOPE_LABEL * (1 + s["nest"])
            frames[s["id"]] = (fx, fy, fr, fb)
            shared = s["kind"] == "shared"
            self.used.add("shared" if shared else "isolated")
            S.rect(fx, fy, fr - fx, fb - fy, fill=t["accent_zone"] if shared else "none",
                   stroke=t["accent"] if shared else t["muted"], rx=10, dash="6,4", z=0, id=f"scope_{s['id']}")
            lw = text_w(s["label"]) + 8
            if lw > fr - fx - 16:
                self._f("O4", f"数据域名 '{s['label']}' 比它的框还宽：用简称（≤{int((fr - fx - 24) // FS)} 字），全称写进 desc")
            S.text(fx + 12, fb - SCOPE_LABEL, lw, 18, s["label"], FS, 600, t["accent"] if shared else t["muted"], "left", z=1)
            for k, v in self.n.items():   # O2: a frame must not enclose an org it does not cover
                if k in s["cover"]:
                    continue
                b = self._box(k)
                if b[0] >= fx and b[2] <= fr and b[1] >= fy and b[3] <= fb:
                    self._f("O2", tr(self.t, "数据域 '{0}' 的框住了不属于它的组织 '{1}'：调整成员 / exclude，或把它拆成独立的域", s['label'], v['label']))
        self.frames = frames

        # tree connectors
        for v in self.n.values():
            if not v["parent"]:
                continue
            p = self.n[v["parent"]]
            if v.get("stacked"):
                sx = p["x"] + 12
                pts = [(sx, p["y"] + p["h"]), (sx, v["y"] + v["h"] / 2), (v["x"], v["y"] + v["h"] / 2)]
                S.conn(pts, t["frame"], 1.5, end=False, a=f"org_{p['id']}", b=f"org_{v['id']}", sides=("B", "L"), z=1)
            else:
                pb, ct = p["y"] + p["h"], v["y"]
                mid = ct - 36
                pcx, ccx = p["x"] + p["w"] / 2, v["x"] + v["w"] / 2
                pts = [(pcx, pb), (pcx, mid), (ccx, mid), (ccx, ct)] if abs(pcx - ccx) > 0.5 else [(pcx, pb), (ccx, ct)]
                S.conn(pts, t["frame"], 1.5, end=False, a=f"org_{p['id']}", b=f"org_{v['id']}", sides=("B", "T"), z=1)

        # org units
        cores = []
        for v in self.n.values():
            kind = v["kind"]
            if v["core"]:
                fill, stroke, w_, col = t["accent_tint"], t["accent"], 600, t["accent"]
                cores.append(v["label"])
                self.used.add("core")
            elif kind == "hq":
                fill, stroke, w_, col = t["hub"], None, 600, t["header"]
                self.used.add("hq")
            elif kind == "virtual":
                fill, stroke, w_, col = t["paper"], t["frame"], 400, t["soft"]
                self.used.add("virtual")
            else:
                fill, stroke, w_, col = t["node"], None, 400, t["node_text"]
                self.used.add("unit")
            S.rect(v["x"], v["y"], v["w"], v["h"], fill=fill, stroke=stroke, rx=6, dash="4,3" if kind == "virtual" else None,
                   text=v["label"] if not v["sub"] else None, fs=FS, weight=w_, color=col, z=2, id=f"org_{v['id']}")
            if v["sub"]:
                S.text(v["x"], v["y"] + 6, v["w"], 18, v["label"], FS, w_, col, z=3)
                S.text(v["x"], v["y"] + 26, v["w"], 14, v["sub"], 9, 400, t["soft"], mono=True, z=3)
                if any(is_wide(c) for c in str(v["sub"])):
                    self._f("S1", f"副标签 '{v['sub']}' 含中文：只写编码类拉丁字符（如租户号 T01）")
        if len(cores) > MAX_CORE:
            self._f("F1", f"核心底色用了 {len(cores)} 处，上限 {MAX_CORE}")

        # cross-scope grants
        self.notes = []
        badges = {}
        cross = writes = 0
        for i, g in enumerate(self.spec.get("grants") or []):
            a, b = g.get("from"), g.get("to")
            if a not in self.n or b not in self.n:
                raise SpecError(f"grants 引用了不存在的组织：{g}")
            kind = g.get("kind")
            if kind not in GRANT_KINDS:
                self._f("O3", f"授权 {self.n[a]['label']}→{self.n[b]['label']} 的 kind 必须是 read / write / delegate")
                kind = "read"
            if not g.get("label"):
                self._f("O3", f"授权 {self.n[a]['label']}→{self.n[b]['label']} 没写用途 label：跨域访问必须说明为什么")
            sa, sb = self.scope_of.get(a), self.scope_of.get(b)
            if kind == "read" and sa and sb and sa != sb and self.by_id[sb]["cover"] <= self.by_id[sa]["cover"]:
                self._f("O3", f"授权 {self.n[a]['label']}→{self.n[b]['label']} 多余：外层数据域本来就能看到内层，只读授权不用再画")
            if sa != sb:
                cross += 1
                writes += kind in ("write", "delegate")
            gid = f"A{i + 1}"
            va, vb = self.n[a], self.n[b]
            straight = (va["depth"] == vb["depth"] and not va.get("stacked") and not vb.get("stacked")
                        and not any(o is not va and o is not vb and abs(o["y"] - va["y"]) < 1
                                    and min(va["x"], vb["x"]) < o["x"] < max(va["x"], vb["x"]) for o in self.n.values()))
            col = t["accent"]
            lab = f"{gid} {g.get('label', '')}"
            lw = up4(text_w(lab) + 8)
            if straight:   # fall back to badges when the label would not fit between the two units
                gap_px = abs((vb["x"] if vb["x"] > va["x"] else va["x"]) -
                             ((va["x"] + va["w"]) if vb["x"] > va["x"] else (vb["x"] + vb["w"])))
                straight = gap_px >= lw + 16
            if straight:
                left, rightn = (va, vb) if va["x"] < vb["x"] else (vb, va)
                y = va["y"] + va["h"] / 2
                x1, x2 = left["x"] + left["w"] + 2, rightn["x"] - 2
                fwd = left is va
                S.conn([(x1, y), (x2, y)], col, 1.5, "5,4", start=not fwd, end=fwd, z=3, label=lab)
            else:
                for nid in (a, b):
                    badges.setdefault(nid, []).append(gid)
            self.notes.append(tr(self.t, '{0}  {1} → {2}：{3}（{4}）', gid, va['label'], vb['label'], g.get('label', tr(self.t, '（未写用途）')), tr(self.t, GRANT_KINDS[kind])))
            self.used.add("grant")
        for nid, ids in badges.items():
            v = self.n[nid]
            x = v["x"] + v["w"] + 4
            for gid in reversed(ids):
                bw = up4(len(gid) * 6 + 12)
                x -= bw + 2
                S.rect(x, v["y"] + v["h"] - 7, bw, 16, fill=t["accent_tint"], stroke=t["accent"], rx=8, text=gid, fs=9,
                       weight=600, color=t["accent"], z=4)
        if self.notes:
            self.notes.insert(0, tr(self.t, '跨数据域授权 {0} 条（其中读写 / 委托 {1} 条）', cross, writes))

        # chrome + legend
        _titlebar(S, t, W, sp.get("title", tr(self.t, '组织架构与数据隔离')))
        bottom = max([bottom] + [f[3] for f in frames.values()])
        legend = []
        if "hq" in self.used: legend.append(("hq", tr(self.t, '总部 / 上级')))
        if "unit" in self.used: legend.append(("chip", tr(self.t, '组织单元')))
        if "core" in self.used: legend.append(("core", tr(self.t, '核心单元')))
        if "virtual" in self.used: legend.append(("more", tr(self.t, '虚拟组织')))
        if "shared" in self.used: legend.append(("scope_s", tr(self.t, '共享数据域')))
        if "isolated" in self.used: legend.append(("scope_i", tr(self.t, '隔离数据域')))
        if "grant" in self.used: legend.append(("tag:A1", tr(self.t, '跨域授权')))
        ly = bottom + 40
        extra = self._legend(legend, ly, W)
        ny = ly + 36 + extra * 32
        lines = [line for note in self.notes for line in _wrap_w(note, W - 2 * BODY_PAD - 64)]
        for k, line in enumerate(lines):
            S.text(BODY_PAD + 56, ny + k * 22, max(240, text_w(line) + 16), 20, line, FS, 400, t["muted"], "left")
        self.W, self.H = W, ny + 22 * len(lines) + 24

    def _legend(self, items, y, W):
        t, S = self.t, self.S
        mapped = []
        for kind, label in items:
            if kind == "hq":
                mapped.append(("chip_hub", label))
            elif kind.startswith("scope_"):
                mapped.append((kind, label))
            elif kind.startswith("tag:"):
                mapped.append(("grant", label))
            else:
                mapped.append((kind, label))
        S.rect(BODY_PAD, y - 16, W - 2 * BODY_PAD, 1, fill=t["rule"], rx=0)
        S.text(BODY_PAD + 8, y, 40, 20, tr(self.t, '图例'), FS, 600, t["soft"], "left")
        x, line = BODY_PAD + 56, 0
        for kind, label in mapped:
            if x + 40 + text_w(label) + 24 > W - BODY_PAD and x > BODY_PAD + 56:
                x, line = BODY_PAD + 56, line + 1
            yy = y + line * 32
            if kind == "chip_hub":
                S.rect(x, yy + 2, 28, 16, fill=t["hub"], rx=4)
            elif kind == "chip":
                S.rect(x, yy + 2, 28, 16, fill=t["node"], rx=4)
            elif kind == "core":
                S.rect(x, yy + 2, 28, 16, fill=t["accent_tint"], stroke=t["accent"], rx=4)
            elif kind == "more":
                S.rect(x, yy + 2, 28, 16, fill=t["paper"], stroke=t["frame"], rx=4, dash="4,3")
            elif kind == "scope_s":
                S.rect(x, yy + 2, 28, 16, fill=t["accent_zone"], stroke=t["accent"], rx=4, dash="4,3")
            elif kind == "scope_i":
                S.rect(x, yy + 2, 28, 16, fill=t["paper"], stroke=t["muted"], rx=4, dash="4,3")
            elif kind == "grant":
                S.rect(x, yy + 2, 28, 16, fill=t["accent_tint"], stroke=t["accent"], rx=8, text="A1", fs=9,
                       weight=600, color=t["accent"], z=2)
            x += 36
            S.text(x, yy, text_w(label) + 8, 20, label, FS, 400, t["ink"], "left")
            x += text_w(label) + 24
        return line

    # ---------------------------------------------------------------- outputs
    def svg(self, slug="biz"):
        sp = self.spec
        return scene_svg(self.S, self.W, self.H, self.t, sp.get("title", tr(self.t, '组织架构')), sp.get("desc", sp.get("title", "")),
                         slug), self.W, self.H

    def wb(self, route_mode="fixed"):
        return scene_wb(self.S, self.t)

    def lint(self):
        return list(self.findings)

    def stats(self):
        return f"{len(self.n)} 组织 · {len(self.scopes)} 数据域"


# ================================================================ shared helpers for fishbone / timeline / quadrant
def _legend_sw(S, t, items, y, W):
    """items: (kind, label, opts). kind: box | diamond | dot | line. Wraps at the page edge; returns extra lines."""
    S.rect(BODY_PAD, y - 16, W - 2 * BODY_PAD, 1, fill=t["rule"], rx=0)
    S.text(BODY_PAD + 8, y, 40, 20, tr(t, '图例'), FS, 600, t["soft"], "left")
    x0 = BODY_PAD + 56
    x, line = x0, 0
    for kind, label, o in items:
        if x + 40 + text_w(label) + 24 > W - BODY_PAD and x > x0:
            x, line = x0, line + 1
        yy = y + line * 32
        if kind == "box":
            S.rect(x, yy + 2, 28, 16, fill=o.get("fill", t["node"]), stroke=o.get("stroke"), rx=o.get("rx", 4),
                   dash=o.get("dash"), z=2)
            x += 36
        elif kind == "diamond":
            S.rect(x + 6, yy + 3, 14, 14, fill=o.get("fill", t["paper"]), stroke=o.get("stroke"), dash=o.get("dash"),
                   shape="diamond", z=2)
            x += 28
        elif kind == "dot":
            S.rect(x + 7, yy + 4, 12, 12, fill=o.get("fill", t["ink"]), stroke=o.get("stroke"), rx=6, z=2)
            x += 28
        else:   # line
            S.conn([(x, yy + 10), (x + 30, yy + 10)], o.get("color", t["muted"]), 1.5, o.get("dash", ""),
                   end=o.get("arrow", True), z=2)
            x += 40
        S.text(x, yy, text_w(label) + 8, 20, label, FS, 400, t["ink"], "left")
        x += text_w(label) + 24
    return line


class _SceneDiagram:
    """Common plumbing: theme, scene, findings, outputs."""
    vertical = False
    default_title = "图示"

    def __init__(self, spec, theme=None, brand=None, titlebar=None, orient=None):
        self.spec = spec
        self.t = _theme_from(spec, theme, brand, titlebar)
        self.S = Scene()
        self.findings = []
        self.notes = []
        self.layout()

    def _f(self, code, msg):
        self.findings.append((code, f"[{code}] {msg}"))

    def _notes(self, y, width):
        lines = [line for note in self.notes for line in _wrap_w(note, width - 2 * BODY_PAD - 64)]
        for k, line in enumerate(lines):
            self.S.text(BODY_PAD + 56, y + k * 22, max(240, text_w(line) + 16), 20, line, FS, 400, self.t["muted"], "left")
        return y + 22 * len(lines)

    def svg(self, slug="biz"):
        sp = self.spec
        title = sp.get("title", tr(self.t, self.default_title))
        return scene_svg(self.S, self.W, self.H, self.t, title, sp.get("desc", title), slug), self.W, self.H

    def wb(self, route_mode="fixed"):
        return scene_wb(self.S, self.t)

    def lint(self):
        return list(self.findings)


# ================================================================ 鱼骨图 (layout: fishbone)
FB_CHIP_H, FB_PITCH, FB_HEAD_H = 24, 32, 32
MAX_FB_CATS, MAX_FB_CAUSES = 6, 6


class FishboneDiagram(_SceneDiagram):
    """Cause-effect: problem head on the right, a spine, category bones above / below, causes as chips on each bone.
    Bones are orthogonal (comb layout) to stay inside the connector grammar: no diagonals."""
    default_title = "原因分析"

    def layout(self):
        sp, t, S = self.spec, self.t, self.S
        effect = sp.get("effect")
        if not effect:
            raise SpecError("layout: fishbone 需要 effect（要分析的问题，写成现象：如『评标周期超 30 天』）")
        cats = []
        for c in sp.get("categories") or []:
            causes = [x if isinstance(x, dict) else {"label": x} for x in c.get("causes") or []]
            cats.append({"label": c["label"], "causes": causes})
        if not cats:
            raise SpecError("layout: fishbone 需要 categories（原因大类，如 人 / 机 / 料 / 法 / 环 / 测）")
        if len(cats) > MAX_FB_CATS:
            self._f("D2", f"原因大类 {len(cats)} 个，上限 {MAX_FB_CATS}：合并相近大类，或拆成两张图")
        for c in cats:
            if not c["causes"]:
                self._f("FB1", f"大类 '{c['label']}' 没有任何原因：要么补原因，要么删掉这个大类（凑齐 6M 不是目的）")
            if len(c["causes"]) > MAX_FB_CAUSES:
                self._f("D1", f"大类 '{c['label']}' 有 {len(c['causes'])} 个原因，上限 {MAX_FB_CAUSES}：合并同类，或下钻成子图")
            for x in c["causes"]:
                if wide_len(x["label"]) > 12:
                    self._f("T1", f"原因 '{x['label']}' 过长：精简到 12 个字以内")
        top, bot = cats[0::2], cats[1::2]
        ncol = len(top)
        n_top = max([len(c["causes"]) for c in top] + [1])
        n_bot = max([len(c["causes"]) for c in bot] + [1])

        def chip_w(x):
            return up4(text_w(x["label"]) + 20)

        def head_w(c):
            return max(96, up4(text_w(c["label"], 14) + 32))
        cols = []
        for i in range(ncol):
            pair = [top[i]] + ([bot[i]] if i < len(bot) else [])
            need = max([chip_w(x) for c in pair for x in c["causes"]] + [64]) + 16
            half = max(head_w(c) for c in pair) / 2
            right = max(24, half + 8)
            colw = up4(max(need, half + 8) + right + 24)
            cols.append((colw, right))
        x0 = BODY_PAD + 24
        y_head = TOP_TITLE + 32
        chips_top = y_head + FB_HEAD_H + 20
        spine_y = chips_top + n_top * FB_PITCH + 20
        chips_bot = spine_y + 32
        y_head_b = chips_bot + n_bot * FB_PITCH + 12
        bottom = y_head_b + (FB_HEAD_H if bot else -40)
        hw = max(160, up4(text_w(effect, 14) + 40))
        hx = x0 + sum(c[0] for c in cols) + 24
        W = up4(hx + hw + BODY_PAD + 16)
        roots = []

        def draw_cat(c, bone_x, side):
            hwid = head_w(c)
            hy = y_head if side == "top" else y_head_b
            S.rect(bone_x - hwid / 2, hy, hwid, FB_HEAD_H, fill=t["hub"], rx=6, text=c["label"], fs=14, weight=600,
                   color=t["header"], z=2)
            if side == "top":
                S.conn([(bone_x, hy + FB_HEAD_H), (bone_x, spine_y - 2)], t["muted"], 1.5, end=True, z=1)
            else:
                S.conn([(bone_x, hy), (bone_x, spine_y + 2)], t["muted"], 1.5, end=True, z=1)
            for k, x in enumerate(c["causes"]):
                w = chip_w(x)
                cy = (chips_top + k * FB_PITCH) if side == "top" else (chips_bot + k * FB_PITCH)
                cx = bone_x - 16 - w
                root = bool(x.get("root"))
                if root:
                    roots.append(f"{c['label']} / {x['label']}")
                S.rect(cx, cy, w, FB_CHIP_H, fill=t["accent_tint"] if root else t["node"],
                       stroke=t["accent"] if root else None, rx=4, text=x["label"], fs=FS,
                       weight=600 if root else 400, color=t["node_text"], z=2)
                S.conn([(cx + w, cy + FB_CHIP_H / 2), (bone_x, cy + FB_CHIP_H / 2)], t["frame"], 1.2, end=False, z=1)

        left = x0
        for i, (colw, right) in enumerate(cols):
            bone_x = left + colw - right
            draw_cat(top[i], bone_x, "top")
            if i < len(bot):
                draw_cat(bot[i], bone_x, "bot")
            left += colw
        # spine + head (the problem is the focus: accent tint)
        S.conn([(x0, spine_y), (hx - 2, spine_y)], t["ink"], 2, end=True, z=1)
        S.rect(hx, spine_y - 28, hw, 56, fill=t["accent_tint"], stroke=t["accent"], rx=8, text=effect, fs=14, weight=600,
               color=t["accent"], z=2)
        if len(roots) > MAX_CORE:
            self._f("F1", f"标了 {len(roots)} 个根因，上限 {MAX_CORE}：根因多于 3 个，说明还没找到真正的根因")
        if roots:
            self.notes.append(tr(self.t, '已验证根因 {0} 个：{1}', len(roots), '；'.join(roots)))
            per = {}
            for r in roots:
                per[r.split(' / ')[0]] = per.get(r.split(' / ')[0], 0) + 1
            if len(per) == 1 and len(roots) > 1:
                self.notes.append(tr(self.t, '根因全部集中在『{0}』：先在这一类上做对策', next(iter(per))))
        else:
            self.notes.append(tr(self.t, '尚未标出根因：现在这张图只是假设清单，逐条验证后用 root: true 标出（≤3 个）'))
        _titlebar(S, t, W, sp.get("title", tr(self.t, self.default_title)))
        ly = bottom + 48
        legend = [("box", tr(self.t, '原因大类'), {"fill": t["hub"]}), ("box", tr(self.t, '可能原因'), {"fill": t["node"]})]
        if roots:
            legend.append(("box", tr(self.t, '已验证根因'), {"fill": t["accent_tint"], "stroke": t["accent"]}))
        legend.append(("box", tr(self.t, '问题（结果）'), {"fill": t["accent_tint"], "stroke": t["accent"], "rx": 6}))
        extra = _legend_sw(S, t, legend, ly, W)
        end = self._notes(ly + 36 + extra * 32, W)
        self.W, self.H = W, end + 16
        self.ncause = sum(len(c["causes"]) for c in cats)
        self.ncat = len(cats)

    def stats(self):
        return f"{self.ncat} 大类 · {self.ncause} 原因"


# ================================================================ 里程碑时间线 (layout: timeline)
TL_BAR_H, TL_BAR_PITCH = 28, 36
TL_CHIP_H, TL_ROW_PITCH = 36, 48
MAX_MILESTONES, MAX_PHASES, MAX_TL_ROWS = 15, 8, 3


def _day(v, end=False):
    """YAML gives date objects for YYYY-MM-DD; YYYY-MM strings mean the 1st (or the last day when end=True)."""
    import datetime as _dt
    if isinstance(v, _dt.datetime):
        return v.date()
    if isinstance(v, _dt.date):
        return v
    s = str(v).strip().replace("/", "-").replace(".", "-")
    parts = [int(p) for p in s.split("-")]
    if len(parts) == 2:
        d = _dt.date(parts[0], parts[1], 1)
        if end:
            nxt = _dt.date(parts[0] + (parts[1] == 12), parts[1] % 12 + 1, 1)
            d = nxt - _dt.timedelta(days=1)
        return d
    if len(parts) == 3:
        return _dt.date(*parts)
    raise SpecError(f"日期 '{v}' 无法识别：写成 2026-10 或 2026-10-22")


class TimelineDiagram(_SceneDiagram):
    """Milestone timeline: phases as bars above the axis, milestones as diamonds on it, labels below.
    Optional `today` line and plan-vs-forecast slips (the insight a status report usually hides)."""
    default_title = "里程碑计划"

    def layout(self):
        import datetime as _dt
        sp, t, S = self.spec, self.t, self.S
        ms = [dict(m) for m in sp.get("milestones") or []]
        ph = [dict(p) for p in sp.get("phases") or []]
        if not ms and not ph:
            raise SpecError("layout: timeline 需要 milestones 和/或 phases")
        for m in ms:
            m["d"] = _day(m["date"])
            m["p"] = _day(m["plan"]) if m.get("plan") else None
        for p in ph:
            p["a"], p["b"] = _day(p["from"]), _day(p["to"], end=True)
            if p["a"] > p["b"]:
                self._f("TL3", f"阶段 '{p['label']}' 的开始晚于结束")
        alld = [m["d"] for m in ms] + [m["p"] for m in ms if m["p"]] + [p["a"] for p in ph] + [p["b"] for p in ph]
        start = _day(sp["start"]) if sp.get("start") else min(alld).replace(day=1)
        if sp.get("end"):
            end = _day(sp["end"], end=True)
        else:
            mx = max(alld)
            end = _dt.date(mx.year + (mx.month == 12), mx.month % 12 + 1, 1)
        today = _day(sp["today"]) if sp.get("today") else None
        if len(ms) > MAX_MILESTONES:
            self._f("D2", f"里程碑 {len(ms)} 个，上限 {MAX_MILESTONES}：只留需要决策或对外承诺的节点")
        if len(ph) > MAX_PHASES:
            self._f("D2", f"阶段 {len(ph)} 个，上限 {MAX_PHASES}：合并阶段，或改用甘特图")
        for d, what in [(m["d"], m["label"]) for m in ms] + [(m["p"], m["label"]) for m in ms if m["p"]]:
            if not (start <= d <= end):
                self._f("TL1", f"'{what}' 的日期 {d} 不在时间轴 {start}～{end} 内：调整 start / end")
        W = int(sp.get("width", 1200))
        x0, x1 = BODY_PAD + 40, W - BODY_PAD - 40
        span = max(1, (end - start).days)

        def X(d):
            return x0 + (d - start).days * (x1 - x0) / span

        # phases: greedy rows above the axis
        rows = []
        for p in sorted(ph, key=lambda p: p["a"]):
            a, b = X(p["a"]), X(p["b"])
            r = next((i for i, last in enumerate(rows) if last + 4 <= a), None)
            if r is None:
                rows.append(b)
                r = len(rows) - 1
            else:
                rows[r] = b
            p["row"], p["x"], p["w"] = r, a, max(4, b - a)
        top = TOP_TITLE + (48 if today else 32)
        slips = [m for m in ms if m["p"] and m["p"] != m["d"]]
        axis_y = top + len(rows) * TL_BAR_PITCH + (84 if slips else 44)
        cores = []
        for p in ph:
            y = top + p["row"] * TL_BAR_PITCH
            done = today and p["b"] < today
            now = today and p["a"] <= today <= p["b"]
            if p.get("core"):
                fill, stroke, col, wt = t["accent_tint"], t["accent"], t["accent"], 600
                cores.append(p["label"])
            elif now:
                fill, stroke, col, wt = t["hub"], None, t["header"], 600
            elif done:
                fill, stroke, col, wt = t["node"], None, t["soft"], 400
            else:
                fill, stroke, col, wt = t["paper"], t["frame"], t["node_text"], 400
            S.rect(p["x"], y, p["w"], TL_BAR_H, fill=fill, stroke=stroke, rx=4, text=p["label"], fs=FS, weight=wt,
                   color=col, z=2)
            if text_w(p["label"]) + 12 > p["w"]:
                self._f("T1", f"阶段 '{p['label']}' 太短，放不下名称：缩短名称，或把它改成里程碑")
        # axis + ticks
        S.conn([(x0 - 16, axis_y), (x1 + 16, axis_y)], t["ink"], 2, end=True, z=1)
        quarter = span > 540
        d = start.replace(day=1)
        first = True
        while d <= end:
            if not quarter or d.month in (1, 4, 7, 10):
                x = X(d)
                if x >= x0 - 0.5:
                    S.rect(x - 0.5, axis_y - 8, 1, 6, fill=t["muted"], rx=0, z=1)
                    lab = (f"{d.year} Q{(d.month - 1) // 3 + 1}" if quarter else
                           (f"{d.year}.{d.month:02d}" if first or d.month == 1 else (str(d.month) if self.t['language'] == 'en' else f'{d.month}月')))
                    lw = text_w(lab) + 8
                    S.text(x - lw / 2, axis_y - 28, lw, 16, lab, FS, 400, t["soft"])   # above the axis: leaders run below
                    first = False
            d = _dt.date(d.year + (d.month == 12), d.month % 12 + 1, 1)
        # milestones: diamonds on the axis, labels below in greedy rows (a leader never crosses an earlier label)
        placed = []
        row_bottom = axis_y + 36
        done_n = unknown_n = overdue_n = 0
        for m in sorted(ms, key=lambda m: m["d"]):
            x = X(m["d"])
            lab = m["label"]
            if wide_len(lab) > 10:
                self._f("T1", f"里程碑 '{lab}' 过长：精简到 10 个字以内")
            w = max(72, up4(text_w(lab) + 20))
            cx = min(max(x - w / 2, BODY_PAD), W - BODY_PAD - w)
            r = 0
            while True:
                y = axis_y + 32 + r * TL_ROW_PITCH
                clash = any(pr == r and not (cx + w + 8 <= px or px + pw + 8 <= cx) for px, pr, pw in placed)
                cross = any(pr < r and px - 4 <= x <= px + pw + 4 for px, pr, pw in placed)
                if not clash and not cross:
                    break
                r += 1
                if r > MAX_TL_ROWS + 2:   # 同一天的多个里程碑会无限下沉：到上限就停，交给 TL2 报错
                    break
            placed.append((cx, r, w))
            if r + 1 > MAX_TL_ROWS:
                self._f("TL2", f"里程碑 '{lab}' 排到了第 {r + 1} 行：太密了，合并相邻节点或拉长时间轴（width）")
            done = m.get("status") == "done"
            unknown = m.get("status", "unknown") == "unknown"
            done_n += bool(done)
            unknown_n += bool(unknown)
            overdue_n += bool(m.get("status") == "pending" and today and m["d"] < today)
            if m.get("core"):
                dfill, dstroke = (t["accent"], None) if done else (t["paper"], t["accent"])
                cfill, cstroke, wt = t["accent_tint"], t["accent"], 600
                cores.append(lab)
            elif done:
                dfill, dstroke, cfill, cstroke, wt = t["ink"], None, t["node"], None, 400
            else:
                dfill, dstroke, cfill, cstroke, wt = t["paper"], t["ink"], t["paper"], t["frame"], 400
            S.conn([(x, axis_y + 8), (x, y)], t["frame"], 1.2, end=False, z=1)
            S.rect(x - 8, axis_y - 8, 16, 16, fill=dfill, stroke=dstroke, dash="3,3" if unknown else None, shape="diamond", z=3)
            S.rect(cx, y, w, TL_CHIP_H, fill=cfill, stroke=cstroke, rx=4, z=2)
            S.text(cx, y + 3, w, 16, lab, FS, wt, t["node_text"], z=3)
            S.text(cx, y + 19, w, 14, m["d"].strftime("%m-%d"), 9, 400, t["soft"], mono=True, z=3)
            row_bottom = max(row_bottom, y + TL_CHIP_H)
            if m["p"] and m["p"] != m["d"]:
                px = X(m["p"])
                S.rect(px - 6, axis_y - 6, 12, 12, fill=t["paper"], stroke=t["muted"], dash="2,2", shape="diamond", z=3)
                days = (m["d"] - m["p"]).days
                sy = axis_y - 44
                S.conn([(px, sy), (x, sy)], t["ink"], 1.2, "5,4", end=True, z=3)
                sl = tr(self.t, '{0}{1}天', '+' if days > 0 else '', days)   # free text above the arrow: a board label would hide a short arrow
                S.text((px + x) / 2 - (text_w(sl) + 8) / 2, sy - 22, text_w(sl) + 8, 16, sl, FS, 600, t["ink"], mask=t["paper"], z=5)
                if abs(x - px) < MIN_END:
                    self._f("A1", f"里程碑 '{lab}' 的偏移只有 {abs(days)} 天，箭头画不出来：拉长时间轴或去掉 plan")
        if len(cores) > MAX_CORE:
            self._f("F1", f"焦点（core）用了 {len(cores)} 处，上限 {MAX_CORE}")
        if today:
            if start <= today <= end:
                tx = X(today)
                S.conn([(tx, TOP_TITLE + 30), (tx, row_bottom + 8)], t["accent"], 1.2, "5,4", end=False, z=1)
                lab = tr(self.t, '今天 {0}', today.strftime('%m-%d'))
                S.text(tx - (text_w(lab) + 8) / 2, TOP_TITLE + 12, text_w(lab) + 8, 16, lab, FS, 600, t["accent"],
                       mask=t["paper"], z=5)
            else:
                self._f("TL1", f"today {today} 不在时间轴内")
        # notes: progress + slips
        if ms:
            line = tr(self.t, '里程碑 {0} 个', len(ms))
            if today or any(m.get("status") for m in ms):
                line += tr(self.t, ' · 已完成 {0} 个', done_n)
            if unknown_n:
                line += tr(self.t, ' · 状态待确认 {0} 个', unknown_n)
            if overdue_n:
                line += tr(self.t, ' · 到期未完成 {0} 个', overdue_n)
            self.notes.append(line)
        if slips:
            late = [m for m in slips if m["d"] > m["p"]]
            if late:
                worst = max(late, key=lambda m: (m["d"] - m["p"]).days)
                tot = sum((m["d"] - m["p"]).days for m in late)
                self.notes.append(tr(self.t, '延期 {0} 个，累计 {1} 天；最大：{2} +{3} 天', len(late), tot, worst['label'], (worst['d'] - worst['p']).days))
                after = [m for m in ms if m["d"] > worst["d"] and not m["p"]]
                if after:
                    self.notes.append(tr(self.t, '{0} 之后还有 {1} 个节点没写 plan：是否顺延需核实依赖与缓冲', worst['label'], len(after)))
        _titlebar(S, t, W, sp.get("title", tr(self.t, self.default_title)))
        ly = row_bottom + 48
        legend = [("diamond", tr(self.t, '已完成'), {"fill": t["ink"]}), ("diamond", tr(self.t, '未完成'), {"fill": t["paper"], "stroke": t["ink"]})]
        if unknown_n:
            legend.append(("diamond", tr(self.t, '待确认'), {"fill": t["paper"], "stroke": t["ink"], "dash": "3,3"}))
        if cores:
            legend.append(("diamond", tr(self.t, '关键节点'), {"fill": t["accent"]}))
        if ph:
            legend.append(("box", tr(self.t, '阶段'), {"fill": t["paper"], "stroke": t["frame"]}))
        if slips:
            legend.append(("diamond", tr(self.t, '原计划'), {"fill": t["paper"], "stroke": t["muted"], "dash": "2,2"}))
            legend.append(("line", tr(self.t, '计划 → 预测'), {"color": t["ink"], "dash": "5,4"}))
        if today:
            legend.append(("line", tr(self.t, '今天'), {"color": t["accent"], "dash": "5,4", "arrow": False}))
        extra = _legend_sw(S, t, legend, ly, W)
        endy = self._notes(ly + 36 + extra * 32, W)
        self.W, self.H = W, endy + 16
        self.nms, self.nph = len(ms), len(ph)

    def stats(self):
        return f"{self.nms} 里程碑 · {self.nph} 阶段"


# ================================================================ 四象限图 (layout: quadrant)
MAX_Q_ITEMS = 20
Q_DOT = 12


class QuadrantDiagram(_SceneDiagram):
    """2×2 matrix on two named axes (0–10). Items are dots with labels; `from` draws a move (现状 → 目标)."""
    default_title = "四象限分析"

    def layout(self):
        sp, t, S = self.spec, self.t, self.S
        ax, ay = sp.get("x") or {}, sp.get("y") or {}
        if not ax.get("label") or not ay.get("label"):
            raise SpecError("layout: quadrant 需要 x: {label, low, high} 和 y: {label, low, high}")
        qs = sp.get("quadrants") or {}
        focus = sp.get("focus") or []
        focus = [focus] if isinstance(focus, str) else list(focus)
        items = sp.get("items") or []
        if len(items) > MAX_Q_ITEMS:
            self._f("D2", f"事项 {len(items)} 个，上限 {MAX_Q_ITEMS}：只放需要做取舍的事项")
        size = int(sp.get("size", 560))
        half = size / 2
        px, py = BODY_PAD + 72, TOP_TITLE + 32
        W = up4(px + size + 48 + BODY_PAD)

        def X(v):
            return px + float(v) / 10 * size

        def Y(v):
            return py + size - float(v) / 10 * size
        # quadrants: q1 右上, q2 左上, q3 左下, q4 右下
        geo = {"q1": (px + half, py, "right", "top"), "q2": (px, py, "left", "top"),
               "q3": (px, py + half, "left", "bottom"), "q4": (px + half, py + half, "right", "bottom")}
        obstacles = []
        for q, (qx, qy, ha, va) in geo.items():
            fz = q in focus
            S.rect(qx, qy, half, half, fill=t["accent_zone"] if fz else "#FAFAFB", stroke=t["rule"], rx=0, z=0)
            info = qs.get(q) or {}
            if isinstance(info, str):
                info = {"label": info}
            if info.get("label"):
                lab, note = info["label"], info.get("note")
                lw = max(text_w(lab, 14), text_w(note or "")) + 8
                lh = 20 + (18 if note else 0)
                lx = qx + 12 if ha == "left" else qx + half - 12 - lw
                ly = qy + 10 if va == "top" else qy + half - 10 - lh
                S.text(lx, ly, lw, 20, lab, 14, 600, t["accent"] if fz else t["header"], ha, z=2)
                if note:
                    S.text(lx, ly + 20, lw, 18, note, FS, 400, t["muted"], ha, z=2)
                obstacles.append((lx, ly, lx + lw, ly + lh))
        # axes
        S.conn([(px, py + size + 20), (px + size + 8, py + size + 20)], t["ink"], 1.5, end=True, z=1)
        S.conn([(px - 20, py + size), (px - 20, py - 8)], t["ink"], 1.5, end=True, z=1)
        for v, s_, al in ((0, ax.get("low", tr(self.t, '低')), "left"), (10, ax.get("high", tr(self.t, '高')), "right")):
            w = text_w(s_) + 8
            S.text(X(v) - (0 if al == "left" else w), py + size + 26, w, 16, s_, FS, 400, t["soft"], al)
        xl = ax["label"]
        S.text(px + half - (text_w(xl, 14) + 8) / 2, py + size + 44, text_w(xl, 14) + 8, 20, xl, 14, 600, t["header"])
        for v, s_ in ((0, ay.get("low", tr(self.t, '低'))), (10, ay.get("high", tr(self.t, '高')))):
            w = text_w(s_) + 8
            S.text(px - 28 - w, Y(v) - (16 if v == 0 else 0), w, 16, s_, FS, 400, t["soft"], "right")
        yl = ay["label"]
        vh = len(_vlines(yl)) * (14 + 6) + 8
        S.rect(BODY_PAD, py + half - vh / 2, 24, vh, fill="none", rx=0, text=yl, fs=14, weight=600, color=t["header"],
               vtext=True, z=2)
        # items
        cores, labels, counts = [], [], {q: 0 for q in geo}
        dots = [(X(i["x"]), Y(i["y"])) for i in items]
        for (dx, dy) in dots:
            obstacles.append((dx - Q_DOT / 2 - 2, dy - Q_DOT / 2 - 2, dx + Q_DOT / 2 + 2, dy + Q_DOT / 2 + 2))
        moves = 0
        for it, (dx, dy) in zip(items, dots):
            lab = it["label"]
            for k in ("x", "y"):
                v = float(it[k])
                if not 0 <= v <= 10:
                    self._f("Q1", f"事项 '{lab}' 的 {k}={v} 超出 0–10")
                if abs(v - 5) < 0.25:
                    self._f("Q3", tr(self.t, "事项 '{0}' 正好压在分界线上（{1}={2}）：四象限的价值就是逼你选边，挪到一侧", lab, k, v))
            if wide_len(lab) > 10:
                self._f("T1", f"事项 '{lab}' 过长：精简到 10 个字以内")
            q = ("q1" if it["x"] >= 5 else "q2") if it["y"] >= 5 else ("q4" if it["x"] >= 5 else "q3")
            counts[q] += 1
            core = bool(it.get("core"))
            if core:
                cores.append(lab)
            if it.get("from"):
                fx, fy = X(it["from"][0]), Y(it["from"][1])
                S.rect(fx - 5, fy - 5, 10, 10, fill=t["paper"], stroke=t["muted"], rx=5, dash="2,2", z=3)
                S.conn([(fx, fy), (dx, dy)], t["muted"], 1.2, "5,4", end=True, z=1)
                moves += 1
            S.rect(dx - Q_DOT / 2, dy - Q_DOT / 2, Q_DOT, Q_DOT, fill=t["accent"] if core else t["ink"], rx=Q_DOT / 2, z=3)
            lw, lh = text_w(lab) + 8, 18
            cands = [(dx + 10, dy - lh / 2), (dx - 10 - lw, dy - lh / 2), (dx - lw / 2, dy - 10 - lh),
                     (dx - lw / 2, dy + 10)]
            spot = None
            for cx, cy in cands:
                r = (cx, cy, cx + lw, cy + lh)
                inside = px + 2 <= cx and cx + lw <= px + size - 2 and py + 2 <= cy and cy + lh <= py + size - 2  # inside the plot: the board nests labels in a quadrant
                if inside and not any(_overlap_rect(r, o, 0) for o in obstacles + labels):
                    spot = r
                    break
            if spot is None:
                self._f("Q2", f"事项 '{lab}' 的标签放不下（四周都被占了）：微调坐标或缩短名称")
                spot = (cands[0][0], cands[0][1], cands[0][0] + lw, cands[0][1] + lh)
            labels.append(spot)
            S.text(spot[0], spot[1], lw, lh, lab, FS, 600 if core else 400, t["accent"] if core else t["ink"], "left",
                   mask=None, z=4)
        if len(cores) > MAX_CORE:
            self._f("F1", f"焦点事项 {len(cores)} 个，上限 {MAX_CORE}")
        named = {q: ((qs.get(q) or {}) if isinstance(qs.get(q), dict) else {"label": qs.get(q)}).get("label") or q.upper()
                 for q in geo}
        if items:
            self.notes.append(" · ".join(f"{named[q]} {counts[q]}" for q in ("q1", "q2", "q3", "q4")))
            heavy = max(counts, key=counts.get)
            if counts[heavy] / len(items) >= 0.6 and len(items) >= 4:
                self.notes.append(tr(self.t, '{0}/{1} 个事项挤在『{2}』：评分可能没拉开，复核打分标准', counts[heavy], len(items), named[heavy]))
        if moves:
            self.notes.append(tr(self.t, '现状 → 目标迁移 {0} 项', moves))
        _titlebar(S, t, W, sp.get("title", tr(self.t, self.default_title)))
        ly = py + size + 96
        legend = [("dot", tr(self.t, '事项'), {"fill": t["ink"]})]
        if cores:
            legend.append(("dot", tr(self.t, '重点事项'), {"fill": t["accent"]}))
        if focus:
            legend.append(("box", tr(self.t, '优先象限'), {"fill": t["accent_zone"], "stroke": t["rule"], "rx": 0}))
        if moves:
            legend.append(("line", tr(self.t, '现状 → 目标'), {"color": t["muted"], "dash": "5,4"}))
        extra = _legend_sw(S, t, legend, ly, W)
        endy = self._notes(ly + 36 + extra * 32, W)
        self.W, self.H = W, endy + 16
        self.nitems = len(items)

    def stats(self):
        return f"{self.nitems} 事项"


# ================================================================ IDEF0 功能模型 (layout: idef0)
I0_W, I0_H = 168, 96        # activity box
I0_GX, I0_GY = 112, 56      # staircase step between boxes
I0_PORT = 16                # min spacing between ports on one side
I0_TRUNK = 26               # vertical pitch between control / mechanism trunks
MIN_ACTS, MAX_ACTS = 3, 6


class IDEF0Diagram(_SceneDiagram):
    """IDEF0: activities on a staircase; Input enters left, Control top, Output leaves right, Mechanism bottom.
    Controls are rules (dashed), mechanisms are who/what does the work (systems keep their VI colour)."""
    default_title = "功能模型"

    def layout(self):
        sp, t, S = self.spec, self.t, self.S
        acts = []
        for i, a in enumerate(sp.get("activities") or []):
            acts.append({"i": i, "id": a.get("id") or a["label"], "label": a["label"], "core": bool(a.get("core")),
                         "L": [], "T": [], "R": [], "B": []})
        if not acts:
            raise SpecError("layout: idef0 需要 activities（3–6 个活动，动词开头：编制计划、组织评审…）")
        n = len(acts)
        if not MIN_ACTS <= n <= MAX_ACTS:
            self._f("ID3", f"一张 IDEF0 图放 {MIN_ACTS}–{MAX_ACTS} 个活动，现在 {n} 个：太少说明不用分解，太多就拆成子图（A1 → A11、A12…）")
        idx = {a["id"]: a for a in acts}

        def act(ref, ctx):
            if ref not in idx:
                raise SpecError(f"{ctx} 引用了不存在的活动：{ref}")
            return idx[ref]
        node = str(sp.get("node", "A0"))
        prefix = "A" if node in ("A0", "A-0") else node
        for a in acts:
            a["no"] = f"{prefix}{a['i'] + 1}"
            if wide_len(a["label"]) > 10:
                self._f("T1", f"活动名 '{a['label']}' 过长：动词 + 宾语，≤10 字")
        cores = [a["label"] for a in acts if a["core"]]
        if len(cores) > MAX_CORE:
            self._f("F1", f"核心活动 {len(cores)} 个，上限 {MAX_CORE}")

        # ---- arrows (each records the ports it uses)
        arrows = []
        for x in sp.get("inputs") or []:
            arrows.append({"t": "bin", "to": act(x["to"], "inputs"), "label": x.get("label", "")})
        for x in sp.get("outputs") or []:
            arrows.append({"t": "bout", "from": act(x["from"], "outputs"), "label": x.get("label", "")})
        for x in sp.get("flows") or []:
            a, b = act(x["from"], "flows.from"), act(x["to"], "flows.to")
            as_ = x.get("as", "input")
            if as_ not in ("input", "control"):
                raise SpecError(f"flows 的 as 只能是 input / control：{x}")
            arrows.append({"t": "flow", "from": a, "to": b, "as": as_, "label": x.get("label", ""),
                           "back": b["i"] <= a["i"]})
        ctrls = []
        for k, x in enumerate(sp.get("controls") or []):
            tg = [act(r, "controls.to") for r in (x.get("to") or [])]
            if not tg:
                raise SpecError(f"控制 '{x.get('label')}' 没有 to")
            ctrls.append({"label": x.get("label", ""), "to": sorted(tg, key=lambda a: a["i"]), "k": k})
        mechs = []
        for k, x in enumerate(sp.get("mechanisms") or []):
            tg = [act(r, "mechanisms.to") for r in (x.get("to") or [])]
            if not tg:
                raise SpecError(f"机制 '{x.get('label')}' 没有 to")
            mechs.append({"label": x.get("label", ""), "owner": x.get("owner"), "to": sorted(tg, key=lambda a: a["i"]), "k": k})

        # ---- port order per side (chosen so arrows meet without crossing where avoidable)
        for a in acts:
            fwd_in = sorted([r for r in arrows if r["t"] == "flow" and r["to"] is a and r["as"] == "input" and not r["back"]],
                            key=lambda r: r["from"]["i"])
            bins = [r for r in arrows if r["t"] == "bin" and r["to"] is a]
            fb_in = [r for r in arrows if r["t"] == "flow" and r["to"] is a and r["as"] == "input" and r["back"]]
            a["L"] = [("in", r) for r in fwd_in + bins + fb_in]
            fwd_c = sorted([r for r in arrows if r["t"] == "flow" and r["to"] is a and r["as"] == "control" and not r["back"]],
                           key=lambda r: r["from"]["i"])
            fb_c = [r for r in arrows if r["t"] == "flow" and r["to"] is a and r["as"] == "control" and r["back"]]
            a["T"] = [("in", r) for r in fwd_c] + [("ctl", c) for c in ctrls if a in c["to"]] + [("in", r) for r in fb_c]
            out_fb_c = [r for r in arrows if r["t"] == "flow" and r["from"] is a and r["back"] and r["as"] == "control"]
            outs = [r for r in arrows if r["t"] == "bout" and r["from"] is a]
            fwd_oc = sorted([r for r in arrows if r["t"] == "flow" and r["from"] is a and not r["back"] and r["as"] == "control"],
                            key=lambda r: -r["to"]["i"])
            fwd_oi = sorted([r for r in arrows if r["t"] == "flow" and r["from"] is a and not r["back"] and r["as"] == "input"],
                            key=lambda r: r["to"]["i"])
            out_fb_i = [r for r in arrows if r["t"] == "flow" and r["from"] is a and r["back"] and r["as"] == "input"]
            a["R"] = [("out", r) for r in out_fb_c + outs + fwd_oc + fwd_oi + out_fb_i]
            a["B"] = [("mech", m) for m in mechs if a in m["to"]]
            if not a["T"]:
                self._f("ID1", tr(self.t, "活动 '{0}' 没有控制：IDEF0 要求每个活动至少一个控制（制度、标准、计划、审批规则）——没有约束的活动就是失控点", a['label']))
            if not a["R"]:
                self._f("ID2", tr(self.t, "活动 '{0}' 没有输出：没有产出的活动要么多余，要么漏画了结果", a['label']))
            for side, length in (("L", I0_H), ("R", I0_H), ("T", I0_W), ("B", I0_W)):
                if (len(a[side]) + 1) * I0_PORT > length:
                    self._f("ID5", f"活动 '{a['label']}' 的{'左右上下'['LRTB'.index(side)]}侧有 {len(a[side])} 个箭头，挤不下：拆分活动，或把同类输入合并成一条")

        # ---- geometry
        lw_in = max([text_w(r["label"]) for r in arrows if r["t"] == "bin"] + [40])
        lw_out = max([text_w(r["label"]) for r in arrows if r["t"] == "bout"] + [40])
        x_L = BODY_PAD + 16
        x0 = up4(x_L + lw_in + 40)
        n_fb_c = sum(1 for r in arrows if r["t"] == "flow" and r["back"] and r["as"] == "control")
        n_fb_i = sum(1 for r in arrows if r["t"] == "flow" and r["back"] and r["as"] == "input")
        top_trunk = TOP_TITLE + 40
        y0 = top_trunk + max(0, len(ctrls) - 1) * I0_TRUNK + 40 + 12 * n_fb_c
        for a in acts:
            a["x"], a["y"] = x0 + a["i"] * (I0_W + I0_GX), y0 + a["i"] * (I0_H + I0_GY)
            a["r"], a["b"] = a["x"] + I0_W, a["y"] + I0_H

        def port(a, side, item):
            lst = a[side]
            k = next(j for j, it in enumerate(lst) if it[1] is item)
            m = len(lst)
            if side in ("L", "R"):
                return (a["x"] if side == "L" else a["r"]), a["y"] + I0_H * (k + 1) / (m + 1)
            return a["x"] + I0_W * (k + 1) / (m + 1), (a["y"] if side == "T" else a["b"])
        last = acts[-1]
        x_R = up4(last["r"] + 40 + lw_out + 16)
        W = up4(x_R + BODY_PAD + 8)
        segs, labels = [], []   # for the label lint: (pts, owner) and (rect, owner)

        def line(pts, kind, owner, end=True):
            col, wdt, dash = {"io": (t["ink"], 1.5, ""), "ctl": (t["muted"], 1.2, "5,4"),
                              "mech": (t["muted"], 1.2, "2,3")}[kind]
            S.conn(pts, col, wdt, dash, end=end, z=1)
            segs.append((pts, owner))

        def label(x, y, s, owner, align="left", color=None):
            if not s:
                return
            if wide_len(s) > 10:
                self._f("L1", f"箭头标签 '{s}' 超过 10 字：写成名词短语（采购计划、评审报告）")
            w = text_w(s) + 8
            lx = x if align == "left" else x - w
            S.text(lx, y, w, 16, s, FS, 500, color or t["soft"], "left", mask=t["paper"], z=4)
            labels.append(((lx, y, lx + w, y + 16), owner, s))

        def seg_label(pts, s, owner):
            k = max(range(len(pts) - 1), key=lambda j: math.hypot(pts[j + 1][0] - pts[j][0], pts[j + 1][1] - pts[j][1]))
            (xa, ya), (xb, yb) = pts[k], pts[k + 1]
            if abs(ya - yb) < 0.5:
                label((xa + xb) / 2 - (text_w(s) + 8) / 2, ya - LABEL_GAP - 16, s, owner, color=t["ink"])
            else:
                label(xa + LABEL_GAP, (ya + yb) / 2 - 8, s, owner, color=t["ink"])

        # boundary inputs / outputs
        for r in arrows:
            if r["t"] == "bin":
                px, py = port(r["to"], "L", r)
                pts = [(x_L, py), (px, py)]
                line(pts, "io", id(r))
                label(x_L + 2, py - LABEL_GAP - 16, r["label"], id(r), color=t["ink"])
            elif r["t"] == "bout":
                px, py = port(r["from"], "R", r)
                pts = [(px, py), (x_R, py)]
                line(pts, "io", id(r))
                label(x_R - 2, py - LABEL_GAP - 16, r["label"], id(r), "right", t["ink"])
        # internal flows
        for a in acts:
            fwd = [it[1] for it in a["R"] if it[1]["t"] == "flow" and not it[1]["back"]]
            fwd_in = [r for r in fwd if r["as"] == "input"]
            has_fbi = any(it[1]["t"] == "flow" and it[1]["back"] and it[1]["as"] == "input" for it in a["R"])
            base = a["r"] + (30 if has_fbi else 20)
            for k, r in enumerate(reversed(fwd_in)):   # lower ports turn first: no crossing on the way down
                r["mx"] = base + 14 * k
        fb_c_k = fb_i_k = 0
        for r in arrows:
            if r["t"] != "flow":
                continue
            a, b = r["from"], r["to"]
            px, py = port(a, "R", r)
            if not r["back"] and r["as"] == "input":
                qx, qy = port(b, "L", r)
                pts = [(px, py), (r["mx"], py), (r["mx"], qy), (qx, qy)]
            elif not r["back"]:
                qx, qy = port(b, "T", r)
                pts = [(px, py), (qx, py), (qx, qy)]
            elif r["as"] == "control":
                qx, qy = port(b, "T", r)
                yy = b["y"] - 20 - 12 * fb_c_k
                fb_c_k += 1
                pts = [(px, py), (a["r"] + 20, py), (a["r"] + 20, yy), (qx, yy), (qx, qy)]
            else:
                qx, qy = port(b, "L", r)
                yy = a["b"] + 24 + 12 * fb_i_k
                xx = b["x"] - 16 - 12 * fb_i_k
                fb_i_k += 1
                pts = [(px, py), (a["r"] + 16, py), (a["r"] + 16, yy), (xx, yy), (xx, qy), (qx, qy)]
            line(pts, "ctl" if r["as"] == "control" else "io", id(r))
            if r["label"]:
                seg_label(pts, r["label"], id(r))

        # control trunks (rules come in from the top edge)
        for c in ctrls:
            yk = top_trunk + c["k"] * I0_TRUNK
            xs = [port(a, "T", c)[0] for a in c["to"]]
            if len(xs) > 1:
                line([(min(xs), yk), (max(xs), yk)], "ctl", id(c), end=False)
            for a in c["to"]:
                px, py = port(a, "T", c)
                line([(px, yk), (px, py)], "ctl", id(c))
            c["span"] = (min(xs), max(xs), yk)
        for c in ctrls:   # label: left end, else right end — whichever no foreign line crosses
            x1, x2, yk = c["span"]
            w = text_w(c["label"]) + 8
            for lx in (x1 + 6, x2 + 6, x1 - 6 - w):
                rect = (lx, yk - 20, lx + w, yk - 4)
                if not any(o != id(c) and any(_seg_hits(p, q, rect) for p, q in zip(pts, pts[1:])) for pts, o in segs):
                    break
            label(lx, yk - 20, c["label"], id(c), color=t["muted"])

        # mechanism trunks + chips (who / what does the work)
        n_fbi_all = n_fb_i
        y_m = last["b"] + 44 + 12 * n_fbi_all
        chips, used = [], set()
        for m in mechs:
            yk = y_m + m["k"] * I0_TRUNK
            xs = [port(a, "B", m)[0] for a in m["to"]]
            cw = max(72, up4(text_w(m["label"]) + 24))
            cx = xs[0] - cw / 2
            for ox, ow in chips:
                if cx < ox + ow + 12 and cx + cw + 12 > ox:
                    cx = ox + ow + 12
            chips.append((cx, cw))
            m["chip"] = (cx, cw)
            ccx = cx + cw / 2
            lo, hi = min(xs + [ccx]), max(xs + [ccx])
            if hi - lo > 0.5:
                line([(lo, yk), (hi, yk)], "mech", id(m), end=False)
            for a in m["to"]:
                px, py = port(a, "B", m)
                line([(px, yk), (px, py)], "mech", id(m))
            m["yk"] = yk
        y_chip = y_m + max(0, len(mechs) - 1) * I0_TRUNK + 28
        for m in mechs:
            cx, cw = m["chip"]
            line([(cx + cw / 2, y_chip), (cx + cw / 2, m["yk"])], "mech", id(m), end=False)
            own = m["owner"]
            if own == "internal":
                fill, col, rx = t["sys_int"], t["sys_int_text"], 8
                used.add("sys")
            elif own == "external":
                fill, col, rx = t["sys_ext"], t["sys_ext_text"], 8
                used.add("ext")
            else:
                fill, col, rx = t["node"], t["node_text"], 14
                used.add("people")
            S.rect(cx, y_chip, cw, 28, fill=fill, rx=rx, text=m["label"], fs=FS, weight=500, color=col, z=3)
        W = max(W, up4(max([cx + cw for cx, cw in chips] + [0]) + BODY_PAD + 16))

        # activity boxes
        for a in acts:
            fill, stroke, col, wt = ((t["accent_tint"], t["accent"], t["accent"], 600) if a["core"]
                                     else (t["hub"], None, t["header"], 600))
            S.rect(a["x"], a["y"], I0_W, I0_H, fill=fill, stroke=stroke, rx=4, text=a["label"], fs=14, weight=wt,
                   color=col, z=2, id=f"act_{a['i']}")
            S.text(a["r"] - 40, a["b"] - 20, 34, 14, a["no"], 10, 600, t["soft"], "right", mono=True, z=3)

        # ---- lint: labels vs boxes / labels / foreign lines
        boxes = [(a["x"], a["y"], a["r"], a["b"]) for a in acts]
        for rect, own, s in labels:
            if any(_overlap_rect(rect, bx, 0) for bx in boxes):
                self._f("L2", f"标签 '{s}' 压住了活动框：缩短标签，或调整箭头顺序")
            if any(o != own and any(_seg_hits(p, q, rect) for p, q in zip(pts, pts[1:])) for pts, o in segs):
                self._f("L3", f"标签 '{s}' 压在别的箭头上：缩短标签，或调整 spec 里控制 / 机制的顺序")
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                if _overlap_rect(labels[i][0], labels[j][0], 0):
                    self._f("L3", f"标签 '{labels[i][2]}' 与 '{labels[j][2]}' 重叠")

        # ---- insight notes
        self.notes.append(tr(self.t, '活动 {0} 个 · 控制 {1} 条 · 机制 {2} 个 · 内部流转 {3} 条', n, len(ctrls), len(mechs), sum(1 for r in arrows if r['t'] == 'flow')))
        for m in mechs:
            if n >= 3 and len(m["to"]) / n >= 0.6:
                self.notes.append(tr(self.t, '『{0}』支撑 {1}/{2} 个活动：它一停，整条链就停', m['label'], len(m['to']), n))
        bare = [a["label"] for a in acts if not a["B"]]
        if bare:
            self.notes.append(tr(self.t, '未标机制：{0}——谁来做、用什么做没说清', join_labels(self.t, bare)))
        back = [r for r in arrows if r["t"] == "flow" and r["back"]]
        if back:
            self.notes.append(tr(self.t, '回路 {0} 条（{1}）：每条回路都是潜在的返工，会拉长周期', len(back), join_labels(self.t, (r['label'] or tr(self.t, '未命名') for r in back))))
        only_fb = [a["label"] for a in acts if a["T"] and all(it[0] == "in" for it in a["T"])]
        if only_fb:
            self.notes.append(tr(self.t, '{0} 只受上游结果约束、没有制度控制：标准靠人记，最容易走样', join_labels(self.t, only_fb)))

        _titlebar(S, t, W, (f"{node} " if sp.get("node") else "") + sp.get("title", tr(self.t, self.default_title)))
        bottom = y_chip + 28 if mechs else last["b"] + 24 + 12 * n_fb_i
        ly = bottom + 44
        legend = [("box", tr(self.t, '活动'), {"fill": t["hub"]})]
        if cores:
            legend.append(("box", tr(self.t, '核心活动'), {"fill": t["accent_tint"], "stroke": t["accent"]}))
        legend += [("line", tr(self.t, '输入 / 输出'), {"color": t["ink"]})]
        if ctrls or any(r["t"] == "flow" and r["as"] == "control" for r in arrows):
            legend.append(("line", tr(self.t, '控制（制度 / 规则）'), {"color": t["muted"], "dash": "5,4"}))
        if mechs:
            legend.append(("line", tr(self.t, '机制（谁做 / 用什么做）'), {"color": t["muted"], "dash": "2,3"}))
        if "sys" in used:
            legend.append(("box", tr(self.t, '内部系统'), {"fill": t["sys_int"], "rx": 6}))
        if "ext" in used:
            legend.append(("box", tr(self.t, '外部系统'), {"fill": t["sys_ext"], "rx": 6}))
        if "people" in used:
            legend.append(("box", tr(self.t, '部门 / 岗位'), {"fill": t["node"], "rx": 8}))
        extra = _legend_sw(S, t, legend, ly, W)
        endy = self._notes(ly + 36 + extra * 32, W)
        self.W, self.H = W, endy + 16
        self.nacts = n

    def stats(self):
        return f"{self.nacts} 活动"


def _seg_hits(p, q, rect, inset=1):
    (x0, y0), (x1, y1) = p, q
    lx, hx, ly, hy = min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1)
    return lx < rect[2] - inset and hx > rect[0] + inset and ly < rect[3] - inset and hy > rect[1] + inset


LAYOUTS = {"layers": LayersDiagram, "er": ERDiagram, "org": OrgDiagram,
           "fishbone": FishboneDiagram, "timeline": TimelineDiagram, "quadrant": QuadrantDiagram, "idef0": IDEF0Diagram}


def render_html(svg, W, title, language="zh-CN"):
    return f"""<!doctype html>
<html lang="{esc(language)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<style>
:root{{--bg:#F5F6F7}}
html,body{{margin:0;background:var(--bg)}}
.wrap{{overflow-x:auto;padding:16px}}
.wrap svg{{display:block;min-width:{W:.0f}px;margin:0 auto;background:#fff;box-shadow:0 0 0 1px #E4E6EB}}
</style></head><body><div class="wrap">
{svg}
</div></body></html>"""


def build(spec_path, theme=None, brand=None, titlebar=None, orient=None):
    return build_spec(load_spec(spec_path), theme, brand, titlebar, orient,
                      Path(spec_path).stem.replace(".", "-") or "biz")


CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]
CHROME_NAMES = ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "microsoft-edge", "msedge", "chrome")


def find_chrome():
    """System Chrome / Chromium / Edge / Brave; SAAN_CHROME overrides."""
    import os, shutil
    env = os.environ.get("SAAN_CHROME")
    if env:
        found = shutil.which(env) or (env if Path(env).is_file() else None)
        if not found:
            raise FileNotFoundError(f"SAAN_CHROME 指向的浏览器不存在：{env}")
        return found
    for c in CHROME_CANDIDATES:
        if Path(c).is_file():
            return c
    for name in CHROME_NAMES:
        if shutil.which(name):
            return shutil.which(name)
    raise FileNotFoundError("PNG 需要本机 Chrome / Chromium / Edge；装在非默认位置时用环境变量 SAAN_CHROME 指定可执行文件")


def snapshot(html_path, png_path, scale=1.5):
    """PNG for visual QA / export, via the system Chrome in headless mode (no playwright)."""
    import os, re, subprocess, tempfile
    page = Path(html_path).read_text(encoding="utf-8")
    m = re.search(r"<svg\b.*</svg>", page, re.S)
    vb = m and re.search(r'viewBox="\s*[-\d.]+[\s,]+[-\d.]+[\s,]+([\d.]+)[\s,]+([\d.]+)', m.group(0))
    if not vb:
        raise ValueError(f"{html_path} 中没有带 viewBox 的 <svg>")
    w, h = math.ceil(float(vb.group(1))), math.ceil(float(vb.group(2)))
    png = Path(png_path).resolve()
    with tempfile.TemporaryDirectory(prefix="saan-png-") as td:
        # Standalone page sized exactly to the SVG, so the viewport screenshot equals the SVG element.
        src = Path(td) / "snap.html"
        src.write_text(
            '<!doctype html><html><head><meta charset="utf-8"><style>'
            f'html,body{{margin:0;background:#fff;overflow:hidden}}svg{{display:block;width:{w}px;height:{h}px}}'
            f'</style></head><body>{m.group(0)}</body></html>', encoding="utf-8")
        cmd = [find_chrome(), "--headless", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
               "--no-default-browser-check", f"--user-data-dir={Path(td) / 'profile'}",
               f"--force-device-scale-factor={scale}", f"--window-size={w},{h}",
               f"--screenshot={png}", src.as_uri()]
        if hasattr(os, "geteuid") and os.geteuid() == 0:
            cmd.insert(1, "--no-sandbox")   # Chrome refuses to run as root (containers) without it; the page is our own local file
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if r.returncode != 0 or not png.exists() or not png.stat().st_size:
        raise RuntimeError(f"Chrome 截图失败（退出码 {r.returncode}）：{(r.stderr or '').strip()[-300:]}")


# ================================================================ CLI：--all / --init / --guide / --selftest
# 规则分两类：排版类（随便改到通过）与业务发现类（不许为了通过而改，要么修业务、要么 accept 后写进图例）。
import copy as _copy
import re as _re

FINDING_CODES = {"ID1", "ID2", "DF1", "DF2", "DF3", "AU1", "AU2", "O1", "O2", "Q3", "C1",
                 "P1", "P2", "P3", "P4", "P5"}

FIX = {
    "A1": "拉开两端元素：上下相连 row 差 ≥1.4（进出菱形 ≥1.6），左右相连 lane 差 ≥1.2；分组内用 row_step；U 形回线加大 offset。",
    "G1": "挪开 lane / row；系统块移到对应节点正下方或正右方，用直线接入。",
    "G2": "先改 mid_x / mid_row 让拐点走空白泳道或阶段缝隙，再试 port_a，最后才挪节点。",
    "G3": "给其中一条加 mid_x / mid_row 偏移 ≥12px；本该共用起点的用 bus: true。",
    "G4": "两个有框或有底色的分组拉开位置，或去掉其中一个的框（frame）。",
    "B1": "改连分组里的主线节点，或确认这个框值得画后加 frame: true。",
    "R1": "process 分组里给主线条目标 main: true，跨组 flow 只连 main。",
    "R3": "把系统节点移出分组，在分组外用 data 点线接入。",
    "R5": "标签改成以 special.prefix 开头；这张图不需要强制前缀就删掉 prefix。",
    "R6": "路径行只能沿阶段向前；要回头用 break: true 换行。",
    "E3": "meta 连线补 label（≤8 字）。",
    "F1": "只留真正的核心（≤3 处），其余用 hub 表示主线。",
    "L1": "连线标签精简到 ≤8 字，写动作或数据名。",
    "L2": "用 label_at: start / end 把标签挪到经过空白的那一段。",
    "L3": "删掉能从布局看出来的标签，或换 label_at、拉开行距；数据流图用处理/存储交替排行 + label_at: 1。",
    "T1": "精简措辞（不缩字号）；分层图可减 cols、加 w 或加大 width。",
    "S1": "副标签只写拉丁字符技术值（SHA-256、MySQL），中文挪进节点名或 desc。",
    "D1": "单阶段节点过多：拆成『全景 + 子图』，或合并同类条目。",
    "D2": "超出这类图的预算：按业务域 / 子公司 / 阶段拆图。",
    "V1": "贯穿栏精简到 4–6 个关注点；side 列给 section 加 span 或减条目。",
    "W1": "能力链合并阶段、减少步骤，或让能力层区块单独占满一层。",
    "K1": "links 两端要左右相对、间距 ≥40px：换成相邻两列的 side 或 section。",
    "F2": "实体只留主键、外键和讲故事需要的字段（≤8）。",
    "O3": "授权补 kind（read / write / delegate）和 label；外层看内层本来就可见，不用画只读授权。",
    "O4": "缩短域名，说明放进 desc。",
    "FB1": "删掉没有原因的大类，不要为凑齐 6M 硬造原因。",
    "TL1": "调整 start / end，让所有日期落在轴内。",
    "TL2": "合并相邻里程碑、只留需要决策的节点，或加大 width。",
    "TL3": "阶段的 from 要早于 to。",
    "Q1": "坐标用 0–10 打分。",
    "Q2": "把挤在一起的事项坐标微调 0.3–0.5，或缩短名称。",
    "ID3": "活动合并成 3–6 个，或分解成子图（node: A1 …）。",
    "ID5": "同类箭头合并（多份文件合成『投标文件』），或调整 controls / mechanisms 的顺序。",
    # 业务发现类：给出的是"该问用户什么"，不是"怎么让它通过"
    "ID1": "这个活动没有制度或标准约束。问用户：实际靠什么约束？真没有就 accept，图例会写明『失控点』。不要编一个控制。",
    "ID2": "这个活动没有产出。问用户：它产出什么？产出不明的活动多半该删或合并。",
    "DF1": "两个存储 / 实体之间直接搬数据：问清谁在搬（那就是漏画的处理过程）。",
    "DF2": "处理只进不出或只出不进：问清它的输出去哪、输入从哪来。",
    "DF3": "存储只写不读或只读不写：问清谁在读 / 谁在写；真没人读就说明这份数据没用。",
    "AU1": "控制点说不出防什么风险：问用户。说不出的多半不是关键控制。",
    "AU2": "单据没有来源或去向：问清谁产生、流向谁。",
    "O1": "两个数据域部分交叉：这是权限设计问题，问用户该嵌套还是拆开，不要只挪框。",
    "O2": "数据域框住了不属于它的组织：问清这个组织的数据到底归谁。",
    "Q3": "事项压在分界线上等于没打分：请用户选边并说理由。",
    "C1": "关系缺基数：问清几对几，不要猜。",
    "P1": "存在绕过控制点的路径：这是流程漏洞。问用户这条路径是否真实存在；真实就报告，不要删边让它通过。",
    "P2": "有步骤从起点走不到：问清它从哪里进入流程，或是否该删。",
    "P3": "有步骤走不到终点（死路）：问清它之后发生什么。",
    "P4": "判断只有一个出口：问清另一个分支去哪。",
    "P5": "不相容的两个步骤由同一角色执行：岗位分离问题，报告用户，不要挪列让它通过。",
}

RESOURCE_ROOT = Path(__file__).resolve().parent.parent
GUIDES = {p.stem: p for p in sorted((RESOURCE_ROOT / "guides").glob("*.md"))}
EXAMPLES = {p.stem: p.read_text(encoding="utf-8") for p in sorted((RESOURCE_ROOT / "assets").glob("*.yaml"))}

INIT_ALIAS = {"arch": "1-arch", "flow": "2-flow", "paths": "3-paths", "swim": "4-swim",
              "dfd": "bid-dfd", "audit": "payment-audit", "opportunity": "vendor-opportunity",
              "layers": "biz-platform", "er": "procurement-er", "org": "group-org",
              "fishbone": "bid-fishbone", "timeline": "platform-timeline",
              "quadrant": "ai-quadrant", "idef0": "proc-idef0"}


def build_spec(spec, theme=None, brand=None, titlebar=None, orient=None, slug="biz"):
    validate_spec(spec)
    spec = _copy.deepcopy(spec)
    spec.pop("_special", None)
    lay = spec.get("layout") or "stages"
    if lay in LAYOUTS:
        d = LAYOUTS[lay](spec, theme, brand, titlebar, orient)
    elif lay == "stages":
        d = Diagram(spec, theme, brand, titlebar, orient)
    else:
        raise SpecError(f"layout '{lay}' 无效，可选 stages（默认）| {' | '.join(LAYOUTS)}")
    if spec.get("verify") is not None and spec.get("verify") is not False and not isinstance(d, Diagram):
        raise SpecError("verify 只支持阶段类图示（架构视图 / 主流程 / 泳道 / 审计流程图）")
    svg, W, H = d.svg(slug)
    return d, svg, W, H


# ---------------------------------------------------------------- 流程路径验证（P1–P5）
def _flow_graph(d):
    # Steps exist even when the author forgot all their connectors. Documents,
    # systems, stores and path-row headings are not executable business steps.
    V = d.spec.get("verify")
    scope = V.get("nodes") if isinstance(V, dict) else None
    if scope:
        refs = scope if isinstance(scope, list) else [scope]
        nodes = {d.resolve(n, "verify.nodes").id for n in refs}
        if not nodes <= d.nodes.keys():
            raise SpecError("verify.nodes: 只能引用步骤，不能引用分组")
    else:
        nodes = {n.id for n in d.nodes.values()
                 if n.kind in ("module", "hub", "decision", "optional", "ai", "special") and not getattr(n, "path_tag", False)}
    out, inc = {n: [] for n in d.nodes if n in nodes}, {n: [] for n in d.nodes if n in nodes}
    for e in d.edges:
        a, b = e["a"], e["b"]
        if not (hasattr(a, "cx") and a.id in d.nodes and b.id in d.nodes):
            continue
        if a.id not in nodes or b.id not in nodes:
            continue
        if e["kind"] in ("flow", "return") or e.get("path_step"):
            out.setdefault(a.id, []).append(b.id)
            out.setdefault(b.id, [])
            inc.setdefault(b.id, []).append((a.id, e["kind"]))
            inc.setdefault(a.id, [])
    return out, inc


def _bfs(out, starts, avoid=()):
    par = {s: None for s in starts if s not in avoid}
    q = list(par)
    while q:
        u = q.pop(0)
        for v in out.get(u, []):
            if v not in par and v not in avoid:
                par[v] = u
                q.append(v)
    return par


def _trace(par, x, d):
    p = []
    while x is not None:
        p.append(d.nodes[x].label)
        x = par[x]
    return " → ".join(reversed(p))


def verify_flow(d):
    """Return (findings, verified_notes). Graph = flow / return edges + consecutive path steps."""
    V = d.spec.get("verify")
    if V is None or V is False:
        return [], []
    if V is True:
        V = {}
    out, inc = _flow_graph(d)
    if not out:
        return [("P2", tr(d.t, '[P2] verify 需要流程连线（kind: flow / return 或 paths），这张图没有'))], []
    def ref(r, ctx):
        nid = d.resolve(r, f"verify.{ctx}").id
        if nid not in out:
            raise SpecError(f"verify.{ctx}: '{r}' 不在流程步骤集合中")
        return nid
    lst = lambda v: v if isinstance(v, list) else [v]
    starts = [ref(s, "start") for s in lst(V["start"])] if V.get("start") else \
        [n for n in out if out[n] and not any(k != "return" for _, k in inc.get(n, []))]
    ends = [ref(s, "end") for s in lst(V["end"])] if V.get("end") else [n for n in out if inc[n] and not out[n]]
    L = lambda n: d.nodes[n].label
    found, ok = [], []
    if V.get("nodes"):
        ok.append(tr(d.t, '验证范围：指定的 {0} 个步骤；未列入的节点与跨范围连线不验证', len(out)))
    reach = _bfs(out, starts)
    if V.get("reachable", True):
        miss = [n for n in out if n not in reach]
        for n in miss:
            found.append(("P2", tr(d.t, '[P2] 步骤『{0}』从起点（{1}）走不到', L(n), join_labels(d.t, (L(s) for s in starts)))))
    if V.get("terminates", True):
        rev = {}
        for u, vs in out.items():
            for v in vs:
                rev.setdefault(v, []).append(u)
        back = _bfs(rev, ends)
        for n in reach:
            if n not in back:
                found.append(("P3", tr(d.t, '[P3] 死路：{0} 之后走不到任何终点（{1}）', _trace(reach, n, d), join_labels(d.t, (L(e) for e in ends)))))
    for n in out:
        if d.nodes[n].kind == "decision" and len(set(out[n])) < 2:
            found.append(("P4", tr(d.t, '[P4] 判断『{0}』只有 {1} 个出口', L(n), len(set(out[n])))))
    if not [f for f in found if f[0] in ("P2", "P3")] and V.get("reachable", True) and V.get("terminates", True):
        ok.append(tr(d.t, '已验证：{0} 个步骤都能从起点到达，也都能走到终点', len(out)))
    for m in V.get("must_pass") or []:
        tgt = ref(m["before"], "must_pass.before")
        thr = [ref(x, "must_pass.through") for x in lst(m["through"])]
        if tgt not in reach:
            found.append(("P1", tr(d.t, '[P1] 目标『{0}』从起点不可达，无法确认控制点必经关系', L(tgt))))
            continue
        miss, ex = [], None
        for y in thr:
            par = _bfs(out, starts, avoid={y})
            if tgt in par:
                miss.append(y)
                ex = ex or _trace(par, tgt, d)
        if miss:
            found.append(("P1", tr(d.t, '[P1] 可以绕过 {0} 到达『{1}』，例如：{2}', join_labels(d.t, (L(y) for y in miss), quoted=True), L(tgt), ex)))
        else:
            ok.append(tr(d.t, '已验证：到达『{0}』之前必经 {1}', L(tgt), join_labels(d.t, (L(y) for y in thr), quoted=True)))
    for pair in V.get("separate") or []:
        a, b = ref(pair[0], "separate"), ref(pair[1], "separate")
        def actor(n):
            explicit = getattr(d.nodes[n], "actor", None)
            if explicit:
                return explicit
            if d.spec.get("column_semantics") == "roles":
                col = next(c for c in d.spec["columns"] if c["id"] == d.nodes[n].col)
                return col.get("actor") or col.get("label") or col["id"]
            return None
        aa, ab = actor(a), actor(b)
        if not aa or not ab:
            found.append(("P5", tr(d.t, '[P5] 『{0}』与『{1}』的执行角色待确认，不能由排版列推断岗位分离', L(a), L(b))))
        elif aa == ab:
            found.append(("P5", tr(d.t, '[P5] 『{0}』与『{1}』都由『{2}』执行，违反岗位分离', L(a), L(b), aa)))
        else:
            ok.append(tr(d.t, '已验证：『{0}』与『{1}』声明了不同角色（{2} / {3}）；实际权限另行核验', L(a), L(b), aa, ab))
    return found, ok


# ---------------------------------------------------------------- 校验汇总与分类
def collect(d):
    found = d.lint() if hasattr(d, "lint") else lint(d)
    ok = []
    if isinstance(d, Diagram):
        f2, ok = verify_flow(d)
        found = list(found) + f2
    acc = d.spec.get("accept") or []
    layout, finds, accepted = [], [], []
    for code, msg in found:
        if code in FINDING_CODES:
            hit = next((a for a in acc if a.get("code") == code and (not a.get("match") or a["match"] in msg)), None)
            (accepted if hit else finds).append((code, msg, hit))
        else:
            layout.append((code, msg))
    for a in acc:
        if a.get("code") not in FINDING_CODES:
            layout.append(("ACC", f"[ACC] accept 只能确认业务发现类规则，{a.get('code')} 是排版类，必须修到通过"))
    return layout, finds, accepted, ok


def report(layout, finds, accepted, ok, hints=True):
    seen = set()
    if layout:
        print("— 排版问题（改 spec 直到通过）")
        for code, msg in layout:
            print("  " + msg)
            if hints and code in FIX and code not in seen:
                seen.add(code)
                print(f"    修法：{FIX[code]}")
    if finds:
        print("— 业务发现（不许为了通过而改图；向用户报告，用户确认后写进 accept）")
        for code, msg, _ in finds:
            print("  " + msg)
            if hints and code in FIX and code not in seen:
                seen.add(code)
                print(f"    处理：{FIX[code]}")
    for code, msg, a in accepted:
        print(f"  已确认 {msg}" + (f"（{a.get('note')}）" if a.get("note") else ""))
    for line in ok:
        print("  " + line)


def note_lines(accepted, ok, context=None):
    context = context or {}
    lines = list(ok)
    for code, msg, a in accepted:
        body = _re.sub(r"^\[\w+\]\s*", "", msg)
        lines.append(tr(context, "已确认的发现（{0}）：{1}", code, body) + (tr(context, "。说明：{0}", a["note"]) if a.get("note") else ""))
    return lines


def _wrap(s, n):
    return _wrap_w(s, n)


def add_notes_svg(svg, W, H, t, lines):
    if not lines:
        return svg, H
    rows = []
    for ln in lines:
        rows += _wrap(ln, W - 2 * BODY_PAD - 16)
    extra = 16 + 22 * len(rows) + 8
    H2 = H + extra
    svg = svg.replace(f'viewBox="0 0 {W:.0f} {H:.0f}" width="{W:.0f}" height="{H:.0f}"',
                      f'viewBox="0 0 {W:.0f} {H2:.0f}" width="{W:.0f}" height="{H2:.0f}"', 1)
    parts = [f'<rect x="0" y="{H:.0f}" width="{W:.0f}" height="{extra:.0f}" fill="{t["paper"]}"/>',
             f'<line x1="{BODY_PAD}" y1="{H + 4:.0f}" x2="{W - BODY_PAD:.0f}" y2="{H + 4:.0f}" stroke="{t["rule"]}"/>']
    for k, r in enumerate(rows):
        col = t["ink"] if r.startswith(("已确认", "Confirmed finding")) else t["muted"]
        parts.append(f'<text x="{BODY_PAD + 8}" y="{H + 28 + 22 * k:.0f}" fill="{col}" font-size="12">{esc(r)}</text>')
    i = svg.rindex("</svg>")
    return svg[:i] + "".join(parts) + svg[i:], H2


def add_notes_wb(dsl, W, H, t, lines):
    rows = []
    for ln in lines:
        rows += _wrap(ln, W - 2 * BODY_PAD - 16)
    for k, r in enumerate(rows):
        dsl["nodes"].append({"type": "text", "id": f"note_{k}", "x": BODY_PAD + 8, "y": round(H + 14 + 22 * k),
                             "width": round(W - 2 * BODY_PAD - 16), "height": 20, "text": r, "fontSize": 12,
                             "textColor": t["ink"] if r.startswith(("已确认", "Confirmed finding")) else t["muted"],
                             "textAlign": "left", "verticalAlign": "middle"})
    return dsl


# ---------------------------------------------------------------- 自测：每条规则都要见过它失败
def _load_example(name):
    return yaml.safe_load(EXAMPLES[name])


def _mut(name, fn):
    def run():
        s = _load_example(name)
        fn(s)
        return s
    return run


def _nodes(s):
    return s["nodes"]


def _by_label(lst, label):
    return next(x for x in lst if x.get("label") == label or x.get("id") == label)


MUTATIONS = []   # (code, 说明, builder)


def M(code, what, name, fn):
    MUTATIONS.append((code, what, _mut(name, fn)))


def _m_setup():
    if MUTATIONS:
        return
    # stages
    M("G1", "两个节点放在同一格", "1-arch", lambda s: s["nodes"][1].update(col=s["nodes"][0]["col"], lane=s["nodes"][0].get("lane", 0), row=s["nodes"][0].get("row", 0)))
    M("T1", "节点名超过 10 字", "1-arch", lambda s: s["groups"][0]["items"].__setitem__(0, "需求填报与预算校验汇总表"))
    M("S1", "副标签写中文", "1-arch", lambda s: s["nodes"][0].update(sub="中文副标签"))
    M("F1", "核心底色超过 3 处", "1-arch", lambda s: [n.update(core=True) for n in s["nodes"][:4]])
    M("E3", "meta 连线不带标签", "1-arch", lambda s: s["edges"].append({"from": s["nodes"][0]["label"], "to": s["nodes"][1]["label"], "kind": "meta", "route": "tt", "offset": 40}))
    M("L1", "连线标签超过 8 字", "1-arch", lambda s: s["edges"][0].update(label="这是一个非常长的连线标签"))
    M("B1", "连线指向无框分组", "1-arch", lambda s: s["edges"].append({"from": s["nodes"][0]["label"], "to": "plan_d", "kind": "data"}))
    M("R3", "系统节点放进分组", "1-arch", lambda s: s["groups"][0]["items"].append({"label": "预算系统X", "kind": "system", "owner": "internal"}))
    M("R6", "路径行往回走", "3-paths", lambda s: s["paths"]["rows"][0]["steps"].append(dict(s["paths"]["rows"][0]["steps"][0], label="回到起点", id="back")))
    M("G2", "连线穿过别的节点", "1-arch", lambda s: s["edges"].append({"from": "采购需求", "to": "合同签订", "kind": "data", "route": "h"}))
    M("G3", "两条连线叠在一起", "1-arch", lambda s: s["edges"].append({"from": "合同签订", "to": "CA 签章", "kind": "data", "route": "h"}))
    M("G5", "左右相接的两个节点高低差过半行，只能折两次", "bid-dfd", lambda s: _by_label(s["nodes"], "评分表").update(row=5.95))
    M("G4", "两个有框分组交叠", "1-arch", lambda s: next(x for x in s["groups"] if x["id"] == "source_d").update(frame=True, row=3.6, lane=1.0))
    M("L2", "连线标签压住节点", "1-arch", lambda s: s["edges"].append({"from": "采购需求", "to": "采购寻源", "kind": "data", "route": "v", "label": "标签"}))
    M("L3", "两个连线标签互相重叠", "1-arch", lambda s: s["edges"].append({"from": "财务系统", "to": "结算支付", "kind": "data", "route": "h", "label": "标签"}))
    M("R1", "跨组主流程挂在非主线条目上", "1-arch", lambda s: (next(x for x in s["groups"] if x["id"] == "methods").update(type="process", items=[{"label": "公开招标", "main": True}, "询比采购", "竞争谈判", "单一来源"]), s["edges"].append({"from": "采购需求", "to": "询比采购", "kind": "flow"})))
    M("A1", "上下相连的两节点贴得太近", "2-flow", lambda s: s["paths"]["rows"][0]["steps"][-1].update(drow=0.7))
    M("D1", "单阶段节点过多", "1-arch", lambda s: s["groups"][0]["items"].extend(f"条目{k}" for k in range(26)))
    # profiles
    M("AU1", "控制点不写风险", "payment-audit", lambda s: _by_label(s["nodes"], "审核发票").pop("risk"))
    M("AU2", "单据没有连线", "payment-audit", lambda s: s["edges"].__setitem__(slice(None), [e for e in s["edges"] if e["from"] != "发票"]))
    M("DF1", "存储直连存储", "bid-dfd", lambda s: s["edges"].append({"from": [n for n in s["nodes"] if n.get("kind") == "store"][0]["label"], "to": [n for n in s["nodes"] if n.get("kind") == "store"][1]["label"], "kind": "data", "route": "rr", "offset": 40}))
    M("DF2", "处理只进不出", "bid-dfd", lambda s: s["edges"].__setitem__(slice(None), [e for e in s["edges"] if e["from"] != [n for n in s["nodes"] if n.get("kind", "module") == "module"][0]["label"]]))
    M("DF3", "存储只写不读", "bid-dfd", lambda s: s["edges"].__setitem__(slice(None), [e for e in s["edges"] if e["from"] != [n for n in s["nodes"] if n.get("kind") == "store"][0]["label"]]))
    # flow verification
    M("P1", "加一条绕过控制点的直达路径", "payment-audit", lambda s: s["edges"].append({"from": "提交付款申请", "to": "执行支付", "kind": "flow", "route": "rr", "offset": 40}))
    M("P2", "起点之外孤立的步骤", "payment-audit", lambda s: (s["nodes"].append({"label": "紧急付款", "col": "pay", "lane": 1.15, "row": 0.4}), s["edges"].append({"from": "紧急付款", "to": "执行支付", "kind": "flow"}), s["verify"].update(start="提交付款申请")))
    M("P3", "走不到终点的死路", "payment-audit", lambda s: (s["nodes"].append({"label": "挂起待查", "col": "fin", "lane": 1.15, "row": 5.2}), s["edges"].append({"from": "match", "to": "挂起待查", "kind": "flow"})))
    M("P4", "判断只有一个出口", "payment-audit", lambda s: s["edges"].__setitem__(slice(None), [e for e in s["edges"] if e.get("kind") != "return"]))
    M("P5", "不相容岗位由同一角色执行", "payment-audit", lambda s: _by_label(s["nodes"], "执行支付").update(col="biz"))
    # layers / er / org
    M("R5", "重点能力标签不符前缀", "biz-platform", lambda s: (s.update(special={"label": "AI 能力", "prefix": "AI"}), s["layers"][3]["blocks"][1].update(title="智能平台")))
    M("D2", "分层超过 6 层", "biz-platform", lambda s: s["layers"].extend(dict(_copy.deepcopy(l), id=l["id"] + "2") for l in s["layers"][:2]))
    M("V1", "贯穿栏放不下", "biz-platform", lambda s: s["rails"].update(left=[f"关注点{k}的很长很长的说明文字" for k in range(9)]))
    M("W1", "能力链太宽", "biz-platform", lambda s: s["layers"][2]["blocks"][0]["stages"].extend(_copy.deepcopy(s["layers"][2]["blocks"][0]["stages"]) * 2))
    M("K1", "集成连线两端不相对", "biz-platform", lambda s: s["links"].append({"from": "ui", "to": "tech", "kind": "bidir", "label": "集成"}))
    M("F2", "实体字段超过 8 个", "procurement-er", lambda s: s["entities"][0]["fields"].extend([f"字段{k}" for k in range(9)]))
    M("C1", "关系缺基数", "procurement-er", lambda s: s["relations"][0].update(card=["1"]))
    M("O1", "两个数据域部分交叉", "group-org", lambda s: s["scopes"].append({"id": "x", "label": "交叉域", "members": ["group"], "exclude": [s["scopes"][1]["members"][0]]}))
    M("O2", "数据域的框圈进了别的组织", "group-org", lambda s: s["scopes"].append({"id": "y", "label": "跨域", "members": ["coa", "coc"]}))
    M("O3", "授权不写类型", "group-org", lambda s: s["grants"][0].pop("kind"))
    M("O4", "域名太长放不下", "group-org", lambda s: s["scopes"][1].update(label="这是一个名字非常非常非常长以至于放不进框里的数据域"))
    # fishbone / timeline / quadrant / idef0
    M("FB1", "空的原因大类", "bid-fishbone", lambda s: s["categories"].append({"label": "测", "causes": []}))
    M("TL1", "日期超出轴范围", "platform-timeline", lambda s: s["milestones"].append({"label": "远期目标", "date": "2029-01-01"}))
    M("TL2", "里程碑挤成一团", "platform-timeline", lambda s: s["milestones"].extend({"label": f"节点{k}", "date": s["milestones"][0]["date"]} for k in range(5)))
    M("TL3", "阶段开始晚于结束", "platform-timeline", lambda s: s["phases"][0].update(to="2026-01"))
    M("Q1", "坐标超出 0–10", "ai-quadrant", lambda s: s["items"][0].update(x=11))
    M("Q2", "事项挤在一点", "ai-quadrant", lambda s: s["items"].extend({"label": f"事项{k}号很长的名字", "x": 7.6, "y": 8.3} for k in range(4)))
    M("Q3", "事项压在分界线上", "ai-quadrant", lambda s: s["items"][0].update(x=5))
    M("ID1", "活动没有控制", "proc-idef0", lambda s: [c.update(to=[x for x in c["to"] if x != s["activities"][0]["id"]]) for c in s["controls"]] and s.update(flows=[f for f in s.get("flows", []) if not (f["to"] == s["activities"][0]["id"] and f.get("as") == "control")]))
    M("ID2", "活动没有输出", "proc-idef0", lambda s: (s.update(outputs=[o for o in s.get("outputs", []) if o["from"] != s["activities"][-1]["id"]]), s.update(flows=[f for f in s.get("flows", []) if f["from"] != s["activities"][-1]["id"]])))
    M("ID3", "活动少于 3 个", "proc-idef0", lambda s: _idef0_trim(s))
    M("ID5", "同一侧箭头太多", "proc-idef0", lambda s: s["inputs"].extend({"to": "plan", "label": f"输入{k}"} for k in range(6)))


def _idef0_trim(s):
    keep = {a["id"] for a in s["activities"][:2]}
    s["activities"] = s["activities"][:2]
    s["inputs"] = [x for x in s.get("inputs", []) if x["to"] in keep]
    s["outputs"] = [x for x in s.get("outputs", []) if x["from"] in keep] or [{"from": s["activities"][-1]["id"], "label": "结果"}]
    s["flows"] = [x for x in s.get("flows", []) if x["from"] in keep and x["to"] in keep]
    for k in ("controls", "mechanisms"):
        s[k] = [dict(x, to=[t for t in x["to"] if t in keep]) for x in s.get(k, []) if any(t in keep for t in x["to"])]


ALL_CODES = {"A1", "AU1", "AU2", "B1", "C1", "D1", "D2", "DF1", "DF2", "DF3", "E3", "F1", "F2", "FB1",
             "G1", "G2", "G3", "G4", "G5", "ID1", "ID2", "ID3", "ID5", "K1", "L1", "L2", "L3", "O1", "O2", "O3", "O4",
             "Q1", "Q2", "Q3", "R1", "R3", "R5", "R6", "S1", "T1", "TL1", "TL2", "TL3", "V1", "W1",
             "P1", "P2", "P3", "P4", "P5"}


def selftest():
    _m_setup()
    bad = 0
    print("① 示例全部通过（含已确认的发现）")
    for name in sorted(EXAMPLES):
        try:
            d, *_ = build_spec(_load_example(name))
            layout, finds, acc, ok = collect(d)
        except SpecError as ex:
            layout, finds = [("SPEC", str(ex))], []
        st = "PASS" if not layout and not finds else "FAIL"
        bad += st == "FAIL"
        print(f"  {st}  {name}" + ("" if st == "PASS" else f"：{[c for c, *_ in layout + finds]}"))
    print("② 每条规则都要能失败（把示例故意改坏一处）")
    covered = set()
    for code, what, mk in MUTATIONS:
        try:
            d, *_ = build_spec(mk())
            layout, finds, acc, ok = collect(d)
            got = {c for c, *_ in layout} | {c for c, *_ in finds}
        except SpecError as ex:
            got = {"SPEC"}
        hit = code in got
        covered |= {code} if hit else set()
        bad += not hit
        print(f"  {'DETECTED' if hit else 'MISSED  '}  {code:<4} {what}" + ("" if hit else f"（实际报出：{sorted(got) or '无'}）"))
    allc = ALL_CODES
    left = sorted(allc - covered)
    bad += len(left)
    print(f"③ 规则覆盖 {len(covered)}/{len(allc)}" + (f"；尚无改坏样例：{'、'.join(left)}" if left else ""))
    print("SELFTEST " + ("PASS" if not bad else f"FAIL（{bad} 项）"))
    return bad == 0


# ---------------------------------------------------------------- 入口
def main():
    ap = argparse.ArgumentParser(description="saan-diagram v1.3.0: YAML spec -> HTML/SVG/PNG/whiteboard DSL")
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--language", choices=["en", "zh-CN"], help="Language of generated captions; overrides spec.language, does not translate input labels")
    ap.add_argument("--result-json", help="保存机器可读的校验与产物状态（出图默认写 <slug>.result.json）")
    ap.add_argument("--all", action="store_true", help="一次完成：校验 → HTML + PNG + 画板 DSL（推荐）")
    ap.add_argument("--outdir", help="--all 的输出目录（默认与 spec 同目录）")
    ap.add_argument("--init", nargs="?", const="list", help="打印起步模板：arch flow paths swim dfd audit opportunity layers er org fishbone timeline quadrant idef0")
    ap.add_argument("--guide", nargs="?", const="list", help="打印某类图的详细写法：" + " ".join(sorted(GUIDES) or ["…"]))
    ap.add_argument("--selftest", action="store_true", help="自测：示例全部通过 + 每条规则都能被改坏样例触发")
    ap.add_argument("-o", "--out", help="输出 HTML（默认与 spec 同名）")
    ap.add_argument("--svg", help="另存纯 SVG")
    ap.add_argument("--png", help="另存 PNG（调用本机 Chrome headless；SAAN_CHROME 可指定浏览器）")
    ap.add_argument("--scale", type=float, default=1.5)
    ap.add_argument("--theme", choices=sorted(PRESETS), help="兼容旧版：gray=飞书蓝主色，blue=汇报蓝主色")
    ap.add_argument("--brand", help="VI 主色 #RRGGBB")
    ap.add_argument("--titlebar", choices=TITLEBARS, help="标题栏：plain（默认，无边框）| outline（白底线框）| gray | brand | dark")
    ap.add_argument("--orient", choices=["horizontal", "vertical"], help="横向或竖向（只对阶段类图示有效）")
    ap.add_argument("--lint", action="store_true", help="只校验")
    ap.add_argument("--wb", help="另存飞书画板 DSL（JSON）")
    ap.add_argument("--wb-route", choices=["fixed", "auto"], default="fixed")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(0 if selftest() else 1)
    if a.guide:
        if a.guide == "list" or a.guide not in GUIDES:
            print("可用主题：" + "、".join(sorted(GUIDES)))
            sys.exit(0 if a.guide == "list" else 3)
        print(GUIDES[a.guide].read_text(encoding="utf-8"))
        return
    if a.init:
        name = INIT_ALIAS.get(a.init, a.init)
        if a.init == "list" or name not in EXAMPLES:
            print("可用模板：" + "  ".join(f"{k}（{v}）" for k, v in INIT_ALIAS.items()))
            sys.exit(0 if a.init == "list" else 3)
        print(EXAMPLES[name])
        return
    if not a.spec:
        ap.error("需要 spec 文件；或用 --init / --guide / --selftest")

    slug = Path(a.spec).stem.replace(".", "-") or "biz"
    outdir = Path(a.outdir) if a.outdir else Path(a.spec).parent
    result_path = Path(a.result_json) if a.result_json else (None if a.lint else outdir / f"{slug}.result.json")
    result = {"schema_version": 1, "status": "pending", "validation": "not_run", "artifacts": {}, "errors": []}

    def finish(code, status):
        result.update(exit_code=code, status=status)
        if result_path:
            try:
                result_path.parent.mkdir(parents=True, exist_ok=True)
                result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                print(f"结果：{result_path}")
            except OSError as ex:
                print(f"结果文件写入失败：{ex}")
                return 4
        return code

    try:
        spec = load_spec(a.spec)
        if a.language:
            spec["language"] = a.language
        d, svg, W, H = build_spec(spec, a.theme, a.brand, a.titlebar, a.orient, slug)
        layout, finds, accepted, ok = collect(d)
    except SpecError as ex:
        print(f"SPEC 错误: {ex}")
        result["errors"].append(str(ex))
        return finish(3, "invalid_spec")
    report(layout, finds, accepted, ok)
    result["language"] = d.t["language"]
    result["validation"] = "failed" if layout or finds else "passed"
    result["findings"] = {"layout": layout, "unconfirmed": finds, "accepted": accepted, "verified": ok}
    size = d.stats() if hasattr(d, "stats") else f"{len(d.nodes)} 节点 · {len(d.edges)} 连线"
    if a.lint or layout or finds:
        print(f"{'FAIL' if layout or finds else 'PASS'}: 排版 {len(layout)} 条 · 发现 {len(finds)} 条（已确认 {len(accepted)}） · {size}")
        return finish(1 if layout else 2 if finds else 0, "validation_failed" if layout or finds else "validated")
    notes = note_lines(accepted, ok, d.t)
    svg, H2 = add_notes_svg(svg, W, H, d.t, notes)
    out = Path(a.out) if a.out else outdir / f"{slug}.html"

    def produce(kind, path, writer):
        dest = Path(path)
        entry = result["artifacts"][kind] = {"path": str(dest), "status": "pending"}
        # Replace only after successful generation, so stale files are never reported as new.
        import tempfile
        tmp = None
        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(dir=dest.parent, suffix=dest.suffix, delete=False) as fh:
                tmp = Path(fh.name)
            writer(tmp)
            if not tmp.stat().st_size:
                raise OSError("输出文件为空")
            tmp.replace(dest)
            entry["status"] = "generated"
            print(f"  {dest}")
        except Exception as ex:
            entry.update(status="failed", error=f"{ex.__class__.__name__}: {ex}")
            result["errors"].append(f"{kind}: {entry['error']}")
            print(f"{kind} 生成失败：{entry['error']}")
        finally:
            if tmp and tmp.exists():
                tmp.unlink()

    produce("html", out, lambda p: p.write_text(render_html(svg, W, d.spec.get("title", "diagram"), d.t["language"]), encoding="utf-8"))
    if a.svg:
        produce("svg", a.svg, lambda p: p.write_text(svg, encoding="utf-8"))
    png = a.png or (str(outdir / f"{slug}.png") if a.all else None)
    if png:
        if result["artifacts"]["html"]["status"] == "generated":
            produce("png", png, lambda p: snapshot(out, p, a.scale))
        else:
            result["artifacts"]["png"] = {"path": str(png), "status": "blocked", "error": "HTML 未生成"}
    wbp = a.wb or (str(outdir / f"{slug}.wb.json") if a.all else None)
    if wbp:
        def write_wb(path):
            dsl = d.wb(a.wb_route) if hasattr(d, "wb") else to_wb_dsl(d, a.wb_route)
            dsl = add_notes_wb(dsl, W, H, d.t, notes)
            path.write_text(json.dumps(dsl, ensure_ascii=False, indent=1), encoding="utf-8")
        produce("whiteboard_dsl", wbp, write_wb)
    failed = any(v["status"] != "generated" for v in result["artifacts"].values())
    print(f"{'PARTIAL' if failed else 'OK'} {W:.0f}x{H2:.0f} · {size} · 已确认发现 {len(accepted)} · 已验证 {len(ok)}")
    return finish(4 if failed else 0, "partial" if failed else "generated")


if __name__ == "__main__":
    sys.exit(main())
