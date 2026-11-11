# Saan X-Ray

**English** | [简体中文](README.zh-CN.md)

X-ray an existing live system (via browser or Computer Use), codebase, or UI screenshots to produce an easy-to-read **System Overview Briefing** first, then drill into **As-Is module specifications** on demand. The [introduction](https://kits.yishan.app/xray/) includes English and Chinese.

Skill version: **0.1.0**.

## When to use it

Use `saan-xray` when you need to understand what an existing system or project actually does today:

- Onboarding to an unfamiliar codebase or legacy system without up-to-date product documentation.
- Walking through a running web or desktop application (via browser automation or Computer Use) to map its modules, roles, user journeys, and business objects.
- Cross-checking live UI behavior against source code to uncover hidden features, dead UI stubs, or terminology drift before writing a redesign or change PRD.

`saan-discovery` focuses on customer interviews, field research, and product-fit assessment. `saan-prd-writing` writes target To-Be specifications and feature changes. `saan-xray` establishes the **As-Is system baseline** in plain business language and hands off cleanly to both.

## Installation

Install just Saan X-Ray from Saan Kits:

```bash
npx skills add yishan/saankits --skill saan-xray
```

Installation is project-level by default. For manual installation, copy the complete `skills/saan-xray/` directory into your agent's skills directory. The skill itself is text-only and requires no external runtime or other skill; inspecting a live application or repository uses whatever browser, Computer Use, or file-reading tools your agent has available.

The canonical instruction entry point is English. Outputs follow the requested language, otherwise the language of the request.

## How to start

Ask for a quick overview briefing from a codebase, live URL, or screenshots:

```text
Use saan-xray to inspect this repository and give me a System Overview Briefing in plain product language: what it does, roles, module map, core user journeys, business objects and states, and blind spots.
```

Walk a live system safely in read-only mode:

```text
Use saan-xray in Observe-only mode on our staging portal. Walk the main menus and list views without submitting or deleting anything, and summarize the modules, statuses, and key flows.
```

Drill into a specific module for a change PRD baseline:

```text
Now run Pass 2 of saan-xray on the Room Booking module: extract the screen fields, validation rules, state transition table, and UI-vs-code discrepancies so we can feed them into saan-prd-writing.
```

## What to expect

1. **Safety first on live systems:** Defaults to **`Observe-only`** (navigating menus, tabs, list filters, and read-only modals without clicking `Save`, `Submit`, `Delete`, `Approve`, `Pay`, or `Send`). Switches to **`Sandbox / Test-walk`** only when you explicitly confirm a test environment and test account.
2. **Two-pass progressive delivery:**
   - **Pass 1 — System Overview Briefing (default):** A 5-minute product-level briefing covering System Identity, Roles & Portals (≤4), Module & Capability Map (`Module → Function`, ≤6), Top User Journeys (2–4), Core Business Objects & Lifecycles (≤5), UI vs. Code Discrepancies, and Blind Spots.
   - **Pass 2 — As-Is Module Deep Dive (on demand):** Field inventories, validation rules, centralized state transition tables (`current state × trigger/actor/condition → target state`), and open questions structured to drop directly into `saan-prd-writing`.
3. **Explicit evidence tags:** Keeps **`[Observed-UI]`**, **`[Observed-Code]`**, **`[Inferred]`**, and **`[Unobserved]`** distinct so guesses are never presented as confirmed product rules.

See the [exploration playbook](../../skills/saan-xray/references/exploration-playbook.md), [briefing and As-Is templates](../../skills/saan-xray/references/briefing-and-asis-templates.md), [design note](../plans/2026-11-11-saan-xray-design.zh-CN.md), and [validation record](validation.zh-CN.md).

## Package

```text
saan-xray/
  SKILL.md
  agents/openai.yaml
  references/
    exploration-playbook.md
    briefing-and-asis-templates.md
```

Back to [Saan Kits](../../README.md).
