# 我的报销单（报销发起、撤回与退回补件）— 现状模块规格说明（Pass 2: As-Is Module Specification）

## 1. 模块职责与对象生命周期（Module Responsibility & Object Lifecycle）

### 1.1 范围、角色与权限边界
- **所属模块：** 我的报销单（涵盖员工端列表与筛选、新建/提审报销单、审批前撤回、退回补件处理，以及关联的后端分级审批流转、财务平账与夜间自动归档）
- **访问入口与路由：**
  - **员工端页面：** `/app/claims`（顶部导航「我的报销单」激活态）`[Observed-UI: ui.html:3, 9]`
  - **后端业务接口：**
    - `POST /api/claims`（员工创建草稿或提交审批，`create_or_submit_claim`）`[Observed-UI: ui.html:50]`、`[Observed-Code: server.py:18-34]`
    - `POST /api/claims/<id>/withdraw`（员工撤回待审批单据，`withdraw_claim`）`[Observed-Code: server.py:37-45]`
    - `POST /api/admin/claims/<id>/review`（部门经理／CFO 审批或退回，`review_claim`）`[Observed-Code: server.py:48-64]`
    - `POST /api/claims/<id>/force-settle`（财务管理员手工平账，`force_settle_claim`）`[Observed-Code: server.py:67-76]`
    - `nightly_auto_archive_returned_claims`（每日 `02:00` 定时任务：超期退回单据自动归档）`[Observed-Code: server.py:79-84]`
- **角色与数据可见范围：**
  - `employee`（普通员工）：仅可发起报销单（`user.role == "employee"`），在 `/app/claims` 查看、撤回本人的报销单（`claim.user_id == user.id`）。`[Observed-UI: ui.html:7, 38-45]`、`[Observed-Code: server.py:20-21, 40-41]`
  - `dept_manager`（部门经理）：可对 `SUBMITTED` 状态的报销单执行一级审批通过或退回补件。`[Observed-Code: server.py:51-60]`
  - `cfo`（CFO）：可对 `MANAGER_OK` 状态（金额 > 5,000 元）的报销单执行二级审批通过或退回补件。`[Observed-Code: server.py:51-63]`
  - `finance_admin`（财务管理员）：可对 `APPROVED` 状态的报销单执行手工平账。`[Observed-Code: server.py:69-76]`

---

### 1.2 报销单（`Claim`）集中状态生命周期定义

#### （1）状态枚举与术语映射（含初始态／终态标识）

| 数据库存储值（`CLAIM_STATES`） | 代码状态枚举（`server.py`） | 员工端 UI 展示文案（`ui.html`） | 生命周期属性 | 员工端筛选器是否可见 | 行级可见操作按钮（员工端 UI） | 证据来源 |
|---|---|---|---|---|---|---|
| `0` | `DRAFT` | 草稿 | **初始态**（存草稿时） | 是（`value="DRAFT"`） | 样本未展示行记录 `[Unobserved]` | `[Observed-UI: ui.html:20]`、`[Observed-Code: server.py:6, 33]` |
| `1` | `SUBMITTED` | 待审批 | **初始态**（直接提审时）／**中间态** | 是（`value="SUBMITTED"`） | `撤回`（`data-action="withdraw"`） | `[Observed-UI: ui.html:21, 39-40]`、`[Observed-Code: server.py:7, 33]` |
| `2` | `MANAGER_OK` | *(未在筛选器单列，或仍显示为“待审批” `[Inferred]`)* | **中间态**（金额 > 5,000 元经理已审、待 CFO 审） | **否**（筛选器缺失该枚举） | 代码允许 `withdraw`（撤回） | `[Observed-UI: ui.html:18-26]`、`[Observed-Code: server.py:8, 42, 59]` |
| `3` | `NEEDS_RECEIPT` | **退回补件** | **中间态** | 是（`value="NEEDS_RECEIPT"`） | `补充发票并重提`（`data-action="edit"`）、`作废删除`（`data-action="delete"`） | `[Observed-UI: ui.html:22, 43-44]`、`[Observed-Code: server.py:4, 9, 54]` |
| `4` | `APPROVED` | 待打款 | **中间态** | 是（`value="APPROVED"`） | 无员工操作 `[Inferred]` | `[Observed-UI: ui.html:23]`、`[Observed-Code: server.py:10, 59, 62]` |
| `5` | `PAID` | 已打款 | **终态（Terminal）** | 是（`value="PAID"`） | 无操作 `[Inferred]` | `[Observed-UI: ui.html:24]`、`[Observed-Code: server.py:11, 74]` |
| `6` | `ARCHIVED` | 已归档 | **终态（Terminal）** | 是（`value="ARCHIVED"`） | 无操作 `[Inferred]` | `[Observed-UI: ui.html:25]`、`[Observed-Code: server.py:12, 83]` |

