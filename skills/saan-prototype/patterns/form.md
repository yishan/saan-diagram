# Form

Use for create and edit: 新建预约, 改期.

```js
'<form class="p-card" data-action="book">' +
  '<label class="p-field"><span>会议主题 *</span><input name="topic" value="' + c.esc(d.topic || "") + '"></label>' +
  '<label class="p-field"><span>开始时间</span><select name="start">' + options + "</select></label>" +
  '<div class="p-row"><button class="p-btn primary" data-proposal="FR-B05">提交预约</button>' +
  '<button type="button" class="p-btn" data-go="rooms">返回</button></div></form>'
```

```js
Proto.action("book", function (c, a) {
  var f = a.fields;                       // form values by name
  var why = c.rules.bookingProblem(f, c.data, c.now);
  if (why) return c.flash(why.text, { kind: "error", rule: why.rule });
  c.data.bookings.push({ /* … */ status: "有效" });
  c.flash("预约成功", { proposal: "FR-B05" });
  c.go("mine");
});
```

- A form submits through `data-action` on the `<form>`; values arrive in `a.fields`.
- Do not use the HTML `required` attribute. The browser would block an empty submit, so the rule's rejection (for example "主题为空被拒") could never be shown. Mark the field with ` *` and let the rule reject.
- Every action re-renders the page. If a field has its own `data-action`, keep what the user has typed in `c.data` (a draft object, `d` above) and render the form from it.
- To show a message on the next page, switch first: `c.go("mine"); c.flash("预约成功", {…})` or the reverse both work; an old message from an earlier action is cleared automatically.
- Field limits the source leaves open (for example a length limit) stay unenforced and get a `data-open` note next to the field.
- On failure keep the user on the form unless the source says otherwise.
- A form can be a sub-page (`Proto.page("book", {nav: false, …})`) or a dialog (`c.dialog(html)`). Prefer a dialog when the source names no page for it.
- A date or filter field can refresh the page by itself: `<input type="date" name="day" data-action="setDay">`, then `Proto.action("setDay", function (c, a) { c.data.day = a.value; })`.
