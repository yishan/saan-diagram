# 鱼骨图

> 用 `python3 scripts/render.py --guide fishbone` 输出本文；起步模板用 `--init <示例名>`。

## 鱼骨图（`layout: fishbone`）
讲"一个结果背后有哪些原因"。右侧是问题（主色浅底），一条主骨，原因大类交替排在上下，每类的原因挂在各自的骨上。
- **骨是正交的**（梳状）：竖骨垂直接入主骨，原因用短横线挂在竖骨左侧，不画斜线，与全局连线规则一致。
- **effect 写成现象**（"评标周期平均 32 天"），不要写成目标或对策。
- **大类**常用 6M（人 / 机 / 料 / 法 / 环 / 测），但**不要为了凑齐 6 类硬造原因**：没有原因的大类直接删（FB1）。≤6 类、每类 ≤6 个原因。
- **根因**：验证过的原因加 `root: true`（主色浅底），≤3 个。图例下方自动列出根因；一个都没标时会提示"这张图现在只是假设清单"；根因都在同一类时会点出"先在这一类上做对策"。
- **洞察用法**：鱼骨图最大的误用是把头脑风暴当结论。没有 root 的鱼骨图只能用于讨论，不能用于汇报。

**鱼骨图 / 时间线 / 四象限写法**（完整示例见 `assets/bid-fishbone.yaml`、`assets/platform-timeline.yaml`、`assets/ai-quadrant.yaml`）：

```yaml
layout: fishbone
effect: 评标周期平均 32 天
categories:
  - {label: 人, causes: [专家临时回避, {label: 评委同时评多个项目, root: true}]}
  - {label: 法, causes: [{label: 澄清环节无时限, root: true}, 复核需线下签字]}
```