#### （2）状态流转矩阵（Transition Table）

| 当前状态（Current State） | 触发动作／事件（Trigger / Action） | 执行角色／主体（Actor） | 前置条件与校验规则（Preconditions / Validation） | 目标状态（Target State） | 失败／拦截处理（On Failure / Rejection） | 证据来源 |
|---|---|---|---|---|---|---|
| *(无 / 新建)* | 点击「存为草稿」(`create_or_submit_claim(submit=False)`) | `employee`（普通员工） | 1. `user.role == "employee"`<br>2. `0 < amount <= 50000`<br>3. `(date.today() - expense_date).days <= 90`<br>4. `!InvoiceRepo.is_used_by_active_claim(invoice_no)` | `DRAFT` | 抛出对应 `PermissionError` 或 `ValueError`，不生成单据 | `[Observed-UI: ui.html:57]`、`[Observed-Code: server.py:18-34]` |
| *(无 / 新建)* | 点击「提交审批」(`create_or_submit_claim(submit=True)`) | `employee`（普通员工） | 除上述 4 项外，额外校验：<br>5. `8 <= len(invoice_no.strip()) <= 20` | `SUBMITTED` | 抛出 `ValueError("提交审批时必须填写 8–20 位有效发票号")` 等异常，不生成单据 | `[Observed-UI: ui.html:58]`、`[Observed-Code: server.py:18-34]` |
| `SUBMITTED` 或 `MANAGER_OK` | 点击「撤回」(`POST /api/claims/<id>/withdraw`) | `employee`（单据申请人本人） | 1. `claim.user_id == user.id`<br>2. `claim.status in ("SUBMITTED", "MANAGER_OK")` | `DRAFT` | 非本人抛 `PermissionError("只能撤回本人的报销单")`；其他状态抛 `ValueError("仅待审批状态的报销单可撤回")`；保持原状态 | `[Observed-UI: ui.html:40]`、`[Observed-Code: server.py:37-45]` |
| `SUBMITTED` | 一级审批通过 (`POST /api/admin/claims/<id>/review`, `decision="approve"`) | `dept_manager`（部门经理） | `claim.status == "SUBMITTED"` 且 `reviewer.role == "dept_manager"` 且 **`claim.amount <= 5000`** | `APPROVED` | 角色或状态不符抛 `PermissionError("当前状态或角色无权执行该审批动作")`；保持 `SUBMITTED` | `[Observed-Code: server.py:56-60, 64]` |
| `SUBMITTED` | 一级审批通过（大额转复核）(`POST /api/admin/claims/<id>/review`, `decision="approve"`) | `dept_manager`（部门经理） | `claim.status == "SUBMITTED"` 且 `reviewer.role == "dept_manager"` 且 **`claim.amount > 5000`** | `MANAGER_OK` | 角色或状态不符抛 `PermissionError("当前状态或角色无权执行该审批动作")`；保持 `SUBMITTED` | `[Observed-Code: server.py:56-60, 64]` |
| `MANAGER_OK` | 二级审批通过 (`POST /api/admin/claims/<id>/review`, `decision="approve"`) | `cfo`（CFO） | `claim.status == "MANAGER_OK"` 且 `reviewer.role == "cfo"` | `APPROVED` | 角色或状态不符抛 `PermissionError("当前状态或角色无权执行该审批动作")`；保持 `MANAGER_OK` | `[Observed-Code: server.py:61-64]` |
| `SUBMITTED` / `MANAGER_OK` *(注：代码未限制当前状态)* | 审批退回补件 (`POST /api/admin/claims/<id>/review`, `decision="return"`) | 审批人（代码未校验 `reviewer.role`） | `comment.strip() != ""`（必填退回原因） | `NEEDS_RECEIPT` | 原因空白抛 `ValueError("退回补件必须填写退回原因")`；保持原状态 | `[Observed-Code: server.py:51-55]` |
| `DRAFT` / `NEEDS_RECEIPT` | 点击「补充发票并重提」(`data-action="edit"`) | `employee`（单据申请人本人） | 员工补充/修改有效发票号后重新提交 `[Inferred]` | `SUBMITTED` | `server.py` 中尚未实现既有单据更新/重提函数（仅注释提及 `from DRAFT / NEEDS_RECEIPT`） | `[Observed-UI: ui.html:44]`、`[Observed-Code: server.py:7]`、`[Inferred]` |
| `NEEDS_RECEIPT` | 点击「作废删除」(`data-action="delete"`) | `employee`（单据申请人本人） | 员工主动放弃补件并作废单据 `[Inferred]` | `ARCHIVED` | `server.py` 中尚未实现员工手动软删除函数（仅注释提及 `soft-deleted`） | `[Observed-UI: ui.html:44]`、`[Observed-Code: server.py:12]`、`[Inferred]` |
| `NEEDS_RECEIPT` | 夜间定时任务 (`nightly_auto_archive_returned_claims`) | 系统定时任务（每日 `02:00`） | `claim.status == "NEEDS_RECEIPT"` 且 `updated_before < date.today() - timedelta(days=14)`（超 14 天未更新） | `ARCHIVED` | 未满 14 天不处理，保持 `NEEDS_RECEIPT` | `[Observed-Code: server.py:79-84]` |
| `APPROVED` | 财务手工平账 (`POST /api/claims/<id>/force-settle`) | `finance_admin`（财务管理员） | 1. `admin_user.role == "finance_admin"`<br>2. `claim.status == "APPROVED"`<br>3. 传入 `voucher_no` | `PAID` | 非财务管理员抛 `PermissionError("仅财务管理员可执行手工平账")`；非待打款状态抛 `ValueError("仅待打款单据可手工平账")` | `[Observed-Code: server.py:67-76]` |
| `APPROVED` | ERP 打款回调 | 外部 ERP 系统 | ERP 完成付款后异步回调 | `PAID` | 当前代码库未包含回调路由实现 | `[Observed-Code: server.py:11]`、`[Unobserved]` |

