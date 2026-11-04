# Saan Discovery

[English](README.md) | **简体中文** · [Saan Kits](../../README.zh-CN.md)

结合已有产品逻辑开展 ToC、ToB/G 或混合场景调研，通过交互逐项补充信息，也可直接准备访谈提纲或整理调研记录。

用户通常负责实际访谈。技能负责准备提纲、组织证据和生成补问；`user-interview` 的方法已包含在内部参考文件中，无需另外安装访谈技能。

技能指令和公开介绍默认使用英文；[中文介绍页](https://kits.yishan.app/discovery/zh/)与本中文指南可通过语言链接选择。交互问题、调研底稿及其他交付物优先使用用户指定的语言，否则沿用请求语言。中文提问默认得到中文产出，也可明确指定英文。

## 先确定对象，再逐项展开

开放式调用默认交互推进：读取已有材料 → 确认尚未明确的调研类型和本轮范围 → 建议简短提纲 → 一次推进一个专题。通常每轮只问一个主要问题，回答后更新该专题，再选择下一问。材料中已经明确或用户已经确认的内容不重复询问。

| 类型 | 调研重点 | 产出侧重 |
|---|---|---|
| ToC | 个人的场景、触发、真实经历、替代选择、动机、信任、使用或放弃 | 用户旅程、行为差异、摩擦与未满足需求、待验证机会 |
| ToB/G | 具体岗位、职责、业务流转、适用的审批与规则、数据和系统、实施约束 | 按业务专题整理的纪要、流程及企业差异、适配条件、待决议事项 |
| 混合 | 消费者或居民的体验，以及组织如何提供服务 | 分别保留用户旅程与组织流程，并说明它们的衔接 |

ToB/G 内仍保留企业与公共部门的区别。ToG 根据任务关注服务对象、政策依据、职责与公共服务结果；国企并不自动归为 ToG。ToC 有审核环节时也会调研，ToB/G 同样关注使用体验与实际采纳。

每个专题逐步写出“已知现状或行为、流程、摩擦、期待、产品关系、待确认”。没有材料的部分保持未知。用户可随时纠正、跳过、换专题或索取阶段小结；不知道的事实转为适合向客户或其他岗位核实的问题。

确认表示本轮方向或表述与用户理解一致，不等于客户规则、产品运行或业务验收已核实。等待回答时不会自行补全答案。用户明确要求直接产出完整提纲、整理纪要或不再提问时，技能直接交付已有材料支持的结果。

## 三种使用方式

| 阶段 | 提供什么 | 得到什么 |
|---|---|---|
| 访谈前准备 | 产品材料、客户背景、本次参与岗位和时间 | 产品基线摘要、岗位访谈提纲、需要查看的业务记录 |
| 访谈后整理 | 纪要、转写、行为记录、单据或制度 | 用户旅程或业务流程、适用规则、摩擦与期待、证据和冲突记录 |
| 查漏与补访 | 已有调研底稿和新增信息 | 更新后的底稿、优先补问、适合回答的岗位和适配判断 |

产品材料不完整时仍可开展业务调研；产品适配结论会保留待核实状态。

## 安装

从 Saan Kits 单独安装 Discovery：

```bash
npx skills add yishan/saankits --skill saan-discovery
```

本地开发时，可以在包含此技能的仓库根目录执行 `npx skills add . --skill saan-discovery`。也可以把完整的 `skills/saan-discovery/` 复制到所用 Agent 的技能目录。核心流程只有文本指令，不需要 Python、Node.js 运行环境或外部服务；使用 skills CLI 安装时需要其自身的 Node.js 环境。

## 请求示例

**交互式调研**

> 用 saan-discovery 带我做这次调研。先确认是 ToC、ToB/G 还是混合场景，再确定本轮重点，一次问一个问题。每个专题形成小结后继续，不清楚的内容先记为待核实。

**ToC 访谈准备**

> 这是一个 ToC 活动推荐产品。我想了解用户收藏活动后没有参加的原因。用 saan-discovery 先和我确认访谈范围，再逐项准备问题，不预设用户已经付费。

**准备访谈**

> 用 saan-discovery，根据这份产品手册和客户背景，准备一次 30 分钟的付款业务访谈。参加者是经办人和项目负责人。给我内部准备简报，以及能直接带去使用的客户提纲。

**整理纪要**

> 用 saan-discovery 整理这些调研记录。把客户当前做法、制度要求和目标期待分开，业务流程与审批流程分别记录，列出有冲突或缺少证据的规则。

**继续调研**

> 用 saan-discovery 将新增的管理员答复补入已有调研底稿。保留原来的证据和问题编号，标记已解决项，只提出下一轮最关键的三个问题。

## 怎样选择问题

技能从产品的业务对象、状态、规则、权限和数据依赖中寻找必需的客户条件。同时保留客户独有的任务、线下处理和异常。

每个重要问题关联具体判断：缺什么信息、适合向谁问、需要什么证据、答案影响什么。问题优先级取决于前置关系和业务后果。客户事实问题采用中性问法；需要用户选择调研顺序时可以给出建议。

内部访谈方法见 [user-interview.md](../../skills/saan-discovery/references/user-interview.md)。它包含最近一次真实案例、原因与影响追问、岗位定向补问，以及从现状了解切换到方案验证的方法。

## 输出和证据边界

小任务可以用一份 Markdown 调研底稿承载；需要交给客户的问题另成提纲。正文按用户旅程或业务专题组织，把该专题的现状、问题、期待和产品关系放在一起。详细证据台账放附表，重要结论仍能就近找到来源。多企业汇总保留共性与差异，后续材料更新原有记录及当前专题，保留来源和重要变更。

适配分类包含已有能力覆盖、可配置适配、业务做法调整、系统集成、产品能力缺口和待核实。同一项业务可能涉及多条适配路径。

产品手册、代码、环境配置和实际运行证明的范围不同。客户陈述也不自动等于规则已核实。审批通过与付款、核对等业务完成状态分别记录。技能不会根据缺失信息编造规则、阈值、收益或开发承诺。

流程图可选用 `saan-diagram` 或 `saan-mermaid`，未安装时用步骤表即可。技能不会自动发送问卷或联系客户。

## 验证

模拟输入和评审标准位于 [tests/saan-discovery](../../tests/saan-discovery/README.md)。v0.1.0 的实际运行结果见 [原验证记录](validation.zh-CN.md)；交互与类型分流更新的检查范围见 [v0.2.0 验证记录](validation-v0.2.zh-CN.md)。

这些验证检查技能在给定材料下怎样工作，不证明真实访谈效果，也不代表与无技能模型的对比提升。

英文默认介绍和打包检查见 [发布准备验证](validation-release.zh-CN.md)。

## 方法来源

本技能独立编写，参考以下方法；这些技能不是安装或运行依赖：

- [Matt Pocock：grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md)、[domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md)、[to-questionnaire](https://github.com/mattpocock/skills/blob/main/skills/productivity/to-questionnaire/SKILL.md)：问题依赖、领域术语、按接收人生成问卷。
- [grill-me 精简变体](https://github.com/hburaktasyurek/agent-skills-and-commands/blob/main/skills/grill-me/SKILL.md)：聚焦会改变决定的问题和阶段收敛。
- [user-interview](https://github.com/assimovt/productskills/blob/main/skills/user-interview/SKILL.md)：具体经历、实际行为和避免诱导。针对企业权限与组织约束进行了调整。
- [elicit-requirements](https://github.com/vesviet/agent-skills/blob/main/core/skills/business/elicit-requirements/SKILL.md)：开放探索、深入追问和明确确认。
- [discover-interview-synthesis](https://github.com/product-on-purpose/pm-skills/blob/main/skills/discover-interview-synthesis/SKILL.md)：带来源的访谈归纳和研究局限。

[技能入口](../../skills/saan-discovery/SKILL.md) · [设计研究](../plans/2026-11-04-business-discovery-skill-plan.zh-CN.md)
