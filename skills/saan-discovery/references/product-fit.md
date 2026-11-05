# Product baseline and fit assessment

## Build a scoped baseline

For each relevant capability, record its object, behavior or rule, configuration dimensions, limits, source/version, and evidence scope. Use supplied manuals, specifications, code, environment settings, or observed runs when accessible. Do not invent missing capability evidence or require code access for ordinary interview preparation.

Map product terms to customer terms explicitly. Identical words can name different objects; different words can describe the same object. Preserve unresolved mappings.

| Product dependency | Customer information to establish | Decision it informs |
|---|---|---|
| A consumer journey requires registration or purchase before value is experienced | The person's trigger, current alternative, trust/effort concerns, and actual point of abandonment | Whether the proposed journey fits the context; adoption remains a separate hypothesis |
| Notifications or repeat use are central to the intended experience | Actual recurrence of the need, user control, context, and interruptions | Whether the repeat-use assumption and interaction fit the person's task |
| A request belongs to one parent object | Actual relationship and exceptional cases | Whether the object model fits |
| Routing uses amount and organization | Amount basis, boundary, organization meaning, authority | Whether available configuration expresses the rule |
| A fixed lifecycle controls actions | Entry/exit conditions, corrections, effective time | Whether state transitions fit actual work |
| Role-based actions and data scopes | Who may see, modify, approve, or act across organizations | Permission and responsibility mapping |
| An external data source | Authority, identifiers, timing, failure handling, reconciliation owner | Integration scope and operational ownership |
| Reports consume business records | Who supplies each value, when, definition, corrections | Whether the desired measure can be trusted |

Also start from the customer's task, independently of the product menu. Look for offline coordination, unmodeled objects, and outcomes the customer needs. Do not persuade the customer to change merely to preserve a product-fit label.

## Classify with an evidence boundary

For each item use: customer condition and source; product behavior and source; fit category; evidence boundary; impact; next verification. Keep partial coverage visible.

| Category | Evidence needed | Common overclaim to avoid |
|---|---|---|
| Existing coverage / 已有能力覆盖 | Matching customer conditions and product behavior at a stated version/evidence level | A manual or demo proves the customer's production workflow works |
| Configurable fit / 可配置适配 | The needed dimensions and boundaries are available and can express the rule | A configurable threshold implies arbitrary routing is configurable |
| Business-practice change / 业务做法调整 | Named change to people's work, cost, constraints, and authority | The customer has agreed because the agent recommends it |
| Integration / 系统集成 | Both systems' capabilities, authority, timing, and responsibility | Missing integration evidence proves a connector exists or is absent |
| Capability gap / 产品能力缺口 | A necessary customer behavior contradicts a verified product limit | The manual does not mention it, therefore the product lacks it |
| Unverified / 待核实 | A customer rule or product capability lacks sufficient evidence | A plausible implementation is treated as confirmed coverage |

Categories may be combined. If only documentation is available, label a match as a documented fit candidate with runtime/customer validation pending. If a necessary condition is unknown, retain an unverified judgment for that condition rather than filling it from convention.

A source can establish a narrow negative: a documented one-contract limit contradicts a verified multi-contract requirement for that version. That does not prove a later version or an add-on cannot address it.

## Preserve decisions and measurement limits

Keep a requested outcome separate from an approved requirement. For a metric, record its definition, population, time window, baseline source, target source, measurement method, and acceptance authority where known. A few case durations do not establish an organization-wide baseline or service guarantee.

Do not promise implementation, price, delivery dates, or benefits. Identify what needs design or technical assessment next. Where a critical unknown affects only one branch, continue evaluating other supported branches and clearly exclude the blocked one.
