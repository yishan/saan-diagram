# Saan Prototype

[English](README.md) | **简体中文**

[介绍页与在线示例](https://kits.yishan.app/prototype/zh/)

把需求规格变成评审用的可交互原型：一个单独的 HTML 文件，浏览器直接打开，不需要安装或构建。评审时可以切换角色和场景，看成功和失败时界面怎么反馈，哪些文案还是建议，哪些问题还没定。

原型用来对齐交互、状态和规则，不是可上线的前端代码，也不替代视觉设计稿。

## 什么时候用

| 用 Saan Prototype | 用别的 |
|---|---|
| 评审前，想让大家点一遍页面、角色和状态 | 写需求本身：[Saan PRD Writing](../saan-prd-writing/README.zh-CN.md) |
| 检查已确认的规则在界面上是否说得通 | 讲清业务结构和流程：[Saan Diagram](../saan-diagram/README.zh-CN.md)、[Saan Mermaid](../saan-mermaid/README.zh-CN.md) |
| 把待确认事项标在它影响的界面位置上 | 前端工程、视觉稿、移动端设备外框：不在本技能范围内 |

首选输入是 `saan-prd-writing` 那样的规格：功能清单、界面设计、功能约束、验收场景和待确认事项都带编号。它是可选的同级技能，不是前提。只有一段描述或截图时也能用，原型会先列出假设，所有文字都标为建议。

## 安装

```bash
npx skills add yishan/saankits --skill saan-prototype
```

手动安装时，把完整的 `skills/saan-prototype/` 目录复制到目标 Agent 的技能目录。

## 依赖

- Python 3，用于运行 `scripts/build.py` 和 `scripts/check.py`，只用标准库。
- 一个浏览器，用来打开产出的原型。原型不请求任何网络资源。

## 怎么用

把规格交给 Agent：

```text
用 saan-prototype 根据 prd.md 做一个评审原型。先给我页面、角色和场景清单。
```

Agent 会先列出范围（例如“4 个页面、2 个角色、9 个场景”），然后在工作目录里写出：

| 产出 | 内容 |
|---|---|
| `prototype.html` | 内联了运行时、主题和页面的单个文件 |
| `prototype/` | 规格副本、`manifest.json`、`rules.js`、`scenarios.json`、`pages/*.js`，修改后可以重新打包 |
| `prototype/trace.md` | 页面、场景与来源编号的对应关系，以及没有画进原型的待确认事项和原因 |

打开 `prototype.html`，顶部的评审栏可以：

- **切换场景。** 每个场景对应一个或几个验收编号，带着自己的初始数据和当前时间（“已开始”这类规则靠时间判断）。切换会重置数据。
- **切换角色。** 同一页面以不同身份看到的内容和可做的操作。
- **切换主题。** 内置 `neutral`（中性灰）、`blue`（品牌蓝）、`dark`（暗色）。
- **开关标注层。** 默认打开。〔建议〕文案带角标，待确认事项显示为“此处待 Q-xx 决定”的占位块，点开能看到问题原文；已确认规则只显示编号。关掉后是干净的演示版。

规则只写来源中**已确认**的部分；待确认的规则不写成逻辑，只显示占位。

## 检查

```bash
python3 skills/saan-prototype/scripts/build.py prototype/manifest.json -o prototype.html
python3 skills/saan-prototype/scripts/check.py prototype/manifest.json
```

`check.py` 退出码：0 无问题，1 有必须修改的问题，2 只有业务发现。

| 输出 | 编号 | 含义 | 怎么处理 |
|---|---|---|---|
| 必须修改 | T1、T3 | 标注的编号在来源中不存在，或类型用错 | 修改原型 |
| | T2 | 待确认事项既没标出，也没在 `trace.md` 写明「不涉及」 | 标出，或写明原因 |
| | S1、S3、S4 | 场景引用了不存在的验收编号、未声明的角色，或 id 重复 | 修改场景 |
| | C2 | 场景数据用了 manifest 之外的状态 | 原型不能新增状态 |
| | W1 | 已确认文案没有原样出现 | 修改页面 |
| | B1、B2 | 请求了外部资源；主题对比度不达标 | 修改原型或主题 |
| | M1 | manifest 或文件缺失 | 修复文件 |
| 业务发现 | C1、W2 | 声明的状态或已确认文案在来源中找不到 | 报告给用户，不能为了通过而改 |
| 提示 | N1 | 有验收场景没有被任何场景覆盖 | 在 `trace.md` 说明为什么不能在界面上演示 |
| | N2 | 标注编号在运行时才确定，无法核对 | 能写死的写死 |

编号格式默认是 `Q-01`、`AC-01`、`FR-B01`（字母可省略）；来源用别的格式时，在 manifest 的 `id_patterns` 里改。

## 局限

- 原型是评审工具：示例数据为虚构，规则只覆盖已确认的部分。
- 检查只核对编号和文本。它不评价交互是否好用，看不出动作是否真的走了规则函数，也看不出某个标注在哪个场景里能被看到。
- 没有规格时，来源是 Agent 自己写的复述，检查等于自己核对自己。
- 多套主题只保证对比度，不保证品牌合规。
- 没有真实用户可用性测试。验证时的评审人也是安排运行的会话，不是盲审。

## 开发与验证

```bash
python3 skills/saan-prototype/scripts/check.py --selftest
python3 -m unittest discover -s tests/saan-prototype -v
```

两个案例（room-booking 的 PRD、一段没有 PRD 的描述）各在全新上下文中跑了两轮，评审标准在生成前写定。过程、发现的问题和修改见[验证记录](validation.zh-CN.md)。
