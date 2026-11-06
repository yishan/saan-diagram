# Design profile

A design profile makes the prototype look and read like the user's design system: its colours, its component names, and its wording rules. It changes presentation only. It never adds pages, steps, or rules to the source.

## When to use one

Use a profile when the user mentions a design system, a design spec, or a component library (设计系统、设计规范、组件库), or gives a profile folder. If they do not, do not ask: use a bundled theme, and say in the delivery that a design profile can be specified. `assets/design-example/` is a fictional profile that shows the format.

## Format

A profile is a folder with two files:

```text
<design>/
  design.json   name, version, themes, components, content rules (read by the scripts)
  guide.md      layout and interaction rules in prose (read by you, not by the checker)
```

`design.json`:

| Key | Required | Value |
|---|---|---|
| `name` | yes | The profile's name, shown in the review bar: 按《示例规范 1.0》 |
| `version` | no | Text, for example `"1.0"` |
| `themes` | yes, at least one | Theme name → token object with the same keys as `themes/*.json`: `label`, `bg`, `surface`, `border`, `text`, `muted`, `accent`, `accent_text`, `danger`, `notice`, `radius`, `font_size`, plus an optional `success`. Every theme must pass the contrast check; `success` needs 4.5:1 against `surface`. |
| `components` | no | Component name (as in the design system) → `{"use": …, "rule": …}`. `use` names the runtime component it maps to: `status`, `actions`, `confirm`, `field`, `filter`, or `table`; see [components](../patterns/components.md). A component without `use` is built from the basic runtime classes. `rule` is one sentence on when to use it; it appears in the badge tooltip. |
| `content` | no | `forbid`: `[{"text", "message"}]`, text that may not appear in `pages/*.js` or `rules.js` outside comments (attribute values included); sample data in `scenarios.json` is not checked, so keep it clean yourself. `button_forbid`: the same shape, matched only when a button's whole label equals `text`, so 确定 is caught and 确定人选 is not. Plain text, no regular expressions. |

The profile's themes replace the bundled ones; the theme menu shows only the profile's themes. Token names that differ in the design system are mapped once, by whoever writes the profile, not at run time. Rules that cannot be written as fixed text (one primary button per view, long forms on one page, short tasks only in dialogs) go into `guide.md`.

## Copy it into the prototype

Like `source.md`, copy `design.json` and `guide.md` into `prototype/design/`, so the folder still builds after it is moved. In `manifest.json`:

```json
"design": "design/design.json",
```

Remove `theme`, or set it to one of the profile's theme names. Without `theme` the first theme in the profile is used. Name the profile in the scope list: "4 pages, 2 roles, 9 scenarios, following 《示例规范 1.0》".

## Build pages with it

- Pick components first. For each block, read `components` and choose the one whose `rule` fits; then lay out the page as `guide.md` says.
- Write `data-component="Name"` on each block that stands for a profile component: a table, a card, a field, a control. On a `<tr>` or `<tbody>` the badge goes into the first cell; on a `<table>`, list, or form field it goes just before it. For a confirmation, pass `component` to `c.confirm`. The name must be a key in `components`.
- The review bar gets a 组件名 switch. It is off by default and independent of 标注: reviewers turn it on to see the component names, developers use it to match the component library.
- When the profile has no component for something, build it from the basic classes in `patterns/` and write "外观近似" for it in `trace.md`. Do the same for components without `use`.
- Use theme tokens through the runtime classes; never write colour values in pages.
- In `trace.md`, add a 页面—组件 table: each page, the components it uses, and which of them are only approximate.

```markdown
## 页面—组件

| 页面 | 组件 | 外观近似 |
|---|---|---|
| 预约管理 | DataTable、StatusBadge、ChangeConfirm | PeriodPicker（用 p-field 和 select 搭建） |
```

## Conflicts with the source

The source wins. When the profile asks for something the source does not describe, for example a confirmation step before an action the source performs directly, the addition is a proposal: a confirmation box the source does not ask for gets `proposal` on its title. Write every conflict into `trace.md`. A profile never turns an open question into a decided behaviour.

## Only documentation, no design.json

When the user has design-system documents but no profile, you may draft one: map the documented tokens to the theme keys, list the components with `use` and `rule`, copy fixed wording rules into `content`, and put the rest into `guide.md`. Mark the draft in both files: put a line at the top of `guide.md` saying the profile is a draft awaiting confirmation (草稿，待确认), and add `"status": "草稿，待确认"` to `design.json` (a text line there would break the JSON and fail M1; unknown keys are accepted). Show it to the user, and use it only after they confirm. Do not copy a real company's design system into examples or tests; keep examples fictional.

## Checks

With `design` in the manifest, `check.py` adds D checks. Without a profile none of them runs.

| Code | Level | Meaning |
|---|---|---|
| D1 | 必须修改 | A `data-component` name is not in the profile's `components` |
| D2 | 必须修改 | Page or rule wording contains a `forbid` text, or a button label equals a `button_forbid` text |
| D2 | 业务发现 | The forbidden text is inside wording the source confirms (`confirmed_text`) |
| D3 | 提示 | A page file has more than one primary button (`p-btn` with `primary`) |
| D4 | 必须修改 | A page or rule file writes a colour value instead of using the runtime classes or theme tokens |
| B2 | 必须修改 | A profile theme fails the contrast check or misses a token |
| M1 | 必须修改 | `design.json` is missing, cannot be parsed, or has the wrong shape (no theme, an unknown `use`) |

A D2 业务发现 is handled like any 业务发现: report it to the user, and do not change confirmed wording, the source, or the manifest to make it pass. Confirmed wording stays exactly as the source has it, even when the profile forbids part of it.

The checks are text scans of static code, so know their limits:

- D2 and D4 read page and rule code line by line, with comments removed. A `//` inside a string that follows a space, or a comment directly after `)`, can be misread, so a hit or a miss there may be wrong.
- D4 only sees CSS-style declarations (`color: #…`, `background: rgb(…)`), not colours assigned in JavaScript.
- D3 counts class attributes that contain both `p-btn` and `primary` in each page file. Mutually exclusive branches count twice, which is why it is only a note.
- No check reads `guide.md` or judges whether the layout follows it.
