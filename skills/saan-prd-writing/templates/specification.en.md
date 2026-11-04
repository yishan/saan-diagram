# [Project] — Requirements Specification

Writing guidance: bracketed text is a prompt, not a project fact. Replace prompts before delivery. Move unknown facts or decisions into open questions. Adapt to the user's required format.

## Document control

| Item | Value |
|---|---|
| Document ID | [Project convention] |
| Version | [Version] |
| Status | Draft |
| Author | [Actual author] |
| Updated | [Actual date] |
| Applies to | [System, version, business scope] |

### Revision history

| Date | Version | Changes | Author | Notes |
|---|---|---|---|---|
| [Date] | [Version] | [Affected sections and rules] | [Actual author] | [Impact] |

### Contents

1. Introduction
2. Project overview
3. System overview
4. Functional requirements
5. Nonfunctional requirements
6. Overall design constraints

Add acceptance scenarios, open decisions, and review records as needed. Update pagination from the final layout when producing a paginated document.

## 1. Introduction

### 1.1 Document scope

[Which project/version and business areas are covered? Which adjacent areas are excluded? Identify primary requirement sources and confirmation status.]

### 1.2 Intended readers

[Actual readers and their tasks: verifying business rules, designing, implementing, or testing.]

### 1.3 Terms and abbreviations

| Term | Abbreviation | Meaning |
|---|---|---|
| [Potentially ambiguous object or state] | [If applicable] | [Project-specific meaning] |

### 1.4 References

| ID | Source | Version / date | Coverage | Location |
|---|---|---|---|---|
| S-01 | [Material actually read] | [Version/date] | [Supported requirements] | [Accessible link/path] |

## 2. Project overview

### 2.1 Background

[Who currently handles what work, by which process? What concrete problem and impact motivate this change?]

### 2.2 Objectives

[Business coverage, intended improvement, and how it will be assessed. Use metrics only with evidence; identify missing baseline, target, or measurement conditions.]

## 3. System overview

### 3.1 Application relationships

[Diagram or concise explanation of user surfaces, application systems, external systems, responsibility boundaries, and the current change. Explain key relationships after any diagram.]

Record databases, middleware, and deployment choices only when confirmed. Do not inherit a gateway, microservices, cache, or queue from an illustration.

### 3.2 Overall business framework

[Business flow or relationship diagram showing role collaboration, object movement, state changes, and scope. This explains business cooperation; section 3.1 explains system boundaries. Avoid two copies of a menu tree.]

### 3.3 Function inventory

| No. | Business area | Module | Function | Purpose | Detail reference |
|---|---|---|---|---|---|
| 1 | [Area] | [Module] | [Function] | [For whom, to do what] | [4.1.1] |

Adjust hierarchy depth to the project. Keep overview rows brief; put validation and exception rules in the detailed functions.

## 4. Functional requirements

### 4.1 [Module]

[Responsibility, roles, inputs/results, and relationships between functions. Add a module flow when it clarifies handoffs or branches.]

### 4.1.1 [Function]

**Business description**

[Role] performs [task] when [trigger/preconditions], producing [business result]. Explain the main flow, then reference branch rules.

**Interface design**

[Prototype/page/callout references and relevant entry points or regions. Without a visual design, describe structure and interaction without claiming visual acceptance.]

| Element / callout | Display requirements | Interaction | Rules |
|---|---|---|---|
| [Control/region] | [Content, position, conditions] | [Action, switch, navigation] | [FR-001] |

Preserve confirmed labels and messages. Describe input retention on selection/mode changes where relevant. Reference field limits and business rules instead of duplicating them.

**Business fields**

| Field name | Data type | Length / format | Required | Notes |
|---|---|---|---|---|
| [Field] | [Known business type] | [Unit, precision, range] | [Yes/no/condition] | [Source, default, dependency, use] |

Add source/default or persistence/display/export columns only if useful. Distinguish inputs, calculations, display values, and operation records. Do not infer a physical database schema.

**Functional constraints**

