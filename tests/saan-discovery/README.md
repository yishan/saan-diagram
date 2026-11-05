# Discovery behavioral evaluation

All fixtures are fictional. They are not product capability statements or customer evidence.

Evaluate the copied standalone skill in a fresh context with only the relevant fixture directory. Do not give the runner the rubric or intended answers. Save its actual deliverables before review. No external communication, live customer data, or credentials are needed.

## Scenarios

1. **Prepare:** create a 30-minute role-specific guide from `fixtures/prepare/`.
2. **Synthesize, then continue:** synthesize `fixtures/synthesis/` except `follow-up.md`; later provide that file and ask the same runner to update its brief.
3. **No product:** create an interim English brief from `fixtures/no-product/`, without inventing product behavior or waiting indefinitely for the absent user.

## Reviewer rubric

Inspect the generated meaning and cited evidence, not headings or exact wording.

| Criterion | Where to check |
|---|---|
| Reuses known product facts; asks missing customer conditions | Prepare |
| Uses recent-case, neutral prompts and routes absent-role questions | Prepare |
| Connects questions to the decision; respects the available time | Prepare |
| Separates business execution from approval | Synthesis, including failed payment |
| Keeps policy, operator account, and unobserved review steps distinct | Synthesis |
| Does not fill the equality boundary or tax basis from convention | Synthesis before follow-up |
| Preserves product evidence levels; no connector invented from silence | All applicable scenarios |
| Keeps reported multi-contract practice and documented limit visible | Synthesis |
| Treats desired two-day completion and two case durations with correct limits | Synthesis |
| Routes the user's unknown OA rules to a suitable role | Synthesis |
| New evidence updates stable questions; UAT configuration is not production validation | Continuation |
| Continues customer research when product evidence is missing | No product |
| Does not invent respondent answers, assignments, dates, metrics or acceptance | All |

Report failures and revisions explicitly. A passing simulation does not establish real interview effectiveness or superiority over an unassisted model. This is a workflow evaluation, not an A/B benchmark.

## Recorded run

The [2026-11-04 results](results/2026-11-04/) preserve the raw inputs and outputs, including the initial long brief, the compact retest with a presupposed closure question, and the later targeted correction. See the [review and validation record](../../docs/saan-discovery/validation.zh-CN.md) for outcomes and limits. `question-check/request.txt` records the additional focused request. Snapshot inputs intentionally duplicate the fixtures so each run remains inspectable after future fixture edits.

## v0.2.0 interactive and research-type cases

The [v0.2.0 results](results/2026-11-04-v0.2/) preserve three independent contexts and seven task responses. Each interactive conversation contains its exact simulated user inputs and actual outputs; use them to replay turns in order. Keep later inputs hidden until their turn. The enterprise case contains raw materials and a direct-output request. The runners did not receive this reviewer checklist:

- **Consumer:** ambiguous activity-product setup, then an explicit ToC scope, then two secondhand user accounts and a request to skip unknown experiences. Check whether the assistant asks a consequential next question, respects the agreed scope, routes actual experiences to the respondents, and avoids inventing causes or population findings.
- **Public service:** street-office procurement, resident booking, and service-point delivery. Check whether both perspectives remain present, reservation approval stays distinct from service completion, missing service details stay unknown, and excluded procurement/budget topics stay excluded.
- **Enterprise direct:** known ToB scope and an explicit request for a concise interim synthesis without questions. Check whether the artifact is delivered without a setup gate and preserves material rule and product-evidence limits.

The [v0.2.0 review](../../docs/saan-discovery/validation-v0.2.zh-CN.md) records actual observations and the package/page checks. These are text-based interaction checks, not a test of a host's question UI, nor a full rerun of the v0.1.0 scenarios.
