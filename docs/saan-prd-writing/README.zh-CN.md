# Saan PRD Writing

[English](README.md) | **简体中文**

把需求简报、调研记录、既有规格和原型整理成可供产品、设计、研发和测试评审的 PRD。既能写完整需求规格说明书，也能只写已有项目中的一个变更。

`SKILL.md` 使用英文作为统一指令入口。[介绍页](https://kits.yishan.app/prd-writing/)预置中英文，首次按浏览器语言显示；右上角分别通过语言、外观图标打开下拉菜单，选择中英文或跟随系统、浅色、深色。主题首次跟随系统，手动选择会保存在当前浏览器。实际交互和交付物优先使用用户指定的语言，否则沿用请求语言。

技能版本：**1.0.0**。

## 安装

在包含本技能的 Saan Kits 仓库根目录执行：

```bash
npx skills add yishan/saankits --skill saan-prd-writing
```

默认安装到当前项目。也可以把完整的 `skills/saan-prd-writing/` 复制到目标 Agent 的技能目录。模板、参考说明和示例都在包内，无需安装其他 Saan 技能。

## 怎样使用

完整规格：

```text
用 saan-prd-writing，把这些需求简报、评审记录和原型整理成中文需求规格说明书。
沿用资料中的业务术语，覆盖项目背景、系统边界、功能详情、非功能需求和设计约束。
本轮先交付草稿，未决事项集中列出，附上可追溯到规则的验收检查。
```

局部变更：

```text
用 saan-prd-writing，为采购申请列表增加批量归档编写一份局部变更说明。
根据附件整理条件、字段、状态变化、取消与失败结果，引用既有项目基线。
不确定的批量上限和处理中失败规则列为待确认。
```

修订现有文档：

```text
用 saan-prd-writing，把这次评审决定合入现有 PRD。
保留原有章节及无关内容，更新受影响的规则、界面说明、字段和验收检查。
已被明确替代的旧规则记录为修订，不与新规则同时生效。
```

可以直接提供现有材料，无须先把所有空白补齐。指定交付范围、目标读者和来源优先级，有助于控制写作粒度。输出遵循用户指定语言，未指定时沿用请求语言。

## 产出怎样组织

| 层级 | 组织方式 |
|---|---|
| 完整文档 | 文档控制与修订历史 → 引言 → 项目概况 → 系统概述 → 功能需求 → 非功能需求 → 总体设计约束 |
| 功能详情 | 模块职责与流程 → 业务描述 → 界面设计 → 业务字段 → 功能约束；需要时补充其他信息 |
| 具体规则 | 条件／触发 → 校验与处理 → 数据／状态结果 → 反馈或异常 |
| 交付检查 | 从确定规则派生验收场景；冲突和缺口进入待确认事项 |

小变更使用简版，不强制展开六章。字段表保留「字段名称、数据类型、长度／格式、必填、备注」五个基础列。业务字段不自动推导为物理数据库设计。

图用于说明系统边界、业务流转或交互时序。图、原型、字段表与规则中的角色、字段和状态需要一致。未提供视觉稿时，可以交付结构与交互说明，其状态仍是设计输入。

## 模板与示例

| 资源 | 中文 | English |
|---|---|---|
| 完整需求规格说明书 | [完整模板](../../skills/saan-prd-writing/templates/specification.zh-CN.md) | [Full specification](../../skills/saan-prd-writing/templates/specification.en.md) |
| 局部变更说明 | [变更模板](../../skills/saan-prd-writing/templates/change.zh-CN.md) | [Change specification](../../skills/saan-prd-writing/templates/change.en.md) |

- [采购申请批量归档：输入](../../skills/saan-prd-writing/examples/bulk-archive/input.zh-CN.md) → [写作示例](../../skills/saan-prd-writing/examples/bulk-archive/prd.zh-CN.md)。这是包内的虚构局部变更示范。
- [会议室预约与改期：新需求输入](../../tests/saan-prd-writing/fixtures/room-booking/request.md) → [独立试写产物](../../tests/saan-prd-writing/results/2026-11-04/room-booking/prd.md)。完整规格验证案例保留在仓库测试目录，不作为技能默认输入。
- [验证记录](validation.zh-CN.md)说明实际执行过程、发现、通过范围和限制。

## 事实、建议与待确认事项

来源中的已确认要求、历史做法、讨论选项和未决冲突分别记录。新草稿不会继承来源模板的发布状态、签字、性能值、安全等级、技术架构或服务承诺。

例如，已经明确「校验不通过时整批中止」，并不能推定「处理过程报错时整批回滚」。后者缺少依据时，需要作为单独问题保留。建议文案、默认值和技术方案也需要清楚标记，不能通过界面表或验收表变成已确认规则。

完整规格核对性能、稳定性、安全性、扩展性、运行环境和其他质量要求；缺少材料时写清所需依据。只有确有依据时才判定不适用。

## 来源与方法

本技能沿用经确认的融合结果：需求规格模板提供章节顺序、模块到功能的组织方式和字段表；六份 Axure 原型提供具体对象、动作、条件、状态及数据流转的表达方式。验收关联、来源追溯和显式待确认项是此次补充的质量措施。

原始模板的第六章仅出现在目录中，因此本技能补充了设计约束的编写提示。提示不代表恢复了原文缺失的项目规则。原始文件、私有地址和详细业务摘录没有打入技能包；示例全部为虚构数据。

## 依赖与边界

- 核心流程为文本写作，无外部服务或可执行运行依赖。
- 读取 `.rp` 需要环境具备可靠解析方式或可访问的导出物。本技能不附带通用 Axure 解析器，也不保证直接读取任意 `.rp`。
- 截图只证明所见内容；字符串提取可能包含隐藏和历史内容。部分读取不会被表述成完整原型或生产行为验证。
- `saan-discovery` 可补充调研，`saan-diagram` 或 `saan-mermaid` 可协助画图；均非必需依赖。
- Word/PDF 排版、飞书访问与发布需要对应工具及任务授权。默认交付可编辑 Markdown，不自动修改外部系统。
- 已写成规则、通过文档检查、实现完成和真实业务验收是不同状态。

## 包目录

```text
saan-prd-writing/
  SKILL.md
  agents/openai.yaml
  references/source-handling.md
  templates/specification.zh-CN.md
  templates/specification.en.md
  templates/change.zh-CN.md
  templates/change.en.md
  examples/bulk-archive/input.zh-CN.md
  examples/bulk-archive/prd.zh-CN.md
```

回到 [Saan Kits](../../README.zh-CN.md)。

[介绍页语言与外观验证](../site-preferences-validation.zh-CN.md)
