# Interim business discovery brief: Harbor Facilities asset repairs

Prepared 4 November 2026. All organizations, roles, and source observations are fictional. This brief contains paraphrases, not direct quotations.

The field notes establish participant reports of a manual repair intake process and one urgent repair involving telephone authorization and later spreadsheet entry. They do not establish the governing approval policy, the path to repair closure, or the frequency and impact of missed updates. Customer discovery can proceed now. **Product fit remains unverified for every candidate need because no product evidence or product/version context is available.**

## 1. Purpose, scope, and limits

The immediate purpose is to organize the supplied notes, prepare the next useful workshop, and identify what evidence would allow a scoped product-fit assessment. The working scope is repair request intake, contractor coordination, authorization, progress visibility, and closure at Harbor Facilities. Scope boundaries beyond these tasks are unknown.

The operator is a source for current handling practices. The maintenance manager is a source for the reported cost-related approval condition and the desired site visibility. A supervisor reportedly authorized the urgent contractor call; the supervisor has not been interviewed. Contractors and site staff are mentioned or implied recipients of work or information, not confirmed workshop participants. The policy owner, business decision-maker, data owner, and person authorized to accept an outcome are unknown.

The maintenance manager requested a workshop following one urgent repair from request to closure. Its duration, date, and attendance are unspecified. The user is unavailable today, so this is an interim artifact with proposed follow-ups; no questions require a response today. No follow-up ownership, attendance, or action has been agreed.

## 2. Source and claim ledger

Source locators refer to `input/notes.md`.

| Source ID | Locator and scope |
|---|---|
| S1 | A1, operator interview, 2 November 2026; paraphrased account of intake and the last urgent repair, plus a desired outcome. |
| S2 | A2, maintenance manager interview, 2 November 2026; paraphrased approval account, desired visibility, and workshop request. |
| S3 | A3, available-materials statement; no product manual, demonstration, code, configuration, policy, or actual repair record available. User unavailable today. |

| Claim ID | Statement | Content category | Source and locator | Evidence status and limit |
|---|---|---|---|---|
| F1 | Repair requests arrive by chat; the operator copies them to a spreadsheet and phones a contractor. | Current practice | S1, A1 paragraph 1, sentences 1–2 | Participant report; no record or walkthrough checks the sequence or its coverage. |
| F2 | For the last urgent repair, a supervisor authorized the call by phone, and the spreadsheet was updated the next morning. | Current practice | S1, A1 paragraph 1, sentence 3 | Participant report about one case; exact event times, authority basis, repair execution, and closure are unknown. |
| F3 | The operator wants fewer missed updates. | Desired outcome | S1, A1 paragraph 2 | Participant report; no failure-count report or measured baseline supplied. The delayed entry in F2 is not established as a missed update. |
| F4 | Monthly volume cannot be estimated from the operator's memory. | Current-practice measurement | S1, A1 paragraph 2 | Unknown; no volume value or estimate is supported. |
| F5 | Jobs above an unspecified cost require approval, according to the manager. | Policy claim | S2, A2 paragraph 1 | Participant report, unverified. Threshold, rule source, rule owner, and scope are unknown. |
| F6 | The manager wants repair status visible to each site. | Desired outcome | S2, A2 paragraph 1 | Participant report; viewers, information needed, access boundaries, and acceptance criteria are unspecified. |
| F7 | The next workshop should examine one urgent repair from request to closure. | Research expectation | S2, A2 paragraph 2 | Participant report; no workshop arrangements are supplied. |

“Repair request,” “job,” “urgent repair,” and “repair status” are retained as customer terms. Whether a request and a job are the same record, or have a one-to-many relationship, is unknown. A site-to-job relationship, asset identifier, status vocabulary, and spreadsheet fields have not been established. No mapping to product terminology is possible yet.

## 3. Current business and approval

### Reported workflow

| Path and step | Role, input, and action | Known output or handoff | Missing transition or condition |
|---|---|---|---|
| Routine intake | Requester unspecified; a repair request arrives by chat. Operator copies it to a spreadsheet. | Spreadsheet entry; operator then phones a contractor. (F1) | Required request information, entry ownership, duplicate handling, and linkage to the asset/site are unknown. |
| Contractor contact | Operator phones a contractor. | Contractor contacted. (F1) | Contractor acceptance, assignment, scheduling, and authority to begin work are unknown. A call does not establish that work started. |
| Last urgent case: authorization | Supervisor authorizes the contractor call by phone. | Reported authorization to make the call. (F2) | How urgency was determined, the authority basis, and the scope of the authorization are unknown. |
| Last urgent case: recording | Spreadsheet updated the next morning. | A later spreadsheet update is reported. (F2) | Contents, author, exact timing, and connection to an authorization record are unknown. |
| Execution through closure | No account supplied. | Unknown. | Who performs, verifies, accepts, records, and closes the repair remains open. |

