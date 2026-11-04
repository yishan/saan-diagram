#!/usr/bin/env python3
"""Review Mermaid source against a control list, business logic, and Saan style rules. Python 3 stdlib only."""
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

THEMES = Path(__file__).resolve().parent.parent / "assets" / "themes"
KINDS = {"arch", "flow", "overview", "approval", "audit"}
SHAPE = r'@\{(?:[^{}"]|"[^"]*")*\}|\(\[.*?\]\)|\[\(.*?\)\]|\[\[.*?\]\]|\(\(.*?\)\)|\{\{.*?\}\}|\[.*?\]|\(.*?\)|\{.*?\}|>.*?\]'
NODE = re.compile(rf"\s*([^\s\[\]\(\)\{{\}}<>|&:;\"@-]+(?:-[^\s\[\]\(\)\{{\}}<>|&:;\"@-]+)*)\s*({SHAPE})?(?::::(\w+))?\s*")
LINK = re.compile(r"\s*(?:([^\s@|&]+)@)?(?:(--|-\.|==)\s+([^|]*?)\s+)?(<?-{2,}>|<?-\.+->|-\.+-|<?={2,}>|-{3,}|--[xo]|~~~)\s*(?:\|([^|]*)\|)?\s*")
DECISION_SHAPES = {"diam", "diamond", "decision", "question"}
REVIEW = re.compile(r"审|批|核|校验|复验|验收")
REJECT = re.compile(r"退回|驳回|拒绝|不通过|不合格|否|修改")
SEQ_OPEN = re.compile(r"(alt|opt|loop|par|par_over|critical|break|rect|box)\b")
SEQ_MID = {"else": "alt", "and": "par", "option": "critical"}
SEQ_MSG = re.compile(r"^(.+?)\s*(<<-->>|<<->>|-->>|->>|--x|-x|--\)|-\)|-->|->)\s*([+-]?)\s*([^:]+?)\s*:(.*)$")
FENCE = re.compile(r"^[ \t]*(`{3,}|~{3,})[ \t]*mermaid[ \t]*\n(.*?)^[ \t]*\1[ \t]*$", re.M | re.S)
GANTT_TAGS = {"active", "done", "crit", "milestone", "vert"}
GANTT_KEYS = ("dateFormat", "axisFormat", "title", "section", "excludes", "includes", "todayMarker", "tickInterval",
              "weekday", "weekend", "displayMode", "inclusiveEndDates", "topAxis", "accTitle", "accDescr")
FLOWLIKE = ("flowchart", "graph", "swimlane-beta")
THEMED = FLOWLIKE + ("sequenceDiagram", "stateDiagram", "stateDiagram-v2", "erDiagram")

# Mermaid release that added each diagram header. Source: mermaid-pro src/diagram-types.json (built from mermaid@12.1.0).
SINCE = {
    "graph": "8.0.0", "flowchart": "9.0.0", "flowchart-elk": "9.4.0", "sequenceDiagram": "8.0.0",
    "classDiagram": "8.0.0", "stateDiagram": "8.0.0", "stateDiagram-v2": "8.0.0", "erDiagram": "8.0.0",
    "gantt": "8.0.0", "pie": "8.0.0", "journey": "8.0.0", "gitGraph": "8.0.0", "requirementDiagram": "9.0.0",
    "C4Context": "9.0.0", "C4Container": "9.0.0", "C4Component": "9.0.0", "C4Dynamic": "9.0.0", "C4Deployment": "9.0.0",
    "info": "9.0.0", "mindmap": "9.3.0", "timeline": "9.4.0", "zenuml": "10.0.0", "quadrantChart": "10.2.0",
    "sankey": "10.3.0", "sankey-beta": "10.3.0", "xychart": "10.5.0", "xychart-beta": "10.5.0",
    "block": "10.8.0", "block-beta": "10.8.0", "packet": "11.0.0", "packet-beta": "11.0.0",
    "architecture-beta": "11.1.0", "kanban": "11.4.0", "radar-beta": "11.6.0", "treemap-beta": "11.8.0",
    "venn-beta": "11.13.0", "ishikawa-beta": "11.13.0", "wardley-beta": "11.14.0", "treeView-beta": "11.14.0",
    "eventmodeling": "11.15.0", "cynefin-beta": "11.16.0", "railroad-beta": "11.16.0", "railroad-ebnf-beta": "11.16.0",
    "railroad-abnf-beta": "11.16.0", "railroad-peg-beta": "11.16.0", "swimlane-beta": "11.16.0",
    "usecase-beta": "12.0.0", "agentflow-beta": "12.0.0",
}
# Syntax features with their first release, from the Mermaid docs and changelog.
FEATURES = [
    (re.compile(r"\A\s*---\n"), "10.5.0", "frontmatter 配置"),
    (re.compile(r"[\w-]@\{\s*(?:shape|label|icon|img)\s*:"), "11.3.0", "@{ shape } 节点写法"),
    (re.compile(r"\s[^\s@|&\[\]\(\)\{\}]+@(?:<?[-=.~])"), "11.5.0", "边 ID（e1@-->）"),
    (re.compile(r"<<--?>>"), "11.0.0", "时序图双向箭头"),
]


