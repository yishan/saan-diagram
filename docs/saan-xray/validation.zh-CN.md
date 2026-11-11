# Saan X-Ray v0.1.0 验证记录

日期：2026-11-11。范围：本地初版技能包、参考手册与双语模板、中英文用户指南、双语站点页面、全站导航校验，以及本地安装与双阶段独立行为测试。

## 1. 设计与同业对比依据

结合[设计说明](../plans/2026-11-11-saan-xray-design.zh-CN.md)及对社区同类技能（`codebase-onboarding`、`architecture-analyze`、`to-prd` 等）的对比分析，`saan-xray` 重点解决三类常见问题：

1. **避免把代码目录树当业务说明**：要求按 `模块 → 功能` 组织能力地图，把文件或路由路径作为紧凑证据引注。
2. **避免 Computer Use / 浏览器盲目点击触发写操作**：默认强制 `Observe-only`（只读漫游），仅在明确授权的测试环境下才开启 `Sandbox / Test-walk`。
3. **避免为凑齐模板而编造未见规则**：所有关键结论区分 `[Observed-UI]`、`[Observed-Code]`、`[Inferred]` 和 `[Unobserved]`，并显式暴露 UI 与代码之间的差异（死代码、未开放入口、术语偏差）。

## 2. 包结构、本地安装与静态检查

- **独立目录检查**：`skills/saan-xray/` 包含 `SKILL.md`、`agents/openai.yaml`、`references/exploration-playbook.md` 与 `references/briefing-and-asis-templates.md`；通过 `quick_validate.py skills/saan-xray` 校验（`Skill is valid!`），无外部运行时或跨目录硬依赖。
- **本地 CLI 发现与安装测试**：
  - `npx --offline skills add . --list` 正常识别仓库全部 7 个技能（含 `saan-xray`）。
  - `npx --offline skills add . --skill saan-xray -y` 成功安装至本地工作区 `.agents/skills/saan-xray`。
- **站点与链接校验**：`python3 scripts/check_site.py` 校验全站 16 个中英文 HTML 页面（含新增 `page/xray/index.html` 与 `page/xray/zh/index.html`）、导航链接、锚点一致性和复制按钮目标。
- **视觉对比度检查**：`page/xray/xray.css` 在浅色与深色模式下的正文、次要文字、链接与代码块对比度均 `> 4.51`（符合 W3C WCAG AA 标准）。

## 3. 独立子代理双阶段行为测试（`tests/saan-xray/`）

使用 `tests/saan-xray/fixtures/expense-claim/`（包含带前端死按钮和筛选枚举缺失的 `ui.html`，以及带二级审批、隐藏平账接口与夜间定时归档任务的 `server.py`）对独立子代理进行黑盒评测，评测标准见 [`tests/saan-xray/review-criteria.md`](../../tests/saan-xray/review-criteria.md)：

| 轮次 | 输入 | 产物归档 | 评审结论 |
| --- | --- | --- | --- |
| Turn 1（Pass 1：系统概览简报） | [`request-pass1.md`](../../tests/saan-xray/fixtures/expense-claim/request-pass1.md) + `ui.html` + `server.py` | [`turn-1-pass1.md`](../../tests/saan-xray/results/2026-11-11/turn-1-pass1.md) | **PASS（5/5）**：明确声明并遵守 `Observe-only` 只读边界；准确提炼 4 类角色、5 个业务模块（`Module → Function`）、3 条核心业务主线与 7 个报销单状态；完整捕获全部 3 处预设冲突（`#btn-export-pdf` 死按钮、`MANAGER_OK` 二级审批状态在筛选器缺失与隐藏接口 `/force-settle`、`退回补件 = NEEDS_RECEIPT = 3` 术语映射）并额外发现 3 处前后端校验与数据落库隐患。 |
| Turn 2（Pass 2：模块现状规格） | [`request-pass2.md`](../../tests/saan-xray/fixtures/expense-claim/request-pass2.md) | [`turn-2-pass2.md`](../../tests/saan-xray/results/2026-11-11/turn-2-pass2.md) | **PASS（5/5）**：输出与 `saan-prd-writing` 对齐的集中状态生命周期表（含 >5,000 元转 CFO 审批与 14 天夜间自动归档）、页面区域与表单字段清单、`FR-ASIS-001`～`006` 严格校验顺序规则，以及 `OQ-001`～`006` 待业务/财务确认问题清单。 |
