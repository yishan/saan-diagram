# 差旅与日常报销系统 — 系统概览简报（Pass 1）

## 1. 系统定性与透视范围
- **核心定位：** 面向企业内部员工、各级审批人（部门经理、CFO）及财务人员的线上费用报销与结算流转系统，覆盖员工发票关联与报销提单、按金额分级的审批/退回补件、以及财务打款与超期自动归档闭环。
- **透视依据：**
  - 前端线上工作台快照：`ui.html`（员工端 `/app/claims`，当前登录身份：`普通员工 (employee)`）`[Observed-UI: ui.html:3-7]`
  - 后端核心业务服务代码：`server.py`（状态枚举、创建/撤回/审批/财务平账接口及夜间定时任务）`[Observed-Code: server.py:1-84]`
- **探索安全模式：** **`Observe-only`（只读漫游）**——严格遵循安全边界，仅静态检视页面 DOM、弹窗字段属性与后端代码逻辑，未触发任何真实表单提交（`提交审批`、`存为草稿`）、撤回或删除（`作废删除`）等变更操作。

---

## 2. 角色与入口视图（4 类）

| 角色／端 | 角色标识（Code） | 入口与数据范围 | 核心职责与可见操作 | 证据来源 |
|---|---|---|---|---|
| **普通员工** | `employee` | 员工工作台 `/app/claims`、`/app/invoices`、`/app/policies`（仅限本人报销单） | 按状态筛选报销单、新建报销单（存为草稿／提交审批）、撤回待审批单据、对退回单据补充发票重提或作废删除 | `[Observed-UI: ui.html:7-62]`、`[Observed-Code: server.py:18-45]` |
| **部门经理（一级审批人）** | `dept_manager` | 审批接口 `POST /api/admin/claims/<id>/review`（管理端界面本次未见） | 审批处于 `SUBMITTED` 状态的报销单：可执行**通过**（≤ 5,000 元直接进待打款，> 5,000 元转 CFO 复核）或**退回补件**（必填退回原因） | `[Observed-Code: server.py:48-60]` |
| **CFO（二级审批人）** | `cfo` | 审批接口 `POST /api/admin/claims/<id>/review`（管理端界面本次未见） | 对单笔金额 > 5,000 元且经部门经理初审通过（`MANAGER_OK`）的报销单进行复核通过，或退回补件 | `[Observed-Code: server.py:48-64]` |
| **财务管理员** | `finance_admin` | 隐藏接口 `POST /api/claims/<id>/force-settle`（界面无入口） | 对已审批待打款（`APPROVED`）的报销单执行**手工平账**（录入凭证号 `voucher_no`，将状态置为已打款 `PAID`） | `[Observed-Code: server.py:67-76]` |

---

## 3. 模块与功能地图（按 `模块 → 功能` 组织）

| 业务模块 | 下属核心功能／页面／接口 | 一句话业务职责 | 证据来源 |
|---|---|---|---|
| **1. 我的报销单（员工提单与管理）** | 报销单列表与状态筛选（`/app/claims`）、新建报销单弹窗（`POST /api/claims`）、撤回（`POST /api/claims/<id>/withdraw`）、退回重提与作废删除按钮、导出 PDF 按钮 | 负责员工日常与差旅费用的发起、草稿保存、进度跟踪及审批前撤回／退回后处理 | `[Observed-UI: ui.html:9-62]`、`[Observed-Code: server.py:18-45]` |
| **2. 发票夹** | 顶部导航入口 `/app/invoices`、发票占用校验 `InvoiceRepo.is_used_by_active_claim` | 管理员工名下发票档案，供提单时选择关联，并防止同一发票号被多张未归档报销单重复占用 | `[Observed-UI: ui.html:10, 54]`、`[Observed-Code: server.py:31-32]` |
| **3. 报销标准说明** | 顶部导航入口 `/app/policies` | 向员工展示公司差旅与日常报销政策及额度规范（具体页面内容未包含在本次快照中） | `[Observed-UI: ui.html:11]` |
| **4. 报销审批管理** | 审批决策接口 `POST /api/admin/claims/<id>/review`（`approve` / `return`） | 按报销金额（5,000 元分界）执行部门经理一级审批与 CFO 二级审批，支持带原因退回补件 | `[Observed-Code: server.py:48-64]` |
| **5. 财务结算与自动归档** | ERP 打款回调（注释提及）、财务手工平账接口 `POST /api/claims/<id>/force-settle`、每日 02:00 定时归档任务 `nightly_auto_archive_returned_claims` | 完成审批通过单据的打款状态闭环，并自动清理超期未处理的退回单据 | `[Observed-Code: server.py:11-12, 67-84]` |

