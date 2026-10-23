---
name: "saan-diagram"
description: "Create consistent business diagrams from descriptions, requirements, or whiteboard screenshots. Use for business architecture, process flows, role handoffs, data relationships, and milestones in English or Chinese. Render HTML/SVG/PNG; publish to a Feishu/Lark whiteboard when requested. Not for sequence diagrams, state machines, physical database schemas, or task-level Gantt charts."
metadata:
  author: "Yishan"
  version: "1.2.0"
---

# Saan Diagram

Turn business information into diagrams with a consistent visual language. Write a YAML spec using stages, lanes, and rows. `scripts/render.py` owns coordinates, routing, colors, typography, legends, and validation. Standardize the rules, not the business solution.

## Output language

**Follow the user's explicitly requested output language. Otherwise, use the language of the user's request.** The language of this file, a template, or a source document must not override that choice.

- Use the selected language for titles, labels, edge captions, explanatory notes, and the delivery response. Preserve proper names, identifiers, and any original wording the user asks to retain.
- Set `language: en` for English or `language: zh-CN` for Chinese in the spec. `--language en|zh-CN` overrides the spec. Omission retains the renderer's Chinese default for existing specs; do not rely on that default when creating an English diagram.
- Quote YAML labels such as `"Yes"`, `"No"`, `"On"`, and `"Off"` so they remain strings, not booleans.
- The renderer localizes its own legends and generated annotations. It does **not** translate user-provided spec content. Adapt template text to the requested language and keep IDs and references consistent. Stable IDs help avoid breaking edges when labels change.
- English examples are in `assets/en/`. Most other templates and detailed guides are in Chinese; read only the relevant guide and explain findings in the user's language. Some CLI diagnostics remain in Chinese; that does not require a Chinese deliverable.
- English and Chinese are the currently implemented caption locales. Do not claim another locale is supported or silently substitute it; explain the limitation if a different language is requested.

## Choose a diagram

When a user requests a diagram, proceed. For an explanation-only request, use this skill only if a diagram materially helps communicate relationships.

| What the user needs | Diagram | `--init` | `--guide` |
|---|---|---|---|
| Modules by stage and connected systems | Architecture view | `arch` | `stages` |
| Main process with decisions and returns | Process flow | `flow` | `stages` |
| Different approaches across common stages | Path comparison | `paths` | `stages` |
| Handoffs between roles | Swimlane | `swim` | `stages` |
| Data sources, processing, and storage | Data flow | `dfd` | `profile` |
| Documents and controls | Audit flow | `audit` | `profile`, `verify` |
| Value-adding versus other steps | Opportunity flow | `opportunity` | `profile` |
| Platform layers and integrations | Layered architecture | `layers` | `layers` |
| Entities, relationships, and cardinality | Entity relationship | `er` | `er` |
| Reporting lines and declared access scopes | Organization and data isolation | `org` | `org` |
| Causes behind an outcome | Fishbone | `fishbone` | `fishbone` |
| Milestones and schedule variance | Timeline | `timeline` | `timeline` |
| Priorities across two dimensions | Quadrant | `quadrant` | `quadrant` |
| Activity inputs, controls, outputs, and mechanisms | IDEF0 | `idef0` | `idef0` |

For sequence diagrams, state machines, physical database schemas, or task-level Gantt charts, choose a suitable tool such as Mermaid or a database modeler. For mixed needs, choose the main organizing axis: stages, step order, roles, or technical layers. Do not add swimlanes, alternate paths, or highlighted capabilities when the source does not call for them.

## Establish necessary context

Infer the diagram type from the request and source. Unless specified, use horizontal orientation, the default blue brand color, an outlined title bar, and HTML + PNG delivery. Ask only when missing information changes business meaning, the delivery target, or the scope of an external write. Reuse existing authorization and preferences.

- Do not invent core functions, controls, completion states, role permissions, or other missing business facts.
- Only when whiteboard delivery is selected, run `python3 scripts/wb_publish.py --probe` and read `guides/feishu.md`. Local rendering does not require a Feishu probe.
- A supplied board target and append instruction authorize that write. Overwriting existing content requires explicit approval. Without an external target, deliver local files and clarify the destination if publishing is still needed.

## Workflow

Run commands from the installed skill root, or use absolute paths to its scripts and resources.

```bash
python3 scripts/render.py --init audit > pay.yaml
python3 scripts/render.py --guide verify
# Edit the spec content and set its output language before rendering.
python3 scripts/render.py pay.yaml --all
```

