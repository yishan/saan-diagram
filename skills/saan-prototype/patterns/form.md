# Form

Use for create and edit: 新建预约, 改期.

```js
'<form class="p-card" data-action="book">' +
  '<label class="p-field"><span>会议主题</span><input name="topic" required></label>' +
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
- Field limits the source leaves open (for example a length limit) stay unenforced and get a `data-open` note next to the field.
- On failure keep the user on the form unless the source says otherwise.
