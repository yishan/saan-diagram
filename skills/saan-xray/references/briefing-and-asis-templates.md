# Briefing and As-Is Specification Templates

Use **Template 1 (Pass 1: System Overview Briefing)** by default so the user can grasp the whole system in a few minutes. Use **Template 2 (Pass 2: As-Is Module Specification)** when the user asks to drill into a specific module, flow, or screen, or when preparing a baseline for `saan-prd-writing`.

Follow the user's requested language (or the language of the request). Both English and Chinese structures are provided below.

---

## Template 1 — Pass 1: System Overview Briefing (English)

```markdown
# [System / Project Name] — System Overview Briefing

## 1. System Identity & Exploration Scope
- **What it does:** [1–2 sentences in plain business language: who uses it, what core problem it solves, and how value is delivered.]
- **Sources inspected:** [e.g., Live UI (`Observe-only` at `<url>`, Role: Employee), Codebase (`src/pages`, `server/models`), 6 screenshots]
- **Safety mode:** [`Observe-only` | `Sandbox / Test-walk`]

## 2. Roles & Entry Points (≤ 4 groups)
| Role / Portal | Entry / Scope | Core Responsibilities | Evidence |
|---|---|---|---|
| [e.g., Employee] | [Web portal `/app`] | [Search availability, submit and cancel own requests] | `[Observed-UI]` |
| [e.g., Approver / Admin] | [Admin console `/admin`] | [Configure resources, review exceptions, view all records] | `[Observed-Code: routes/admin.ts]` |

## 3. Module & Capability Map (`Module → Function`, ≤ 6 modules)
| Module | Core Functions / Screens | One-Line Business Responsibility | Evidence |
|---|---|---|---|
| **[Module 1]** | [Function 1.1, Function 1.2] | [What business job this module owns] | `[Observed-UI]` / `[Observed-Code]` |

## 4. Core User Journeys (Top 2–4 end-to-end flows)
1. **[Journey Name, e.g., Standard Booking & Check-In]:**
   - **Trigger & Actor:** [Who starts it and when]
   - **Flow:** `[Step 1 (Module A)]` → `[Step 2 (Module B)]` → `[Step 3]`
   - **Outcome:** [What record/state changes when it succeeds, and main rejection/cancellation path]
   - **Basis:** `[Observed-UI]` / `[Observed-Code]`

## 5. Core Business Objects & Lifecycles (≤ 5 objects)
| Object | Key Identifying Fields | Confirmed States (`Initial` → ... → `Terminal`) | Key Transitions & Rules | Evidence |
|---|---|---|---|---|
| **[Object Name]** | [ID, owner, time window, status] | `Pending` (initial) → `In Use` → `Completed` (terminal); `Cancelled` / `Released` (terminal) | [e.g., Check-in within window moves `Pending → In Use`; no-show after 15m moves `Pending → Released`] | `[Observed-UI]`, `[Observed-Code: jobs/release.py]` |

## 6. UI vs. Code Discrepancies & Notable Findings
- **[Discrepancy / Finding 1]:** [e.g., Filter dropdown includes `Pending Approval`, but no approval route or handler is active in current config (`[Observed-UI]` vs. `[Observed-Code]`).]
- **[Terminology Mapping]:** [e.g., UI label "Released" = API status `EXPIRED` = DB `status: 4`.]

## 7. Coverage Boundary & Blind Spots (`[Inferred]` / `[Unobserved]`)
- **`[Inferred]`:** [Rules deduced from clues that still need confirmation, and how to verify them.]
- **`[Unobserved]`:** [Portals, roles, external callbacks, or offline rules not reachable in this pass.]
- **Suggested next step:** [Drill into Module X (`Pass 2`), render a flow/state diagram (`saan-diagram` / `saan-mermaid`), draft a change PRD (`saan-prd-writing`), or verify blind spots with stakeholders (`saan-discovery`).]
```

---

## Template 1 — Pass 1：系统概览简报（中文）