---

## 2. 功能拆解（Function Breakdown — `4.x.x` 结构）

### 2.1 报销单列表查询与行级操作（撤回／退回处理）

1. **业务说明（Business Description）：**
   - 普通员工进入 `/app/claims` 查看名下报销单列表，可通过顶部状态筛选器按状态过滤单据，并根据单据当前状态在行尾执行「撤回」（针对待审批单据）或「补充发票并重提」「作废删除」（针对退回补件单据）。
2. **界面区域与字段／控件清单（Interface & Field Inventory）：**
   - **页面包含 3 个主区域：** 顶部导航栏（`header`）、筛选与全局工具栏（`section.filters`）、报销单数据表格（`table.claim-list`）。

| 区域 | 字段／控件名称 | 控件类型 | 必填 | 默认值／数据来源 | 校验与边界规则 | 可见性／可编辑性 | 证据来源 |
|---|---|---|---|---|---|---|---|
| 顶部导航栏 | 当前角色标识 (`.user-role`) | 静态文本 | — | 当前登录会话 (`普通员工 (employee)`) | 只读展示 | 全局可见 | `[Observed-UI: ui.html:7]` |
| 顶部导航栏 | 模块导航 (`nav a`) | 链接组 | — | `我的报销单` (`/app/claims`, 默认激活)、`发票夹` (`/app/invoices`)、`报销标准说明` (`/app/policies`) | 点击切换页面 | 员工可见 | `[Observed-UI: ui.html:8-12]` |
| 筛选与工具栏 | 状态筛选 (`status_filter`) | `Select` 下拉框 | 否 | 默认选中 `""`（全部）；选项：`全部("")`、`草稿(DRAFT)`、`待审批(SUBMITTED)`、`退回补件(NEEDS_RECEIPT)`、`待打款(APPROVED)`、`已打款(PAID)`、`已归档(ARCHIVED)` | 缺失 `MANAGER_OK` 枚举选项 | 员工可切换筛选 | `[Observed-UI: ui.html:17-27]`、`[Observed-Code: server.py:8]` |
| 筛选与工具栏 | 新建报销单 (`#btn-new-claim`) | `Button` | — | — | 点击唤起新建弹窗 `#modal-new-claim` | 员工可见可用 | `[Observed-UI: ui.html:28]` |
| 筛选与工具栏 | 导出 PDF (`#btn-export-pdf`) | `Button` | — | — | **前端死按钮：** 绑定 `onclick="return false;"`，未接后端接口 | 界面可见，点击无效 | `[Observed-UI: ui.html:29-30]` |
| 报销单表格 | 报销单号 (`tr[data-id]`) | 表格列（文本） | — | 系统生成，格式如 `CLM-202611-001` | 唯一标识单据 | 列表只读展示 | `[Observed-UI: ui.html:35, 38-39]` |
| 报销单表格 | 费用类型 | 表格列（文本） | — | 单据 `category` 字段（如 `差旅住宿`、`市内交通`） | 枚举范围：`差旅住宿`、`市内交通`、`业务招待` | 列表只读展示 | `[Observed-UI: ui.html:35, 39, 43]`、`[Observed-Code: server.py:15]` |
| 报销单表格 | 发生日期 | 表格列（日期） | — | 单据 `expense_date` 字段（`YYYY-MM-DD`） | — | 列表只读展示 | `[Observed-UI: ui.html:35, 39, 43]` |
| 报销单表格 | 报销金额(元) | 表格列（金额） | — | 单据 `amount` 字段（千分位保留两位小数，如 `1,280.00`） | — | 列表只读展示 | `[Observed-UI: ui.html:35, 39, 43]` |
| 报销单表格 | 当前状态 | 表格列（文本） | — | 状态中文映射（如 `待审批`、`退回补件`） | — | 列表只读展示 | `[Observed-UI: ui.html:35, 39, 43]` |
| 报销单表格 | 撤回 (`button[data-action="withdraw"]`) | 行操作按钮 | — | 调 `POST /api/claims/<id>/withdraw` | 仅本人单据且状态为 `SUBMITTED` 或 `MANAGER_OK` 可撤回 | `待审批` 行可见 | `[Observed-UI: ui.html:40]`、`[Observed-Code: server.py:37-45]` |
| 报销单表格 | 补充发票并重提 (`button[data-action="edit"]`) | 行操作按钮 | — | 前端操作标识 `edit` | 后端 `server.py` 缺失对应更新/重提路由 | `退回补件` 行可见 | `[Observed-UI: ui.html:44]`、`[Observed-Code: server.py]` |
| 报销单表格 | 作废删除 (`button[data-action="delete"]`) | 行操作按钮 | — | 前端操作标识 `delete` | 后端 `server.py` 缺失对应软删除路由 | `退回补件` 行可见 | `[Observed-UI: ui.html:44]`、`[Observed-Code: server.py]` |

