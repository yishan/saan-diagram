# Source and uncertainty handling

Read this reference when source access is partial, prototypes are involved, or project rules are missing or contradictory.

## Prototypes and Axure files

Record the files, versions, pages, and evidence types actually read. A screenshot proves visible content at that moment. Decoded strings can include hidden states, copied screens, historical versions, and unused content. A flat string dump does not establish reading order, control relationships, interactions, or conditional visibility.

Use a reliable parser or available native/exported representation. If direct `.rp` reading is unavailable or incomplete, use accessible HTML exports, Word specifications, or relevant screenshots. Do not claim full prototype parsing based on a filename or a partial text extraction. State the unverified scope and continue the supported sections.

Deduplicate copied pages and repeated versions before treating recurrence as a style convention. Preserve page identifiers for important or disputed rules. Keep page references distinct from generated requirement identifiers. A prototype can specify intended behavior without proving current production behavior.

Keep private source files and detailed extracts out of reusable packages unless the user has specifically requested their inclusion and sharing is appropriate. Sanitize examples; retain source-specific business rules only in the corresponding project deliverable.

## Conflicts and vague references

Record each source's actual authority and coverage. An explicit later decision may supersede an earlier note; date order alone does not resolve two equally authoritative but incompatible rules. Surface a conflict at the affected rule and link to one open-decision entry.

Examples of material conflicts:

- a field described as single choice in one source and multiple choice in another;
- a batch described as atomic in one place and allowing partial completion in another;
- an operation described as reversible without specifying what data can be restored;
- fields or branches shown in a diagram but absent from the table or prose.

Turn “same as before” into a specific baseline and version. If that baseline is unavailable, identify the missing reference. Treat “if possible” or “developer decides” as a proposal or open decision, not an approved requirement. Resolve “see the red text” to the relevant text or callout when accessible.

Useful open-decision records contain the precise question or conflicting statements, source locations, affected rules, required decision or evidence, and actual owner/status if known. Do not assign an owner merely because a role seems plausible; label an unconfirmed reviewer as a suggestion.

## Source trace without repetition

Use stable source IDs and rule IDs when they improve review. Put references beside important or contested claims. A short feature with one supplied brief may cite it once for the whole section; do not scatter identical citations into every cell.

Keep one authoritative home for each rule. Interface tables reference field and rule IDs. Function lists link to functional sections. Acceptance scenarios reference confirmed rules. A trace table is useful for a complex change but is not mandatory for every draft.

Distinguish approved requirements, proposals, and unanswered questions. Any illustrative number, example name, or invented test value must be labeled as demonstration data. Test values can exercise confirmed boundaries; they cannot define new business limits.

## Missing project context

Draft supported portions without pretending that research is complete. In a full document, show the required chapter categories and the specific evidence needed. In a small change, describe only relevant gaps and references to known baselines; do not expand a narrow change into speculative project architecture.

A proposal can help the user choose, but mark its rationale, scope, and unconfirmed status. It must remain distinguishable from a requirement in interface descriptions, field defaults, acceptance tables, and summaries as well as in the main rule text.
