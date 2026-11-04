# Saan Discovery v0.1.0 验证记录

日期：2026-11-04（Asia/Shanghai）。验证对象为本地技能包和本地介绍页。所有客户、产品、制度、金额与访谈内容均为模拟材料。

本记录及对应 manifest 保留 v0.1.0 的历史执行结果。后续交互方式与 ToC、ToB/G 分流更新见 [v0.2.0 验证记录](validation-v0.2.zh-CN.md)；以下结果不冒充新版本的全量复测。

## 方法与结果范围

使用五个独立上下文运行三类模拟场景。付款场景在同一上下文中追加一次补访；产品资料缺失场景增加一次长度复测和一次问法定向检查，共六次任务执行。

运行代理只获得独立复制的技能包、对应场景原始材料和用户任务。它们没有获得评审标准、预期答案或本轮设计讨论。主代理在交付后逐份检查实际输出。模拟输入、原始输出和续接前后版本均保留在 [运行记录](../../tests/saan-discovery/results/2026-11-04/)；[manifest.json](../../tests/saan-discovery/results/2026-11-04/manifest.json) 记录最终技能文件摘要及迭代范围。

这是一组定性工作流验证，不是自动评分、对照实验或真实客户调研验收。它验证给定案例下的可观察行为，不证明模型以后每次都产生相同结果。

## 场景检查

| 场景 | 实际观察 | 产物 |
|---|---|---|
| 30 分钟访谈准备 | 按经办人与项目负责人组织五个主问题；时间合计 30 分钟；区分条件追问；将财务与 OA 专属问题交给后续岗位；使用已有产品事实，不让客户确认产品能力 | [客户提纲](../../tests/saan-discovery/results/2026-11-04/prepare/output/interview-guide-project-payment.md)、[内部准备简报](../../tests/saan-discovery/results/2026-11-04/prepare/output/discovery-project-payment.md) |
| 多岗位付款记录整理 | 保留财务复核制度与经办人可见范围；未因看不到记录认定复核缺失；未自行补齐等于 50,000 元的规则或税口径；分别记录审批通过、银行退回和关账 | [首轮底稿](../../tests/saan-discovery/results/2026-11-04/synthesis/before-follow-up/discovery-payment.md) |
| 产品适配和数据边界 | 跨合同付款包未被直接等同跨合同申请；单合同产品限制仅形成条件性差异；手册没写 OA 集成，结论保持待核实；两笔记录只计算为 48/96 个连续小时，未推广为总体基线、付款时长或达标率 | [首轮底稿](../../tests/saan-discovery/results/2026-11-04/synthesis/before-follow-up/discovery-payment.md) |
| 追加财务解释与 UAT 配置 | 保留 S1–S7、F01–F15、Q01–Q14；增加新证据；按解释层、配置层分别更新问题；UAT 配置没有被升级为生产运行证据；只提出 Q01、Q03、Q05 三个优先补问 | [续接摘要](../../tests/saan-discovery/results/2026-11-04/synthesis/output/continuation-summary.md)、[底稿 v2](../../tests/saan-discovery/results/2026-11-04/synthesis/output/discovery-payment.md) |
| 没有产品资料 | 在用户暂时不可回复的条件下仍交付英文阶段简报；审批阈值、维修关闭条件和产品能力保持未知；未编造指标、负责人分派或开发承诺 | [初次输出](../../tests/saan-discovery/results/2026-11-04/no-product/output/discovery-asset-repairs.md)、[长度复测输出](../../tests/saan-discovery/results/2026-11-04/no-product-retest/output/discovery-asset-repairs.md) |
| 未知结果的问法 | 最终定向检查使用“怎样到达当前状态”，没有预设维修已关闭；是否有状态差异也采用条件问法；共五个英文问题，并分别建议适合回答的岗位 | [最终提纲](../../tests/saan-discovery/results/2026-11-04/question-check/output/interview-guide-asset-repairs.md) |

## 发现的问题与修正

### 1. 短材料的简报过长

初次英文阶段简报为 2,628 词，同一事实和未知项在多个表格中重复。修改 `references/deliverables.md`，要求小任务合并重叠章节，共同证据限制只记录一次，不为填满模板而展开。

在新上下文中使用相同材料和相同请求复测，输出为 1,290 词。当前做法、制度陈述、期望、产品资料缺失与后续岗位仍被区分。该变化是一次样本观察，不是长度或质量提升的统计结论。

### 2. 一个问题预设维修已关闭

长度复测的问题 Q1 使用了 “through the point the case was considered closed”。材料只说明想沿着维修流程调研到关闭，并没有证明该例已经关闭。

修改 `references/user-interview.md`：结果未知时先问当前状态，受访者确认完成后再问完成证据。使用新的独立上下文定向生成五个客户问题，首问变为：

> After the spreadsheet was updated the next morning, how did that repair reach its current state?

最终提纲还写明，仅当维修被报告为已关闭时检查关闭证据。原始失败输出保留，未回改成通过结果。

### 3. UI 简述长度

结构检查发现 `agents/openai.yaml` 的简述超出 64 字符限制，已缩短并重新校验。该修改只影响技能列表展示。

前两项初次场景使用修正前指令；两次针对性复测验证对应改动。最终完整技能包随后重新做了结构与隔离安装检查，没有把每次模拟都描述为对最终文件的全量重跑。

## 包装与页面检查

- `quick_validate.py`：技能 frontmatter 与命名校验通过。
- 独立目录检查：入口引用的四份参考文件全部存在且均位于技能包内；无跨技能必需资源。
- `agents/openai.yaml`：展示字段、简述长度和 `$saan-discovery` 默认提示通过检查。
- 本地 skills CLI 1.5.18：列出三个技能，包含 `saan-discovery`。因 `npx --offline` 缺少 npm 索引缓存，改用本机已缓存的 CLI 执行相同命令。
- 隔离安装：从独立复制目录安装到临时项目的 `.agents/skills/saan-discovery`，逐文件读回与最终源码一致。没有安装到用户级技能目录。
- 本地页面：`scripts/check_site.py` 检查四个页面及原有示例同步，全部通过。
- 浏览器：1280×1000 桌面和 390×844 手机视口无页面横向溢出；手机深色模式截图已人工查看；安装命令和请求示例复制后读回一致；总览与 Discovery 往返导航正确；页面控制台未出现错误。
- 中英文指南、根目录入口、插件 JSON 和本地文档链接已检查。新技能为文本工作流，未增加可执行运行脚本，也未变更现有渲染器。

截图保存在本地忽略目录 `out/discovery-validation/`，不作为发布产物。

## 尚未验证

- 真实客户访谈中的提问质量、访谈负担和业务决策效果。
- 不同行业、组织规模和更大材料量下的持续表现。
- 不使用技能的对照表现。
- 用户级安装、远程仓库安装、skills.sh 收录和在线站点发布。

使用本技能交付客户材料时，仍需核对来源、适用范围、冲突和待确认事项。模拟材料及本报告不构成客户规则或产品能力证据。
