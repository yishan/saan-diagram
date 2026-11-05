# Saan Prototype

**English** | [简体中文](README.zh-CN.md)

[Introduction and live example](https://kits.yishan.app/prototype/)

Turn a requirements specification into an interactive prototype for review: one HTML file that opens in a browser with nothing to install or build. Reviewers switch roles and scenarios and see how the interface responds to success and failure. They can also see which wording is still a proposal and which questions are still open.

The prototype aligns interactions, states, and rules. It is not production front-end code and does not replace visual design.

## When to use it

| Use Saan Prototype | Use something else |
|---|---|
| Before a review, so people can click through pages, roles, and states | Writing the requirements themselves: [Saan PRD Writing](../saan-prd-writing/README.md) |
| Checking that confirmed rules make sense in the interface | Explaining business structure and processes: [Saan Diagram](../saan-diagram/README.md), [Saan Mermaid](../saan-mermaid/README.md) |
| Marking open questions where they affect the interface | Front-end projects, visual comps, mobile device frames: out of scope |

The preferred input is a specification like the ones `saan-prd-writing` produces, with numbered functions, interface descriptions, rules, acceptance scenarios, and open questions. That skill is an optional peer, not a prerequisite. A description or screenshots also work: the prototype then lists its assumptions first and marks every label as a proposal.

## Installation

```bash
npx skills add yishan/saankits --skill saan-prototype
```

For manual installation, copy the complete `skills/saan-prototype/` directory into the target agent's skills directory.

## Dependencies

- Python 3 for `scripts/build.py` and `scripts/check.py`, standard library only.
- A browser to open the result. The prototype makes no network requests.

## How to use it

Give your agent the specification:

```text
Use saan-prototype to build a review prototype from prd.md. List the pages, roles, and scenarios first.
```

The agent proposes a scope (for example "4 pages, 2 roles, 9 scenarios") and then writes these files to your working directory:

| Output | Contents |
|---|---|
| `prototype.html` | One file with the runtime, theme, and pages inlined |
| `prototype/` | A copy of the specification, `manifest.json`, `rules.js`, `scenarios.json`, and `pages/*.js`, which you can edit and rebuild |
| `prototype/trace.md` | How pages and scenarios map to source IDs, and which open questions are not shown and why |

Open `prototype.html`. The review bar at the top lets you:

- **Switch scenarios.** Each scenario maps to one or more acceptance IDs and carries its own initial data and current time, because rules such as "already started" depend on time. Switching resets the data.
- **Switch roles.** See what each role can view and do on the same page.
- **Switch themes.** `neutral`, `blue`, and `dark` are included.
- **Toggle annotations.** On by default. Proposed wording carries a badge. Each open question shows as a placeholder ("decided by Q-xx") that opens the original question. Confirmed rules show only their ID. Turn annotations off for a clean demo.

Only **confirmed** rules become logic. An open question is shown as a placeholder, never implemented as a guess.

## Checks

```bash
python3 skills/saan-prototype/scripts/build.py prototype/manifest.json -o prototype.html
python3 skills/saan-prototype/scripts/check.py prototype/manifest.json
```

`check.py` exits with 0 when clean, 1 when something must be fixed, and 2 when there are only business findings. Messages are in Chinese.

| Output | Codes | Meaning | What to do |
|---|---|---|---|
| Must fix (必须修改) | T1, T3 | An annotation ID is missing from the source or is the wrong kind | Fix the prototype |
| | T2 | An open question is neither shown nor listed as not covered (「不涉及」) in `trace.md` | Show it or give the reason |
| | S1, S3, S4 | A scenario cites an unknown acceptance ID or undeclared role, or repeats an ID | Fix the scenario |
| | C2 | Scenario data uses a state outside the manifest | Prototypes cannot add states |
| | W1 | Confirmed wording does not appear verbatim | Fix the page |
| | B1, B2 | An external resource is requested, or a theme fails contrast | Fix the prototype or theme |
| | M1 | The manifest or a file is missing | Fix the files |
| Business finding (业务发现) | C1, W2 | A declared state or confirmed wording is not in the source | Report it; do not edit just to pass |
| Note (提示) | N1 | An acceptance scenario is not covered by any scenario | Explain in `trace.md` why it cannot be shown |
| | N2 | An annotation ID is only known at runtime and cannot be checked | Write it literally where possible |

IDs default to `Q-01`, `AC-01`, and `FR-B01` (the letters are optional). If your source uses another format, set `id_patterns` in the manifest.

## Limitations

- The prototype is a review tool. Sample data is fictional, and only confirmed rules are simulated.
- The checker matches IDs and text. It does not judge whether the interaction is good, whether an action really goes through the rule functions, or in which scenario an annotation is visible.
- Without a specification, the source is the agent's own restatement, so the check only compares the agent's work with itself.
- Themes are checked for contrast only, not brand compliance.
- There has been no usability testing with real users. The reviewer during validation was the session that arranged the runs, not a blind reviewer.

## Development and validation

```bash
python3 skills/saan-prototype/scripts/check.py --selftest
python3 -m unittest discover -s tests/saan-prototype -v
```

Two cases, the room-booking PRD and a short description with no PRD, were each run twice in fresh contexts against review criteria written before generation. The [validation record (Chinese)](validation.zh-CN.md) lists the process, the issues found, and the fixes.
