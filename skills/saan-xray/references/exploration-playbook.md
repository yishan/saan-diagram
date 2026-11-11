# Exploration Playbook: Live UI, Codebase, and Hybrid X-Ray

Use this playbook to gather high-signal product and business facts without getting lost in framework noise or triggering unsafe actions in a live system.

---

## 1. Live System Exploration (Browser / Computer Use)

### 1.1 Establish the Safety Boundary First
Before clicking through any live application:
1. Check the URL, environment indicator, and logged-in identity.
2. Default to **`Observe-only`** unless the user explicitly states that the target is a disposable sandbox/test environment and authorizes **`Sandbox / Test-walk`**.

| Action type | `Observe-only` (Default) | `Sandbox / Test-walk` (Explicit Opt-in) |
|---|---|---|
| Top/side navigation, tabs, breadcrumbs | Allowed | Allowed |
| Search, filter dropdowns, sorting, pagination | Allowed | Allowed |
| Opening detail views, read-only drawers/modals | Allowed | Allowed |
| Opening "New / Edit" modal to inspect fields, then clicking **Cancel / Close** | Allowed (do not submit) | Allowed |
| Submitting forms with empty/boundary values to read validation errors | **Blocked** (unless pure client-side & non-submitting) | Allowed with `XRAY-TEST-*` data |
| Creating, editing, or transitioning test records | **Blocked** | Allowed on `XRAY-TEST-*` records only |
| Destructive, financial, or external actions (`Deleteexisting`, `Pay`, `Send email/SMS`, `Publish`) | **Blocked** | **Blocked** without per-action user confirmation |

### 1.2 4-Step UI Walk Sequence
1. **Shell & Navigation Pass:**
   - Record the global layout: portal switcher, role badge, top/side navigation items, notification center, and settings entry.
   - Group navigation items into business modules (`Module → Function`).
2. **List & Filter Pass (High-Signal Shortcut):**
   - List pages reveal the domain model fast:
     - **Status tabs / filter dropdowns** expose the object's state enum (e.g., *Draft, Pending Approval, In Use, Released, Cancelled*).
     - **Table columns** expose primary business attributes and identifiers.
     - **Row-level actions** expose which operations are allowed in each status.
3. **Detail & Form Pass:**
   - Open 1–2 representative detail views to see status timelines, sub-tables (child entities), and audit logs.
   - Open the creation/action form (and cancel in `Observe-only` mode) to record field labels, input controls, required markers (`*`), default values, helper text, and unit/format hints.
4. **Role & State Comparison (When Multiple Accounts or Sandbox Are Available):**
   - Compare what changes across roles (hidden menu items, disabled buttons, masked columns, data scope filters).
   - In `Sandbox / Test-walk` mode, walk one test record from creation to completion/cancellation and record the exact state transitions and validation messages.

---

## 2. Codebase & API Exploration

When reading a repository, avoid reading every file linearly. Follow a **top-down business extraction order**:

### 2.1 High-Signal Entry Points (Read First)
1. **Routes & Navigation Config:**
   - Frontend router (`routes.*`, `app/`, `pages/`, menu config) → maps directly to user-facing modules and screens.
   - Backend API router (`urls.py`, `routes/`, OpenAPI/GraphQL schema, controller annotations) → maps to actions and resources.
2. **Domain Models, Schemas & Enums:**
   - Database schemas, ORM models, Prisma/SQL migrations, TypeScript/Pydantic types, and status enums → reveals core business objects, relationships, and all possible states (including states rarely seen in the UI).
3. **State Transitions, Validators & Permission Guards:**
   - Service/use-case methods, state machine definitions, form validation schemas (`zod`, `yup`, backend validators), and RBAC/permission middleware → reveals the exact conditions, validation priorities, and rejection rules.
4. **Background Jobs & External Integrations:**
   - Cron jobs, queue workers, webhooks, and third-party clients → reveals invisible business rules (e.g., *"auto-release unconfirmed bookings after 15 minutes"*) that black-box UI exploration cannot see.

### 2.2 What to Ignore During Pass 1
- Build toolchains, CSS styling utilities, generic UI primitives (`Button`, `Modal`), boilerplate state plumbing, and third-party vendor bundles—unless they contain hardcoded business rules.

---

## 3. Hybrid Cross-Check (UI + Code Together)

When both a running system (or screenshots) and the codebase are available, cross-check them to find high-value insights:

1. **Map UI Terms to Code Identifiers:**
   - Record a compact glossary when names diverge (e.g., UI says *"Released / 已释放"*, API returns `EXPIRED`, DB column is `status = 4`).
2. **Spot Discrepancies Explicitly:**
   - **Code-only (Hidden/Unreleased/Legacy):** A route, status enum, or validation rule exists in code, but no active UI entry triggers it.
   - **UI-only (Stub/Mock/Broken):** A button, filter, or tab renders in the UI, but its handler is empty, mocked, or unconnected.
   - **Rule Mismatch:** Frontend form hint says *"up to 4 hours"*, while backend validator allows up to 240 minutes or checks a different condition.
3. **Fill UI Blind Spots from Code:**
   - Use backend jobs and permission guards to answer questions the UI walk left as `[Inferred]` (such as exact timeout thresholds, validation execution order, or admin-only actions), upgrading their tag to `[Observed-Code]`.
