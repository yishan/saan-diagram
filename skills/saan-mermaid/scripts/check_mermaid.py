#!/usr/bin/env python3
"""Review Mermaid source against a control list, business logic, and Saan style rules. Python 3 stdlib only."""
import re, sys
from collections import defaultdict

ROLES = {
    "core": ("#E2EBFF", "#2B5FD8", "#1F2329"),
    "hub": ("#D0D3D9", "#D0D3D9", "#1F2329"),
    "system": ("#2B5FD8", "#2B5FD8", "#FFFFFF"),
    "external": ("#8FB0FF", "#8FB0FF", "#1F2329"),
    "ai": ("#FDEBD8", "#F5C99B", "#1F2329"),
}
KINDS = {"arch", "flow", "overview", "approval", "audit"}
SHAPE = r"\(\[.*?\]\)|\[\(.*?\)\]|\[\[.*?\]\]|\(\(.*?\)\)|\{\{.*?\}\}|\[.*?\]|\(.*?\)|\{.*?\}|>.*?\]"
NODE = re.compile(rf"\s*([^\s\[\]\(\)\{{\}}<>|&:;\"-]+(?:-[^\s\[\]\(\)\{{\}}<>|&:;\"-]+)*)\s*({SHAPE})?(?::::(\w+))?\s*")
LINK = re.compile(r"\s*(?:(--|-\.|==)\s+([^|]*?)\s+)?(<?-{2,}>|-\.+->|-\.+-|={2,}>|-{3,}|--[xo]|~~~)\s*(?:\|([^|]*)\|)?\s*")
REVIEW = re.compile(r"审|批|核|校验|复验|验收")
REJECT = re.compile(r"退回|驳回|拒绝|不通过|不合格|否|修改")


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


class D:
    def __init__(self, text):
        self.kind = self.type = None
        self.fm = ""
        self.verify = defaultdict(list)
        self.accept = {}
        self.nodes, self.classes, self.edges = {}, defaultdict(set), []
        self.subs, self.lane, self.sublabel = {}, {}, {}
        self.classdefs, self.errors = {}, []
        self.custom_style = False
        self.parse(text)

    def node(self, m, stack):
        nid, shape, cls = m.group(1), m.group(2), m.group(3)
        if nid in self.subs:
            return nid
        n = self.nodes.setdefault(nid, {"label": nid, "decision": False})
        if shape:
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
        if m:
            self.fm, text = m.group(1), text[m.end():]
        stack = []
        for raw in text.splitlines():
            line = raw.strip()
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
                self.type = line.split()[0]
                continue
            if self.type.startswith("state"):
                self.state_line(line)
            elif self.type in ("flowchart", "graph", "swimlane-beta"):
                self.flow_line(line, stack)

    def state_line(self, line):
        m = re.match(r"(\[\*\]|[^\s:]+)\s*-->\s*(\[\*\]|[^\s:]+)", line)
        if not m:
            return
        a, b = m.groups()
        a = "__start" if a == "[*]" else a
        b = "__end" if b == "[*]" else b
        for x in (a, b):
            self.nodes.setdefault(x, {"label": x, "decision": False})
        self.edges.append((a, b, "-->", ""))

    def flow_line(self, line, stack):
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
            return
        if line.startswith("class "):
            p = line.split()
            for nid in p[1].split(","):
                self.classes[p[2]].add(nid)
            return
        if line.startswith(("style ", "linkStyle ")):
            self.custom_style = True
            return
        pos, left = 0, None
        while pos < len(line):
            group = []
            while True:
                m = NODE.match(line, pos)
                if not m:
                    self.errors.append(f"[S1] 无法解析这一行：{line}")
                    return
                group.append(self.node(m, stack))
                pos = m.end()
                if line[pos:pos + 1] == "&":
                    pos += 1
                    continue
                break
            if left:
                for a in left[0]:
                    for b in group:
                        if left[1] != "~~~":
                            self.edges.append((a, b, left[1], left[2]))
            if pos >= len(line):
                break
            m = LINK.match(line, pos)
            if not m:
                self.errors.append(f"[S1] 无法解析这一行：{line}")
                return
            left = (group, m.group(3), (m.group(4) or m.group(2) or "").strip())
            pos = m.end()

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