---

### 2.2 新建报销单与提交审批／存为草稿

1. **业务说明（Business Description）：**
   - 员工点击「新建报销单」打开模态框 `<dialog id="modal-new-claim">`，填写费用明细并关联发票后，可选择「存为草稿」（状态置为 `DRAFT`）或「提交审批」（状态置为 `SUBMITTED`），表单提交目标为 `POST /api/claims`。
2. **弹窗表单字段与控件清单（Interface & Field Inventory）：**

| 字段／控件名称 | 字段名 (`name`) | 控件类型 | 必填 | 默认值／占位提示 (`placeholder`) | 校验与边界规则（前端 HTML vs. 后端 `server.py`） | 可见性／可编辑性 | 证据来源 |
|---|---|---|---|---|---|---|---|
| 费用类型 | `category` | `Select` 下拉框 | 是 (`required`) | 默认首项 `差旅住宿`；选项：`差旅住宿`、`市内交通`、`业务招待` | 前后端选项一致（`CATEGORIES = ("差旅住宿", "市内交通", "业务招待")`），但后端 `create_or_submit_claim` 未显式校验 `category in CATEGORIES` | 新建弹窗可编辑 | `[Observed-UI: ui.html:51]`、`[Observed-Code: server.py:15, 18-34]` |
| 发生日期 | `expense_date` | `Input[type="date"]` | 是 (`required`) | 无默认值 | • **前端：** 仅 `required`，无日期范围属性限制<br>• **后端：** `date.fromisoformat(payload["expense_date"])`，校验 `(date.today() - exp_date).days > 90` 时抛 `ValueError("发生日期超过 90 天的费用不可线上报销")`（注：未拦截未来日期 `< 0`） | 新建弹窗可编辑 | `[Observed-UI: ui.html:52]`、`[Observed-Code: server.py:25-27]` |
| 报销金额(元) | `amount` | `Input[type="number"]` | 是 (`required`) | `placeholder="单笔最高 50,000 元"` | • **前端：** `min="0.01" max="50000" step="0.01"`<br>• **后端：** `amount = float(payload.get("amount", 0))`，若 `amount <= 0 or amount > 50000` 抛 `ValueError("报销金额须在 0.01 至 50,000.00 元之间")` | 新建弹窗可编辑 | `[Observed-UI: ui.html:53]`、`[Observed-Code: server.py:22-24]` |
| 关联发票号 | `invoice_no` | `Input[type="text"]` | 前端 `required`；后端仅提审时强制长度 | `placeholder="从发票夹选择或输入 8-20 位发票号"` | • **前端：** `required`（纯文本输入，尚未见发票夹选择器弹窗实现）<br>• **后端长度校验：** 仅当 `submit=True` 时校验 `8 <= len(invoice_no.strip()) <= 20`，不满足抛 `ValueError("提交审批时必须填写 8–20 位有效发票号")`<br>• **后端占用校验：** 无论草稿或提审，均校验 `InvoiceRepo.is_used_by_active_claim(invoice_no)`，若占用抛 `ValueError("该发票号已被其他未归档报销单占用")` | 新建弹窗可编辑 | `[Observed-UI: ui.html:54]`、`[Observed-Code: server.py:28-32]` |
| 事由说明 | `memo` | `Textarea` | 是 (`required`) | 空 | • **前端：** `maxlength="200" required`<br>• **后端：** 直接透传 `**payload` 入库，后端未做非空或 200 字长度复核 | 新建弹窗可编辑 | `[Observed-UI: ui.html:55]`、`[Observed-Code: server.py:34]` |
| 存为草稿 | `save_draft` | `Button[type="button"]` | — | — | 调 `create_or_submit_claim(..., submit=False)`，生成状态为 `DRAFT` 的报销单 | 新建弹窗可见 | `[Observed-UI: ui.html:57]`、`[Observed-Code: server.py:18, 33]` |
| 提交审批 | `submit_claim` | `Button[type="submit"]` | — | — | 提交表单至 `POST /api/claims`（`submit=True`），生成状态为 `SUBMITTED` 的报销单 | 新建弹窗可见 | `[Observed-UI: ui.html:50, 58]`、`[Observed-Code: server.py:18, 33]` |
| 取消 | `.close` | `Button[type="button"]` | — | — | 关闭新建报销单弹窗，不保存数据 | 新建弹窗可见 | `[Observed-UI: ui.html:59]` |

