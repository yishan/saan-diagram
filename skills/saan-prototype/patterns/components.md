# Components

Use with a [design profile](../references/design-profile.md). Each `use` value in `design.json` maps to one of the runtime components below. They resemble common ToB components closely enough for a review; they are not a component library. Write `data-component` with the profile's name on each block, and keep the annotations from [annotations](../references/annotations.md): a component changes how something looks, not whether it is confirmed.

## status

Colour, icon, and text together, never colour alone. `data-tone` is `neutral`, `success`, `notice`, or `danger`.

```js
var TONE = {"有效": "success", "已取消": "neutral"};
'<span class="p-status" data-component="StatusBadge" data-tone="' + (TONE[b.status] || "neutral") + '">' + c.esc(b.status) + "</span>"
```

- The status text comes from the source states. Choosing a tone is presentation; it needs no annotation.

## actions

Keep an action that cannot run visible, with the reason next to it. Show it as `<button class="p-btn" disabled data-disabled-reason="…">`; the runtime shows the text beside the button and links it with `aria-describedby`. The runtime blocks only disabled buttons, so do not use a link with `data-action` for an unavailable action: `<a>` has no `disabled`. `data-disabled-reason` on a field still shows the reason, but not on `<option>`.

```js
var why = c.rules.cancelBlocked(b, c.now);  // null, or the reason text
'<div class="p-row" data-component="ActionBar">' +
  (!why ? '<button class="p-btn" data-action="askCancel" data-id="' + c.esc(b.id) + '">取消预约</button>'
        : '<button class="p-btn" disabled data-rule="FR-B05" data-disabled-reason="' + c.esc(why) + '">取消预约</button>') +
  "</div>"
```

- The reason comes from the rule function. If the source does not word it, the reason is a proposal: add `data-proposal`.
- When a scenario exists to show a rejection, keep the action enabled in that state instead, as in [list](list.md).

## confirm

Lists each change as old → new and the consequences, and runs the action only after the user confirms. Room-booking, an administrator cancelling someone else's booking (FR-M01—FR-M04):

```js
Proto.action("askCancel", function (c, a) {
  c.confirm({
    title: "取消这条预约？", proposal: "FR-M04", component: "ChangeConfirm",
    body: '<label class="p-field"><span>取消原因 *</span><textarea name="reason"></textarea></label>',
    changes: [{label: "状态", from: "有效", to: "已取消"}],
    effects: ["释放该时段的占用", {text: "预约人能否看到取消原因待定", open: "Q-08"}],
    confirm: {text: "确认取消", proposal: "FR-M04"}, danger: true, data: {id: a.id}
  }, "cancel");
});
Proto.action("cancel", function (c, a) {
  var b = c.data.bookings.filter(function (x) { return x.id === a.id; })[0];  // ids kept as strings
  var problem = c.rules.adminCancelProblem(b, a.fields.reason, c.now);  // FR-M03: null or the reason text
  if (problem) return c.flash(problem, {kind: "error", rule: "FR-M03"});
  b.status = "已取消"; b.cancelReason = a.fields.reason;
  c.close();
  c.flash("已取消这条预约", {proposal: "FR-M04"});
});
```

`c.confirm(opt, actionName)` renders a form whose submit runs `actionName`; 返回 closes it without changes.

| Key | Value |
|---|---|
| `title` | The question. `proposal`, `open`, or `rule` next to it annotate the title. |
| `body` | Raw HTML placed under the title, for example a reason field. Fields arrive in the action as `a.fields`, by `name`. |
| `changes` | `[{label, from, to}]`, one row per changed value |
| `effects` | Strings, or `{text, proposal, open, rule}`. An effect with `open` renders as a pending item and is hidden when 标注 is off. |
| `confirm` | `{text: …, proposal: …}`. Always write `text`, and write it first: D2 reads the button label only when `text` is the first key. Without it the button says 确认. |
| `danger` | `true` for a destructive action: the button uses the danger style instead of primary |
| `component` | The profile's component name, for example `"ChangeConfirm"`; written as `data-component` on the form and checked by D1 |
| `data` | `{key: value}` passed to the action. Values arrive as strings (they pass through `dataset`), and camelCase keys come back camelCase: `data: {bookingId: b.id}` arrives as `a.bookingId`, a string. Compare with `String(id)`, or keep ids as strings. |

- `c.confirm` only changes how the step looks. The confirming action still calls the rule functions, shows their feedback, and calls `c.close()` when it succeeds.
- If the source has no confirmation step, the confirmation itself is a proposal: put `proposal` on the `title`.
- Consequences the source does not state are proposals; consequences that depend on an open question use `open`, never an invented answer.
- No `required` attribute in `body`, so an empty reason can be rejected by the rule, as in [dialog](dialog.md).

## field

Read-only values are text, not disabled inputs. When editing changes a value, `data-changed-from` shows the old value below the field value.

```js
'<div class="p-field read" data-component="Field"><span>会议室</span><div>' + c.esc(b.room) + "</div></div>" +
'<div class="p-field read" data-component="Field"' + (old.time !== b.time ? ' data-changed-from="' + c.esc(old.time) + '"' : "") + '><span>时间</span><div>' + c.esc(b.time) + "</div></div>"
```

## filter

Common conditions stay visible; the rest fold into 更多条件 with a count of the hidden conditions in effect.

```js
var hidden = [c.data.filter.room].filter(Boolean).length;  // hidden conditions in effect
'<div class="p-row" data-component="FilterBar">' +
  '<label class="p-field"><span>状态</span><select data-action="filterStatus">…</select></label>' +
  '<details class="p-filter"><summary>更多条件 <span class="p-count">' + hidden + "</span></summary>" +
    '<label class="p-field"><span>会议室</span><select data-action="filterRoom">…</select></label>' +
  "</details></div>"
```

- Show only filters the source describes. Which ones stay visible follows the profile's `rule` or `guide.md`; if neither says, it is a proposal.

## table

`.p-table` with `.p-cell-sub` for a second line inside a cell: the main value, then its explanation.

```js
'<table class="p-table" data-component="DataTable"><thead><tr><th>会议室</th><th>时间</th><th>状态</th></tr></thead><tbody>' +
  rows.map(function (b) {
    return "<tr><td>" + c.esc(b.room) + '<span class="p-cell-sub">' + c.esc(b.floor) + "</span></td><td>" +
      c.esc(b.start + "—" + b.end) + "</td><td>" + status(b) + "</td></tr>";
  }).join("") + "</tbody></table>"
```

- `data-component` on a `<tr>` or `<tbody>` puts the badge in the first cell.
