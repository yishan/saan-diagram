# Saan Kits

[English](README.md) | **简体中文**

[浏览 Saan Kits 总览](https://kits.yishan.app/)

一套逐步扩展的 Agent 技能工具集，帮助用户把需求转化为图示、文档和原型。可以按需安装单个技能，也可以选择整套工具集。

**目前可用：`saan-diagram`、`saan-mermaid`、`saan-discovery`、`saan-prd-writing`、`saan-prototype`、`saan-inquiry` 和 `saan-xray`。**

GitHub 仓库已由 `yishan/saan-diagram` 更名为 [`yishan/saankits`](https://github.com/yishan/saankits)。安装命令使用新仓库地址，现有 `saan-diagram` 技能名和插件标识保持不变。

## 可用技能

| 技能 | 适用任务 | 交付物 | 使用说明 |
|---|---|---|---|
| [`saan-diagram`](skills/saan-diagram/SKILL.md) | 中英文业务架构、流程、角色交接、数据关系和里程碑图示 | 可编辑 YAML/JSON spec、HTML、SVG、PNG 和飞书画板 DSL | [中文指南](docs/saan-diagram/README.zh-CN.md) · [English guide](docs/saan-diagram/README.md) · [示例图库](https://kits.yishan.app/diagram/) |
| [`saan-mermaid`](skills/saan-mermaid/SKILL.md) | 放在 Markdown 和设计文档里的图，时序图、状态图、甘特图，以及按控制点清单审查流程 | Mermaid 源码、可选的渲染图片和审查发现 | [中文指南](docs/saan-mermaid/README.zh-CN.md) · [English guide](docs/saan-mermaid/README.md) · [介绍页](https://kits.yishan.app/mermaid/) |
| [`saan-discovery`](skills/saan-discovery/SKILL.md) | ToC、ToB/G 与混合场景的交互调研、访谈准备和产品适配评估 | 按专题展开的调研底稿、访谈提纲、缺口清单和适配判断 | [中文指南](docs/saan-discovery/README.zh-CN.md) · [English guide](docs/saan-discovery/README.md) · [English introduction](https://kits.yishan.app/discovery/) · [中文介绍](https://kits.yishan.app/discovery/zh/) |
| [`saan-prd-writing`](skills/saan-prd-writing/SKILL.md) | 完整 PRD、需求规格说明书、局部功能变更与既有文档修订 | 具体规则、业务字段、状态变化、验收场景和待确认事项 | [中文指南](docs/saan-prd-writing/README.zh-CN.md) · [English guide](docs/saan-prd-writing/README.md) · [介绍页](https://kits.yishan.app/prd-writing/) |
| [`saan-prototype`](skills/saan-prototype/SKILL.md) | 根据需求规格生成评审原型，可切换角色和场景，在界面上标出待确认事项 | 单个离线 HTML、可修改的源码、追溯表和检查结果 | [中文指南](docs/saan-prototype/README.zh-CN.md) · [English guide](docs/saan-prototype/README.md) · [介绍页](https://kits.yishan.app/prototype/zh/) |
| [`saan-inquiry`](skills/saan-inquiry/SKILL.md) | 通过自适应对话澄清问题、探索盲点、形成下一步并回看结果 | 清晰的问题表述、暂定判断、行动和回看条件 | [中文指南](docs/saan-inquiry/README.zh-CN.md) · [English guide](docs/saan-inquiry/README.md) · [介绍页](https://kits.yishan.app/inquiry/zh/) |
| [`saan-xray`](skills/saan-xray/SKILL.md) | 透视运行中的系统（浏览器 / Computer Use）、代码库或界面截图，快速摸清既有项目并提取现状基线 | 系统概览简报、模块能力地图、模块现状规格与 UI/代码差异发现 | [中文指南](docs/saan-xray/README.zh-CN.md) · [English guide](docs/saan-xray/README.md) · [介绍页](https://kits.yishan.app/xray/zh/) |

每个技能有独立的 `SKILL.md`，并携带核心流程需要的资源。安装单个技能不要求安装整个工具集。

## 安装

### skills CLI

使用当前 [skills CLI](https://github.com/vercel-labs/skills) 支持的 Node.js 版本。

```bash
# 只查看可用技能，不安装
npx skills add yishan/saankits --list

# 交互选择技能和目标 Agent
npx skills add yishan/saankits

# 只安装 Saan Diagram
npx skills add yishan/saankits --skill saan-diagram

# 只安装 Saan Mermaid
npx skills add yishan/saankits --skill saan-mermaid

# 只安装 Saan Discovery
npx skills add yishan/saankits --skill saan-discovery

# 只安装 Saan PRD Writing
npx skills add yishan/saankits --skill saan-prd-writing

# 只安装 Saan Prototype
npx skills add yishan/saankits --skill saan-prototype

# 只安装 Saan Inquiry
npx skills add yishan/saankits --skill saan-inquiry

# 只安装 Saan X-Ray
npx skills add yishan/saankits --skill saan-xray

# 把当前全部可用技能安装到 Codex
npx skills add yishan/saankits --skill '*' -a codex
```

默认安装到当前项目；加 `-g` 可安装到用户级目录。工具集目前包含以上七个技能。以后新增的技能需要再次安装，整套安装不会自动订阅未来技能。

Saan Discovery、Saan PRD Writing、Saan Inquiry 和 Saan X-Ray 是文本技能，核心流程无需外部运行环境或服务。读取来源文件或走查运行界面可能需要额外工具。运行依赖由各技能分别说明。见 [Saan Diagram 依赖说明](docs/saan-diagram/README.zh-CN.md#依赖)、[Saan Mermaid 依赖说明](docs/saan-mermaid/README.zh-CN.md#依赖)和 [Saan Prototype 依赖说明](docs/saan-prototype/README.zh-CN.md#依赖)。

### Claude Code 插件

```text
/plugin marketplace add yishan/saankits
/plugin install saan-diagram@saan-diagram
```

插件展示名为 **Saan Kits**。为兼容已有安装，插件与市场标识仍保留 `saan-diagram`。插件安装包含包内技能；需要单独选择时使用 skills CLI。

手动安装时，复制完整的 `skills/<skill-name>/` 目录到目标 Agent 的技能目录。Claude Code 和 Claude.ai 的具体方法见 [Saan Diagram 安装说明](docs/saan-diagram/README.zh-CN.md#安装)。

## 计划中的技能

目前没有计划中的技能。新的计划范围以表格记在这里，不要建立可被识别为技能的占位目录。

各技能先独立可用；跨技能的重复流程经过验证后，再考虑加入统一工作流技能。

## 仓库结构

```text
skills/                  可独立安装的技能包
  saan-diagram/          现有图示技能及其运行资源
  saan-mermaid/          Mermaid 画图和流程审查技能
  saan-discovery/        业务调研及内置访谈方法
  saan-prd-writing/      需求写作、模板与完整示例
  saan-prototype/        评审原型的运行时、主题、页面范式和检查
  saan-inquiry/          自适应问题澄清与结果回看
  saan-xray/             存量系统与代码库全景简报及现状规格提取
docs/                    用户说明和预览图片
  saan-diagram/          图示技能的中英文指南
  saan-mermaid/          Mermaid 技能的中英文指南
  saan-discovery/        Discovery 中英文指南和验证记录
  saan-prd-writing/      PRD 中英文指南和验证记录
  saan-prototype/        Prototype 中英文指南和验证记录
  saan-inquiry/          Inquiry 中英文指南和验证记录
  saan-xray/             X-Ray 中英文指南和验证记录
scripts/                 仓库维护和验证脚本
tests/                   Saan Diagram 回归测试；saan-mermaid/ 放 Mermaid 测试
page/                    工具集总览页，每个技能一个二级页面
.claude-plugin/          工具集打包信息，保留原有标识
```

Agent 执行入口位于 `skills/<skill-name>/SKILL.md`。根目录 README 提供工具集目录，技能详细使用说明放在 `docs/<skill-name>/`。站点总览在 `/`，下设 `/diagram/`、`/mermaid/`、`/discovery/`、`/prd-writing/`、`/prototype/`、`/inquiry/` 和 `/xray/`。八个页面均提供中英文版本，右上角统一切换语言和主题。默认跟随浏览器语言与系统主题，手动选择在全站记忆。Diagram 与 Mermaid 的示例保留源文件语言。

## 开发

新增技能前阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，了解职责边界、独立打包、文档和验证约定。技能已有可用实现时再加入对应目录；未来想法先记入计划表，避免占位文件被识别为可安装技能。

现有渲染器、示例和测试保留原位。检查命令见 [Saan Diagram 开发与验证](docs/saan-diagram/README.zh-CN.md#开发与验证)，图库同步方法见 [页面维护说明](page/README.md)。

技能使用英文作为统一指令入口。输出优先遵循用户明确指定的语言，否则沿用请求语言。各技能需说明自身的输出语言限制。

## 许可

[MIT](LICENSE) © 2026 Yishan。各技能的致谢保留在对应使用说明中。
