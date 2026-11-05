# List

Use for records the user scans and acts on: 我的预约, 设备, 审批记录.

```js
return '<section class="p-card"><h2 class="p-h">我的预约</h2>' +
  (rows.length ? '<table class="p-table"><thead><tr><th>会议室</th><th>时间</th><th>状态</th><th>操作</th></tr></thead><tbody>' +
    rows.map(function (b) {
      return "<tr><td>" + c.esc(b.room) + "</td><td>" + c.esc(b.start + "—" + b.end) + '</td><td><span class="p-tag">' +
        c.esc(b.status) + "</span></td><td>" + actions(b) + "</td></tr>";
    }).join("") + "</tbody></table>"
   : '<div class="p-empty" data-proposal="FR-L01">暂无预约</div>') + "</section>";
```

- Show an action only when the rule allows it, and still check the rule inside the action: the source usually says the server re-checks.
- Exception: when a scenario exists to show a rejection (for example "已被借出" in the bundled example), keep the action visible in that state so the reviewer can trigger the rejection. Say so in `trace.md`.
- Sorting and paging belong to the source. If it does not say, keep the source order and mark the order as open or proposed.
