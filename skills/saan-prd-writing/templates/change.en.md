# [Feature] — Change Specification

Status: Draft. Version: [version]. Date: [actual date].

Writing guidance: use this form for a scoped change within an existing project. Keep useful sections, replace prompts, and move unresolved conditions into open decisions. Use the [full template](specification.en.md) for a complete specification.

## Background and scope

[Who encounters which problem, in what situation? What changes, for which roles, surfaces, and business objects? Define relevant exclusions.]

Sources: [materials actually read, versions, dates, locations]. Project baseline: [confirmed project rules or documents; identify missing references and their impact].

## [Module]

[Responsibility, main flow, and relationships between functions. Repeat the function unit as needed. A single function does not need a duplicate function inventory. When the change affects a business object's state across functions, define the confirmed state list (initial and terminal states) and transition table or state diagram (`current state × trigger/actor/condition → target state`, plus rejected states and state preservation on failure or cancellation) here so individual rules reference it instead of forming an implicit state machine.]

### [Function]

**Business description**

[Role] performs [task] under [trigger and preconditions] to achieve [business result]. Reference branch rules.

**Interface design**

[Prototype/page references, entry points, interactions, feedback, and rule references. Without visual design, describe structure and interaction only. Label unconfirmed messages as proposed wording.]

| Element | Display / interaction | Rules |
|---|---|---|
| [Element] | [Behavior] | [FR-001] |

**Business fields**

| Field name | Data type | Length / format | Required | Notes |
|---|---|---|---|---|
| [Field] | [Business type] | [Units, precision, range] | [Condition] | [Source, default, persistence, use; reference open questions] |

**Functional constraints**

| ID | Condition / trigger | Processing and data / state result | Feedback / exception |
|---|---|---|---|
| FR-001 | [Who acts in which state and conditions] | [Validation, processing, referenced state transition or state preservation, data effects] | [Feedback or failure result] |

[Add other dependencies, permissions, or inputs/outputs only if not already covered. Do not create a parallel set of repeated rules.]

## Project baseline and relevant impacts

[Affected quality requirements and design constraints; reference the established baseline. Keep missing scale, targets, service commitments, and technology choices unresolved. Do not expand a small change into unrelated categories.]

## Acceptance scenarios

| ID | Rules | Preconditions and action | Observable result |
|---|---|---|---|
| AC-01 | [FR/NFR] | [Conditions, data, action] | [Result derived from confirmed rules] |

## Open decisions

| ID | Question / conflict and source | Impact | Decision / evidence needed |
|---|---|---|---|
| Q-01 | [Specific gap] | [Rule, implementation, or acceptance impact] | [Smallest decision needed] |

Omit an empty table only after checking conditions, failure semantics, data scope, and baseline completeness.