def check(text):
    d = D(text)
    errs, finds, warns = list(d.errors), [], []
    L = lambda n: d.nodes.get(n, {}).get("label", n)
    flowlike = d.type in ("flowchart", "graph", "swimlane-beta")
    if "theme: base" not in d.fm and d.type in ("flowchart", "graph", "swimlane-beta", "sequenceDiagram", "stateDiagram-v2", "erDiagram"):
        errs.append("[CL3] 缺少 Saan 主题 frontmatter")
    m1 = re.search(r'primaryColor:\s*"(#\w{6})"', d.fm)
    m2 = re.search(r'primaryTextColor:\s*"(#\w{6})"', d.fm)
    if m1 and m2 and contrast(m1.group(1), m2.group(1)) < 4.5:
        errs.append(f"[CT1] 节点文字对比度 {contrast(m1.group(1), m2.group(1)):.2f}，低于 4.5")
    if flowlike:
        if d.kind not in KINDS:
            errs.append("[K1] 第一行正文前要声明类型：%% saan: arch|flow|overview|approval|audit")
        for name, props in d.classdefs.items():
            if name not in ROLES:
                errs.append(f"[CL2] classDef {name} 不是角色配色（{'、'.join(ROLES)}）")
                continue
            want = dict(zip(("fill", "stroke", "color"), ROLES[name]))
            if any(props.get(k, "").strip().upper() != v for k, v in want.items()):
                errs.append(f"[CL2] classDef {name} 的颜色和规范不一致")
        for name in d.classes:
            if name not in d.classdefs:
                errs.append(f"[CL2] 用了 {name}，但没有定义 classDef")
        if d.custom_style:
            errs.append("[CL2] 不要用 style 或 linkStyle 单独改色，改用角色配色")
        if len(d.classes.get("core", ())) > 3:
            errs.append(f"[CL1] 核心节点 {len(d.classes['core'])} 个，最多 3 个")
        if len(d.nodes) > 15:
            warns.append(f"[N1] {len(d.nodes)} 个节点，超过 15 个，考虑拆图")
        for nid, n in d.nodes.items():
            if len(re.sub(r"<br\s*/?>", "", n["label"])) > 18:
                warns.append(f"[L1] 节点文字太长：{n['label']}")
            if re.search(r"[^\x00-\x7f]", nid):
                warns.append(f"[S2] 节点 ID 建议用英文：{nid}")
            if nid == "end":
                errs.append("[S2] 不要用 end 作节点 ID")
        dotted = [e for e in d.edges if e[2].startswith("-.")]
        if len(dotted) > 2 and len(dotted) / max(len(d.edges), 1) > 0.3:
            warns.append(f"[DS1] 虚线 {len(dotted)}/{len(d.edges)} 条，太多。虚线只留给退回或可选路径")

    logic = d.kind in ("flow", "overview", "approval", "audit") or d.type.startswith("state") if d.type else False
    if d.kind == "arch":
        for n in d.nodes.values():
            if n["decision"]:
                finds.append(("AR1", f"架构图里有判断节点『{n['label']}』：架构讲有什么，判断属于流程图"))
    no_return = []
    if logic and d.nodes:
        g, r = d.graph()
        ids = set(d.nodes)
        starts, ends = d.endpoints(g)
        fwd = reach(g, starts)
        for n in sorted(ids - fwd):
            finds.append(("P2", f"『{L(n)}』从起点（{'、'.join(map(L, starts)) or '无'}）走不到"))
        back = reach(r, ends)
        for n in sorted(fwd - back):
            finds.append(("P3", f"死路：『{L(n)}』之后走不到任何终点"))
        if not ends:
            finds.append(("P3", "流程没有终点，所有路径都在循环"))
        if d.kind in ("approval", "audit"):
            reviews = [n for n, a in d.nodes.items() if a["decision"]]
            if not reviews:
                finds.append(("AP1", "审批或审计流程没有判断节点"))
            for n in reviews:
                labels = [e[3] for e in d.edges if e[0] == n]
                ahead = reach(g, g.get(n, []))
                if n not in ahead and not any(REJECT.search(x) for x in labels) and REVIEW.search(d.nodes[n]["label"]):
                    no_return.append(n)
            if no_return:
                finds.append(("RT1", f"{len(no_return)} 个审批判断没有退回分支，资料或流程要写明未通过怎么走：{'、'.join(map(L, no_return))}"))
        single = [n for n, a in d.nodes.items() if a["decision"] and n not in no_return and len(set(g.get(n, []))) < 2]
        if single:
            finds.append(("P4", f"{len(single)} 个判断只有一个出口，要写明另一个分支去哪：{'、'.join(map(L, single))}"))
        if d.kind == "overview":
            seen_cycle = [n for n in ids if n in reach(g, g.get(n, []))]
            if seen_cycle:
                finds.append(("OV1", f"总览只画正向主线，这里有回路：{'、'.join(map(L, sorted(seen_cycle)[:3]))}"))
    kept = [(c, m) for c, m in finds if c not in d.accept]
    accepted = [(c, d.accept[c], m) for c, m in finds if c in d.accept]
    return errs, kept, warns, accepted


