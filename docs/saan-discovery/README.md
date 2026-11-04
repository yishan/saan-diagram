# Saan Discovery

**English** | [简体中文](README.zh-CN.md) · [Saan Kits](../../README.md)

Develop consumer (ToC), enterprise (ToB), public-sector (ToG), or mixed discovery interactively using existing product logic, or directly prepare interview guides and synthesize field evidence.

The user normally conducts the customer interview. This skill prepares questions, synthesizes notes, and routes follow-ups. User-interview methods are bundled internally; there is no separate interview-skill dependency.

The skill instructions and public introduction default to English. A [Chinese introduction](https://kits.yishan.app/discovery/zh/) and this guide's Chinese version are available through explicit language links. Questions, briefs, and other deliverables follow the user's requested language, or the language of the request when none is specified. English instructions do not require English answers.

## Agree the context, then expand by topic

For an open-ended request, read existing material, confirm unresolved research type and scope, suggest a short outline, and develop one topic at a time. Usually ask one main question per turn, update the topic from the answer, and select the next question. Reuse facts and choices already supplied.

| Type | Research emphasis | Output emphasis |
|---|---|---|
| ToC | Personal context, triggers, recent behavior, alternatives, motivation, trust, use or abandonment | User journeys, behavioral differences, friction, unmet needs, opportunity hypotheses |
| ToB/G | Concrete roles, responsibility, business handoffs, applicable approval/rule details, data, systems, implementation constraints | Business-topic notes, workflows and organization differences, fit conditions, unresolved decisions |
| Mixed | The consumer or resident experience and the organization delivering the service | Separate but connected user journeys and organizational processes |

Keep enterprise and public-sector distinctions within ToB/G when they matter. ToG can require service-recipient outcomes, policy sources, and accountability. A state-owned business is not automatically ToG. Consumer journeys may include reviews, and organizational discovery still investigates usability and adoption.

Develop each topic only as evidence arrives. The user can correct, skip, change topics, or request an interim brief. Unknown facts become targeted follow-ups. Confirming an outline or summary does not verify policy, production behavior, or customer acceptance; silence does not confirm anything. An explicit request for a complete guide, direct synthesis, or no more questions overrides the interactive default.

## Workflows

| Stage | Inputs | Outputs |
|---|---|---|
| Prepare | Product material, customer context, participants and available time | Product baseline, role-specific guide, useful evidence requests |
| Synthesize | Notes, transcripts, policies, business records or observed behavior | User journey or business workflow, applicable rules, friction, expectations, sources and conflicts |
| Continue | Existing brief and new evidence | Updated brief, prioritized gaps, suitable respondents and revised fit judgments |

Missing product information does not prevent customer discovery. Product fit remains unverified where the necessary evidence is absent.

## Installation

Install just Saan Discovery from Saan Kits:

```bash
npx skills add yishan/saankits --skill saan-discovery
```

For local development, run `npx skills add . --skill saan-discovery` from a checkout containing the skill. Alternatively, copy the complete `skills/saan-discovery/` directory into your agent's skill directory. The core workflow is text-only and has no Python, Node.js, or service dependency. Installing through the skills CLI requires that CLI's own Node.js environment.

## Example requests

> Use saan-discovery to agree the research type and scope with me, then develop one topic at a time. Ask one main question per turn and keep unknown facts open.

> This is a ToC activity-recommendation product. I want to understand why people save an activity but do not attend. Agree the interview scope with me, then prepare the questions without assuming the person has paid.

> Use saan-discovery to prepare a 30-minute payment-process interview from this product manual and customer context. The operator and project manager will attend. Create an internal preparation brief and a customer-facing guide.

> Use saan-discovery to organize these field notes. Separate actual practice, policy, and desired behavior. Record business execution and approval separately, and identify contradictory or unsupported rules.

> Use saan-discovery to update the existing brief with the administrator's reply. Preserve sources and question IDs, mark resolved items, and propose only the three most consequential follow-ups.

## How questions are selected

Product objects, states, rules, permissions, and data dependencies determine which customer conditions need checking. Customer work outside the product remains part of the research.

Each consequential question connects an information gap to a decision, a suitable respondent, and useful evidence. Prerequisites and business consequences determine order. Factual prompts remain neutral; research choices may include a recommendation.

The bundled [user-interview reference](../../skills/saan-discovery/references/user-interview.md) covers recent-case reconstruction, causes and consequences, role-specific follow-ups, and the transition from current-practice research to solution-fit testing.

## Artifacts and limits

A small engagement can use one Markdown brief. Create a separate interview guide when the audience differs. Organize the main account by journey or business topic, keeping related behavior, friction, expectations, and product implications together. Detailed evidence ledgers can sit in an appendix while consequential claims retain nearby sources. Multi-organization summaries preserve common needs and differences. Later rounds update the same record and active topic while retaining consequential history.

Fit categories are existing coverage, configurable fit, business-practice change, integration, capability gap, and unverified. An item can involve more than one path.

Documentation, code, environment settings, and observed runs prove different things. A participant's statement is not automatically a verified rule. Approval passed does not imply payment or reconciliation completed. Missing facts do not become invented rules, thresholds, benefits, or development commitments.

`saan-diagram` and `saan-mermaid` are optional diagram companions. A step table works without them. Preparing a questionnaire does not send it or contact customers.

## Validation

Fictional inputs and review criteria are in [tests/saan-discovery](../../tests/saan-discovery/README.md). See the [v0.1.0 validation record](validation.zh-CN.md) for the original runs and the [v0.2.0 validation record](validation-v0.2.zh-CN.md) for the interaction and research-type update.

Simulation checks workflow behavior on the supplied cases. It does not establish real interview effectiveness or an advantage over a model without the skill.

See the [release preparation checks](validation-release.zh-CN.md) for the English-first introduction and packaging validation.

## Method acknowledgments

Independently written with method-level inspiration from these sources; none is a runtime dependency:

- Matt Pocock's [grilling](https://github.com/mattpocock/skills/blob/main/skills/productivity/grilling/SKILL.md), [domain-modeling](https://github.com/mattpocock/skills/blob/main/skills/engineering/domain-modeling/SKILL.md), and [to-questionnaire](https://github.com/mattpocock/skills/blob/main/skills/productivity/to-questionnaire/SKILL.md): question dependencies, precise terms, and recipient-specific questionnaires.
- [Focused grill-me variant](https://github.com/hburaktasyurek/agent-skills-and-commands/blob/main/skills/grill-me/SKILL.md): consequential questions and explicit closure.
- [user-interview](https://github.com/assimovt/productskills/blob/main/skills/user-interview/SKILL.md): concrete experience and non-leading questions, adapted for enterprise authority and organizational constraints.
- [elicit-requirements](https://github.com/vesviet/agent-skills/blob/main/core/skills/business/elicit-requirements/SKILL.md): open exploration, probing, and confirmation.
- [discover-interview-synthesis](https://github.com/product-on-purpose/pm-skills/blob/main/skills/discover-interview-synthesis/SKILL.md): attributed synthesis and explicit limits.

[Skill entry point](../../skills/saan-discovery/SKILL.md) · [Design research, Chinese](../plans/2026-11-04-business-discovery-skill-plan.zh-CN.md)