The urgent account is not forced into the routine sequence. Telephone coordination and later entry are part of the reported work. The notes do not establish whether chat or the spreadsheet is the authoritative record, or whether other records exist.

### Approval evidence, kept separate from execution

| Aspect | Current evidence | Unresolved point |
|---|---|---|
| Cost-related approval | Manager reports that jobs above an unspecified cost require approval. (F5) | Decision object, amount basis, threshold, equality boundary, currency, authority, routing, and permitted next action are unknown. |
| Urgent authorization | Supervisor authorized a call by phone in one case. (F2) | Whether this was a permitted urgent path, ordinary delegated authority, or another arrangement is unknown. |
| Approval result | Authorization of the call is reported. (F2) | It does not establish approval of expenditure, approval of the completed repair, or business completion. |
| Rule ownership | Manager is unsure who owns the threshold. (F5) | Locate the governing source and responsible role before treating any amount as a configuration requirement. |

The two accounts are not a proven contradiction: the urgent job's cost and the relationship between telephone authorization and cost approval are unknown. Both accounts remain visible until the same case and applicable rule can be checked. No threshold, escalation path, or emergency exception is proposed as an existing rule.

## 4. Friction and expected outcomes

| Item | What the notes support | Measurement and acceptance limits |
|---|---|---|
| Missed updates | Operator wants fewer missed updates. The relevant area to investigate is recording and status handoff. (F3) | No specific missed-update incident, definition, cause, consequence, frequency, or failure count is supplied. Manual copying alone does not prove an error cause. |
| Delayed recording | The spreadsheet was updated the following morning for one urgent case. (F2) | No measured active work time or waiting time; no evidence that this delay breached a requirement or caused harm. |
| Site visibility | Manager wants each site to see repair status. (F6) | The decision enabled by that visibility, information needed, freshness, viewer permissions, baseline, target, and acceptance authority are unknown. |

The notes do not establish why change is needed now, the consequence of deferral, relative priority, constraints, or a success target. These are desired outcomes, not approved requirements. Once “missed update” is defined, a record review could establish a baseline for a specified population and period; neither the period nor a target is set here. Monthly volume should be obtained from records if needed, rather than requesting another memory estimate from the operator.

## 5. Current product-fit assessment

Product identity, version, available objects, lifecycle, permissions, rules, configuration boundaries, integrations, and known limits are all unknown. S3 provides evidence of unavailable materials, not evidence that capabilities are absent.

| Candidate assessment area | Customer condition and source | Product evidence | Current classification | Decision affected and next verification |
|---|---|---|---|---|
| Intake and contractor handoff | Chat intake, spreadsheet entry, contractor call. (F1) | None; version unknown. | Unverified | Establish record relationships and handoffs, then compare with product object and lifecycle evidence. No chat connector requirement is assumed. |
| Urgent handling | Telephone authorization followed by later recording in one case. (F2) | None; version unknown. | Unverified | Establish authority, timing, and recording requirements; later test the established path against documented behavior and a relevant walkthrough. |
| Cost approval | Manager reports a cost-dependent approval rule. (F5) | None; version unknown. | Unverified | Verify the rule and owner first, then assess the product's actual routing dimensions and boundaries. |
| Site status visibility | Desired visibility for each site. (F6) | None; version unknown. | Unverified | Define the site user, needed information, and access scope, then inspect product permissions and status presentation. |
| Update reliability and closure | Fewer missed updates desired; closure path unknown. (F3; workflow gap) | None; version unknown. | Unverified | Establish update obligations and closure evidence, then assess how the product records and exposes those events. |

There is no evidential basis yet to classify any item as existing coverage, configurable fit, integration, business-practice change, or a capability gap. These remain possible assessment outcomes, not recommendations or commitments. No implementation scope, delivery estimate, numeric benefit, or product acceptance is established.

## 6. Next workshop: a small, ordered question set

**Purpose:** complete the already described urgent case, identify the applicable authority, and make the two desired outcomes concrete. Proposed participants are the operator and maintenance manager, with the supervisor for the authorization question and a relevant site user for the visibility question. These are respondent suggestions, not assignments. Partial answers and explicit unknowns are useful.

Reuse the known intake, telephone authorization, and next-morning update. Start at the missing continuation rather than asking participants to repeat the whole interview.