---

## 4. 核心业务主线（3 条端到端主流程）

1. **员工发起报销与分级审批打款主线（正向闭环）**
   - **触发与角色：** 普通员工（`employee`）在 `/app/claims` 点击「新建报销单」填写费用并保存或提审。
   - **流转路径：**
     1. `[新建报销单（我的报销单）]`：选择费用类型（差旅住宿／市内交通／业务招待）、发生日期（≤ 90 天）、金额（0.01–50,000.00 元）、8–20 位未被占用的发票号及事由说明，点击「存为草稿」生成 `DRAFT` 或点击「提交审批」生成 `SUBMITTED`。
     2. `[一级审批（报销审批管理）]`：部门经理（`dept_manager`）审批 `SUBMITTED` 单据——若金额 **≤ 5,000 元**，直接流转至 `APPROVED`（待打款）；若金额 **> 5,000 元**，流转至 `MANAGER_OK`（待 CFO 复核）。
     3. `[二级审批（报销审批管理）]`：针对 `MANAGER_OK` 单据，CFO（`cfo`）审批通过后流转至 `APPROVED`（待打款）。
     4. `[打款结算（财务结算）]`：通过外部 ERP 打款回调，或由财务管理员（`finance_admin`）调用手工平账接口录入凭证号 `voucher_no`，单据进入终态 `PAID`（已打款）。
   - **业务结果：** 报销单完成从 `DRAFT`/`SUBMITTED` 到 `PAID` 的全链路闭环。
   - **证据等级：** `[Observed-UI: ui.html:49-62]`、`[Observed-Code: server.py:18-35, 48-76]`

2. **审批前员工主动撤回主线**
   - **触发与角色：** 普通员工（`employee`）在审批最终完成前发现填报有误，点击列表行操作「撤回」。
   - **流转路径：** `[报销单列表点击撤回]` → `[调用 POST /api/claims/<id>/withdraw]` → 校验是否为本人单据且状态处于 `SUBMITTED` 或 `MANAGER_OK`。
   - **业务结果：** 报销单状态回退至 `DRAFT`（草稿），员工可重新编辑。
   - **证据等级：** `[Observed-UI: ui.html:38-40]`、`[Observed-Code: server.py:37-45]`

3. **审批退回补件、重提与超期自动归档主线（异常与兜底分支）**
   - **触发与角色：** 部门经理或 CFO 在审批时发现发票缺失或无效，执行 `decision="return"` 并填写退回原因 `comment`。
   - **流转路径：**
     - `[审批退回]`：单据状态变为 `NEEDS_RECEIPT`（界面显示“退回补件”）。
     - **分支 A（员工处理）：** 员工在列表看到「补充发票并重提」与「作废删除」操作按钮 `[Observed-UI: ui.html:42-44]`（注：后端重提与作废删除的具体路由尚未在 `server.py` 中出现，详见第 6、7 节）。
     - **分支 B（超期自动归档）：** 若单据处于 `NEEDS_RECEIPT` 状态且超过 **14 天**未更新，每日凌晨 02:00 定时任务自动将其置为终态 `ARCHIVED`（已归档）。
   - **业务结果：** 退回单据被补充重提，或因超期 14 天未处理自动归档释放发票占用。
   - **证据等级：** `[Observed-UI: ui.html:42-45]`、`[Observed-Code: server.py:51-55, 79-84]`

---

## 5. 核心业务对象与生命周期（2 个核心对象）