def svg_width(text):
    m = re.search(r'viewBox="[-\d.]+ [-\d.]+ ([\d.]+) [\d.]+"', text)
    return float(m.group(1)) if m else 0


def norm(x):
    return re.sub(r'<br\s*/?>|[\s"]', "", x)


def parse_controls(text):
    c = {"source": "", "controls": [], "must_pass": [], "separate": [], "none": ""}
    for raw in text.splitlines():
        m = re.match(r"\s*(source|control|must_pass|separate|none):\s*(.+)", raw)
        if not m:
            continue
        key, val = m.group(1), m.group(2).strip()
        if key == "control":
            c["controls"].append(val)
        elif key == "must_pass":
            p = re.split(r"\s+through\s+", val)
            if len(p) == 2:
                c["must_pass"].append(p)
            else:
                c["bad"] = val
        elif key == "separate":
            p = [x.strip() for x in val.split("|")]
            if len(p) == 2:
                c["separate"].append(p)
            else:
                c["bad"] = val
        else:
            c[key] = val
    return c


def find(d, name):
    q = norm(name)
    return [n for n, a in d.nodes.items() if q and q in norm(a["label"])]


def review(texts, controls=None):
    errs, finds, warns, accepted = [], [], [], []
    docs = [D(t) for t in texts]
    for t in texts:
        e, f, w, a = check(t)
        errs += e
        finds += f
        warns += w
        accepted += a
    needs = any(d.kind in ("approval", "audit") for d in docs)
    if controls is None:
        if needs:
            errs.append("[CP2] 审批或审计流程要先写控制点清单，并用 --controls 传入")
        return errs, finds, warns, accepted
    c = parse_controls(controls)
    if c["source"] not in ("user", "document"):
        errs.append("[CP2] 清单第一行要写 source: user 或 source: document")
    if c.get("bad"):
        errs.append(f"[V1] 清单写法有误：{c['bad']}")
    if needs and not (c["controls"] or c["must_pass"] or c["separate"] or c["none"]):
        errs.append("[CP2] 清单是空的。确实没有控制点时，写 none: 原因")
    accept = {}
    for d in docs:
        accept.update(d.accept)
    names = c["controls"] + [x for p in c["must_pass"] + c["separate"] for x in p]
    for name in dict.fromkeys(names):
        if not any(find(d, name) for d in docs):
            errs.append(f"[CP1] 控制点清单里的『{name}』不在图上。补上节点，或告诉用户它为什么不用画")
    found = []
    for target, ctl in c["must_pass"]:
        if any(find(d, target) for d in docs) and any(find(d, ctl) for d in docs) and not any(find(d, target) and find(d, ctl) for d in docs):
            warns.append(f"[CP3] 『{target}』和『{ctl}』分在两张图，无法判断能否绕过")
        for d in docs:
            ts, cs = find(d, target), find(d, ctl)
            if not ts or not cs:
                continue
            g, _ = d.graph()
            starts, _ = d.endpoints(g)
            seen, stack = {s for s in starts if s not in cs}, [s for s in starts if s not in cs]
            while stack:
                for v in g.get(stack.pop(), []):
                    if v not in cs and v not in seen:
                        seen.add(v)
                        stack.append(v)
            if any(t in seen for t in ts):
                found.append(("P1", f"可以绕过『{ctl}』到达『{target}』"))
    for x, y in c["separate"]:
        for d in docs:
            xs, ys = find(d, x), find(d, y)
            if not xs or not ys:
                continue
            la, lb = d.lane.get(xs[0]), d.lane.get(ys[0])
            if d.type != "swimlane-beta" or not la or not lb:
                found.append(("P5", f"『{x}』与『{y}』的执行角色待确认：只有 swimlane-beta 的泳道才算角色"))
            elif la == lb:
                found.append(("P5", f"『{x}』与『{y}』都由『{d.sublabel.get(la, la)}』执行，违反岗位分离"))
    finds += [(a, m) for a, m in found if a not in accept]
    accepted += [(a, accept[a], m) for a, m in found if a in accept]
    return errs, finds, warns, accepted


