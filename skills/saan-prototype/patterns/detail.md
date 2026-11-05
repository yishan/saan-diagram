# Detail

Use for one record with its fields and the actions allowed on it.

```js
'<section class="p-card"><h2 class="p-h">' + c.esc(b.topic) + "</h2>" +
  '<table class="p-table"><tbody>' +
  "<tr><th>会议室</th><td>" + c.esc(b.room) + "</td></tr>" +
  "<tr><th>状态</th><td>" + c.esc(b.status) + "</td></tr>" +
  "</tbody></table>" +
  '<div class="p-row" style="margin-top:12px">' + actionButtons + "</div></section>"
```

- Fields hidden from some roles are hidden in `render`, using `c.role.id`, with the rule ID on the area: `data-rule="FR-V02"`.
