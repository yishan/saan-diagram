# Business process and approval research

## Reconstruct actual work

Use the recent case or supplied records to build the current process. Retain manual actions and cross-system handoffs. Identify who owns the business result, not only who presses a button.

For a step, capture relevant fields:

`trigger → role → input → action → output/state change → next recipient → exception → source`

Do not force an unknown sequence into a completed diagram. State which transition is missing. Keep current practice, policy, and desired process in separate rows or views when they differ.

Separate the lifecycle of the business object from the approval instance and downstream execution. For example, approval passed, bank transfer submitted, payment succeeded, and reconciliation completed can represent different facts. The source must establish their relationship.

## Record decisions rather than only approver names

An approval rule can include:

`object/granularity → trigger → routing condition → authority/assignment → available actions → result → business effect → exception → source`

Use this list conditionally. A simple approval need not be interrogated about every possible workflow feature.

| Trigger in the material | Probe when it changes the assessment |
|---|---|
| Amount-based routing | Currency, tax basis, original vs revised amount, exact equality boundary, combined conditions |
| Organization or project routing | Administrative vs accounting/project organization, hierarchy, cross-organization responsibility |
| Multiple approvers | Sequence, all-vs-any completion rule, disagreement, duplicate role assignment |
| Document details | Whole-document vs item decisions, partial approval, later item changes |
| Return or resubmission | Where the request returns, what can change, whether prior decisions remain valid |
| Withdrawal or cancellation | Who can act, when, resulting state, effects on in-flight execution |
| Missing or unavailable approver | Delegation authority, empty positions, escalation, self-approval or incompatible duties |
| Urgent or offline handling | Actual path, authorization basis, later recording, audit trail |
| Approval finishes | When the business becomes effective, permitted next action, who executes and checks completion |
| Subsequent change | Which changes require reapproval, treatment of already executed work, traceability |

Do not supply thresholds, implicit comparison operators, return paths, or exception rules from industry habit. Record a policy gap separately from observed practice.

## Locate friction and consequences

Attach friction to a specific step, role, or handoff. Record the event, reported cause, impact, frequency, and current response. Distinguish:

- Active handling time from queueing or missing-material time.
- Repeated work from necessary independent review.
- A system limitation from a rule, access, data-quality, or responsibility problem.
- A single observed case from a measured pattern.
- A business-control requirement from someone's preferred working habit.

Alternative causes may be hypotheses until checked. Connect the next question to the evidence that could distinguish them.

## Reconcile conflicting accounts

Retain each account's source, role, date, organization, business type, and amount range where available. Check whether the accounts describe different cases, policy versions, or meanings of a term. Request the relevant policy, configuration, record, or responsible person's clarification.

Fresh material can resolve one scope while leaving another unknown. Keep the resolution and its source; do not erase the earlier account or interpret silence as agreement. A policy owner's clarification confirms their policy position, not automatically actual system behavior.