For an English starting point, copy a matching file from `assets/en/`, such as `approval-flow.yaml`, `platform-layers.yaml`, or `release-timeline.yaml`. These are examples, not business rules.

1. Extract stages, steps, modules, systems, edges, decisions, roles, and controls from the source. Read screenshot content explicitly.
2. Start with the nearest template and adapt its content and language.
3. Remove redundant decoration and repeated wording. Preserve business steps, branches, roles, and controls; never remove facts to fit the layout or pass validation.
4. Run `--all`. Fix layout errors using the reported guidance, then rerun. Handle business findings as described below.
5. Inspect the generated PNG with the available image tool for overlaps, text, and routing. If PNG generation fails, fix its dependencies, or agree on HTML/SVG delivery and inspect that output. Passing script checks is not visual acceptance.
6. Deliver the requested artifacts and their editable spec.

## Visual constraints

- Business nodes are neutral gray. Internal systems use the brand color; external systems use a lighter tint. Use no more than three core highlights. Pale orange highlights one capability category, named by `special: {label: ...}` with `kind: special`.
- Never shrink text to force a fit. Node labels have a 10-unit width budget; ordinary edge labels have 8 units. A CJK character counts as 1 unit and a typical Latin character as 0.5. These are width budgets, not English word limits. Keep English words intact; abbreviate only when meaning remains clear. Use the layout's measured fit checks and inspect the result.
- Connectors are orthogonal, do not cross nodes or share overlapping strokes, and retain a visible segment before the arrowhead.
- The default title bar is white with an outline and does not consume a core highlight.
- Correct problematic routing or colors in source diagrams and identify substantive corrections in the delivery notes.

Read `--guide style` for detailed visual rules and `--guide lint` for rule-specific fixes.

## Validation and business findings

`--all` distinguishes two categories:

- **Layout errors:** adjust the spec until checks pass.
- **Business findings:** report the finding and its counterexample. Do not hide missing controls, bypasses, data sinks, overlapping access scopes, or conflicting duties by removing edges, moving actors, or inventing policies. Correct a misrepresented diagram from user clarification; if the user confirms the current process, record the finding in `accept` with its rule code, a matching phrase, and the user's explanation.

```yaml
accept:
  - code: P1
    match: Emergency approval
    note: Emergency payments have written authorization and a later review.
```

Use the actual finding text for `match`; keep it aligned if labels or language change. Confirming a finding does not mean its risk has been resolved.

For approval, audit, and swimlane flows, consider `verify`. `verify: {}` enables default checks, including disconnected business steps. Separation of duties uses node `actor` values or explicitly declared `column_semantics: roles`; stage columns do not imply roles. Verification checks declarations in the graph, not real system permissions. Read `--guide verify` when needed.

Renderer exit codes: `0` success, `1` layout errors, `2` unconfirmed business findings, `3` invalid spec, `4` failed or incomplete artifacts. `<slug>.result.json` records validation and artifact statuses; a printed file path alone is not evidence of successful generation.

## Delivery

- **HTML + PNG:** confirm both artifact statuses are `generated`. `--all` also creates `<slug>.wb.json`. Show the PNG and provide the spec location. Future edits belong in the spec; `--orient` and `--brand` change presentation.
- **Feishu/Lark:** use `scripts/wb_publish.py`; do not construct direct write commands. Read `--guide feishu` first. Exit `20` means review the exported existing board and choose a write mode; a failed read is not an empty board. Exit `10` is a confirmation gate: relay it and use `--pass=--yes` only when requested by the gate and authorized by the user. Exit `21` means the write succeeded but readback failed: retry with `--verify-only`, not another write. Exit `0` still requires distinguishing conversion, readback-only, and write-plus-readback in the result JSON, then inspecting the exported image. Do not create a document when the user has not supplied a target.
- **Both:** deliver the PNG first, then follow the authorized whiteboard workflow.

Before delivery: validation passes, the main process is understandable from its main nodes and solid edges, systems have connections, and assumptions and confirmed findings are disclosed in the selected language.

## Runtime boundaries

Install the entire skill directory, including `scripts/`, `guides/`, and `assets/`. Guides and templates are loaded on demand from their source files; do not load them all or reconstruct a missing renderer from memory.

Python dependencies are in `requirements.txt`; PNG dependencies are in `requirements-png.txt`. After installation or updates, run `python3 scripts/render.py --selftest`. Self-tests validate examples and rule triggers; they do not replace inspection of the current diagram or whiteboard readback.