```markdown
# [系统／项目名称] — 系统概览简报

## 1. 系统定性与透视范围
- **核心定位：** [用 1–2 句业务语言说明：给谁用、解决什么核心业务问题、关键运转闭环是什么。]
- **透视依据：** [例如：测试环境界面走查（`Observe-only`，角色：普通员工）、代码库（`src/pages`、`server/models`）、截图 X 张]
- **探索安全模式：** [`Observe-only`（只读漫游） | `Sandbox / Test-walk`（测试环境实测）]

## 2. 角色与入口视图（≤ 4 类）
| 角色／端 | 入口与数据范围 | 核心职责与可见操作 | 证据来源 |
|---|---|---|---|
| [如：预订人（全员）] | [工作台 `/booking`] | [按条件查询空闲资源、发起预订、签到、取消本人预订] | `[Observed-UI]` |
| [如：行政管理员] | [管理后台 `/admin`] | [维护空间档案、查看全量预订、强制释放异常占用] | `[Observed-Code: routes/admin.ts]` |

## 3. 模块与功能地图（按 `模块 → 功能` 组织，≤ 6 个模块）
| 业务模块 | 下属核心功能／页面 | 一句话业务职责 | 证据来源 |
|---|---|---|---|
| **[模块一]** | [功能 1.1、功能 1.2] | [该模块负责的业务目标与边界] | `[Observed-UI]` / `[Observed-Code]` |

## 4. 核心业务主线（2–4 条端到端主流程）
1. **[主线名称，如：常规预订与签到履约]**
   - **触发与角色：** [谁在什么场景下发起]
   - **流转路径：** `[步骤 1（模块 A）]` → `[步骤 2（模块 B）]` → `[步骤 3]`
   - **业务结果：** [成功后的对象状态变化，以及主要异常/取消分支]
   - **证据等级：** `[Observed-UI]` / `[Observed-Code]`

## 5. 核心业务对象与生命周期（≤ 5 个对象）
| 业务对象 | 关键业务标识与字段 | 已确认状态（标明初始态与终态） | 关键流转条件与规则 | 证据来源 |
|---|---|---|---|---|
| **[对象名称]** | [单号、申请人、资源、时间段、状态] | `待使用`（初始态）→ `使用中` → `已结束`（终态）；`已取消`／`已释放`（终态） | [如：开始前 15 分钟至开始后 15 分钟内签到转为`使用中`；逾时未签到自动转为`已释放`] | `[Observed-UI]`、`[Observed-Code: jobs/release.py]` |

## 6. 界面与代码差异及关键发现
- **[差异／发现 1]：** [如：界面筛选器存在“待审批”选项，但代码路由中审批分支已被注释或未启用（`[Observed-UI]` vs. `[Observed-Code]`）。]
- **[术语与枚举映射]：** [如：界面文案“已释放” = 接口字段 `EXPIRED` = 数据库存储值 `4`。]

## 7. 覆盖边界与待确认盲区（`[Inferred]` / `[Unobserved]`）
- **`[Inferred]`（合理推断，待核实）：** [由界面线索或局部命名推断出的规则及核实方式。]
- **`[Unobserved]`（未覆盖盲区）：** [本次未登录的角色视角、跨系统回调或线下制度约束。]
- **建议下一步：** [按需下钻某模块的现状规格（Pass 2）、交接 `saan-diagram` / `saan-mermaid` 出图、交接 `saan-prd-writing` 编写改版需求，或交接 `saan-discovery` 向业务方核实盲区。]
```

---

## Template 2 — Pass 2: As-Is Module Specification (Aligned with `saan-prd-writing`)

Use this structure when drilling into a specific module or feature so it can drop directly into `saan-prd-writing` (`specification` or `change` template):

```markdown
# [Module Name] — As-Is Module Specification

## 1. Module Responsibility & Object Lifecycle
- **Scope & Roles:** [Which roles use this module, entry URL/navigation path, and data visibility scope.]
- **Centralized State Lifecycle (when applicable):**
  - **States:** [List all confirmed states, marking `Initial` and `Terminal` states, plus UI label ↔ code enum mapping.]
  - **Transition Table:**

| Current State | Trigger / Action | Actor | Preconditions / Validation | Target State | On Failure / Rejection | Evidence |
|---|---|---|---|---|---|---|
| `Pending` | Check in | Requester | Current time within `[start - 15m, start + 15m]` | `In Use` | Reject with message; preserve `Pending` | `[Observed-Code]` |

## 2. Function Breakdown (`4.x.x` structure)

### 2.1 [Function Name]
1. **Business Description:** [Trigger, actor, main path, and observed branches.]
2. **Interface & Field Inventory:**
   - **Regions & Controls:** [List filters, table columns, form fields, and action buttons per state.]

| Field / Control | Type | Required | Default / Source | Validation & Boundary Rules | Visibility / Editability | Evidence |
|---|---|---|---|---|---|---|
| [Field name] | [Input/Select/...] | [Yes/No] | [Default or upstream source] | [Exact rule and observed error message] | [Which roles/states can see or edit] | `[Observed-UI]` / `[Observed-Code]` |

3. **As-Is Functional Rules (`FR-ASIS-*`):**

| ID | Trigger, Role & Condition | System Check / Calculation | State / Data Effect | Visible Feedback / Navigation | Evidence |
|---|---|---|---|---|---|
| FR-ASIS-001 | [Role + action] | [Validation order & rule] | [Record created/updated or preserved on failure] | [Toast/inline error/redirect] | `[Observed-UI]` |

4. **Discrepancies & Open Questions (`OQ-*`):**
   - [List any UI vs. code conflicts, unspecified validation priorities, or `[Inferred]` / `[Unobserved]` behaviors that must be confirmed before modifying this module.]
```
