# 组织架构图 + 数据隔离

> 用 `python3 scripts/render.py --guide org` 输出本文；起步模板用 `--init <示例名>`。

## 组织架构图 + 数据隔离边界（`layout: org`）
普通组织架构图只回答"谁管谁"。这里多回答一个问题：**谁能看到谁的数据**。管理关系和数据边界经常不一致，比如集团管控的子公司却是独立数据域，或者兄弟公司之间要共享供应商库。这类不一致正是要画出来给人看的。

- **组织树**：`orgs` 嵌套写 `children`，renderer 按树形自动排版，用直角折线连接。`kind: hq` 表示总部/上级（深一档灰），`unit`（默认）表示组织单元，`virtual` 表示临时或虚拟组织（如项目部，白底虚线框）；`core: true` 表示核心单元（主色浅底，≤3 个）。`sub` 写组织编码（只写拉丁字符）。
- **叶子多时竖排**：某个节点的子节点都是叶子且超过 3 个时，自动改成父节点下方的竖排列表（左侧一条竖线），避免图被拉得很宽。可以用 `stack: true / false` 强制开或关。
- **数据域** `scopes`：每个域写 `members`（默认包含整棵子树）和可选的 `exclude`（把某棵子树排除出去）。规则只有两条：**嵌套 = 外层可以看到内层**（集团汇总下级），**并列 = 互相隔离**。`kind: shared` 的域用主色浅底，表示汇总/共享；默认 `isolated` 只画虚线框。域名写在框内左下角。
- **跨域授权** `grants`：`{from, to, kind: read | write | delegate, label}`，分别表示只读、读写、委托（代办）。同一行、相邻且放得下标签时，画一条主色虚线箭头，标签直接写在线上；否则在节点右下角打 `A1 / A2 …` 角标，图例下方列出授权清单，并统计"跨数据域授权 X 条（其中读写 / 委托 Y 条）"。
- **洞察用法**：读写和委托类授权越多，隔离边界就越像"纸面隔离"。某个独立域只出不进（只有报送），说明它是真隔离；如果兄弟域之间授权成网，就该考虑合并成共享域。
- **预算**：≤24 个组织、≤4 层（D2），超出就按子公司拆成子图。
- **飞书画板**：树的连线导出为带全部拐点的自由折线；授权箭头的标签挂在连接线上，跨框也不会溢出。

**组织架构图写法**（完整示例见 `assets/group-org.yaml`）：

```yaml
layout: org
title: 集团采购组织与数据隔离
orgs:
  - id: group
    label: 甲集团
    kind: hq
    children:
      - {id: center, label: 集采中心, core: true}
      - {id: coa, label: A 建设公司, children: [{label: 第一工程分公司}, {label: 项目部（临时）, kind: virtual}]}
      - {id: coc, label: C 材料公司}
scopes:
  - {id: g,  label: 集团数据域, members: [group], exclude: [coc], kind: shared}
  - {id: a, label: A 公司数据域, members: [coa]}
  - {id: c, label: C 公司独立域, members: [coc]}
grants:
  - {from: center, to: coa, kind: delegate, label: 代理集中采购}
  - {from: coc, to: group,  kind: read,     label: 报送采购统计}
```