| ID | Condition / trigger | Validation / processing | Data / state result | Feedback / exception |
|---|---|---|---|---|
| FR-001 | [Role, condition, action] | [Check/calculation] | [Persist, update, transition, or preserve] | [Feedback, navigation, failure result] |

A numbered list may replace a wide table. Keep rules independently referenceable. Cover relevant permissions and data scope, state/label mappings, validation timing, priority, calculations, success, cancellation, errors, empty/unavailable states, bulk semantics, concurrency, and data transfers. Unsupported behaviors remain open questions.

Reference shared security requirements in chapter 5. Put technical or deployment limits in chapter 6. Keep one authoritative statement per rule.

**Other — optional**

[Only supplementary roles, permissions, flow, inputs, outputs, dependencies, or future scope not already covered. Mark future ideas as proposals, not delivery commitments. Omit this subsection if redundant.]

## 5. Nonfunctional requirements

Assess each category as confirmed, unresolved, or justifiably not applicable. Missing evidence is not non-applicability. Example targets are not defaults.

| Section | Consider | Requirement / target | Conditions and verification | Status / source |
|---|---|---|---|---|
| 5.1 Performance | Users, concurrency, throughput, latency, data scale | [Confirmed target] | [Operation, environment, scale, measurement] | [Status/source] |
| 5.2 Stability | Service window, availability, maintenance, recovery | [Confirmed requirement] | [Period, maintenance treatment, failure definition] | [Status/source] |
| 5.3 Security | Permissions, data protection, logs, backups, applicable obligations | [Confirmed requirement] | [Data/system scope, verification] | [Status/source] |
| 5.4 Extensibility | Expected change, capacity growth, interfaces | [Actual change scenario] | [Boundary and conditions] | [Status/source] |
| 5.5 Operating environment | Clients, OS, browsers, network, deployment | [Confirmed environment] | [Compatibility and test environment] | [Status/source] |
| 5.6 Other | Applicable quality needs not covered above | [Specific requirement] | [Verification] | [Status/source] |

Specify response-time start/end and statistic. Distinguish registered users, concurrent users, and requests per second. Align availability and downtime calculations. Tie service duration, upgrades, and supplier obligations to actual confirmed sources.

## 6. Overall design constraints

Record confirmed external limits. Identify missing evidence or decisions without selecting an unsupported technical solution.

| Section | Constraint | Source / version | Design impact | Status |
|---|---|---|---|---|
| 6.1 Standards | [Applicable standard or policy] | [Source/version] | [Affected objects] | [Status] |
| 6.2 Hardware | [Existing equipment/resource limit] | [Source] | [Capacity/compatibility impact] | [Status] |
| 6.3 Technology | [Existing platform, interface, stack/version restriction] | [Source] | [Boundary/dependency] | [Status] |
| 6.4 Other | [Other actual design limitation] | [Source] | [Impact] | [Status] |

## Appendix A. Acceptance scenarios

| Rule IDs | Preconditions / data | Action | Observable result | Verification method |
|---|---|---|---|---|
| [FR/NFR] | [Confirmed conditions] | [Steps] | [Expected behavior] | [UI/data/log/performance check] |

Derive scenarios from confirmed rules; do not introduce a business condition through a test. Unknown behavior belongs in open decisions.

## Appendix B. Open decisions

| ID | Question / conflict | Affected sections / rules | Decision or evidence needed | Owner / status |
|---|---|---|---|---|
| Q-01 | [Specific issue and source] | [References] | [Decision needed] | [Actual owner, otherwise unassigned] |

## Review records — when applicable

| Reviewer group | Feedback | Signature / confirmation record | Date |
|---|---|---|---|
| Project team | [Actual feedback] | [Actual record] | [Date] |
| Requesting department | [Actual feedback] | [Actual record] | [Date] |
| Department lead | [Actual feedback] | [Actual record] | [Date] |

Keep the document in draft until the actual review process changes its status. Blank signature fields or copied release checkboxes do not establish approval.
