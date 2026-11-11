# Saan X-Ray

[English](README.md) | **简体中文**

对真实运行系统（通过浏览器或 Computer Use）、项目代码库或界面截图做“业务透视”：默认先交付一份 5 分钟可读完的**系统概览简报（System Overview Briefing）**，再按需下钻**模块现状规格（As-Is Module Specification）**。[介绍页](https://kits.yishan.app/xray/zh/)提供中英文版本。

技能版本：**0.1.0**。

## 适合什么任务

当你需要快速摸清一个既有系统或存量项目“现在到底做什么、怎么转”时使用：

- 接手缺少文档或文档已过时的存量系统、历史代码库，需要一份产品与业务视角都能看懂的全景简报。
- 通过浏览器或 Computer Use 走查测试环境/线上系统，梳理角色入口、模块地图、核心业务主线及单据状态流转。
- 在改版、迁移或编写二期需求前，交叉比对“界面实际表现”与“代码底层实现”，找出隐藏功能、未接线按钮或术语偏差。

`saan-discovery` 侧重客户访谈、业务调研与产品适配评估；`saan-prd-writing` 负责编写目标需求规格（To-Be PRD）或局部变更说明；`saan-xray` 负责把**既有系统的真实运行现状（As-Is）**摸清并顺畅交接给下游技能。

## 安装

从 Saan Kits 单独安装 Saan X-Ray：

```bash
npx skills add yishan/saankits --skill saan-xray
```

默认安装到当前项目。手动安装时，把完整的 `skills/saan-xray/` 复制到目标 Agent 的技能目录。技能本身为纯文本包，不依赖特定脚本运行时或其他技能；走查运行系统或读取代码库时，使用当前 Agent 已有的浏览器、Computer Use 或文件读取工具。

统一指令入口使用英文，实际输出优先采用用户指定语言，否则沿用请求语言。

## 怎样开始

从代码库、运行地址或界面截图生成全景简报：

```text
用 saan-xray 透视当前项目，先给我一份系统概览简报：用业务语言讲清系统定位、角色入口、模块与功能地图、核心业务主线、核心业务对象与状态流转，以及还没覆盖到的盲区。
```

以只读模式安全走查运行中的系统：

```text
用 saan-xray 的 Observe-only 只读模式走查这个测试环境。只浏览菜单、列表筛选项和详情，不要点保存、提交或删除，帮我整理模块结构、单据状态和主要流程。
```

按需下钻指定模块，作为改版 PRD 的现状基线：

```text
继续用 saan-xray 对“会议室预订”模块做 Pass 2 深挖：提取页面字段表、校验规则、状态流转表以及界面与代码不一致的地方，准备交给 saan-prd-writing 写改版说明。
```

## 关键机制与交付重点

1. **真实系统探索安全门禁：** 默认采用 **`Observe-only`（只读漫游）**，只切换导航、查看列表/筛选项/详情、打开新建弹窗读取字段后取消关闭，绝不触发保存、提交、删除、审批、支付、发送等写操作；仅在用户明确授权测试环境与测试账号时才启用 **`Sandbox / Test-walk`（沙盒实测）**。
2. **两阶段渐进交付：**
   - **Pass 1 — 系统概览简报（默认必交）：** 控制信息密度（角色 ≤4 类、模块 ≤6 个、核心主线 2–4 条、核心对象 ≤5 个），用业务语言建立全局心智模型，不堆砌框架目录树。
   - **Pass 2 — 模块现状规格（按需下钻）：** 提取界面区域、字段清单、校验规则、集中定义的状态流转表（`当前状态 × 触发动作/角色/条件 → 目标状态`）及待确认项，结构直接对齐 `saan-prd-writing`。
3. **四级证据标记：** 严格区分 **`[Observed-UI]`**（界面实测）、**`[Observed-Code]`**（代码实证）、**`[Inferred]`**（合理推断）与 **`[Unobserved]`**（未覆盖盲区），不靠猜测补造未见规则，并显式暴露界面与代码之间的差异。

详见[探索手册](../../skills/saan-xray/references/exploration-playbook.md)、[简报与现状规格模板](../../skills/saan-xray/references/briefing-and-asis-templates.md)、[设计说明](../plans/2026-11-11-saan-xray-design.zh-CN.md)和[验证记录](validation.zh-CN.md)。

## 包目录

```text
saan-xray/
  SKILL.md
  agents/openai.yaml
  references/
    exploration-playbook.md
    briefing-and-asis-templates.md
```

回到 [Saan Kits](../../README.zh-CN.md)。
