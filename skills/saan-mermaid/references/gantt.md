# gantt

Header: `gantt`. Since 8.0. Example: `assets/examples/gantt.mmd`.

Saan use: schedules with dependencies. Use `timeline` for milestones without dates.

## Syntax

- `dateFormat YYYY-MM-DD`, `axisFormat %m-%d`, then `todayMarker off`.
- Task: `需求确认 :a1, 2026-01-05, 10d`. With three or more values the first is the task ID.
- Dependency: `开发 :a2, after a1, 20d`. Several: `after a1 a2`.
- Tags before the values: `crit`, `done`, `active`, `milestone`.

## Pitfalls

- `after` naming an ID that does not exist (GT1) or a dependency loop (GT2) breaks the schedule.
- Without `todayMarker off`, the red "today" line moves with the viewing date (GT3).
- Tasks without an ID cannot be referenced. Give every task that others depend on an ID.
