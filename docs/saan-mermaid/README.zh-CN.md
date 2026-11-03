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
- [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) 12 或更高版本，用于渲染。`swimlane-beta` 需要 Mermaid 12。

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

## 局限

- 它只查结构和清单，不判断业务本身对不对，清单之外的问题也查不出。
- 清单如果由画图的 Agent 自己提取，证据很弱，结果会标明“不是独立依据”。
- 逻辑检查只覆盖流程图、泳道图和状态图。
- 各 Markdown 平台内置的 Mermaid 版本不同。示例用 Mermaid CLI 12.2 渲染，还没在 GitHub、飞书等平台上测过。
- `swimlane-beta`、`block-beta` 和 `ishikawa-beta` 是 beta 语法，在旧版本平台上可能显示不了。

## 开发与验证

```bash
python skills/saan-mermaid/scripts/check_mermaid.py --selftest
python -m unittest discover -s tests/saan-mermaid -v
```
