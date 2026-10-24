# 实体关系图

> 用 `uv run scripts/render.py --guide er` 输出本文；起步模板用 `--init <示例名>`。

## 实体关系图（`layout: er`）
参照 diagram-design 的 ER / data model：讲"业务对象是什么、几对几"，不讲物理表结构。
- **实体**：表头（实体名，浅灰底 14px 600）+ 字段列表（12px）。字段前缀 `#` = 主键，右侧显示 `PK` 标签；`→` = 外键，显示 `FK`。**只列主键、外键和讲故事需要的字段，每个实体 ≤8 个**（F2）。
- **位置**：`col / row` 网格（列距 104px、行距 72px，行高按内容），renderer 计算坐标。把关系最密的实体放中间，让多数关系是直线。
- **关系**：`relations: [{from, to, card: ['1', 'N'], label}]`。线是中性灰细线、不带箭头；两端都要标基数（C1），写法统一用 `1 / N / 0..1 / 1..*`；标签写动词（立项、划分、递交），≤8 字。同一边多条关系自动错开接点。
- **焦点**：`core: true` 标聚合根（如"采购项目"），最多 2 个（F1）。
- **业务域**：`groups: [{label, members}]` 画虚线框，表示限界上下文（如"评审域"）。
- **预算**：一张图 ≤8 个实体（D2），超出按业务域拆图。

**实体关系图写法**（完整示例见 `assets/procurement-er.yaml`）：

```yaml
layout: er
title: 采购核心数据模型
entities:
  - {id: project, label: 采购项目, col: 1, row: 0, core: true, fields: ["#项目编号", "→计划编号", 项目名称, 采购方式]}
  - {id: lot,     label: 标段,     col: 2, row: 0, fields: ["#标段编号", "→项目编号", 最高限价]}
groups:
  - {label: 评审域, members: [expert, score]}
relations:
  - {from: project, to: lot, card: ["1", "N"], label: 划分}
```