---

### 2.3 现状功能规则表（As-Is Functional Rules: `FR-ASIS-*`）

| 规则编号 | 触发时机、角色与前置条件 | 系统校验逻辑与执行顺序 | 状态与数据变更结果 | 界面反馈／异常提示文案 | 证据来源 |
|---|---|---|---|---|---|
| **FR-ASIS-001** | 用户调用 `POST /api/claims` 发起报销单（存为草稿 `submit=False` 或提交审批 `submit=True`） | **按以下严格代码顺序依次校验：**<br>1. 角色校验：`user.role == "employee"`<br>2. 金额范围：`0 < float(amount) <= 50000`<br>3. 发生日期时效：`(date.today() - date.fromisoformat(expense_date)).days <= 90`<br>4. 发票号长度（**仅 `submit=True` 时执行**）：`8 <= len(invoice_no.strip()) <= 20`<br>5. 发票防重占用：`not InvoiceRepo.is_used_by_active_claim(invoice_no)` | • **校验全部通过：** 调用 `ClaimRepo.insert(user_id=user.id, status="SUBMITTED" if submit else "DRAFT", **payload)` 新增单据<br>• **任一校验失败：** 中断执行，不写入数据库 | 按命中的首个异常返回文案：<br>1. `"仅员工可发起报销单"`<br>2. `"报销金额须在 0.01 至 50,000.00 元之间"`<br>3. `"发生日期超过 90 天的费用不可线上报销"`<br>4. `"提交审批时必须填写 8–20 位有效发票号"`<br>5. `"该发票号已被其他未归档报销单占用"` | `[Observed-Code: server.py:18-34]` |
| **FR-ASIS-002** | 普通员工在列表点击「撤回」按钮，调用 `POST /api/claims/<id>/withdraw` | 1. 归属人校验：`claim.user_id == user.id`<br>2. 状态校验：`claim.status in ("SUBMITTED", "MANAGER_OK")` | • **通过：** 将 `claim.status` 更新为 `"DRAFT"` 并保存<br>• **失败：** 保持原状态不变 | • 非本人：`"只能撤回本人的报销单"`<br>• 状态不符：`"仅待审批状态的报销单可撤回"` | `[Observed-UI: ui.html:40]`、`[Observed-Code: server.py:37-45]` |
| **FR-ASIS-003** | 审批人调用 `POST /api/admin/claims/<id>/review` 且传入 `decision="return"`（退回补件） | 1. 校验退回原因非空：`bool(comment.strip())`<br>*(注：当前代码未校验 `claim.status` 与 `reviewer.role`)* | • **通过：** 将 `claim.status` 更新为 `"NEEDS_RECEIPT"` 并保存（代码中未将 `comment` 赋值给 `claim` 属性）<br>• **失败：** 保持原状态不变 | • 原因空白：`"退回补件必须填写退回原因"` | `[Observed-Code: server.py:48-55]` |
| **FR-ASIS-004** | 审批人调用 `POST /api/admin/claims/<id>/review` 且传入 `decision="approve"`（审批通过） | 1. **一级审批分支：** 若 `claim.status == "SUBMITTED"` 且 `reviewer.role == "dept_manager"`，判断 `claim.amount > 5000`<br>2. **二级审批分支：** 若 `claim.status == "MANAGER_OK"` 且 `reviewer.role == "cfo"` | • 一级审批且 `amount <= 5000`：`claim.status = "APPROVED"`<br>• 一级审批且 `amount > 5000`：`claim.status = "MANAGER_OK"`<br>• 二级审批通过：`claim.status = "APPROVED"`<br>• 其他情况：拒绝修改 | 不满足分支条件时抛出 `PermissionError("当前状态或角色无权执行该审批动作")` | `[Observed-Code: server.py:56-64]` |
| **FR-ASIS-005** | 每日凌晨 `02:00` 触发定时任务 `nightly_auto_archive_returned_claims()` | 查找所有满足 `status == "NEEDS_RECEIPT"` 且最后更新时间早于 `date.today() - timedelta(days=14)`（即超过 14 天未处理）的报销单 | 批量将命中单据的 `claim.status` 更新为 `"ARCHIVED"`（终态）并保存 | 后台静默执行，员工端单据状态变为“已归档” | `[Observed-Code: server.py:79-84]` |
| **FR-ASIS-006** | 财务管理员调用 `POST /api/claims/<id>/force-settle` 执行手工平账 | 1. 角色校验：`admin_user.role == "finance_admin"`<br>2. 状态校验：`claim.status == "APPROVED"` | • **通过：** 将 `claim.status` 置为 `"PAID"`，记录 `claim.voucher_no = voucher_no` 并保存<br>• **失败：** 保持原状态不变 | • 非财务管理员：`"仅财务管理员可执行手工平账"`<br>• 状态不符：`"仅待打款单据可手工平账"` | `[Observed-Code: server.py:67-76]` |