| Question ID | Customer-facing question | Proposed respondent | Gap and affected decision | Prerequisite and useful evidence | Status |
|---|---|---|---|---|---|
| Q1 | After the contractor was contacted for that urgent repair, what happened through to its current state? | Operator, with the person who confirmed closure if applicable and identifiable | Missing execution and completion path; determines lifecycle scope. | Start from the known case. Bring the related chat thread and spreadsheet row, plus any contractor or completion record that exists. | Open |
| Q2 | What gave the supervisor authority to authorize the contractor call in that case? | Supervisor | Urgent authority and its business effect; determines which approval path must be assessed. | Same case as Q1; any retained authorization evidence or applicable instruction. | Open |
| Q3 | What source defines the cost boundary that requires a job to be approved? | Maintenance manager initially; governing role to be identified if unknown | Rule provenance and ownership; blocks amount-routing assessment. | No threshold assumption. Bring an applicable policy or other authoritative rule source if one exists. | Open |
| Q4 | What recent example prompted your concern about missed updates? | Operator | Meaning and location of the reported friction; informs what to measure and improve. | A separate example is valid if the urgent case had no missed update. Bring associated records if available. | Open |
| Q5 | What decision should a site user be able to make from the repair status? | Relevant site user, with maintenance manager | Purpose of visibility; determines useful information and later acceptance discussion. | Use the same repair where useful. Existing status messages or views may help. | Open |

Keep probes separate and use them only when the answer makes them relevant:

- After Q1, if the case was closed: “What evidence showed that this repair was complete?” Then identify who accepted completion. If it remains open, ask what must happen before it can close.
- After Q2, if the authorized action remains unclear: “What action did that authorization allow?” Check later recording separately. Do not assume telephone authorization replaced cost approval.
- After Q3, if the source is unknown: “Who can establish the governing rule?” Once the source is found, check amount basis, exact boundary, and scope individually, then apply them to the urgent case.
- After Q4 identifies an event: “What happened because that update was missed?” Ask about the cause separately. Obtain records before estimating how often it occurs.
- After Q5 establishes the decision: “Which repair information is needed to make that decision?” Check own-site and cross-site access only as relevant to those users.

These are factual discovery questions. A future product demonstration should be a distinct activity, with solution feedback recorded separately from current practice.

### Follow-up queue after the core case

| ID | Residual gap or next action | Decision affected | Proposed respondent / evidence | Prerequisite and status |
|---|---|---|---|---|
| G1 | Clarify the relationship among request, job, asset, and site; identify record identifiers, essential fields, state meanings, and update responsibility. | Object model, handoffs, reliable status data. | Operator and record owner, presently unidentified; actual case records. | After Q1. Open. |
| G2 | Establish why change is needed now, consequences of deferral, priorities, constraints, and who can decide scope. | Whether and where to proceed. | Business sponsor or decision-maker, presently unidentified. | After the concrete case and outcomes are understood. Open. |
| G3 | Define the missed-update measure, relevant population and time window, baseline evidence, desired target, and success-confirming role. Obtain volume from records if scale affects the decision. | Acceptance and significance of the problem. | Operator, record owner, and outcome owner; relevant records rather than recalled volume. | After Q4. Open; no measurement or target agreed. |
| G4 | Define site visibility and access boundaries, needed status freshness, and acceptance authority. | Permission scope and outcome acceptance. | Site users and responsible manager; applicable access requirements if available. | After Q5. Open. |
| G5 | Obtain the product name/version and relevant documentation or a walkthrough when available. | Every product-fit classification. | Product representative or administrator, not yet identified; versioned evidence. | Product assessment deferred pending evidence. Customer discovery continues. |

Do not expand now into migration, integration design, rollout, or performance sizing without a decision that requires those topics. Existing chat and spreadsheet use does not establish a requirement to integrate or migrate either source. No deadline is inferred for any follow-up. No one has been contacted.

## 7. Stage conclusion and continuation

**Round synthesized:** the supplied material is organized with traceable claims, missing transitions, and a bounded follow-up queue. The proposed core questions are ready for workshop preparation; attendance, timing, and evidence availability still need arrangement.

**Further discovery needed:** closure, governing authority, the cost rule, record meanings, and measurable outcomes remain unresolved. These gaps block a reliable lifecycle, approval, and acceptance definition. The absence of product evidence separately blocks all product-fit judgments. The material is not yet ready for a scoped solution assessment.

The next useful step is a record-supported walkthrough of the urgent repair, followed by targeted rule-owner and site-user follow-ups where the participants cannot answer. Once product evidence becomes available, compare only the established customer conditions with that product/version and verify the relevant paths. Update this brief with new source IDs and question resolutions; retain these original reports and any remaining differences rather than rewriting them as previously confirmed facts.
