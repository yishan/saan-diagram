# Saan X-Ray behavioral validation

Evaluate the standalone `skills/saan-xray/` package in an independent context without supplying reviewer criteria. Preserve the actual model outputs in `results/`.

## Scenarios

- **Turn 1 — Pass 1 (System Overview Briefing, Hybrid UI + Code, Observe-only):**
  Supply `fixtures/expense-claim/request-pass1.md` along with `fixtures/expense-claim/ui.html` (representing the observed live interface for an Employee account) and `fixtures/expense-claim/server.py` (representing the backend codebase).
- **Turn 2 — Pass 2 (As-Is Module Deep Dive + Handoff Readiness):**
  In the same context, supply `fixtures/expense-claim/request-pass2.md` asking for a Pass 2 As-Is Module Specification of the Expense Claim Reimbursement flow for `saan-prd-writing`.

See [review criteria](review-criteria.md) and the [validation report](../../docs/saan-xray/validation.zh-CN.md).
