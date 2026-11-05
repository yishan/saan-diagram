# Timeline

Use for occupancy over a day, in fixed slots: 会议室占用, 排班.

```js
var slots = [];                         // one entry per half hour, 09:00—18:00
for (var m = 9 * 60; m < 18 * 60; m += 30) slots.push(m);
'<div class="p-timeline">' + slots.map(function (m) {
  var b = busyAt(room, m);
  return b ? '<div class="p-slot busy" data-rule="FR-V02">' + c.esc(canSeeTopic(b) ? b.topic : "已占用") + "</div>"
           : '<button class="p-slot" data-action="pick" data-room="' + c.esc(room.id) + '" data-min="' + m + '"></button>';
}).join("") + "</div>"
```

- Slot size and day range come from the source; do not widen them.
- What a viewer may see inside a busy slot is a rule; name it.
