/* 4.1.1 查看会议室占用；4.3.1 管理员取消的入口（位置待定 Q-24） */
Proto.page("rooms", {
  label: "会议室",
  render: function (c) {
    var R = c.rules, date = c.data.viewDate || R.today(c.now);
    var isAdmin = c.data.rooms.some(function (r) { return R.isRoomAdmin(r, c.role.id); });
    var head = "";
    for (var h = 9 * 60; h < 18 * 60; h += 30)
      head += '<div style="font-size:11px;color:var(--muted)">' + (h % 60 ? "" : c.esc(R.hhmm(h))) + "</div>";

    function timeline(room) {
      var cells = "", m = 9 * 60;
      while (m < 18 * 60) {
        var b = c.data.bookings.filter(function (x) {      // FR-V01：只显示有效预约
          return x.status === "有效" && x.room === room.id && x.date === date && R.toMin(x.start) <= m && m < R.toMin(x.end);
        })[0];
        if (b) {
          var end = R.toMin(b.end), span = (end - m) / 30, when = b.start + "—" + b.end;
          var style = ' style="grid-column: span ' + span + '"';
          cells += R.canSeeTopic(b, room, c.role.id)
            ? '<button class="p-slot busy"' + style + ' title="' + c.esc(when + " " + b.topic) + '" data-action="openBooking" data-id="' + c.esc(b.id) + '" data-rule="FR-V02">' + c.esc(b.topic) + "</button>"
            : '<div class="p-slot busy"' + style + ' title="' + c.esc(when) + ' 已占用" data-rule="FR-V02">已占用</div>';
          m = end;
        } else {
          cells += '<button class="p-slot" title="' + c.esc(R.hhmm(m)) + ' 空闲" data-action="pick" data-room="' + c.esc(room.id) +
            '" data-date="' + c.esc(date) + '" data-start="' + c.esc(R.hhmm(m)) + '"></button>';
          m += 30;
        }
      }
      return '<div class="p-timeline">' + head + '</div><div class="p-timeline" style="margin-top:2px">' + cells + "</div>";
    }

    var rooms = c.data.rooms.filter(function (r) { return R.roomEnabled(r); }).map(function (r) {
      return '<section class="p-card"><div class="p-row" style="margin-bottom:8px"><strong>' + c.esc(r.name) + "</strong>" +
        '<span style="color:var(--muted)">容量 ' + c.esc(r.capacity) + "</span></div>" + timeline(r) + "</section>";
    }).join("");

    return '<section class="p-card"><h2 class="p-h">会议室</h2>' +
      '<form class="p-row" data-action="setDate">' +
      '<label class="p-row"><span data-proposal="FR-C08">日期</span><input type="date" name="date" value="' + c.esc(date) + '"></label>' +
      '<button class="p-btn" data-proposal="FR-C08">查看</button>' +
      '<span style="color:var(--muted)" data-proposal="FR-C01">默认显示当天；时间均为 Asia/Shanghai</span></form>' +
      '<p style="color:var(--muted)" data-proposal="FR-V01">以半小时为格，覆盖 09:00—18:00。点击空闲格发起新建预约；点击可看到主题的占用块查看详情</p>' +
      '<p class="p-pending p-review-only" data-open="Q-20">停用的会议室（示例中的会议室 C）是否在此展示、如何标识待定，原型暂不列出</p>' +
      (isAdmin ? '<p class="p-pending p-review-only" data-open="Q-01 Q-24">管理员与会议室的对应关系来源待定，原型按示例数据：M 负责会议室 A；管理员取消入口是否就在本页待定，原型暂放在本页占用块的详情中</p>' : "") +
      "</section>" + rooms;
  }
});
Proto.action("setDate", function (c, a) {
  if (a.fields.date) c.data.viewDate = a.fields.date;
});
