# Harbor Facilities: interim asset-repair discovery brief

All organizations, roles, and observations are fictional. Prepared from field notes dated 2 November 2026.

## Current conclusion

**Customer discovery can continue; product fit remains unverified.** The notes establish a partial repair workflow and two desired outcomes: fewer missed updates and repair-status visibility for sites. They do not establish approval policy, repair-closure rules, quantified impact, or any product capability.

This brief prepares the maintenance manager's requested workshop on one urgent repair from request to closure. It supports the next discovery step, not a solution-scope or acceptance decision. The user is unavailable today; no immediate response or product document is needed to use this interim brief. Workshop duration and implementation deadline are unspecified.

**Evidence:** [A1] `input/notes.md`, operator interview, 2 November 2026; [A2] maintenance manager interview, same date; [A3] available materials. A1 and A2 are paraphrased participant reports, not quotations or observed execution. A3 records the absence of product documentation, demonstration, code, configuration, policy, and actual repair records. Product name and version are unspecified. Customer claims below are reported and unverified unless otherwise stated.

## Customer business: known path and limits

| ID | Category / source | Finding | Consequential uncertainty |
|---|---|---|---|
| F1 | Current practice [A1] | Requests arrive by chat. The operator copies them into a spreadsheet and phones a contractor. | Requester, required inputs, identifiers, and request/job/asset/site relationships are unknown. The account does not establish every case's sequence. |
| F2 | Current practice, one urgent case [A1] | A supervisor authorized the contractor call by phone; the spreadsheet was updated the next morning. | Authority and permitted action beyond the call are unclear. Contractor response, execution, checking the repair, and closure are not described. Who updated which fields is unknown. |
| F3 | Policy claim [A2] | The manager says jobs above an unspecified cost require approval, but does not know who owns the threshold. | Decision object, threshold, cost basis, scope, routing, authority, and urgent-case treatment need an authoritative source. |
| F4 | Desired outcome [A1] | The operator wants fewer missed updates. Monthly volume cannot be estimated from memory; no failure-count report was supplied. | The failing step, cause, consequence, frequency, and workaround are unknown. No time, rework, or cost baseline is available. |
| F5 | Desired outcome [A2] | The manager wants repair status visible to each site. | Useful status definitions, site audience, permitted data scope, and the decision visibility should support are unknown. |

The urgent case's next-morning update is not proof of a missed update or policy violation. The two accounts do not yet establish a conflict: the relationship between the manager's cost rule and the supervisor's phone authorization needs checking.

Keep **authorization, contractor contact, repair execution, and business closure** separate. Authorization to make a call does not establish repair completion. The missing execution-to-closure path should be reconstructed before proposing lifecycle states.

The operator handles intake and contractor contact; the supervisor authorized the reported urgent call; the manager expresses a visibility goal. The business decision-maker, policy owner, data owner, and success-acceptance authority remain unidentified. “Request,” “job,” “repair,” “asset,” and “site” are customer terms whose relationships and lifecycle definitions need clarification; no product-term mapping is available.

Why change is needed now, the consequence of deferral, outcome priorities, measurement methods, baselines, and targets are unknown. The desired outcomes are not accepted requirements.

## Next workshop: five core questions

Start from the urgent case already described and fill its missing parts. Proposed respondents are suggestions, not assigned owners or confirmed attendees. All questions are **open**. Explicit unknowns and partial answers are useful.

| ID | Customer-facing question | Proposed respondent | Purpose and useful evidence |
|---|---|---|---|
| Q1 | What happened after the contractor was called in that urgent repair, through the point the case was considered closed? | Operator; person who checked the repair if different | Complete execution and closure. Bring the case's chat thread, spreadsheet entry, and any completion record that exists. |
| Q2 | What did the supervisor's phone authorization permit in that case? | Supervisor and operator | Establish the decision's effect using Q1's timeline. Look for any contemporaneous authorization record; record its absence if none exists. |
| Q3 | What source defines the cost-based approval rule you described? | Maintenance manager; responsible policy role once identified | Locate authority before investigating configuration. Request the applicable policy or rule-owner clarification, if available. |
| Q4 | Can you show the most recent update that was missed? | Operator | Locate the reported problem in a concrete case before attributing cause or measuring scale. Compare the relevant request and spreadsheet entry. Do not presume the urgent example was a missed update. |
| Q5 | What work decision should seeing repair status help a site user make? | Maintenance manager and a site representative | Define the purpose of visibility before specifying fields or access. Use a recent site enquiry or decision if available. |

Use this order where respondents are available. No meeting duration is assumed. The following are conditional follow-ups, not additional prerequisites for delivering this brief:

- **After Q3:** ask the identified policy owner to establish the decision object and rule scope. Then check threshold, comparison boundary, currency, and cost basis individually, followed by urgent authorization and later recording. This resolves the approval-assessment dependency.
- **After Q1/Q5:** inspect record relationships, update ownership, status meanings, and which site users should see which repairs with the operator, manager, and site representative. This enables object and permission mapping; cross-site access is not presumed.
- **After Q4:** locate cause and consequence, then identify a feasible record sample and time window for request volume and missed updates. With the manager and decision-maker once identified, clarify priority, target, measurement method, and acceptance authority. This enables a defensible business case and success criteria.

These actions remain open recommendations with no assigned owners or deadlines. Request only available, appropriately shareable records and use de-identified examples. Where records do not exist, retain the participant-report evidence status.

## Product-fit assessment

| Customer condition | Fit category | Next verification |
|---|---|---|
| Request capture and reliable progress updates [F1, F4] | Unverified | Complete Q1/Q4 and clarify record relationships and update ownership. Later compare these conditions with versioned product evidence for records, transitions, and editing behavior. |
| Cost approval and urgent authorization [F2, F3] | Unverified | Resolve Q2/Q3 and the rule details. Later check product decision objects, routing boundaries, and evidence of offline authorization recording against the established rule. |
| Useful site visibility [F5] | Unverified | Resolve Q5, status definitions, and access scope. Later inspect the relevant product views and permissions. |

There is no product baseline [A3], so existing coverage, configurable fit, business-practice change, integration, and capability gaps are not established. Chat and spreadsheet use alone does not establish an integration requirement. No customization, delivery, or benefit commitment follows from these notes.

When product material becomes available, record its name, version, source, and evidence level. Documentation establishes design intent; configuration establishes an environment setting; an observed run establishes that path. A subsequent real-case walkthrough can test a proposed fit. Keep solution feedback separate from current-practice evidence.

## Stage and residual decisions

**Round synthesized; further discovery needed.** The workshop is prepared with prioritized questions, respondents to approach, and evidence requests. The main residuals are the execution-to-closure path, approval authority and rule, and definitions of the two desired outcomes. They block a scoped solution assessment and acceptance criteria. Missing product evidence separately blocks a product-fit conclusion.

No one has been contacted. No workshop has been booked, product behavior tested, or customer rule validated. Continue customer discovery with the prepared questions; resume product assessment when a scoped baseline becomes available.
