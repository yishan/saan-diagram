---
title: Saan X-Ray 既有系统透视与现状简报技能设计
date: 2026-11-11
status: implemented-local
---

# Saan X-Ray 既有系统透视与现状简报技能设计

## 1. 目标与命名

正式名称：**`saan-xray`**，展示名称：**Saan X-Ray**。

目标：面对一个没有完整文档（或文档已过时）的真实运行系统、项目代码库或界面截图，快速“透视”其业务结构与真实运行逻辑，先交付一份**易读、全景式的系统概览简报（System Overview Briefing）**，再按需深入模块提取现状业务规则、字段、状态流转与待确认盲区，无缝衔接到 `saan-prd-writing`、`saan-diagram`、`saan-mermaid` 或 `saan-discovery`。

为什么采用 `saan-xray`：
- 相比 `saan-walkthrough` 或 `saan-overview`，`saan-xray` 准确表达了“从外部界面（Computer Use / 浏览器）和内部实现（代码 / 接口 / 数据结构）穿透表象、看清系统真实骨骼与规则”的定位。
- 与现有六个技能职责边界清晰：
  - `saan-inquiry`：澄清模糊问题与决策；
  - `saan-discovery`：调研客户/用户现状、准备访谈、评估产品适配；
  - **`saan-xray`**：透视**既有系统/项目本身**现在到底做了什么、怎么运作（UI / Computer Use / 代码 / 截图 → 易读简报 & As-Is 现状规格）；
  - `saan-prd-writing`：编写目标需求规格（To-Be PRD）或局部变更说明（`change`）；
  - `saan-diagram` / `saan-mermaid`：绘制架构图、泳道图、状态图、时序图与流程控制审查；
  - `saan-prototype`：构建可交互的需求评审原型。

---

## 2. 三类输入源与 Computer Use 安全探索模式

`saan-xray` 支持单一来源或多源交叉印证（Hybrid）：

| 输入来源 | 提取重点 | 局限与盲区 |
|---|---|---|
| **1. 真实运行界面（Live UI / Browser / Computer Use）** | 导航与菜单树、角色入口、列表筛选项与表头、表单字段与必填/默认值、状态标签、可执行操作按钮、弹窗/抽屉交互、空状态与错误提示、可见网络请求/枚举 | 看不见未登录角色界面、后台定时任务、未触发的异常分支与跨系统异步回调 |
| **2. 静态视觉材料（Screenshots / 录屏 / 既有原型）** | 页面结构、可见文案、字段、状态标签、按钮分布与局部流程 | 无法主动点击探索隐藏菜单、下拉选项、校验提示或状态流转结果 |
| **3. 项目代码库 / 接口定义（Codebase / API / Schema）** | 路由表、页面组件树、数据模型与字段约束、状态枚举与流转条件、权限守卫、定时任务与外部集成调用 | 代码细节繁杂，直接罗列文件与函数会淹没业务主干；配置开关或线上数据分布未必在代码中可见 |

### Computer Use / 浏览器探索安全门禁（Safety Modes）

当使用浏览器或桌面控制工具（Computer Use）访问真实系统时，必须先确认探索模式：

1. **`Observe-only`（只读观察模式，默认）**
   - 允许：切换菜单与标签页、查看列表与详情、展开筛选器/下拉框查看候选项、打开“新建/编辑”弹窗读取字段与默认值后**取消关闭**、读取浏览器只读请求。
   - 禁止：点击会修改真实业务数据或触发外部副作用的按钮（提交、保存、删除、审批、支付、发送通知、导出敏感生产数据）。
2. **`Sandbox / Test-walk`（测试环境交互模式，需用户明确授权）**
   - 允许：在测试环境或使用测试账号创建标记数据（如 `XRAY-TEST-*`）、故意提交空值/越界值以观察校验文案、走通关键状态流转（如新建 → 提交 → 撤回/取消）。
   - 边界：记录创建或修改的测试单据标识，避免污染非测试数据；遇到高风险确认门禁（生产支付、群发、删除他人数据）立即停止并询问用户。

---

## 3. 两阶段渐进工作流（先易读简报，后按需深挖）

为了避免一上来输出冗长的代码清单或上百条零散字段，`saan-xray` 默认采用**两阶段渐进交付**：

### Pass 1：系统概览简报（System Overview Briefing，默认必交）

用产品与业务语言（而非框架文件名堆砌）在 1 份紧凑简报中回答“这个项目是什么、给谁用、有哪些模块、核心怎么转”：

1. **一句话与一段话定性（System Identity）**
   - 系统解决的核心业务问题、目标使用场景、探索所依据的来源与覆盖范围（例如：已走查哪个环境的哪几个角色入口，或已扫描哪些代码目录）。
2. **角色与入口视图（Roles & Portals）**
   - 识别出的用户角色/端（如员工端、管理员后台、审批端），以及各角色的核心职责与可见范围差异。
3. **模块与功能地图（Module & Capability Map）**
   - 按 **`模块 → 核心功能/页面 → 一句话职责`** 组织的全景目录（对应 `saan-prd-writing` 的 `模块 → 功能` 层级，而非代码目录树）。
4. **核心业务主线（Top User Journeys，2–5 条）**
   - 串联起关键模块的端到端主流程：`触发点 → 关键动作与页面流转 → 最终业务结果`。
5. **核心业务对象与生命周期（Core Objects & States）**
   - 系统围绕哪 3–6 个核心单据/实体运转（如会议室预订、采购单、工单），它们各自有哪些状态及可见的状态变迁。
6. **已确认事实 vs. 盲区清单（Coverage & Blind Spots）**
   - 明确列出本次透视尚未覆盖或无法仅凭当前材料确认的部分（如其它角色视角、后台自动任务、外部系统回调），并给出最省力的核实方式。

