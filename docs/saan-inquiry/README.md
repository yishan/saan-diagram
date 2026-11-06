# Saan Inquiry

**English** | [简体中文](README.zh-CN.md)

Think through an unclear problem with an adaptive dialogue. Clarify the situation, examine possible explanations and overlooked perspectives, and reach a useful decision or next step. The [introduction](https://kits.yishan.app/inquiry/) includes English and Chinese.

Skill version: **0.1.0**.

## When to use it

Start with an incomplete idea, a broad judgment, a difficult choice, or results that challenge your earlier explanation. Suitable topics include product, business, team work, learning, and everyday decisions. The skill can ask, explain, reframe, offer alternatives, synthesize, or suggest a small experiment. It does not require a questionnaire or promise to find every blind spot or one ultimate cause.

`saan-discovery` focuses on customer research, interview preparation, and product fit. `saan-prd-writing` produces requirements documents. Inquiry focuses on thinking with the user; those other skills are optional when a specific deliverable is needed. A clear execution request should proceed without an imposed interview.

## Installation

Install just Saan Inquiry from Saan Kits:

```bash
npx skills add yishan/saankits --skill saan-inquiry
```

Installation is project-level by default. For manual installation, copy the complete `skills/saan-inquiry/` directory into your agent's skills directory. The core workflow is text-only and requires no service, script runtime, or other skill. Reading external sources may require available tools.

The canonical instruction entry point is English. Responses follow the requested language, otherwise the language of the request.

## Start a conversation

```text
Use saan-inquiry to help me think through why our volunteer events keep getting cancelled.
I suspect unclear ownership, but I am not sure. Help me examine that explanation and what I may be missing.
```

You can control the pace:

```text
I don't know the answer. Use what we have and suggest a provisional next step.
```

```text
Don't ask more questions. Summarize the decision, assumptions, and what would make us reconsider.
```

Return with results to continue:

```text
We tried the plan. The intermediate metric improved, but the original problem did not.
Help me compare this result with our expectation and revise the next step.
```

## What to expect

The next question should change the judgment or action, reuse known context, and normally focus on one thing. Unknowns stay unknown; explanations remain provisional until evidence supports them. Relevant blind spots are introduced as possibilities with a reason, not a compulsory checklist.

A short synthesis may contain the current understanding, material uncertainties, next action or observation, and a result or event that would prompt review. A one-sentence clarification may need nothing more than that sentence. A proposed trial remains pending until it is performed; completing it does not by itself establish that the underlying problem is solved.

The skill does not authorize external actions or create reminders merely by proposing follow-up. It saves notes only when requested or already part of the task.

## Naming and examples

The user's original working name was **Questinoare**. **Saan Inquiry** follows the repository's `saan-` naming convention and describes open inquiry without implying a fixed questionnaire. See the [design note](../plans/2026-11-05-saan-inquiry-design.zh-CN.md) for alternatives and scope.

[Fictional dialogue examples](../../skills/saan-inquiry/references/dialogue-examples.md) show how to select the next move. Startup questions about a concrete customer, actual use, payments, differentiation, sales, delivery effort, team capacity, and recent progress are one source of inspiration. They are not a mandatory interview sequence or evidence of a particular methodology's provenance.

See the [behavioral scenarios](../../tests/saan-inquiry/README.md), [validation record](validation.zh-CN.md), and [introduction page](https://kits.yishan.app/inquiry/). Simulated conversations and package checks do not establish long-term user effectiveness.

## Package

```text
saan-inquiry/
  SKILL.md
  agents/openai.yaml
  references/dialogue-examples.md
```

Back to [Saan Kits](../../README.md).
