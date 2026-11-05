Proto.page("rooms", {
  label: "会议室",
  render: function (c) {
    var r = c.rules, me = c.role.id, day = RB.day(c), esc = c.esc;
    var head = '<section class="p-card"><h2 class="p-h">会议室</h2>' +
      '<div class="p-row"><label class="p-field"><span data-proposal="FR-C01">日期</span>' +
      '<input type="date" value="' + esc(day) + '" data-action="setDay"></label>' +
      '<span data-proposal="FR-V01">点击空闲格发起新建预约</span></div>' +
      '<p class="p-pending p-review-only" data-open="Q-20">停用的会议室是否在此展示、如何标识待定；原型暂不列出停用会议室</p>' +
      (RB.manages(c)
        ? '<p class="p-pending p-review-only" data-open="Q-01">管理员与会议室的对应关系来源待定；示例数据假设管理员 M 负责会议室 A</p>' +
          '<p class="p-pending p-review-only" data-open="Q-24">管理员执行取消的位置待定；原型暂放在所管会议室的占用块上</p>'
        : "") + "</section>";

    var scale = '<div class="p-timeline" aria-hidden="true">' + RB.SLOTS.map(function (m) {
      return '<div style="font-size:11px;color:var(--muted)">' + (m % 60 ? "" : RB.hm(m)) + "</div>";
    }).join("") + "</div>";

    var rooms = RB.enabledRooms(c).map(function (room) {
      // FR-V01: valid bookings of this room on the chosen day; cancelled ones are not occupancy
      var list = c.data.bookings.filter(function (b) { return b.status === "有效" && b.room === room.id && b.date === day; });
      var cells = [], m = 9 * 60;
      while (m < 18 * 60) {
        var b = list.filter(function (x) { return r.toMin(x.start) <= m && m < r.toMin(x.end); })[0];
        if (b) {
          var end = r.toMin(b.end), span = (end - m) / 30, when = b.start + "—" + b.end;
          cells.push(r.canSeeTopic(b, room, me)
            ? '<button class="p-slot busy" style="grid-column: span ' + span + '" data-action="openBooking" data-id="' +
              esc(b.id) + '" data-rule="FR-V02" title="' + esc(when) + '">' + esc(b.topic) + "</button>"
            : '<div class="p-slot busy" style="grid-column: span ' + span + '" data-rule="FR-V02" title="' + esc(when) + '">已占用</div>');
          m = end;
        } else {
          cells.push('<button class="p-slot" data-action="pick" data-room="' + esc(room.id) + '" data-min="' + m +
            '" title="' + RB.hm(m) + '" aria-label="' + esc(room.name + " " + RB.hm(m) + " 空闲") + '"></button>');
          m += 30;
        }
      }
      return '<section class="p-card"><h2 class="p-h">' + esc(room.name) + ' <span class="p-tag">容量 ' + esc(room.capacity) + " 人</span></h2>" +
        scale + '<div class="p-timeline">' + cells.join("") + "</div></section>";
    }).join("");

    return head + rooms + RB.extras(c);
  }
});
