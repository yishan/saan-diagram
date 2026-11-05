# Dialog

Use for confirmation before an irreversible action, and for a reason the source requires.

```js
Proto.action("askCancel", function (c, a) {
  c.dialog('<h2 class="p-h" data-proposal="FR-M04">取消这条预约？</h2>' +
    '<form data-action="cancel" data-id="' + c.esc(a.id) + '">' +
    '<label class="p-field"><span>取消原因</span><textarea name="reason" required></textarea></label>' +
    '<div class="p-row"><button class="p-btn danger">确认取消</button>' +
    '<button type="button" class="p-btn" data-action="closeDialog">返回</button></div></form>');
});
Proto.action("closeDialog", function (c) { c.close(); });
```

- Call `c.close()` at the end of the confirming action.
- If the source does not ask for confirmation, a dialog is a proposal: put `data-proposal` on its title.