### Pass 2：按需深挖与下游交接（On-Demand Deep Dive & Handoff）

用户在审阅 Pass 1 简报后，可以指定任一方向继续：

- **方向 A：模块现状规格（As-Is Module Specification）**
  - 针对指定模块或流程，提取完整的界面区域、字段表（字段名、类型、必填、来源/默认值、校验规则）、状态流转表（`当前状态 × 触发动作/角色/条件 → 目标状态`）及已观察到的异常/边界处理。
  - 产出结构直接对齐 `saan-prd-writing` 的第 3、4 章，可直接作为改版/二期需求（`change.md` 或 `specification.md`）的现状基线。
- **方向 B：生成结构化图示（交接 `saan-diagram` / `saan-mermaid`）**
  - 将透视出的模块地图、跨角色泳道、数据模型（ER）或对象状态机直接转为 `saan-diagram` YAML spec 或 `saan-mermaid` 状态图/时序图。
- **方向 C：输出业务核实提纲（交接 `saan-discovery`）**
  - 将“代码/界面中看不出业务原因的硬编码阈值、疑似废弃分支、未覆盖角色权限”整理为面向产品负责人或业务方的核实问题清单。

---

## 4. 证据等级与防幻觉纪律

透视既有系统最忌“把猜测当成现有规则”。所有关键结论必须区分四类证据状态：

- **`[Observed-UI]`（界面实测）**：在运行界面或截图中直接看到的页面、字段、状态标签、按钮或校验提示（注明页面路径/名称）。
- **`[Observed-Code]`（代码/接口实证）**：在路由、组件、模型、枚举、接口响应或配置文件中直接确认的逻辑（注明文件或接口路径，但正文用业务语言表述）。
- **`[Inferred]`（合理推断，待核实）**：由界面线索或局部命名推断出的规则（例如筛选下拉框里有“已超时释放”，但未观察到触发条件与定时周期）。
- **`[Unobserved]`（未覆盖/盲区）**：因权限不足、环境限制或材料缺失而未观察到的部分（如管理员端、外部支付回调、线下审批环节）。

铁律：
1. **业务语言优先**：禁止把代码文件树当功能架构交差；文件路径只作为 `[Observed-Code]` 的证据引注。
2. **不补造未见规则**：没看到定时周期、校验先后顺序或失败回滚逻辑时，如实标为 `[Inferred]` 或 `[Unobserved]`，绝不用“通常做法”暗中补齐。
3. **UI 与代码冲突时如实并列**：当界面展示与代码逻辑不一致（如死代码、未开放入口、文案与枚举名不一致）时，显式列出差异，不私自抹平。

---

## 5. 包结构与文件规划（v0.1.0，纯文本技能）

遵循 `CONTRIBUTING.md` 的独立打包与双语站点规范：

```text
skills/saan-xray/
  SKILL.md                                # 英文统一执行入口：工作流、安全模式、证据等级、两阶段产出与交接规则
  agents/
    openai.yaml                           # Agent 发现元数据
  references/
    exploration-playbook.md               # Live UI (Computer Use)、代码库与混合透视的分步探索指南与安全红线
    briefing-and-asis-templates.md        # 中英文双语模板：Pass 1 系统概览简报 + Pass 2 模块现状规格（对齐 saan-prd-writing）
docs/saan-xray/
  README.md                               # 英文使用说明
  README.zh-CN.md                         # 中文使用说明
  validation.zh-CN.md                     # 验证记录
page/xray/
  index.html                              # 英文技能介绍页
  zh/index.html                           # 中文技能介绍页
  xray.css                                # 样式（文本对比度 > 4.51，支持浅色/深色/跟随系统）
```

同步更新的工具集文件：
- `README.md` 与 `README.zh-CN.md`（可用技能表、安装命令、目录树）
- `.claude-plugin/plugin.json` 与 `.claude-plugin/marketplace.json`（描述同步）
- `page/index.html`、`page/zh/index.html` 与各二级页面的顶部导航栏（加入 `X-Ray` 链接，并通过 `python3 scripts/check_site.py` 校验）

---

## 6. 实施步骤（Implementation Plan）

1. **Task 1：编写 `skills/saan-xray/` 核心技能包**
   - 创建 `skills/saan-xray/SKILL.md`、`skills/saan-xray/agents/openai.yaml`。
   - 创建 `skills/saan-xray/references/exploration-playbook.md`（涵盖 Computer Use 浏览器走查策略、只读/沙盒安全模式、代码库业务抽象映射方法）。
   - 创建 `skills/saan-xray/references/briefing-and-asis-templates.md`（含 Pass 1 系统概览简报与 Pass 2 模块现状规格的中英文模板）。
2. **Task 2：编写 `docs/saan-xray/` 用户指南与验证记录**
   - 创建 `docs/saan-xray/README.md`、`docs/saan-xray/README.zh-CN.md` 和 `docs/saan-xray/validation.zh-CN.md`。
3. **Task 3：构建 `page/xray/` 双语介绍页并更新全站导航**
   - 创建 `page/xray/index.html`、`page/xray/zh/index.html`、`page/xray/xray.css` 及图标资源。
   - 更新 `page/index.html`、`page/zh/index.html` 及现有 6 个二级技能页的顶部导航栏。
   - 更新根 `README.md`、`README.zh-CN.md` 与 `.claude-plugin/` 元数据。
4. **Task 4：运行全量校验与对比度检查**
   - 运行 `python3 scripts/check_site.py`、`python3 -m unittest discover -s tests -v`、`git diff --check`，并核验 `page/xray/` 浅色/深色模式文本对比度均 `> 4.51`。
