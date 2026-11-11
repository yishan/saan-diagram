---
name: saan-xray
description: Walk through an existing live system (via browser or Computer Use), codebase, or UI screenshots to produce an easy-to-read System Overview Briefing and on-demand As-Is module specifications (系统摸底、存量系统梳理、代码逆向业务说明、项目全景简报、现状规格提取). Use when onboarding to an unfamiliar project, reverse-engineering an undocumented product before a redesign or migration, or auditing how UI and code actually behave. For customer research and interview guides, prefer saan-discovery; for writing target To-Be requirements, prefer saan-prd-writing.
metadata:
  author: Yishan
  version: "0.1.0"
---

# Saan X-Ray

Help the user quickly understand what an existing system or project actually does today—who uses it, how its modules and journeys fit together, what business objects and states it manages, and what remains unseen—before drilling into detailed As-Is module specifications. Follow the requested output language, otherwise the language of the request.

## Start with scope, evidence sources, and safety mode

Identify which sources are available before exploring:

- **Live system (browser or Computer Use):** URL or window, current account/role, and environment (production, staging, local).
- **Static visuals:** Screenshots, screen recordings, or existing prototypes.
- **Codebase or API:** Routes, views/pages, domain models, state enums, permissions, background jobs, and API schemas.

When operating a live system through a browser or Computer Use tool, enforce an explicit **Safety Mode**:

1. **`Observe-only` (default):** Navigate menus, tabs, list views, filters, search, detail pages, and read-only modals/drawers. Open "Create" or "Edit" forms only to read fields and defaults, then cancel/close. **Never click mutating or external-effect actions** (`Save`, `Submit`, `Delete`, `Approve`, `Reject`, `Pay`, `Send`, `Reset`, `Publish`, or bulk actions) unless the user explicitly authorizes sandbox testing.
2. **`Sandbox / Test-walk` (requires explicit user confirmation of a test environment or test account):** Permitted to create clearly prefixed test records (e.g., `XRAY-TEST-*`), submit empty/boundary inputs to observe validation messages, and walk status transitions. Stop immediately if an action reaches a real payment, external notification, or destructive confirmation gate.

Read [Exploration playbook](references/exploration-playbook.md) when planning a UI walk, codebase pass, or hybrid cross-check.

## Deliver in two progressive passes

Do not dump raw file trees, framework boilerplate, or a 50-page specification on the first turn. Default to **Pass 1 (System Overview Briefing)** so the user gets a clear mental model in minutes, then expand into **Pass 2 (As-Is Module Specification or Handoffs)** on request.

| Pass | Default scope & budget | Read |
|---|---|---|
| **Pass 1: System Overview Briefing** *(default first output)* | Concise product-language briefing: 1-paragraph identity, ≤4 role groups, ≤6 top-level modules (`Module → Function`), 2–4 core user journeys, ≤5 core business objects with lifecycles, UI/code discrepancies, and blind spots | [Briefing and As-Is templates](references/briefing-and-asis-templates.md) |
| **Pass 2: As-Is Module Deep Dive** *(when requested or scoped to one feature)* | Screen regions, field inventory (type, required, default/source, validation), explicit state transition table (`current state × trigger/actor/condition → target state`), permissions, and open questions aligned with `saan-prd-writing` | [Briefing and As-Is templates](references/briefing-and-asis-templates.md), [Exploration playbook](references/exploration-playbook.md) |

If the user explicitly asks to inspect only one screen, one flow, or one module from the start, deliver a focused Pass 2 breakdown for that scope plus a brief context header.

## Translate implementation into business behavior

Whether reading UI or code, express findings in **user, business, and domain terms** rather than framework mechanics:

- **Organize by `Module → Function`, not directory trees.** Group routes, components, and controllers into the business capabilities users recognize. Keep file paths or route URLs as compact evidence citations rather than section headings.
- **Trace end-to-end journeys.** Connect the trigger, actor, sequence of screens/actions, and resulting record or state change across modules.
- **Extract explicit state lifecycles.** Identify each core business object's confirmed states (marking initial and terminal states) and observed transitions (`current state × trigger/actor/condition → target state`), including which actions are hidden or disabled in each state.
- **Surface UI vs. code discrepancies.** When combining live UI/screenshots with code, explicitly flag:
  - **Hidden or gated capabilities:** Routes, fields, or actions present in code but absent or disabled in the UI (e.g., behind feature flags, role checks, or unlinked pages).
  - **Dead or stubbed UI:** Buttons, filters, or tabs visible in the interface that call no backend logic or hardcode mock responses.
  - **Terminology drift:** Where UI labels, API field names, and database enums use different names for the same concept (record the mapping so downstream PRDs stay unambiguous).

## Keep evidence status explicit

Never invent business rules, validation order, background timers, or permission boundaries to make the system look complete. Tag nontrivial claims with their evidence basis:

- **`[Observed-UI]`:** Directly seen on a live screen, DOM state, network response during a walk, or supplied screenshot (cite page/route or screenshot name).
- **`[Observed-Code]`:** Directly verified in route definitions, components, domain models, validators, or tests (cite `path:line` or symbol).
- **`[Inferred]`:** Deduced from partial clues—such as status values in a filter dropdown that were never triggered, or a field name suggesting a rule—requiring confirmation.
- **`[Unobserved]`:** Outside the current account's permissions, hidden in an unvisited service, or dependent on offline/human processes.

When UI and code disagree, report both rather than silently choosing one.

## Connect cleanly to downstream skills

At the end of an Overview Briefing or Module Deep Dive, offer the most useful next step based on the user's goal:

- **To plan a redesign, v2, or scoped feature change (`saan-prd-writing`):** Hand off the As-Is module breakdown, object state lifecycle, terminology mapping, and `[Inferred]` / `[Unobserved]` open decisions as the baseline for a `change` or `specification` document.
- **To visualize architecture, swimlanes, data models, or state machines (`saan-diagram` / `saan-mermaid`):** Turn the module map, cross-role flow, entity relationships, or state lifecycle into a diagram spec or Mermaid chart. Keep `[Inferred]` paths distinct from confirmed flows.
- **To resolve business blind spots (`saan-discovery`):** Convert `[Inferred]` and `[Unobserved]` items (e.g., unknown policy thresholds, offline approvals, unvisited roles) into targeted stakeholder questions.
- **To build an interactive review baseline (`saan-prototype`):** Use the extracted screens, role switches, and state transitions to build an offline review prototype.

Peer skills are optional integrations, not required dependencies; `saan-xray` completes its briefing and As-Is specifications independently.
