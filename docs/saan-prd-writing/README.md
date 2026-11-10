# Saan PRD Writing

**English** | [简体中文](README.zh-CN.md)

Turn briefs, research notes, existing specifications, and prototypes into PRDs for product, design, engineering, and test review. Write either a complete requirements specification or a scoped change within an existing project.

`SKILL.md` is the canonical English instruction entry point. The [introduction](https://kits.yishan.app/prd-writing/) includes English and Chinese and initially follows the browser language. Top-right controls switch language and choose system, light, or dark appearance. Manual choices are remembered in the current browser. Actual interaction and deliverables follow the requested language, falling back to the request language.

Skill version: **1.0.0**.

## Installation

Install just Saan PRD Writing from Saan Kits:

```bash
npx skills add yishan/saankits --skill saan-prd-writing
```

Installation is project-level by default. For manual installation, copy the complete `skills/saan-prd-writing/` directory into your agent's skills directory. Templates, references, and the worked example travel with the skill. Other Saan skills are optional.

## Usage

Complete specification:

```text
Use saan-prd-writing to turn these briefs, review notes, and prototypes into an English requirements specification.
Preserve the domain terms and cover project context, system boundaries, functional details, quality requirements, and design constraints.
Deliver a draft now, list open decisions, and include acceptance scenarios traceable to confirmed rules.
```

Scoped change:

```text
Use saan-prd-writing to specify bulk archiving on the purchase-request list.
Document conditions, fields, state changes, cancellation and failure outcomes, and references to the project baseline.
Keep the unknown batch limit and processing-failure behavior as open decisions.
```

Revision:

```text
Use saan-prd-writing to incorporate these review decisions into the existing PRD.
Preserve its structure and unrelated content. Update affected rules, interface descriptions, fields, and acceptance scenarios.
Record explicitly superseded rules as revisions rather than leaving both versions active.
```

You can start with incomplete materials. Scope, readers, and explicit source precedence help control the result. Output follows the requested language, falling back to the language of the request.

## Output organization

| Level | Organization |
|---|---|
| Full document | Document control and revisions → introduction → project overview → system overview → functional requirements → nonfunctional requirements → design constraints |
| Function detail | Module responsibility and flow → business description → interface design → business fields → functional constraints; other information only when needed |
| Rule | Condition/trigger → validation and processing → data/state result → feedback or exception |
| Delivery review | Acceptance scenarios derived from confirmed rules; conflicts and gaps recorded as open decisions |

A small change uses the compact form. Field tables retain five core columns: name, type, length/format, requiredness, and notes. Business fields do not automatically define a physical database schema.

Diagrams explain system boundaries, business flow, or interaction sequence. Their roles, fields, and states should agree with prototypes, tables, and rules. Without visual design, structure and interaction descriptions remain design inputs.

## Templates and examples

| Resource | English | 中文 |
|---|---|---|
| Complete requirements specification | [Full template](../../skills/saan-prd-writing/templates/specification.en.md) | [完整模板](../../skills/saan-prd-writing/templates/specification.zh-CN.md) |
| Scoped change | [Change template](../../skills/saan-prd-writing/templates/change.en.md) | [变更模板](../../skills/saan-prd-writing/templates/change.zh-CN.md) |

- [Bulk archive input](../../skills/saan-prd-writing/examples/bulk-archive/input.zh-CN.md) → [worked specification](../../skills/saan-prd-writing/examples/bulk-archive/prd.zh-CN.md): a fictional compact example in Chinese, bundled with the skill.
- [New room-booking request](../../tests/saan-prd-writing/fixtures/room-booking/request.md) → [independent output](../../tests/saan-prd-writing/results/2026-11-04/room-booking/prd.md): a full-specification evaluation kept in repository tests, not used as a default input.
- The [validation record](validation.zh-CN.md) documents executed checks, findings, and limitations.

## Evidence and decisions

Keep confirmed requirements, historical behavior, discussion options, and unresolved conflicts distinct. A new draft does not inherit source-template approval, signatures, performance values, security levels, architecture, or service commitments.

For example, rejecting an entire batch when validation fails does not establish rollback behavior for a processing error. Missing behavior remains a separate question. Proposed wording, defaults, and technical choices must remain distinguishable in interface and acceptance tables as well as rule prose.

A full document assesses performance, stability, security, extensibility, operating environment, and other quality needs. Missing evidence calls for a specific question; it does not establish non-applicability.

## Method and source boundaries

The approved synthesis combines the organization of a requirements-specification template with the concrete object/action, condition, state, and data-flow conventions observed in six Axure projects. Acceptance mapping, lightweight source trace, and explicit open decisions are additional quality practices.

The original template's sixth chapter appeared only in its contents. This skill supplies writing prompts for design constraints without claiming to recover missing project rules. Private files, URLs, and detailed business extracts are excluded from the package. Bundled examples use fictional data.

## Dependencies and limits

- Core writing is text-only, with no external service or executable runtime dependency.
- Reading `.rp` files requires a reliable parser or accessible exports in the environment. This package does not include a general Axure parser or guarantee direct support for every `.rp` version.
- Screenshots establish visible content. String extraction may contain hidden or historical text. Partial reading does not establish full prototype coverage or production behavior.
- Discovery and diagram skills can help when available, but are not mandatory.
- Word/PDF formatting, Feishu access, and publication require suitable tools and task authorization. The default artifact is editable Markdown; this skill does not automatically change external systems.
- Written requirements, document checks, implementation, and business acceptance remain separate outcomes.

## Package

```text
saan-prd-writing/
  SKILL.md
  agents/openai.yaml
  references/source-handling.md
  templates/specification.zh-CN.md
  templates/specification.en.md
  templates/change.zh-CN.md
  templates/change.en.md
  examples/bulk-archive/input.zh-CN.md
  examples/bulk-archive/prd.zh-CN.md
```

## Changes

### v1.0.1

- Clarified that when multiple validations can fail on the same action and their order affects user-visible feedback or return state, an unspecified order should be recorded as an open decision rather than invented downstream.

### v1.0.0

- Initial release with full specification and scoped change templates in English and Chinese, source and uncertainty handling, and the bulk-archive worked example.

Back to [Saan Kits](../../README.md).

[Language and appearance validation](../site-preferences-validation.zh-CN.md)