def ver(v):
    nums = [int(x) for x in re.findall(r"\d+", v)[:3]]
    return tuple(nums + [0] * (3 - len(nums)))


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    x, y = sorted((lum(a), lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def reach(g, starts):
    seen, stack = set(starts), list(starts)
    while stack:
        for v in g.get(stack.pop(), []):
            if v not in seen:
                seen.add(v)
                stack.append(v)
    return seen


def issue(level, code, msg, file="", line=0, why=""):
    return {"level": level, "code": code, "msg": msg, "file": file, "line": line, "why": why}


# ---------- themes ----------

def load_theme(ref):
    p = Path(ref)
    if not p.suffix:
        p = THEMES / f"{ref}.json"
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


def all_themes():
    return [load_theme(p) for p in sorted(THEMES.glob("*.json"))]


def theme_problems(t):
    v, out = t["config"]["themeVariables"], []
    pairs = [("primaryColor", "primaryTextColor"), ("edgeLabelBackground", "textColor")]
    if "background" in v:
        pairs.append(("background", "textColor"))
    for a, b in pairs:
        if a in v and b in v and contrast(v[a], v[b]) < 4.5:
            out.append(f"{t['name']} 的 {a}/{b} 对比度 {contrast(v[a], v[b]):.2f}，低于 4.5")
    for name, r in t["roles"].items():
        if contrast(r["fill"], r["color"]) < 4.5:
            out.append(f"{t['name']} 的 {name} 角色对比度 {contrast(r['fill'], r['color']):.2f}，低于 4.5")
    return out


def theme_block(t):
    def emit(d, depth):
        out = []
        for k, x in d.items():
            pad = "  " * depth
            if isinstance(x, dict):
                out += [f"{pad}{k}:"] + emit(x, depth + 1)
            elif isinstance(x, str) and k not in ("theme", "look"):
                out.append(f'{pad}{k}: "{x}"')
            else:
                out.append(f"{pad}{k}: {x}")
        return out
    return "\n".join(["---", "config:"] + emit(t["config"], 1) + ["---"]) + "\n"


def classdef_block(t):
    return "".join(f"classDef {n} fill:{r['fill']},stroke:{r['stroke']},color:{r['color']}\n" for n, r in t["roles"].items())


def parse_yaml(text):
    root = {}
    stack = [(-1, root)]
    for raw in text.splitlines():
        if not raw.strip() or raw.strip().startswith("#"):
            continue
        ind = len(raw) - len(raw.lstrip())
        key, _, val = raw.strip().partition(":")
        while stack[-1][0] >= ind:
            stack.pop()
        if val.strip():
            stack[-1][1][key.strip()] = val.strip().strip("\"'")
        else:
            d = {}
            stack[-1][1][key.strip()] = d
            stack.append((ind, d))
    return root


# ---------- parsing ----------

class D:
    def __init__(self, text, name="", offset=0):
        self.name, self.offset = name, offset
        self.kind = self.type = None
        self.fm, self.fm_line, self.type_line = "", 0, 0
        self.verify = defaultdict(list)
        self.accept = {}
        self.nodes, self.classes, self.edges = {}, defaultdict(set), []
        self.subs, self.lane, self.sublabel = {}, {}, {}
        self.classdefs, self.classdef_line, self.issues = {}, {}, []
        self.custom_style = 0
        self.init_line = 0
        self.edge_ids, self.seq_blocks = set(), []
        self.participants, self.used, self.active = {}, set(), defaultdict(int)
        self.tasks, self.task_refs, self.today_off = {}, [], False
        self.entities, self.related = {}, set()
        self.text = text
        self.parse(text)

    def at(self, n):
        return self.offset + n

    def err(self, code, msg, line):
        self.issues.append(issue("error", code, msg, self.name, line))

    def node(self, m, stack, line):
        nid, shape, cls = m.group(1), m.group(2), m.group(3)
        if nid in self.subs:
            return nid
        n = self.nodes.setdefault(nid, {"label": nid, "decision": False, "line": line})
        if shape and shape.startswith("@{"):
            kind = re.search(r'shape:\s*"?([\w-]+)', shape)
            label = re.search(r'label:\s*(?:"([^"]*)"|([^,}]+))', shape)
            if label:
                n["label"] = (label.group(1) if label.group(1) is not None else label.group(2)).strip()
            if kind:
                n["decision"] = kind.group(1) in DECISION_SHAPES
        elif shape:
            n["label"] = re.sub(r'^[\[\(\{>]+"?|"?[\]\)\}]+$', "", shape)
            n["decision"] = shape.startswith("{") and not shape.startswith("{{")
        if cls:
            self.classes[cls].add(nid)
        if stack and "lane" not in n:
            n["lane"] = stack[0]
            self.lane[nid] = stack[0]
        for s in stack:
            self.subs[s].add(nid)
        return nid

    def parse(self, text):
        m = re.match(r"\s*---\n(.*?)\n---\n", text, re.S)
        skip = 0
        if m:
            self.fm, self.fm_line = m.group(1), self.at(1)
            skip = text[:m.end()].count("\n")
        stack = []
        for i, raw in enumerate(text.splitlines()[skip:], start=skip + 1):
            ln = self.at(i)
            line = raw.strip()
            if line.startswith("%%{"):
                self.init_line = self.init_line or ln
                continue
            c = re.match(r"%%\s*saan:\s*(\w+)", line)
            if c:
                self.kind = c.group(1)
                continue
            c = re.match(r"%%\s*verify\s+(\w+):\s*(.+)", line)
            if c:
                self.verify[c.group(1)].append(c.group(2).strip())
                continue
            c = re.match(r"%%\s*accept\s+(\w+):\s*(.+)", line)
            if c:
                self.accept[c.group(1)] = c.group(2).strip()
                continue
            line = re.sub(r"%%.*$", "", line).strip().rstrip(";")
            if not line:
                continue
            if not self.type:
                self.type, self.type_line = line.split()[0], ln
                continue
            if self.type == "sequenceDiagram":
                self.seq_line(line, ln)
            elif self.type == "gantt":
                self.gantt_line(line, ln)
            elif self.type == "erDiagram":
                self.er_line(line, ln)
            elif self.type.startswith("state"):
                self.state_line(line, ln)
            elif self.type in FLOWLIKE:
                self.flow_line(line, stack, ln)

    def seq_line(self, line, ln):
        word = line.split()[0]
        m = re.match(r"(?:create\s+)?(participant|actor)\s+(.+?)(?:\s+as\s+.+)?$", line)
        if m:
            self.participants.setdefault(m.group(2).strip(), ln)
            return
        if SEQ_OPEN.match(word) and SEQ_OPEN.match(word).end() == len(word):
            self.seq_blocks.append((word, ln))
            return
        if word in SEQ_MID:
            if not self.seq_blocks or self.seq_blocks[-1][0] != SEQ_MID[word]:
                self.err("S3", f"时序图的 {word} 不在 {SEQ_MID[word]} 块里", ln)
            return
        if line == "end":
            if self.seq_blocks:
                self.seq_blocks.pop()
            else:
                self.err("S3", "时序图多了一个 end", ln)
            return
        m = re.match(r"(activate|deactivate)\s+(.+)$", line)
        if m:
            self.toggle(m.group(2).strip(), m.group(1) == "activate", ln)
            return
        m = re.match(r"[Nn]ote\s+(?:left of|right of|over)\s+([^:]+):", line)
        if m:
            self.used.update(x.strip() for x in m.group(1).split(","))
            return
        m = SEQ_MSG.match(line)
        if m:
            a, mark, b = m.group(1).strip(), m.group(3), m.group(4).strip()
            self.used.update((a, b))
            if mark == "+":
                self.toggle(b, True, ln)
            elif mark == "-":
                self.toggle(a, False, ln)
            if ";" in m.group(5):
                self.issues.append(issue("warning", "SQ3", f"消息文字里有分号，会被当成换行：{m.group(5).strip()}", self.name, ln))

    def toggle(self, who, on, ln):
        self.used.add(who)
        if on:
            self.active[who] += 1
        elif self.active[who] <= 0:
            self.err("SQ2", f"『{who}』没有激活却被取消激活，渲染会报错", ln)
        else:
            self.active[who] -= 1

    def gantt_line(self, line, ln):
        if line.startswith("todayMarker"):
            self.today_off = "off" in line
            return
        if line.startswith(GANTT_KEYS) or ":" not in line:
            return
        _, _, meta = line.partition(":")
        tokens = [t.strip() for t in meta.split(",") if t.strip()]
        rest = [t for t in tokens if t not in GANTT_TAGS]
        tid = rest[0] if len(rest) >= 3 else None
        if tid:
            self.tasks.setdefault(tid, ln)
        for t in rest:
            m = re.match(r"(after|until)\s+(.+)", t)
            if m:
                for ref in m.group(2).split():
                    self.task_refs.append((tid, ref, ln))

    def er_line(self, line, ln):
        if line == "}":
            return
        m = re.match(r'^("[^"]+"|[\w\-]+)(?:\[[^\]]*\])?\s*\{', line)
        if m:
            self.entities.setdefault(m.group(1).strip('"'), ln)
            return
        m = re.match(r'^("[^"]+"|[\w\-]+)\s+(\S*(?:--|\.\.)\S*)\s+("[^"]+"|[\w\-]+)\s*:', line)
        if m:
            for x in (m.group(1), m.group(3)):
                self.entities.setdefault(x.strip('"'), ln)
                self.related.add(x.strip('"'))

    def state_line(self, line, ln):
        m = re.match(r"(\[\*\]|[^\s:]+)\s*-->\s*(\[\*\]|[^\s:]+)", line)
        if not m:
            return
        a, b = m.groups()
        a = "__start" if a == "[*]" else a
        b = "__end" if b == "[*]" else b
        for x in (a, b):
            self.nodes.setdefault(x, {"label": x, "decision": False, "line": ln})
        self.edges.append((a, b, "-->", ""))

    def flow_line(self, line, stack, ln):
        if line.startswith("subgraph"):
            m = re.match(r"subgraph\s+([^\s\[]+)?\s*(?:\[(.*)\])?", line)
            sid = (m.group(1) if m and m.group(1) else line[8:].strip()).strip('"')
            self.subs.setdefault(sid, set())
            self.sublabel[sid] = (m.group(2) or sid).strip('"') if m else sid
            stack.append(sid)
            return
        if line == "end":
            if stack:
                stack.pop()
            return
        if line.startswith("direction"):
            return
        if line.startswith("classDef"):
            p = line.split(None, 2)
            if len(p) == 3:
                self.classdefs[p[1]] = dict(x.split(":", 1) for x in p[2].split(",") if ":" in x)
                self.classdef_line[p[1]] = ln
            return
        if line.startswith("class "):
            p = line.split()
            for nid in p[1].split(","):
                if nid not in self.edge_ids:
                    self.classes[p[2]].add(nid)
            return
        if line.startswith(("style ", "linkStyle ")):
            self.custom_style = self.custom_style or ln
            return
        m = re.match(r"([^\s@]+)@\{", line)
        if m and m.group(1) in self.edge_ids:
            return
        pos, left = 0, None
        while pos < len(line):
            group = []
            while True:
                m = NODE.match(line, pos)
                if not m:
                    self.err("S1", f"无法解析这一行：{line}", ln)
                    return
                group.append(self.node(m, stack, ln))
                pos = m.end()
                if line[pos:pos + 1] == "&":
                    pos += 1
                    continue
                break
            if left:
                for a in left[0]:
                    for b in group:
                        if left[1] != "~~~":
                            op = left[1].lstrip("<")
                            self.edges.append((a, b, op, left[2]))
                            if left[1].startswith("<"):
                                self.edges.append((b, a, op, left[2]))
            if pos >= len(line):
                break
            m = LINK.match(line, pos)
            if not m:
                self.err("S1", f"无法解析这一行：{line}", ln)
                return
            if m.group(1):
                self.edge_ids.add(m.group(1))
            left = (group, m.group(4), (m.group(5) or m.group(3) or "").strip())
            pos = m.end()

    def line_of(self, nid):
        return self.nodes.get(nid, {}).get("line", self.type_line)

    def endpoints(self, g):
        solid_in = {b for a, b, op, _ in self.edges if not op.startswith("-.")}
        pick = lambda key: self.verify.get(key, [""])[0].replace(",", " ").split()
        starts = pick("start") or \
            sorted(n for n in self.nodes if n not in solid_in and not any(n in m for s, m in self.subs.items() if s in solid_in)) or \
            [next(iter(self.nodes))]
        ends = pick("end") or sorted(n for n in self.nodes if not g.get(n))
        return starts, ends

    def graph(self):
        g, r = defaultdict(list), defaultdict(list)
        def expand(x, out):
            if x not in self.subs:
                return [x]
            mem = self.subs[x]
            inner = [(a, b) for a, b, *_ in self.edges if a in mem and b in mem]
            pick = {a for a, _ in inner} if out else {b for _, b in inner}
            return sorted(mem - pick) or sorted(mem)
        for a, b, *_ in self.edges:
            for u in expand(a, True):
                for v in expand(b, False):
                    g[u].append(v)
                    r[v].append(u)
        return g, r


# ---------- per-diagram checks ----------

def check_theme(d, out, theme):
    E = lambda code, msg, line: out.append(issue("error", code, msg, d.name, line))
    fm = parse_yaml(d.fm).get("config", {}) if d.fm else {}
    if d.init_line:
        out.append(issue("warning", "CF1", "%%{init}%% 已弃用，改用 frontmatter 配置", d.name, d.init_line))
    if not isinstance(fm, dict) or not fm:
        if d.type in THEMED:
            E("CL3", "缺少 Saan 主题 frontmatter", d.at(1))
        return None
    tv = fm.get("themeVariables", {}) if isinstance(fm.get("themeVariables"), dict) else {}
    if theme:
        t = theme
    else:
        pc = str(tv.get("primaryColor", "")).upper()
        t = next((x for x in all_themes() if x["config"]["themeVariables"]["primaryColor"].upper() == pc), None)
    if not t:
        E("CL3", f"frontmatter 不是 Saan 主题。可用主题：{'、'.join(x['name'] for x in all_themes())}，用 --theme-block 生成", d.fm_line)
        return None
    want = t["config"]
    bad = [k for k in ("theme", "look") if str(fm.get(k, "")) != want[k]]
    bad += [k for k, v in want["themeVariables"].items() if str(tv.get(k, "")).upper() != v.upper()]
    extra = [k for k in tv if k not in want["themeVariables"]]
    if bad:
        E("CL3", f"frontmatter 和主题 {t['name']} 不一致：{'、'.join(bad[:4])}{' 等' if len(bad) > 4 else ''}。用 --theme-block {t['name']} 重新生成", d.fm_line)
    if extra:
        E("CL3", f"不要另加 themeVariables：{'、'.join(extra[:4])}", d.fm_line)
    for p in theme_problems(t):
        E("CT1", p, d.fm_line)
    return t


def check_target(d, out, target):
    if not target or not d.type:
        return
    need = [(SINCE[d.type], f"图类型 {d.type}")] if d.type in SINCE else []
    need += [(since, what) for rx, since, what in FEATURES if rx.search(d.text)]
    for since, what in need:
        if ver(since) > ver(target):
            out.append(issue("error", "V2", f"目标 Mermaid {target} 不支持{what}（{since} 起）", d.name, d.type_line))


def check(d, theme=None, target=None):
    out = list(d.issues)
    E = lambda code, msg, line: out.append(issue("error", code, msg, d.name, line))
    W = lambda code, msg, line: out.append(issue("warning", code, msg, d.name, line))
    finds = []
    F = lambda code, msg, line: finds.append(issue("finding", code, msg, d.name, line))
    L = lambda n: d.nodes.get(n, {}).get("label", n)
    if not d.type:
        E("S0", "没有找到图类型行", d.at(1))
        return out
    if d.type not in SINCE:
        E("S0", f"『{d.type}』不是已知的 Mermaid 图类型。Markdown 文件请直接传 .md，脚本会提取 mermaid 代码块", d.type_line)
    t = check_theme(d, out, theme)
    check_target(d, out, target)
    roles = (t or load_theme("saan-light"))["roles"]
    for b, ln in d.seq_blocks:
        E("S3", f"时序图的 {b} 块没有 end", ln)
    if d.type == "sequenceDiagram":
        for p, ln in d.participants.items():
            if p not in d.used:
                W("SQ1", f"参与者『{p}』声明了但没有出现在任何消息里", ln)
        for who, n in d.active.items():
            if n > 0:
                W("SQ2", f"『{who}』激活后没有取消激活", d.participants.get(who, d.type_line))
    if d.type == "gantt":
        for tid, ref, ln in d.task_refs:
            if ref not in d.tasks:
                E("GT1", f"after/until 引用了不存在的任务 ID『{ref}』", ln)
        g = defaultdict(list)
        for tid, ref, _ in d.task_refs:
            if tid and ref in d.tasks:
                g[tid].append(ref)
        loop = sorted(x for x in d.tasks if x in reach(g, g.get(x, [])))
        if loop:
            E("GT2", f"任务依赖成环：{'、'.join(loop)}", d.tasks[loop[0]])
        if not d.today_off:
            W("GT3", "甘特图要加 todayMarker off，否则今天的红线会随查看日期变化", d.type_line)
    if d.type == "erDiagram" and len(d.entities) > 1:
        for e, ln in d.entities.items():
            if e not in d.related:
                W("ER1", f"实体『{e}』没有任何关系", ln)
    if d.type in FLOWLIKE:
        if d.kind not in KINDS:
            E("K1", "第一行正文前要声明类型：%% saan: arch|flow|overview|approval|audit", d.type_line)
        for name, props in d.classdefs.items():
            ln = d.classdef_line[name]
            if name not in roles:
                E("CL2", f"classDef {name} 不是角色配色（{'、'.join(roles)}）", ln)
                continue
            if any(props.get(k, "").strip().upper() != v.upper() for k, v in roles[name].items()):
                E("CL2", f"classDef {name} 的颜色和主题不一致", ln)
        for name, ids in d.classes.items():
            if name not in d.classdefs:
                E("CL2", f"用了 {name}，但没有定义 classDef", d.line_of(sorted(ids)[0]))
        if d.custom_style:
            E("CL2", "不要用 style 或 linkStyle 单独改色，改用角色配色", d.custom_style)
        if len(d.classes.get("core", ())) > 3:
            E("CL1", f"核心节点 {len(d.classes['core'])} 个，最多 3 个", d.classdef_line.get("core", d.type_line))
        if len(d.nodes) > 15:
            W("N1", f"{len(d.nodes)} 个节点，超过 15 个，考虑拆图", d.type_line)
        for nid, n in d.nodes.items():
            if len(re.sub(r"<br\s*/?>", "", n["label"])) > 18:
                W("L1", f"节点文字太长：{n['label']}", n["line"])
            if re.search(r"[^\x00-\x7f]", nid):
                W("S2", f"节点 ID 建议用英文：{nid}", n["line"])
            if nid == "end":
                E("S2", "不要用 end 作节点 ID", n["line"])
        dotted = [e for e in d.edges if e[2].startswith("-.")]
        if len(dotted) > 2 and len(dotted) / max(len(d.edges), 1) > 0.3:
            W("DS1", f"虚线 {len(dotted)}/{len(d.edges)} 条，太多。虚线只留给退回或可选路径", d.type_line)

    logic = d.kind in ("flow", "overview", "approval", "audit") or d.type.startswith("state")
    if d.kind == "arch":
        for nid, n in d.nodes.items():
            if n["decision"]:
                F("AR1", f"架构图里有判断节点『{n['label']}』：架构讲有什么，判断属于流程图", n["line"])
    no_return = []
    if logic and d.nodes:
        g, r = d.graph()
        ids = set(d.nodes)
        starts, ends = d.endpoints(g)
        fwd = reach(g, starts)
        for n in sorted(ids - fwd):
            F("P2", f"『{L(n)}』从起点（{'、'.join(map(L, starts)) or '无'}）走不到", d.line_of(n))
        back = reach(r, ends)
        for n in sorted(fwd - back):
            F("P3", f"死路：『{L(n)}』之后走不到任何终点", d.line_of(n))
        if not ends:
            F("P3", "流程没有终点，所有路径都在循环", d.type_line)
        if d.kind in ("approval", "audit"):
            reviews = [n for n, a in d.nodes.items() if a["decision"]]
            if not reviews:
                F("AP1", "审批或审计流程没有判断节点", d.type_line)
            for n in reviews:
                labels = [e[3] for e in d.edges if e[0] == n]
                ahead = reach(g, g.get(n, []))
                if n not in ahead and not any(REJECT.search(x) for x in labels) and REVIEW.search(d.nodes[n]["label"]):
                    no_return.append(n)
            if no_return:
                F("RT1", f"{len(no_return)} 个审批判断没有退回分支，资料或流程要写明未通过怎么走：{'、'.join(map(L, no_return))}", d.line_of(no_return[0]))
        single = [n for n, a in d.nodes.items() if a["decision"] and n not in no_return and len(set(g.get(n, []))) < 2]
        if single:
            F("P4", f"{len(single)} 个判断只有一个出口，要写明另一个分支去哪：{'、'.join(map(L, single))}", d.line_of(single[0]))
        if d.kind == "overview":
            cyc = sorted(n for n in ids if n in reach(g, g.get(n, [])))
            if cyc:
                F("OV1", f"总览只画正向主线，这里有回路：{'、'.join(map(L, cyc[:3]))}", d.line_of(cyc[0]))
    return out + accept(finds, d.accept)


def accept(finds, acc):
    return [dict(f, level="accepted", why=acc[f["code"]]) if f["code"] in acc else f for f in finds]


# ---------- control list ----------

def norm(x):
    return re.sub(r'<br\s*/?>|[\s"]', "", x)


def parse_controls(text):
    c = {"source": "", "controls": [], "must_pass": [], "separate": [], "none": "", "alias": defaultdict(set),
         "line": {}, "bad": []}
    for i, raw in enumerate(text.splitlines(), start=1):
        m = re.match(r"\s*(source|control|must_pass|separate|none|alias):\s*(.+)", raw)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if key == "control":
            c["controls"].append(val)
            c["line"].setdefault(val, i)
        elif key in ("must_pass", "separate"):
            p = re.split(r"\s+through\s+", val) if key == "must_pass" else [x.strip() for x in val.split("|")]
            if len(p) == 2:
                c[key].append(p)
                for x in p:
                    c["line"].setdefault(x, i)
            else:
                c["bad"].append((val, i))
        elif key == "alias":
            name, eq, rest = val.partition("=")
            if not eq or not rest.strip():
                c["bad"].append((val, i))
            else:
                c["alias"][name.strip()].update(x.strip() for x in re.split(r"[,，]", rest) if x.strip())
        else:
            c[key] = val
    return c


def find(d, name, aliases=()):
    want = {norm(name)} | {norm(a) for a in aliases}
    return [n for n, a in d.nodes.items() if norm(a["label"]) in want]


def near(d, name):
    q = norm(name)
    return [a["label"] for a in d.nodes.values() if q and (q in norm(a["label"]) or norm(a["label"]) in q)]


# ---------- review ----------

def sources(items):
    return [x if isinstance(x, tuple) else ("", x, 0) for x in items]


def review_issues(items, controls=None, controls_name="", theme=None, target=None):
    docs = [D(text, name, off) for name, text, off in sources(items)]
    out = []
    for d in docs:
        out += check(d, theme, target)
    C = lambda level, code, msg, line=0: out.append(issue(level, code, msg, controls_name, line))
    needs = any(d.kind in ("approval", "audit") for d in docs)
    if controls is None:
        if needs:
            out.append(issue("error", "CP2", "审批或审计流程要先写控制点清单，并用 --controls 传入"))
        return out
    c = parse_controls(controls)
    if c["source"] not in ("user", "document"):
        C("error", "CP2", "清单第一行要写 source: user 或 source: document", 1)
    for val, ln in c["bad"]:
        C("error", "V1", f"清单写法有误：{val}", ln)
    if needs and not (c["controls"] or c["must_pass"] or c["separate"] or c["none"]):
        C("error", "CP2", "清单是空的。确实没有控制点时，写 none: 原因", 1)
    acc = {}
    for d in docs:
        acc.update(d.accept)
    al = lambda n: c["alias"].get(n, ())
    names = c["controls"] + [x for p in c["must_pass"] + c["separate"] for x in p]
    for name in dict.fromkeys(names):
        if not any(find(d, name, al(name)) for d in docs):
            close = sorted({x for d in docs for x in near(d, name)})
            hint = f"图上有相近的『{'』『'.join(close[:3])}』，如果是同一步，在清单里写 alias: {name} = {close[0]}" if close else "补上节点，或告诉用户它为什么不用画"
            C("error", "CP1", f"控制点清单里的『{name}』不在图上。{hint}", c["line"].get(name, 0))
    found = []
    for target_name, ctl in c["must_pass"]:
        ft = lambda d: find(d, target_name, al(target_name))
        fc = lambda d: find(d, ctl, al(ctl))
        if any(ft(d) for d in docs) and any(fc(d) for d in docs) and not any(ft(d) and fc(d) for d in docs):
            C("warning", "CP3", f"『{target_name}』和『{ctl}』分在两张图，无法判断能否绕过", c["line"].get(target_name, 0))
        for d in docs:
            ts, cs = ft(d), fc(d)
            if not ts or not cs:
                continue
            g, _ = d.graph()
            starts, _ = d.endpoints(g)
            seen = {s for s in starts if s not in cs}
            stack = list(seen)
            while stack:
                for v in g.get(stack.pop(), []):
                    if v not in cs and v not in seen:
                        seen.add(v)
                        stack.append(v)
            hit = [t for t in ts if t in seen]
            if hit:
                found.append(issue("finding", "P1", f"可以绕过『{ctl}』到达『{target_name}』", d.name, d.line_of(hit[0])))
    for x, y in c["separate"]:
        for d in docs:
            xs, ys = find(d, x, al(x)), find(d, y, al(y))
            if not xs or not ys:
                continue
            la, lb = d.lane.get(xs[0]), d.lane.get(ys[0])
            if d.type != "swimlane-beta" or not la or not lb:
                found.append(issue("finding", "P5", f"『{x}』与『{y}』的执行角色待确认：只有 swimlane-beta 的泳道才算角色", d.name, d.line_of(xs[0])))
            elif la == lb:
                found.append(issue("finding", "P5", f"『{x}』与『{y}』都由『{d.sublabel.get(la, la)}』执行，违反岗位分离", d.name, d.line_of(xs[0])))
    return out + accept(found, acc)


def review(texts, controls=None, **kw):
    """Compatibility wrapper: (errors, findings, warnings, accepted) as plain strings and tuples."""
    out = review_issues(texts, controls, **kw)
    e = [f"[{x['code']}] {x['msg']}" for x in out if x["level"] == "error"]
    f = [(x["code"], x["msg"]) for x in out if x["level"] == "finding"]
    w = [f"[{x['code']}] {x['msg']}" for x in out if x["level"] == "warning"]
    a = [(x["code"], x["why"], x["msg"]) for x in out if x["level"] == "accepted"]
    return e, f, w, a


# ---------- files and SVG ----------

def blocks(path, body):
    if path.endswith((".md", ".markdown")):
        return [(path, m.group(2), body[:m.start(2)].count("\n")) for m in FENCE.finditer(body)]
    return [(path, body, 0)]


def svg_width(text):
    m = re.search(r'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) [\d.]+"', text)
    return float(m.group(1)) if m else 0


def _tag(el):
    return el.tag.split("}")[-1]


def _translate(el):
    m = re.search(r"translate\(\s*([-\d.e]+)[\s,]*([-\d.e]+)?\s*\)", el.get("transform", ""))
    return (float(m.group(1)), float(m.group(2) or 0)) if m else (0.0, 0.0)


def _box(el, dx, dy):
    f = lambda k: float(el.get(k, 0) or 0)
    tag = _tag(el)
    if tag in ("rect", "foreignObject") and f("width") and f("height"):
        return (dx + f("x"), dy + f("y"), dx + f("x") + f("width"), dy + f("y") + f("height"))
    if tag == "circle":
        return (dx + f("cx") - f("r"), dy + f("cy") - f("r"), dx + f("cx") + f("r"), dy + f("cy") + f("r"))
    if tag == "ellipse":
        return (dx + f("cx") - f("rx"), dy + f("cy") - f("ry"), dx + f("cx") + f("rx"), dy + f("cy") + f("ry"))
    if tag == "polygon":
        pts = [float(x) for x in re.findall(r"[-\d.e]+", el.get("points", ""))]
        if len(pts) >= 4:
            return (dx + min(pts[0::2]), dy + min(pts[1::2]), dx + max(pts[0::2]), dy + max(pts[1::2]))
    return None


def svg_boxes(body):
    """Return (nodes, edge labels) as (name, (x0, y0, x1, y1)) in SVG coordinates."""
    nodes, labels = [], []

    def collect(el, dx, dy, boxes, label):
        bx = _box(el, dx, dy)
        if bx and bx[2] - bx[0] > 1 and bx[3] - bx[1] > 1:
            boxes.append(bx)
        if _tag(el) == "foreignObject" and not label:
            return
        for ch in el:
            tx, ty = _translate(ch)
            collect(ch, dx + tx, dy + ty, boxes, label)

    def walk(el, dx, dy):
        cls = el.get("class", "").split()
        if _tag(el) == "g" and ("node" in cls or "edgeLabel" in cls):
            boxes = []
            collect(el, dx, dy, boxes, "edgeLabel" in cls)
            if boxes:
                bx = (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))
                name = re.sub(r"^[a-zA-Z]+-(.+)-\d+$", r"\1", el.get("id", "")) or "?"
                (nodes if "node" in cls else labels).append((name, bx))
            return
        for ch in el:
            tx, ty = _translate(ch)
            walk(ch, dx + tx, dy + ty)

    root = ET.fromstring(body)
    walk(root, *_translate(root))
    return nodes, labels


def overlap(a, b, pad=2):
    return min(a[2], b[2]) - max(a[0], b[0]) > pad and min(a[3], b[3]) - max(a[1], b[1]) > pad


def svg_issues(path, body):
    if 'aria-roledescription="error"' in body:
        return [issue("error", "R1", "这是 Mermaid 的错误占位图，渲染失败", path)]
    out = []
    if svg_width(body) > 1200:
        out.append(issue("warning", "W1", f"宽 {svg_width(body):.0f}，放进文档文字会变小。改成纵向或拆图", path))
    try:
        nodes, labels = svg_boxes(body)
    except ET.ParseError as ex:
        return out + [issue("warning", "G0", f"SVG 解析失败，跳过重叠检查：{ex}", path)]
    for i, (a, ba) in enumerate(nodes):
        for b, bb in nodes[i + 1:]:
            if overlap(ba, bb):
                out.append(issue("error", "G1", f"节点『{a}』和『{b}』在图上重叠", path))
    for _, bl in labels:
        for n, bn in nodes:
            if overlap(bl, bn, pad=4):
                out.append(issue("warning", "G2", f"连线文字压在节点『{n}』上", path))
                break
    return out


# ---------- output ----------

LEVEL = {"error": "必须修改", "finding": "业务发现", "warning": "建议", "accepted": "已确认"}


def where(x):
    if x["file"] and x["line"]:
        return f"{x['file']}:{x['line']} "
    return f"{x['file']} " if x["file"] else ""


def render(out, src):
    lines = []
    if src is not None:
        lines.append({"user": "控制点来源：用户提供", "document": "控制点来源：从资料提取，不是独立依据"}.get(src, "控制点来源：未写明"))
    for lv in LEVEL:
        for x in out:
            if x["level"] == lv:
                why = f"（{x['why']}）" if x["why"] else ""
                lines.append(f"{LEVEL[lv]} {where(x)}[{x['code']}] {x['msg']}{why}")
    if not out:
        lines.append("通过")
    return "\n".join(lines)


# ---------- self test ----------

FM = theme_block(load_theme("saan-light"))
CORE = "classDef core fill:#E2EBFF,stroke:#2B5FD8,color:#1F2329\n"
CTL = "source: user\ncontrol: 审核单据\nmust_pass: 执行付款 through 审核单据\nseparate: 提交申请 | 审核单据\n"
GOOD = FM + """%% saan: approval
swimlane-beta LR
  subgraph biz[业务部门]
    apply[提交申请]
    fix[修改申请]
  end
  subgraph fin[财务部门]
    audit{审核单据}
    pay[执行付款]
  end
  apply --> audit
  audit -->|通过| pay
  audit -->|退回| fix
  fix -.-> apply
"""
FLOW = FM + "%% saan: flow\nflowchart LR\n"
SEQ = FM + "sequenceDiagram\n  participant A\n  participant B\n"
GANTT = FM + "gantt\n  dateFormat YYYY-MM-DD\n  todayMarker off\n  section 阶段\n"
TESTS = [
    ("K1", GOOD.replace("%% saan: approval\n", ""), CTL),
    ("CL3", GOOD.replace(FM, ""), CTL),
    ("CL3", GOOD.replace('lineColor: "#4E5563"', 'lineColor: "#FF0000"'), CTL),
    ("CL3", GOOD.replace("  themeVariables:\n", '  themeVariables:\n    nodeBorder: "#000000"\n'), CTL),
    ("CL3", GOOD.replace('primaryColor: "#E3E5EA"', 'primaryColor: "#123456"'), CTL),
    ("CF1", "%%{init: {'theme': 'base'}}%%\n" + GOOD, CTL),
    ("CL2", GOOD + "  classDef pink fill:#FFC0CB,stroke:#000000,color:#000000\n", CTL),
    ("CL2", GOOD + "  classDef core fill:#FF0000,stroke:#2B5FD8,color:#1F2329\n", CTL),
    ("CL2", GOOD + "  style pay fill:#FF0000\n", CTL),
    ("CL1", GOOD + "  " + CORE + "  class apply,fix,audit,pay core\n", CTL),
    ("S1", GOOD + "  a[未闭合 -->\n", CTL),
    ("S2", GOOD + "  pay --> end\n", CTL),
    ("P1", GOOD + "  apply --> pay\n", CTL),
    ("P2", GOOD + "  orphan[孤立步骤] --> orphan2[另一步]\n  orphan2 --> orphan\n", CTL),
    ("P3", GOOD + "  pay --> loop1[对账]\n  loop1 --> loop2[复查]\n  loop2 --> loop1\n", CTL),
    ("P4", FLOW + "  a[甲] --> b{判断}\n  b --> c[丙]\n", None),
    ("P5", GOOD.replace("    audit{审核单据}\n", "").replace("    fix[修改申请]\n", "    fix[修改申请]\n    audit{审核单据}\n"), CTL),
    ("P5", GOOD.replace("swimlane-beta LR", "flowchart LR"), CTL),
    ("RT1", FM + "%% saan: approval\nflowchart LR\n  a[申请] --> b{审核}\n  b --> c[付款]\n  b --> d[归档]\n", "source: document\nnone: 示例\n"),
    ("AP1", FM + "%% saan: approval\nflowchart LR\n  a[申请] --> c[付款]\n", "source: document\nnone: 示例\n"),
    ("AR1", FM + "%% saan: arch\nflowchart LR\n  a[合同] --> b{是否结算}\n", None),
    ("OV1", FM + "%% saan: overview\nflowchart LR\n  a[签约] --> b[结算]\n  b --> c[核算]\n  b -.-> a\n", None),
    ("P3", FM + "stateDiagram-v2\n  [*] --> a\n  a --> b\n  b --> a\n", None),
    ("N1", FLOW + "".join(f"  n{i}[步骤] --> n{i + 1}[步骤]\n" for i in range(16)), None),
    ("L1", FLOW + "  a[这是一个非常非常非常非常非常非常长的节点文字] --> b[结束]\n", None),
    ("DS1", FLOW + "  a[甲] -.-> b[乙]\n  b -.-> c[丙]\n  c -.-> d[丁]\n", None),
    ("CP1", GOOD, CTL + "control: 财务复核\n"),
    ("CP1", GOOD, CTL.replace("control: 审核单据", "control: 审核")),
    ("CP2", GOOD, None),
    ("CP2", GOOD, "control: 审核单据\n"),
    ("CP2", GOOD, "source: user\n"),
    ("V1", GOOD, CTL + "must_pass: 缺少写法\n"),
    ("V1", GOOD, CTL + "alias: 只有名字\n"),
    ("S0", "# 标题\n\n```mermaid\nflowchart LR\n  a --> b\n```\n", None),
    ("S3", SEQ + "  A->>B: 请求\n  alt 成功\n  B->>A: 返回\n", None),
    ("S3", SEQ + "  A->>B: 请求\n  else 失败\n", None),
    ("RT1", FM + "%% saan: approval\nflowchart LR\n  a[申请] --> b@{ shape: diamond, label: \"审核\" }\n  b --> c[付款]\n  b --> d[归档]\n", "source: document\nnone: 示例\n"),
    ("P1", GOOD + "  apply e9@--> pay\n  e9@{ animate: true }\n", CTL),
    ("SQ1", SEQ + "  participant C\n  A->>B: 请求\n", None),
    ("SQ2", SEQ + "  A->>B: 请求\n  deactivate B\n", None),
    ("SQ2", SEQ + "  A->>+B: 请求\n", None),
    ("SQ3", SEQ + "  A->>B: 先登录; 再下单\n", None),
    ("GT1", GANTT + "  设计 :a1, 2026-01-01, 3d\n  开发 :a2, after a9, 5d\n", None),
    ("GT2", GANTT + "  设计 :a1, after a2, 3d\n  开发 :a2, after a1, 5d\n", None),
    ("GT3", GANTT.replace("  todayMarker off\n", "") + "  设计 :a1, 2026-01-01, 3d\n", None),
    ("ER1", FM + "erDiagram\n  CUSTOMER ||--o{ ORDER : places\n  INVOICE {\n    string id\n  }\n", None),
]
TARGET_TESTS = [
    (GOOD, "11.13.0", True), (GOOD, "11.16.0", False),
    (FLOW + "  a[甲] --> b@{ shape: diamond, label: \"判断\" }\n  b --> c[丙]\n  b --> d[丁]\n", "11.2.0", True),
    (FLOW + "  a[甲] e1@--> b[乙]\n", "11.4.0", True),
    (FLOW + "  a[甲] --> b[乙]\n", "10.4.0", True),
    (FLOW + "  a[甲] --> b[乙]\n", "10.5.0", False),
]
SVG_OK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 200"><g class="root"><g class="nodes">
<g class="node default" id="flowchart-a-0" transform="translate(60, 50)"><rect x="-40" y="-20" width="80" height="40"/></g>
<g class="node default" id="flowchart-b-1" transform="translate(200, 50)"><polygon points="0,-30 30,0 0,30 -30,0"/></g>
</g><g class="edgeLabels"><g class="edgeLabel" transform="translate(130, 120)"><g class="label" transform="translate(-15, -10)"><foreignObject width="30" height="20"><div xmlns="http://www.w3.org/1999/xhtml">是</div></foreignObject></g></g></g></g></svg>"""
SVG_BAD = SVG_OK.replace("translate(200, 50)", "translate(110, 50)").replace("translate(130, 120)", "translate(60, 50)")


def selftest():
    bad = []
    e, f, w, _ = review([GOOD], CTL)
    if e or f or w:
        bad.append(f"正确样例不应报错 {e} {f} {w}")
    for code, src, ctl in TESTS:
        got = {x["code"] for x in review_issues([src], ctl) if x["level"] != "accepted"}
        if code not in got:
            bad.append(f"没有触发 {code}，实际 {sorted(got)}")
    for src, tgt, want in TARGET_TESTS:
        if any(x["code"] == "V2" for x in review_issues([src], target=tgt)) != want:
            bad.append(f"--target {tgt} 应{'报' if want else '不报'} V2：{src.splitlines()[-1]}")
    a = GOOD + "  apply --> pay\n%% accept P1: 小额付款免审\n"
    if review([a], CTL)[1] or not review([a], CTL)[3]:
        bad.append("accept 没有生效")
    one = FM + "%% saan: approval\nflowchart LR\n  a[申请] --> b{审核}\n  b --> c[付款]\n"
    if [x for x, _ in review([one], "source: user\ncontrol: 审核\n")[1]] != ["RT1"]:
        bad.append("同一节点不应同时报 P4 和 RT1")
    if review([FLOW + "  a[第一行第一行第一行<br/>第二行第二行] --> b[结束]\n"])[2]:
        bad.append("<br/> 不应计入文字长度")
    shaped = GOOD.replace("audit{审核单据}", 'audit@{ shape: decision, label: "审核单据" }').replace("  fix -.-> apply\n", "  fix e1@-.-> apply\n  e1@{ animate: true }\n")
    if review([shaped], CTL) != review([GOOD], CTL) or "e1" in D(shaped).nodes:
        bad.append(f"@{{ }} 节点或边 ID 解析有误 {review([shaped], CTL)}")
    md = "# 文档\n\n```mermaid\n" + GOOD + "```\n\n正文\n\n~~~mermaid\n" + FLOW + "  a[甲] --> b[乙]\n~~~\n"
    if len(blocks("doc.md", md)) != 2 or review(blocks("doc.md", md), CTL)[:3] != ([], [], []):
        bad.append("Markdown 代码块提取有误")
    broken = md.replace("  fix -.-> apply\n", "  fix -.-> apply\n  pay --> end\n")
    want = broken.splitlines().index("  pay --> end") + 1
    if not any(x["code"] == "S2" and x["file"] == "doc.md" and x["line"] == want for x in review_issues(blocks("doc.md", broken), CTL)):
        bad.append(f"Markdown 里的行号不对，应为 {want}")
    if ("b", "a", "-->", "") not in D(FLOW + "  a[甲] <--> b[乙]\n").edges:
        bad.append("双向箭头没有生成反向边")
    seq = SEQ + "  A->>B: 请求\n  alt 成功\n    B->>A: 返回\n  else 失败\n    loop 重试\n      A->>+B: 请求\n      B-->>-A: 结果\n    end\n  end\n  rect rgb(240,240,240)\n    Note over A,B: 结束\n  end\n"
    if review([seq])[0] or review([seq])[2]:
        bad.append(f"正确的时序块不应报错 {review([seq])}")
    alias = CTL.replace("control: 审核单据", "control: 单据审核\nalias: 单据审核 = 审核单据")
    if review([GOOD], alias)[:3] != ([], [], []):
        bad.append(f"alias 没有生效 {review([GOOD], alias)}")
    dark = GOOD.replace(FM, theme_block(load_theme("saan-dark")))
    if review([dark], CTL)[:3] != ([], [], []):
        bad.append(f"深色主题样例不应报错 {review([dark], CTL)}")
    if not review([dark + "  " + CORE + "  class pay core\n"], CTL)[0]:
        bad.append("深色主题里用浅色角色配色应报 CL2")
    for t in all_themes():
        bad += [f"主题对比度不足：{p}" for p in theme_problems(t)]
    if svg_issues("ok.svg", SVG_OK):
        bad.append(f"正常 SVG 不应报错 {svg_issues('ok.svg', SVG_OK)}")
    got = sorted({x["code"] for x in svg_issues("bad.svg", SVG_BAD)})
    if got != ["G1", "G2"]:
        bad.append(f"重叠 SVG 应报 G1 和 G2，实际 {got}")
    if svg_width('<svg viewBox="4 4 1800.5 200">') != 1800.5:
        bad.append("SVG 宽度读取有误")
    for x in bad:
        print(x)
    print(f"SELFTEST {'PASS' if not bad else 'FAIL'}: {len(TESTS) + len(TARGET_TESTS)} 条改坏样例，{len(bad)} 个问题")
    return 1 if bad else 0


# ---------- CLI ----------

USAGE = """用法：
  check_mermaid.py [选项] 图.mmd|文档.md [图.svg] [更多文件]
  check_mermaid.py --theme-block [saan-light|saan-dark|主题.json]
  check_mermaid.py --selftest
选项：
  --controls 清单.txt   控制点清单
  --target 11.12        目标宿主的 Mermaid 版本，检查图类型和写法是否支持
  --theme 名称或路径     要求使用指定主题；默认按 frontmatter 自动识别
  --json                以 JSON 输出"""


def take(args, flag):
    if flag not in args:
        return None, args
    i = args.index(flag)
    if i + 1 >= len(args):
        raise SystemExit(f"{flag} 后面要写值\n\n{USAGE}")
    return args[i + 1], args[:i] + args[i + 2:]


def main(argv=None):
    args = list(sys.argv[1:] if argv is None else argv)
    if args == ["--selftest"]:
        return selftest()
    if args and args[0] == "--theme-block":
        t = load_theme(args[1] if len(args) > 1 else "saan-light")
        print(theme_block(t) + "\n%% 角色配色，只定义图里用到的：\n" + classdef_block(t), end="")
        return 0
    as_json = "--json" in args
    args = [a for a in args if a != "--json"]
    cpath, args = take(args, "--controls")
    target, args = take(args, "--target")
    tname, args = take(args, "--theme")
    if not args or any(a.startswith("--") for a in args):
        print(USAGE)
        return 2
    theme = load_theme(tname) if tname else None
    controls = None
    if cpath:
        with open(cpath, encoding="utf-8") as fh:
            controls = fh.read()
    items, extra = [], []
    for p in args:
        with open(p, encoding="utf-8") as fh:
            body = fh.read()
        if p.endswith(".svg"):
            extra += svg_issues(p, body)
            continue
        found = blocks(p, body)
        if not found:
            extra.append(issue("error", "R2", "里面没有 mermaid 代码块", p))
        items += found
    out = review_issues(items, controls, cpath or "", theme, target) + extra
    src = parse_controls(controls)["source"] if controls is not None else None
    failed = any(x["level"] in ("error", "finding") for x in out)
    if as_json:
        print(json.dumps({"ok": not failed, "controls_source": src, "issues": out}, ensure_ascii=False, indent=2))
    else:
        print(render(out, src))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
