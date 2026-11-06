/* 4.1.1 查看会议室占用 and 4.3.1 管理员取消预约 (location per Q-24 still open). */
Proto.page("rooms", {
  label: "会议室",
  render: function (c) {
    var R = RB.R, day = c.data.day || RB.today(c);    // default to today is a proposal (4.1.1)
    var isAdminRole = c.data.rooms.some(function (r) { return R.isAdmin(c.data.rooms, r.id, c.role.id); });
    var slots = []; for (var m = 9 * 60; m < 18 * 60; m += 30) slots.push(m);
    var head = '<div class="p-timeline" aria-hidden="true">' + slots.map(function (m) {
      return '<div class="p-cell-sub">' + (m % 60 === 0 ? RB.hhmm(m) : "") + "</div>";
    }).join("") + "</div>";

    function timeline(room) {
      var dayBookings = c.data.bookings.filter(function (b) {   // FR-V01: 已取消 is not shown as occupied
        return b.room === room.id && b.date === day && b.status === "有效";
      });
      var out = [], skip = 0;
      slots.forEach(function (m) {
        if (skip > 0) { skip--; return; }
        var b = dayBookings.filter(function (x) { return R.min(x.start) === m; })[0];
        if (b) {
          var span = (R.min(b.end) - R.min(b.start)) / 30; skip = span - 1;
          var seen = R.canSeeTopic(b, c.role.id, c.data.rooms);
          var label = seen ? b.topic : "已占用";
          var st = ' style="grid-column: span ' + span + '"';
          var tip = c.esc(b.start + "—" + b.end + " " + label);
          if (b.creator === c.role.id && R.canModify(b, c.role.id, c.now)) {
            out.push('<button class="p-slot busy"' + st + ' title="' + tip + '" data-action="startReschedule" data-id="' + c.esc(b.id) +
              '" data-rule="FR-V02" data-proposal="FR-L03">' + c.esc(label) + "</button>");
          } else if (b.creator !== c.role.id && R.adminCanCancel(b, c.role.id, c.data.rooms, c.now)) {
            out.push('<button class="p-slot busy"' + st + ' title="' + tip + '" data-action="askAdminCancel" data-id="' + c.esc(b.id) +
              '" data-rule="FR-V02 FR-M01">' + c.esc(label) + "</button>");
          } else {
            out.push('<div class="p-slot busy"' + st + ' title="' + tip + '" data-rule="FR-V02">' + c.esc(label) + "</div>");
          }
          return;
        }
        var busy = dayBookings.some(function (x) { return R.min(x.start) < m && m < R.min(x.end); });
        if (busy) return;  // covered by a block that starts before 09:00 (not possible under FR-C02)
        out.push('<button class="p-slot" data-action="pick" data-room="' + c.esc(room.id) + '" data-min="' + m +
          '" aria-label="' + c.esc(room.name + " " + RB.hhmm(m) + " 空闲，新建预约") + '"></button>');
      });
      return '<div class="p-timeline">' + out.join("") + "</div>";
    }

    var shown = c.data.rooms.filter(function (r) { return r.enabled; });
    var rows = shown.map(function (r) {
      return "<tr><td>" + c.esc(r.name) + '<span class="p-cell-sub" data-open="Q-14">容量 ' + c.esc(r.capacity) + " 人</span></td><td>" +
        timeline(r) + "</td></tr>";
    }).join("");

    return '<section class="p-card"><h2 class="p-h">会议室</h2>' +
      '<div class="p-row" data-component="FilterBar">' +
        '<label class="p-field" data-component="Field"><span data-proposal="FR-V01">日期</span>' +
        '<input type="date" value="' + c.esc(day) + '" data-action="setDay"></label>' +
        '<span class="p-cell-sub" data-proposal="FR-V01">点击空闲格新建预约；点击本人预约可改期</span>' +
      "</div>" +
      '<table class="p-table" data-component="DataTable"><thead><tr><th>会议室</th><th data-proposal="FR-V01">占用（09:00—18:00，每格半小时）</th></tr></thead>' +
      "<tbody><tr><td></td><td>" + head + "</td></tr>" + rows + "</tbody></table>" +
      '<p class="p-pending p-review-only" data-open="Q-20">停用的会议室（示例中的会议室 C）是否在此展示、如何标识待定，原型暂不列出</p>' +
      "</section>" +
      (isAdminRole ? '<section class="p-card p-review-only"><h2 class="p-h">管理员视角待定事项</h2>' +
        '<p class="p-pending" data-open="Q-24">管理员取消他人预约的入口位置待定：原型暂放在本页所管会议室的占用块上</p>' +
        '<p class="p-pending" data-open="Q-01">管理员与会议室的对应关系来源待定：原型按示例数据中 M 负责会议室 A 演示</p>' +
        '<p class="p-pending" data-open="Q-19">占用块是否显示预约人待定：原型只显示主题</p>' +
        '<p class="p-pending" data-open="Q-26">管理员本人在所管会议室的预约，点击后按预约人规则进入改期；取消走哪条路径待定</p>' +
        "</section>" : "") +
      RB.directPanel(c);
  }
});

Proto.action("setDay", function (c, a) { c.data.day = a.value; });

Proto.action("pick", function (c, a) {
  var start = Number(a.min);
  c.data.draft = { room: a.room, date: c.data.day || RB.today(c), start: RB.hhmm(start), end: RB.hhmm(start + 30), topic: "" };
  c.go("book");
});

Proto.action("askAdminCancel", function (c, a) {
  var b = RB.find(c, a.id);
  c.confirm({
    title: "取消这条预约？", proposal: "FR-M04", component: "ChangeConfirm",
    body: '<div class="p-field read" data-component="Field"><span>预约</span><div>' +
      c.esc(RB.roomName(c, b.room) + " " + b.date + " " + b.start + "—" + b.end + " " + b.topic) + "</div></div>" +
      '<label class="p-field" data-component="Field"><span data-rule="FR-M03">取消原因 *</span><textarea name="reason"></textarea></label>' +
      '<p class="p-pending p-review-only" data-open="Q-25">原因长度上限、纯空格是否算未填写待定</p>',
    changes: [{ label: "状态", from: "有效", to: "已取消" }],
    effects: [
      { text: "释放该时段的占用，其他人可预约", rule: "FR-M04" },
      { text: "保存操作人、取消时间和取消原因", rule: "FR-M04" },
      { text: "预约人的「我的预约」中该记录显示「已取消」", rule: "FR-M04" },
      { text: "是否通知预约人待定", open: "Q-10" },
      { text: "取消原因谁能查看、保存多久待定", open: "Q-08" },
      { text: "与预约人同时改期或取消时以哪个为准待定", open: "Q-18" }
    ],
    confirm: { text: "确认取消", proposal: "FR-M04" }, danger: true, data: { id: b.id }
  }, "adminCancel");
});

Proto.action("adminCancel", function (c, a) {
  var b = RB.find(c, a.id);
  var why = RB.R.adminCancelProblem(b, c.role.id, c.data.rooms, a.fields.reason, c.now);
  if (why === "blocked") { c.close(); return RB.say(c, "mBlocked"); }
  if (why === "reason") return RB.say(c, "mReason");
  b.status = "已取消"; b.cancelBy = c.role.id; b.cancelAt = RB.nowText(c); b.cancelReason = a.fields.reason;
  c.close();
  RB.say(c, "mOk");
});
