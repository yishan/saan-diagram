# Inquiry behavioral validation

All requests are fictional. Evaluate the standalone skill in an independent context; do not supply the reviewer criteria or later user turns. Preserve the actual outputs rather than rewriting them into ideal examples. No external services, purchases, messages, or live operational changes are part of these trials.

## Scenarios

- **Volunteer dialogue:** supply `fixtures/volunteer/turn-1.md`, then turns 2 and 3 sequentially in the same context. Preserve the reply after every turn. Turn 2 requests a provisional action without further questioning; turn 3 supplies contrary results.
- **Direct responses:** supply `fixtures/direct/requests.md`. These are two independent tasks: a constrained personal practice plan without follow-up questions, and a one-sentence clarification.

Copy only `skills/saan-inquiry/` and the relevant inputs into a temporary location for independent evaluation. The evaluator may read the bundled examples when directed by the skill. Keep `review-criteria.md` for the reviewer. Record input and package hashes so subsequent changes are distinguishable.

These are workflow checks, not a comparison with an unassisted model. The direct cases intentionally resemble the bundled examples to check constraint handling; the volunteer dialogue tests transfer to a different setting. Hosting UI, automatic routing, longitudinal user benefit, and real-world causation are not tested here.

See [review criteria](review-criteria.md) and the [validation report](../../docs/saan-inquiry/validation.zh-CN.md) for actual results and limits. No executable runtime or model call is introduced into CI.
