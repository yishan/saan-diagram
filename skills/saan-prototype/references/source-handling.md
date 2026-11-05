# Source handling

## ID formats

By default `check.py` and `build.py` find open questions as `Q-<n>`, acceptance scenarios as `AC-<n>`, and rules as `FR-<letters><n>`. If the source uses other IDs, declare them in the manifest:

```json
"id_patterns": {"open": "TBD-\\d+", "acceptance": "TC-\\d+", "rule": "REQ-\\d+"}
```

The definition shown in a badge is the first table row whose first cell is the ID, otherwise the first line that mentions it.

## Without IDs

When the source is a description, a screenshot, or notes without IDs:

1. Write a short `source.md` next to the manifest that restates the material and assigns IDs: rules you were told (`FR-1`…), your assumptions as open questions (`Q-1`…), and the scenarios you will show (`AC-1`…). Mark it as your restatement, not the user's document.
2. Point `manifest.source` at it and tell the user the IDs are yours.
3. Treat every label as a proposal unless the user confirmed it.

## Conflicts and gaps

- When two source documents disagree, follow the precedence the user or the documents state. If none is stated, do not choose: add an open question and show a pending block.
- A source that is a draft stays a draft. The prototype does not make it confirmed.
- Missing visual design is normal. Do not claim the prototype reflects one.