---

## 3. 界面与代码冲突及待决问题清单（Discrepancies & Open Questions: `OQ-*`）

以下问题直接影响改版 PRD 的状态机严密性、字段校验规则与前后端接口契约，建议在进入 `saan-prd-writing` 编写目标规格前向业务／财务及研发确认：

| 问题编号 | 问题分类 | 现状事实与冲突描述（UI vs. Code） | 需向业务／财务／研发确认的决策点 | 证据来源 |
|---|---|---|---|---|
| **OQ-001** | **状态暴露与筛选一致性** | 后端存在 `2: "MANAGER_OK"`（金额 > 5,000 元时部门经理已审、待 CFO 复核），但员工端 `status_filter` 下拉框无此选项。 | 改版后，员工端是将 `MANAGER_OK` 对外统一映射展示为「待审批」（筛选“待审批”时同时查询 `SUBMITTED` + `MANAGER_OK`），还是在前端新增独立的「复核中／待 CFO 审批」状态展示与筛选项？ | `[Observed-UI: ui.html:18-26]`、`[Observed-Code: server.py:8, 59]` |
| **OQ-002** | **退回补件重提与作废删除的后端闭环** | 员工端在 `NEEDS_RECEIPT`（退回补件）行展示了「补充发票并重提 (`edit`)」和「作废删除 (`delete`)」按钮，且状态枚举注释提到 `from DRAFT / NEEDS_RECEIPT` 与 `soft-deleted`，但 `server.py` 缺失对应接口；同时 `DRAFT`（草稿）状态在列表中也缺少继续编辑／提审／删除入口。 | 1. 补充发票重提时，是否允许修改金额、日期和费用类型，还是仅允许修改 `invoice_no` 和 `memo`？<br>2. 员工点击「作废删除」后，状态是统一置为 `ARCHIVED`（已归档）并立即释放发票号占用，还是新增独立的 `CANCELLED`/`DELETED` 状态？<br>3. `DRAFT` 状态单据的行操作按钮规范是什么？ | `[Observed-UI: ui.html:43-44]`、`[Observed-Code: server.py:6-12, 18-34]` |
| **OQ-003** | **退回原因（`comment`）的持久化与员工端展示** | `review_claim` 在退回补件时强制校验 `if not comment.strip(): raise ValueError(...)`，但代码中**并未将 `comment` 写入 `claim` 对象**（无 `claim.return_comment = comment`），员工端列表也无“退回原因”列或详情查看入口。 | 改版 PRD 是否需要在 `Claim` 模型中正式持久化退回原因、退回人及退回时间，并在员工端列表或编辑弹窗顶部显著展示退回原因？ | `[Observed-UI: ui.html:35-46]`、`[Observed-Code: server.py:51-55]` |
| **OQ-004** | **审批退回（`return`）的权限与状态守卫漏洞** | 在 `review_claim` 中，`if decision == "return":` 分支位于角色与状态判断之前，未校验 `reviewer.role in ("dept_manager", "cfo")` 及 `claim.status in ("SUBMITTED", "MANAGER_OK")`。理论上已打款（`PAID`）或已归档（`ARCHIVED`）单据被调用 `return` 也会被改写为 `NEEDS_RECEIPT`。 | 确认是否为代码缺陷：改版时是否应严格限制仅 `dept_manager` 可退回 `SUBMITTED` 单据、仅 `cfo` 可退回 `MANAGER_OK` 单据？ | `[Observed-Code: server.py:48-64]` |
| **OQ-005** | **草稿保存时的必填项与发票占用策略** | 前端表单对所有字段（含 `invoice_no`）均加了 HTML `required`；后端 `create_or_submit_claim` 虽仅在 `submit=True` 时校验发票号 8–20 位长度，但在 `submit=False`（存草稿）时依然强制校验金额、90 天时效及 `InvoiceRepo.is_used_by_active_claim(invoice_no)`（若传空字符串 `""` 可能引发空发票号互相占用）。 | 1. 「存为草稿」是否允许不填发票号或暂存不完整信息？<br>2. 若草稿未填发票号，后端应跳过 `InvoiceRepo.is_used_by_active_claim` 校验，还是仅在填写了非空发票号时校验占用？<br>3. 发生日期是否需补充“不得晚于当天（禁止未来日期）”的前后端双重校验？ | `[Observed-UI: ui.html:51-58]`、`[Observed-Code: server.py:22-34]` |
| **OQ-006** | **「导出 PDF」占位按钮去留** | 员工端列表工具栏存在 `#btn-export-pdf`（导出 PDF），注释标明未接后端接口且 `onclick="return false;"`。 | 本次改版是将其从界面移除，还是需要补齐报销单 PDF 导出能力（导出单张打印贴票单还是列表汇总）？ | `[Observed-UI: ui.html:29-30]` |

---

## 4. 下一步交接建议（Handoff to `saan-prd-writing`）
- 本份 **Pass 2 现状规格说明**已按 `saan-prd-writing` 的状态生命周期表、字段字典与功能规则表结构对齐。
- 你可以直接回复上述 **`OQ-001` ～ `OQ-006`** 的业务拍板结论（或先按默认推荐方案推进），即可无缝交接 `saan-prd-writing` 生成本次“我的报销单”模块改版 PRD（`change` 或 `specification` 模式）。
