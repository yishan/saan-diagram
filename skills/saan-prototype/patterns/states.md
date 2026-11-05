# Empty, error, and pending states

| State | Markup | When |
|---|---|---|
| Empty | `<div class="p-empty">…</div>` | A list or area with no records |
| Error message | `c.flash(text, {kind: "error", rule: "FR-…"})` | A rule rejected an action |
| Success message | `c.flash(text, {proposal: "FR-…"})` | Unless the source fixes the wording, it is a proposal |
| Pending decision | `<p class="p-pending p-review-only" data-open="Q-…">…</p>` | The source leaves this behaviour open |

- Give every empty and error state that the source mentions a scenario that shows it.
- A pending block names the open question and where the decision lands. It never shows a guessed answer.
