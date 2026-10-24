# IDEF0 功能模型

> 用 `uv run scripts/render.py --guide idef0` 输出本文；起步模板用 `--init <示例名>`。

## IDEF0 功能模型（`layout: idef0`）
讲"一项业务由哪些活动组成，每个活动**受什么约束、靠什么完成**"。和流程图的区别：流程图讲顺序，IDEF0 讲每个活动的四个接口（ICOM）。
- **四个方向是固定语法**：输入（Input）从左进，控制（Control）从上进，输出（Output）从右出，机制（Mechanism）从下进。活动框按阶梯从左上排到右下，右下角自动编号（A1、A2…；写 `node: A2` 时编号为 A21、A22…）。
- **活动**：`activities: [{id, label, core}]`，动词 + 宾语（"组织招标采购"），≤10 字；一张图 3–6 个（ID3），多了就分解成子图。
- **边界箭头**：`inputs: [{to, label}]` 从图左边进来，`outputs: [{from, label}]` 从右边出去。
- **内部流转**：`flows: [{from, to, label, as: input | control}]`。上游的输出可以成为下游的输入，也可以成为下游的**控制**（如"采购计划"约束招标）。指向更早活动的流转自动画成回路：控制回路从上方绕回，输入回路从下方绕回。
- **控制** `controls: [{label, to: [...]}]`：制度、法规、标准、审批规则。从顶部一条虚线总线分到各个活动。
- **机制** `mechanisms: [{label, owner, to: [...]}]`：谁来做、用什么做。`owner: internal / external` 画成 VI 系统块（与其他图示一致），不写 owner 是部门或岗位（灰色圆角块）。从底部总线接入。
- **硬规则**：每个活动至少一个控制（ID1）、至少一个输出（ID2）。没有控制的活动就是失控点，这是 IDEF0 最有价值的检查。
- **洞察用法**：图例下方自动给出：某个机制支撑 ≥60% 的活动（"它一停，整条链就停"）；没有标机制的活动；回路数量（潜在返工）；只受上游结果约束、没有制度控制的活动（"标准靠人记"）。
- **飞书画板**：箭头都是自由折线并带全部拐点，标签是独立文本，可以在画板里拖动微调。

**IDEF0 写法**（完整示例见 `assets/proc-idef0.yaml`）：

```yaml
layout: idef0
node: A0
title: 采购执行
activities:
  - {id: plan, label: 编制采购计划}
  - {id: bid, label: 组织招标采购, core: true}
  - {id: eval, label: 评审与定标}
inputs:  [{to: plan, label: 项目物资需求}]
outputs: [{from: eval, label: 中标通知}]
flows:
  - {from: plan, to: bid, label: 采购计划}
  - {from: bid, to: eval, label: 投标文件}
  - {from: eval, to: bid, as: control, label: 澄清要求}   # 回路
controls:
  - {label: 集团采购管理制度, to: [plan, bid, eval]}
mechanisms:
  - {label: 招采平台, owner: internal, to: [bid, eval]}
  - {label: 采购部, to: [plan]}
```