FM = '---\nconfig:\n  theme: base\n  themeVariables:\n    primaryColor: "#E3E5EA"\n    primaryTextColor: "#1F2329"\n---\n'
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
TESTS = [
    ("K1", GOOD.replace("%% saan: approval\n", ""), CTL),
    ("CL3", GOOD.replace(FM, ""), CTL),
    ("CT1", GOOD.replace('primaryTextColor: "#1F2329"', 'primaryTextColor: "#C0C0C0"'), CTL),
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
    ("CP2", GOOD, None),
    ("CP2", GOOD, "control: 审核单据\n"),
    ("CP2", GOOD, "source: user\n"),
    ("V1", GOOD, CTL + "must_pass: 缺少写法\n"),
]


def selftest():
    bad = 0
    e, f, w, _ = review([GOOD], CTL)
    if e or f or w:
        bad += 1
        print("正确样例不应报错", e, f, w)
    for code, src, ctl in TESTS:
        e, f, w, _ = review([src], ctl)
        got = {re.match(r"\[(\w+)\]", x).group(1) for x in e + w} | {c for c, _ in f}
        if code not in got:
            bad += 1
            print(f"没有触发 {code}，实际 {sorted(got)}")
    a = GOOD + "  apply --> pay\n%% accept P1: 小额付款免审\n"
    if review([a], CTL)[1] or not review([a], CTL)[3]:
        bad += 1
        print("accept 没有生效")
    one = FM + "%% saan: approval\nflowchart LR\n  a[申请] --> b{审核}\n  b --> c[付款]\n"
    codes = [x for x, _ in review([one], "source: user\ncontrol: 审核\n")[1]]
    if codes != ["RT1"]:
        bad += 1
        print("同一节点不应同时报 P4 和 RT1", codes)
    br = FLOW + "  a[第一行第一行第一行<br/>第二行第二行] --> b[结束]\n"
    if review([br])[2]:
        bad += 1
        print("<br/> 不应计入文字长度")
    if svg_width('<svg viewBox="4 4 1800.5 200">') != 1800.5:
        bad += 1
        print("SVG 宽度读取有误")
    print(f"SELFTEST {'PASS' if not bad else 'FAIL'}: {len(TESTS)} 条改坏样例，{bad} 个问题")
    return 1 if bad else 0


def main():
    args = sys.argv[1:]
    if args == ["--selftest"]:
        return selftest()
    controls = None
    if "--controls" in args:
        i = args.index("--controls")
        if i + 1 >= len(args):
            print("--controls 后面要写清单文件")
            return 2
        with open(args[i + 1], encoding="utf-8") as fh:
            controls = fh.read()
        args = args[:i] + args[i + 2:]
    if not args:
        print("用法：check_mermaid.py [--controls controls.txt] diagram.mmd [diagram.svg] [更多文件] | --selftest")
        return 2
    texts, width_notes = [], []
    for p in args:
        with open(p, encoding="utf-8") as fh:
            body = fh.read()
        if p.endswith(".svg"):
            if "aria-roledescription=\"error\"" in body:
                width_notes.append(f"[R1] {p} 是 Mermaid 的错误占位图，渲染失败")
            elif svg_width(body) > 1200:
                width_notes.append(f"[W1] {p} 宽 {svg_width(body):.0f}，放进文档文字会变小。改成纵向或拆图")
        else:
            texts.append(body)
    e, f, w, a = review(texts, controls)
    e += [x for x in width_notes if x.startswith("[R1]")]
    w += [x for x in width_notes if x.startswith("[W1]")]
    if controls is not None:
        src = parse_controls(controls)["source"]
        print({"user": "控制点来源：用户提供", "document": "控制点来源：从资料提取，不是独立依据"}.get(src, "控制点来源：未写明"))
    for x in e:
        print("必须修改", x)
    for c, m in f:
        print("业务发现", f"[{c}] {m}")
    for x in w:
        print("建议", x)
    for c, why, m in a:
        print("已确认", f"[{c}] {m}（{why}）")
    if not (e or f or w or a):
        print("通过")
    return 1 if e or f else 0


if __name__ == "__main__":
    sys.exit(main())
