# 分层架构图

> 用 `python3 scripts/render.py --guide layers` 输出本文；起步模板用 `--init <示例名>`。

## 分层架构图（`layout: layers`）
参照 diagram-design 的 layer stack（层叠）与 high-level（贯穿竖条）两种类型，改成中文平台总体架构的版式。从左到右五条轨道：

| 轨道 | 写法 | 渲染 |
|---|---|---|
| 左侧贯穿栏 | `rails.left: [安全保障体系, 运维支撑体系, …]` | 每个关注点一段竖排文字，交替浅灰；贯穿全部层，说明"每一层都受它约束" |
| 层名列 | `layers[].label` | 浅灰圆角块，14px 600 |
| 主体 | `layers[].blocks` | 每层一条浅底带，区块按 `w` 权重分宽，同层区块等高 |
| 右侧列 | `side[].sections` | 集成平台、内外部系统等跨层元素；`span: [起始层, 结束层]` 对齐到层，不写 span 就按条目数分配高度 |
| 右侧贯穿栏 | `rails.right` | 同左侧，常放法规制度 |

区块（block）的几种写法：
- **普通区块**：`{title, items, cols, w}`。条目是浅灰圆角块；`cols` 不写时按宽度自动排；条目写 `……` 会画成虚线"可扩展"块。
- **工作台区块**：加 `tab: 业务工作台`，在区块顶部加一条角色入口标签（深一档灰），下面是该角色的服务。
- **能力链区块**：写 `stages: [{title, steps: [...]}, …]`。每个阶段是一个子面板，步骤是窄竖块（每行 2 字，`step_wrap` 可改），步骤间小箭头 `›`，阶段间实心 ▶ 表示流程推进。这是把"主流程"嵌进分层图的方式。
- **重点能力区块**：`kind: special`，浅橙底，图例名称取 `special.label`；声明了 `special.prefix` 时，标题以它开头（R5）。

配色仍然遵守统一配色纪律（`--guide style`）：业务条目一律中性灰，**只有系统和核心带颜色**——
- 右侧 section 写 `owner: internal` → 条目是 VI 主色实心块；`owner: external` → 主色提亮块。所以内部系统、外部系统一眼可分。
- `core: true` 可以加在区块、工作台、能力链阶段或单个条目上，全图 ≤3 处（F1）。示例里给了"业务工作台"和"合同执行"两处。
- `vertical: true` 的 section 条目竖排（如集成平台的应用/数据/接口/消息集成）。

连线：分层图默认不画层间连线（层叠本身就表达了依赖）。只有跨列集成关系才用 `links`，例如集成平台 ↔ 外部系统的双向"集成"箭头：`{from: integ, to: ext, kind: bidir, label: 集成}`。端点可以是层 id、带 id 的区块、side 列或 section id，两端必须左右相对、间距 ≥40px（K1，renderer 会自动给有连线的两列留 56px）。

预算（diagram-design layer stack）：**最多 6 层**（D2），每个区块 ≤12 个条目（D1），超出就拆成"总图 + 分层子图"。`width` 默认 1600，内容多时加大，不缩字号。

**分层架构图写法**（完整示例见 `assets/biz-platform.yaml`）：

```yaml
layout: layers
title: 企业业务协同平台
width: 1760                       # 默认 1600
special: {label: AI 能力}          # 重点能力在本图里表示 AI
rails:
  left:  [安全保障体系, 运维支撑体系, 数据标准, 接口标准]
  right: [国家法律法规, 企业管理制度]
layers:                           # 自上而下，≤6 层
  - id: ui
    label: 展示层
    blocks:
      - {w: 3, items: [电脑端, 手机端, 轻应用]}
      - {w: 2, items: [驾驶舱, BI 看板]}
  - id: svc
    label: 服务层
    blocks:
      - {tab: 业务工作台, title: 核心业务服务, core: true, w: 1.4, cols: 2, items: [流程配置, 规则配置, ……]}
      - {tab: 客户门户, title: 客户服务, items: [在线申请, 进度查询, ……]}
  - id: cap
    label: 能力层
    blocks:
      - title: 业务中台
        stages:
          - {title: 需求受理, steps: [需求登记, 需求评估, 立项审批]}
          - {title: 合同执行, core: true, steps: [合同签订, 过程跟踪]}
  - id: tech
    label: 技术层
    blocks:
      - {title: 统一技术底座, items: [流程引擎, 组织权限, ……]}
      - {title: AI 能力平台, kind: special, items: [智能问答, 智能审核]}
side:                             # 跨层的右侧列
  - id: integ
    w: 96
    sections:
      - {title: 集成平台, vertical: true, span: [ui, tech], items: [应用集成, 数据集成, 开放接口]}
      - {title: 第三方AI能力, kind: special, span: [infra, infra]}
  - id: ext
    w: 184
    sections:
      - {title: 企业内部系统, owner: internal, items: [企业 OA, 财务系统]}
      - {title: 外部系统, owner: external, items: [CA 电子签章, 银行系统]}
links:
  - {from: integ, to: ext, kind: bidir, label: 集成}
```
