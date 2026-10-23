# 流程分析三件套：数据流图 / 审计流程图 / 机会流程图

> 用 `python3 scripts/render.py --guide profile` 输出本文；起步模板用 `--init <示例名>`。

## 流程分析三件套（`profile`）
同一个 stages 引擎，加一个 `profile` 打开对应的校验规则。规则是这几种图的"约束语言"，比画法更重要。

**数据流图 `profile: dfd`**（参照 diagram-design data-flow 与 Gane-Sarson 记法）
- 默认不画泳道；列只用来排位，可以写成"外部实体 / 处理过程 / 数据存储 / 结果去向"四列方便定位。外部实体用 `system`（`owner` 决定深浅），处理过程用 `module`（`sub: P1` 编号），存储用 `kind: store`（`sub: D1` 编号）。
- 连线全部用 `kind: data`，标签写**数据名**（加密标书、报价清单），不写动作。
- 处理与存储**交替排行**（P1 → D1 → P2 → D2 …，行距 1.2），连线标签放竖段（`label_at: 1`），不会挤在一起。
- 规则：DF1 数据只能经过处理才能流转，存储↔存储、实体↔存储、实体↔实体不能直连；DF2 处理不能只进不出（黑洞）或只出不进（奇迹）；DF3 存储必须既有写入又有读取。

**审计流程图 `profile: audit`**（泳道 + 单据 + 控制点）
- 列写部门或岗位；每个步骤旁边放它产生或依赖的单据（`kind: doc`，步骤在 `lane: 0.05`，单据在 `lane: 1.15`），单据与步骤用 `data` 连线，箭头方向即"产生 / 附带"，一般不用再写标签。
- 关键步骤加 `control: K1` 和 `risk`；判断节点也可以是控制点（如"三单一致？"）。图例下方自动生成控制点清单。
- 规则：AU1 每个控制点必须写风险，且审计图至少要有一个控制点；AU2 每张单据都要有连线（谁产生、流向谁）。
- 洞察用法：数一数每个部门有几个控制点。控制点全挤在最后一个环节（比如出纳），说明前面是"先放行再把关"。

**机会流程图 `profile: opportunity`**
- 只放两列：`{id: va, label: 增值环节, value: true}` 和 `{id: nva, label: 非增值环节, value: false}`，步骤按时间往下排，在两列之间来回走（`route: vh`）。
- 图例下方自动写出"增值环节 X 个 · 非增值环节 Y 个（占 Z%）"。
- 最该优化的非增值环节用 `core: true` 标出（≤3 处），这就是给决策者看的"机会点"。

**数据流图 / 审计流程图 / 机会流程图写法**（完整示例见 `assets/bid-dfd.yaml`、`assets/payment-audit.yaml`、`assets/vendor-opportunity.yaml`）：

```yaml
profile: audit                    # dfd | audit | opportunity
columns:
  - {id: buy, label: 采购部门, lanes: 2}
  - {id: fin, label: 财务部门, lanes: 2}
nodes:
  - {label: 核对合同验收, col: buy, lane: 0.05, row: 2.0, control: K1, risk: 未验收即付款}
  - {label: 验收单, kind: doc, col: buy, lane: 1.15, row: 2.0}
  - {id: match, label: 三单一致？, kind: decision, col: fin, lane: 0.05, row: 5.2, control: K3, risk: 三单不一致}
  - {label: 投标文件库, kind: store, col: store, lane: 0.5, row: 1.8, sub: D1}     # dfd
edges:
  - {from: 验收单, to: 核对合同验收, kind: data}
```

路径验证（控制点不可绕过、岗位分离等）见 `--guide verify`。