| 业务对象 | 关键业务标识与字段 | 已确认状态（标明初始态与终态） | 关键流转条件与业务校验规则 | 证据来源 |
|---|---|---|---|---|
| **报销单（Claim）** | `id`（如 `CLM-202611-001`）、`user_id`、`category`（差旅住宿／市内交通／业务招待）、`expense_date`、`amount`、`invoice_no`、`memo`、`status`、`voucher_no` | **初始态：** `0: DRAFT`（草稿）、`1: SUBMITTED`（直接提审）<br>**中间态：** `1: SUBMITTED`（待审批）、`2: MANAGER_OK`（经理已审待 CFO 审）、`3: NEEDS_RECEIPT`（退回补件）、`4: APPROVED`（待打款）<br>**终态：** `5: PAID`（已打款）、`6: ARCHIVED`（已归档） | • **金额边界：** `0.01 <= amount <= 50,000.00` 元<br>• **时效限制：** `expense_date` 距今不可超过 **90 天**<br>• **发票规则：** 提审时 `invoice_no` 须为 8–20 位，且未被其他未归档报销单占用<br>• **分级审批：** 金额 `> 5000` 元须经 `dept_manager` → `cfo` 两级审批<br>• **撤回范围：** 仅本人且处于 `SUBMITTED` 或 `MANAGER_OK` 可撤回至 `DRAFT`<br>• **自动归档：** `NEEDS_RECEIPT` 超过 **14 天**未更新，每日 02:00 自动转 `ARCHIVED` | `[Observed-UI: ui.html:18-61]`、`[Observed-Code: server.py:5-84]` |
| **发票记录（Invoice）** | `invoice_no`（8–20 位发票号） | 占用态（被未归档报销单关联） vs. 可用态 `[Inferred]` | 无论存为草稿还是提交审批，后端均调用 `InvoiceRepo.is_used_by_active_claim(invoice_no)` 拦截重复占用；单据归档（`ARCHIVED`）后释放占用 `[Inferred]` | `[Observed-UI: ui.html:54]`、`[Observed-Code: server.py:28-32]` |

---

## 6. 界面与代码差异及关键发现

### 6.1 界面与代码不一致项（Discrepancies）
1. **【UI 假按钮／未接后端】「导出 PDF」按钮无实际功能：**
   - 员工端列表顶部渲染了 `#btn-export-pdf`（导出 PDF）按钮，但 HTML 注释明确标记 `<!-- TODO: 前端占位按钮，尚未接后端接口 -->`，且绑定了 `onclick="return false;"`，`server.py` 中亦无导出接口。`[Observed-UI: ui.html:29-30]` vs. `[Observed-Code: server.py]`
2. **【代码隐藏状态／筛选器缺失】二级审批中间态 `MANAGER_OK` 在员工端筛选器中不可见：**
   - 后端定义了 `2: "MANAGER_OK"`（金额 > 5,000 元时部门经理初审通过、待 CFO 复核的中间状态），且允许员工在该状态下撤回单据；但员工端 `status_filter` 下拉框仅提供 `DRAFT`、`SUBMITTED`、`NEEDS_RECEIPT`、`APPROVED`、`PAID`、`ARCHIVED` 6 个选项，遗漏了 `MANAGER_OK`。`[Observed-UI: ui.html:18-26]` vs. `[Observed-Code: server.py:8, 42, 59-63]`
3. **【代码隐藏能力】财务手工平账接口无前端入口：**
   - 后端存在 `POST /api/claims/<id>/force-settle`（`force_settle_claim`），供 `finance_admin` 角色传入 `voucher_no` 将 `APPROVED` 单据强制平账为 `PAID`，属于员工端不可见的后台隐藏能力。`[Observed-Code: server.py:67-76]`
4. **【前后端校验规则差异】前端未体现“90 天报销时效”与“存草稿时的必填差异”：**
   - **90 天限制：** 后端强制校验 `(date.today() - exp_date).days > 90` 报错拦截，但前端 `<input type="date" name="expense_date" required>` 未设置 `min` 属性或提示文案。`[Observed-UI: ui.html:52]` vs. `[Observed-Code: server.py:25-27]`
   - **草稿发票校验：** 前端弹窗中 `invoice_no` 带有 `required` 属性且「存为草稿」为 `type="button"`；后端 `create_or_submit_claim` 仅在 `submit=True` 时校验 8–20 位发票号长度，但无论草稿还是提审都会执行 `InvoiceRepo.is_used_by_active_claim(invoice_no)` 占用检查。`[Observed-UI: ui.html:54-58]` vs. `[Observed-Code: server.py:28-32]`
