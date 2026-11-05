# 端到端链路验证：会议室预约

材料全部虚构，不代表真实业务或产品能力。

这个案例检验技能之间的交接，不重复各技能自身的验证。链路是 `saan-discovery` → `saan-prd-writing` → `saan-diagram` → `saan-mermaid`。每一步的输入是原始材料加上一步的原样产出。

## 目录

- `fixtures/`：原始简报 S-01、评审记录 S-02（与 `tests/saan-prd-writing/fixtures/room-booking/` 相同），以及四步各自的请求。
- `review-criteria.md`：生成前写定的评审标准 C1—C6，不提供给执行者。
- `results/2026-11-05/`：四步的原样产出和 `manifest.json`（技能、输入、产出散列）。
- [验证记录](../../../docs/e2e/room-booking.zh-CN.md)：观察结果、发现的问题和局限。

## 复现

1. 为每一步建一个临时目录，只放 `skill/`（对应 `skills/<name>/` 的副本）、`input/` 和空的 `output/`。
2. 第 1 步的 `input/` 放 `brief.md`、`review-notes.md` 和 `01-discovery-request.md`（改名为 `request.md`）。之后每一步的 `input/` 放上一步的产出和本步请求：第 2 步再加原始两份材料；第 3 步只放 `prd.md`；第 4 步放 `prd.md` 和泳道图 spec。
3. 每一步用全新上下文执行，只告诉它技能路径和 `input/request.md`，只允许读该目录、写 `output/`。不提供评审标准或其他步骤的回复。
4. 保留未修改的产出，再按 `review-criteria.md` 对照原始材料评审，并记录散列。

这是一次文本行为记录，不是 CI 中的自动化测试。
