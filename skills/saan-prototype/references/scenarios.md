# Scenarios

A scenario is the starting point for one review conversation. Switching scenarios resets the data.

```json
{"id": "ac08", "label": "并发提交同一时段", "acceptance": ["AC-08"], "role": "emp_yi",
 "now": "2026-11-10T13:50:00+08:00", "page": "rooms",
 "data": {"rooms": [], "bookings": []}}
```

- `id`: unique, short. `label`: what the reviewer sees in the picker.
- `acceptance`: acceptance-scenario IDs this scenario demonstrates. One scenario may cover several; leave it empty only for an orientation scenario.
- `role`: a role `id` from the manifest. The reviewer can still switch roles.
- `now`: an ISO time with offset. Rules about "already started", deadlines, or lead time read `c.now`. Pick a time that makes the scenario's rule visible.
- `page` (optional): the page to open.
- `data`: fictional records. Any `status` value must be one of `manifest.states`.

## Choosing scenarios

1. Start from the acceptance scenarios. Make one scenario per case that can be shown in the interface.
2. Cases that need concurrency, back-end bypass, or time passing cannot be fully shown. Show the visible half (for example the conflict message for the second submitter) and say in `trace.md` what is not demonstrated.
3. A rule the interface enforces by not offering the choice (for example, only tomorrow can be picked) has no rejection to show. Demonstrate it by its absence and say so in `trace.md`.
4. Some acceptance checks say "submit directly, bypassing the interface" (the server re-checks). Show them with a review-only panel: `<div class="p-card p-review-only" data-rule="FR-…">` holding buttons such as 「直接提交：取消」 that call the same action with the forbidden input. The panel hides when annotations are off; label it as a review aid, not interface design.
5. Keep the data small: enough records to show the rule, no more.
6. Use the source's own example names when it gives them (甲、乙、会议室 A); otherwise use neutral placeholders.
