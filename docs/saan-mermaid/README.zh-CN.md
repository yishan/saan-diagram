# Saan Mermaid

[English](README.md) | **简体中文**

[介绍页与示例](https://kits.yishan.app/mermaid/)

用 Mermaid 代码画图，图跟着文档走；并拿一份画图前写好的控制点清单，审查业务流程。

审查是这个技能的差异所在。一次小样本匿名对比（3 个场景各跑 1 次）显示，早期版本并没有提高画图质量，所以应首先把它当作审查工具。

## 什么时候用

| 用 Saan Mermaid | 用 [Saan Diagram](../saan-diagram/README.zh-CN.md) |
|---|---|
| 放在 Markdown、README 和设计文档里的图 | 汇报、对外交付和飞书画板 |
| 时序图、状态图、甘特图 | IDEF0、组织架构与数据隔离 |
| 按控制点清单审查流程 | 精确排版和走线 |

两个技能的第一个问题相同，都是先分“有什么”还是“怎么走”，也使用同一套角色配色。两者互不依赖。

## 安装

```bash
npx skills add yishan/saankits --skill saan-mermaid
```

手动安装时，把完整的 `skills/saan-mermaid/` 目录复制到目标 Agent 的技能目录。

## 依赖

- Python 3，用于运行 `scripts/check_mermaid.py`，只用标准库。
- [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) 12 或更高版本，用于渲染。`swimlane-beta` 需要 Mermaid 11.16 或更高版本。

## 审查怎么走

1. 画图前先写 `controls.txt`，最好来自制度或控制要求。

   ```text
   source: user
   control: 财务复核
   must_pass: 执行付款 through 财务复核
   separate: 提交付款申请 | 审核单据
   ```

2. 在图的类型行上方声明类型：`%% saan: arch|flow|overview|approval|audit`。
3. 先渲染，再把同一流程的所有图放在一起检查：

   ```bash
   mmdc -i diagram.mmd -o diagram.svg -b white -q
   python3 skills/saan-mermaid/scripts/check_mermaid.py --controls controls.txt diagram.mmd diagram.svg
   ```

| 输出 | 含义 | 怎么处理 |
|---|---|---|
| 必须修改 | 样式、语法、缺控制点或渲染失败 | 修改图 |
| 业务发现 | 流程结构上的问题 | 报告出来，不能靠删线过关 |
| 建议 | 文字太长、图太宽、虚线太多 | 没有明确理由就照做 |
| 已确认 | 已用 `%% accept P1: 原因` 接受的发现 | 保留原因，且只在用户确认后才写 |

每行结果都带文件和行号，比如 `doc.md:42 [P1]`。Markdown 文件会按 mermaid 代码块逐个检查。

| 选项 | 用途 |
|---|---|
| `--target 11.12` | 按宿主的 Mermaid 版本检查图类型和写法能否渲染。在宿主里渲染只写 `info` 的代码块即可看到版本 |
| `--theme saan-dark` | 要求使用指定主题；默认按 frontmatter 自动识别 |
| `--theme-block saan-dark` | 输出该主题的 frontmatter 和角色配色 |
| `--json` | 以 JSON 输出，便于其他工具读取 |

主题文件在 `skills/saan-mermaid/assets/themes/`。默认用 `saan-light`，只有深色页面才用 `saan-dark`。自定义主题就是复制其中一个文件再改色值，文字和角色配色的对比度低于 4.5:1 时检查不通过。

想在 Claude Code 写入文件后立刻发现语法错误，可以把 `scripts/hook.py` 配成 `PostToolUse` hook。它只在图无法渲染时拦截：

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit|MultiEdit",
        "hooks": [{ "type": "command", "command": "python3 <skill-dir>/scripts/hook.py" }]
      }
    ]
  }
}
```

## 规则

| 触发条件 | 检查内容 |
|---|---|
| `saan: flow` | P2 走不到、P3 死路、P4 判断只有一个出口 |
| `saan: approval` 或 `audit` | 再加 AP1 没有判断节点、RT1 审批没有退回 |
| `saan: overview` | 再加 OV1 总览出现回路 |
| `saan: arch` | AR1 架构图混入判断节点 |
| `control` | CP1 控制点不在任何一张图上 |
| `must_pass` | P1 控制点可被绕过 |
| `separate` | P5 不相容的两步在同一泳道 |
| `alias: 名称 = 节点文字` | 让控制点名称匹配措辞不同的节点 |
| 同名节点 | CP4 提醒多个节点同名、检查把它们当作同一步；清单里改写节点 ID 可以分开查 |
| `sequenceDiagram` | S3 块没有闭合、SQ1 参与者没用到、SQ2 激活不成对、SQ3 消息里有分号 |
| `gantt` | GT1 `after` 引用不存在的 ID、GT2 依赖成环、GT3 缺 `todayMarker off` |
| `erDiagram` | ER1 实体没有任何关系 |
| frontmatter | CL3 和主题文件不一致、CF1 用了已弃用的 `%%{init}%%` |
| 传入 SVG | G1 节点重叠、G2 连线文字压在节点上、W1 图太宽、R1 渲染失败 |

## 局限

- 它只查结构和清单，不判断业务本身对不对，清单之外的问题也查不出。
- 清单如果由画图的 Agent 自己提取，证据很弱，结果会标明“不是独立依据”。
- 路径逻辑只覆盖流程图、泳道图和状态图；时序图、甘特图和 ER 图只做结构检查。
- SVG 重叠检查读取 Mermaid 输出里的节点和文字框，看不出连线交叉。
- 各 Markdown 平台内置的 Mermaid 版本不同。示例用 Mermaid CLI 12.2 渲染，还没在 GitHub、飞书等平台上测过。
- `swimlane-beta`、`block-beta` 和 `ishikawa-beta` 是 beta 语法，在旧版本平台上可能显示不了。

## 开发与验证

```bash
python skills/saan-mermaid/scripts/check_mermaid.py --selftest
python -m unittest discover -s tests/saan-mermaid -v
```
