# Saan PRD Writing behavioral validation

This directory preserves a fictional, unseen requirement and the actual specification produced using the standalone skill. It does not exercise a real business system.

- `fixtures/room-booking/`: user request, brief, and review notes supplied to the independent evaluator.
- `review-criteria.md`: source-based review criteria fixed before generation and withheld from the evaluator.
- `results/2026-11-04/room-booking/`: actual output, source/package hashes, and review evidence.
- [Validation report](../../docs/saan-prd-writing/validation.zh-CN.md): observed results, changes, packaging checks, and limits.

## Reproduce

1. Copy only `skills/saan-prd-writing/` into an isolated temporary workspace.
2. Copy `fixtures/room-booking/` into `input/` and create an empty `output/` directory.
3. In a new agent context, provide only the skill path and the task in `input/request.md`. Allow reading those inputs and writing `output/prd.md`; do not provide review criteria, prior answers, or the research analysis.
4. Preserve the unedited output. Review the behavior against the raw sources and `review-criteria.md`. Record source and package hashes and identify any untested scope.
5. If an observed failure warrants an instruction change, preserve the failed result and perform a fresh evaluation. Do not rewrite the original output to make it pass.

The repository's static site checker validates page links. Skill frontmatter, internal references, and isolated-install readback check packaging. Those checks do not establish writing quality. Behavioral judgment is based on source preservation, coherent data effects, explicit unknowns, and useful acceptance scenarios rather than fixed wording or heading counts.

No new executable runtime is introduced by this text skill. This scenario is a recorded forward test, not an automated LLM call in CI.