5. **【UI 按钮对应后端逻辑缺失】退回补件单据的「补充发票并重提」与「作废删除」未在 `server.py` 中闭环：**
   - 员工端对 `退回补件` 单据展示了 `data-action="edit"`（补充发票并重提）和 `data-action="delete"`（作废删除）按钮，但 `server.py` 仅提供了新建接口 `create_or_submit_claim`（未包含既有单据更新/重提或员工主动软删除转为 `ARCHIVED` 的方法）。`[Observed-UI: ui.html:43-44]` vs. `[Observed-Code: server.py:18-84]`

### 6.2 术语与枚举映射表（Terminology Mapping）

| 界面展示文案（`ui.html`） | 接口／代码状态枚举（`server.py`） | 数据库存储值（`CLAIM_STATES`） | 备注 |
|---|---|---|---|
| 草稿 | `DRAFT` | `0` | 新建存草稿或撤回后的状态 |
| 待审批 | `SUBMITTED` | `1` | 直接提交审批后的初始待审状态 |
| *(员工端筛选器未单独列出)* | `MANAGER_OK` | `2` | 金额 > 5,000 元部门经理通过、待 CFO 审批 |
| **退回补件** | `NEEDS_RECEIPT` | `3` | 审批退回状态（UI 与代码命名字面差异较大，需注意对齐） |
| 待打款 | `APPROVED` | `4` | 审批全部通过，等待 ERP 打款或财务手工平账 |
| 已打款 | `PAID` | `5` | 终态：已完成打款 |
| 已归档 | `ARCHIVED` | `6` | 终态：超 14 天未补件自动归档或作废删除 |

---

## 7. 覆盖边界与待确认盲区（`[Inferred]` / `[Unobserved]`）

- **`[Inferred]`（合理推断，待核实）：**
  1. **「作废删除」与「补充发票并重提」的目标状态流转：** 结合代码注释 `6: "ARCHIVED" # Terminal: auto-archived or soft-deleted` 与 `1: "SUBMITTED" # ... or from DRAFT / NEEDS_RECEIPT` 推断，员工点击「作废删除」应将单据软删除置为 `ARCHIVED`，点击「补充发票并重提」应将单据从 `NEEDS_RECEIPT` 更新回 `SUBMITTED`；需检查其他控制器文件或前端 JS 脚本予以核实。
  2. **审批退回（`return`）的可触发状态范围：** `review_claim` 中 `if decision == "return":` 未校验当前 `claim.status` 及审批人角色（位于 `if decision == "approve":` 之前），代码层面上处于任意状态的单据若被调用 `return` 均会被置为 `NEEDS_RECEIPT`，需确认是否为遗留代码漏洞。`[Observed-Code: server.py:51-55]`
- **`[Unobserved]`（未覆盖盲区）：**
  1. **其他角色视图与子页面：** 部门经理（`dept_manager`）、CFO（`cfo`）、财务管理员（`finance_admin`）的审批/管理后台界面，以及员工端 `/app/invoices`（发票夹）和 `/app/policies`（报销标准说明）的具体页面结构。
  2. **外部集成与持久层实现：** ERP 自动打款回调接口（将 `APPROVED` 转为 `PAID` 的触发逻辑）、`ClaimRepo` / `InvoiceRepo` 的底层实现、以及单号生成规则（如 `CLM-YYYYMM-XXX`）。
- **建议下一步：**
  1. **下钻单模块现状规格（Pass 2）：** 如果你准备重构或修复「我的报销单」模块，我可以为你输出可直接对接 `saan-prd-writing` 的 **Pass 2 现状模块规格说明**（含完整字段字典、状态流转矩阵及 `FR-ASIS-*` 规则表）。
  2. **可视化流转图（`saan-mermaid` / `saan-diagram`）：** 需要直观向团队同步时，可将上述跨角色审批泳道与 7 状态生命周期导出为状态机图或泳道图。
  3. **盲区核实（`saan-discovery`）：** 针对 `MANAGER_OK` 在员工端的展示方式、`return` 缺少状态守卫、以及缺失的编辑/删除接口，整理成研发与财务访谈确认清单。
