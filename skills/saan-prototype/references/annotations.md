# Annotations

Annotations keep a review prototype honest. They are on by default; the review bar turns them off for a clean demo.

| Attribute | Use for | Value | Shown as |
|---|---|---|---|
| `data-proposal` | Wording, labels, and messages the source does not confirm | Any source ID the wording relates to (a rule or the section's function ID) | Dotted underline and a 建议 badge |
| `data-open` | A place that depends on an open question | An open-question ID, for example `Q-20` | Red badge; clicking shows the question text from the source |
| `data-rule` | A control or message governed by a confirmed rule | A rule ID, for example `FR-V02` | Grey badge |

Several IDs may be space-separated: `data-rule="FR-C02 FR-C05"`. An element with the same ID as proposal and rule shows one badge.

A page label is annotated in its definition: `Proto.page("mine", {label: "我的登记", proposal: "FR-3", …})`.

## Rules

- Use only IDs that exist in the source. Write them literally, as an attribute, an object key (`{open: "Q-12"}`), or an assignment (`opt.open = "Q-12"`). `check.py` cannot verify IDs built or passed at run time (`'Q-' + n`, `{rule: why.rule}`) and lists them as 提示 N2. When a rule function returns its ID, also write each possible ID literally somewhere on the page, for example in the pending block or the control it governs, so the check can see it.
- Confirmed wording (`confirmed_text` in the manifest) appears exactly as written in the source and never carries `data-proposal`.
- For an open question, render the smallest pending block that shows where the decision lands, for example `<p class="p-pending p-review-only" data-open="Q-20">停用会议室的显示方式待定</p>`. `p-review-only` hides the block in a clean demo. Do not pick an answer.
- Messages from actions use `c.flash(text, {kind, proposal, open, rule})`; the same rules apply.
- When the whole page area depends on an open question, say so once at the top of the area instead of annotating every control.
