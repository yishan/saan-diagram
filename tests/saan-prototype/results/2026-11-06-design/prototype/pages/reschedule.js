/* 4.2.3 改期. A full page, as the profile's guide asks for edit. */
Proto.page("reschedule", {
  label: "改期", nav: false, proposal: "FR-R01",
  render: function (c) {
    var e = c.data.edit, b = e && RB.find(c, e.id);
    if (!b) return '<section class="p-card"><div class="p-empty">请从「我的预约」选择要改期的预约</div>' +
      '<div class="p-row"><button class="p-btn" data-go="mine">返回我的预约</button></div></section>';
    var rooms = c.data.rooms.filter(function (r) { return r.enabled; })
      .map(function (r) { return { value: r.id, label: r.name + "（容量 " + r.capacity + " 人）" }; });
    function changed(key, text) { return e[key] !== b[key] ? ' data-changed-from="' + c.esc(text) + '"' : ""; }
    return '<form class="p-card" data-action="reschedule" data-id="' + c.esc(b.id) + '">' +
      '<h2 class="p-h" data-proposal="FR-R01">改期</h2>' +
      '<h3 class="p-h">原预约</h3>' +
      '<div class="p-row">' +
        '<div class="p-field read" data-component="Field"><span>会议室</span><div>' + c.esc(RB.roomName(c, b.room)) + "</div></div>" +
        '<div class="p-field read" data-component="Field"><span>日期</span><div>' + c.esc(b.date) + "</div></div>" +
        '<div class="p-field read" data-component="Field"><span>时段</span><div>' + c.esc(b.start + "—" + b.end) + "</div></div>" +
        '<div class="p-field read" data-component="Field" data-rule="FR-R01"><span>会议主题</span><div>' + c.esc(b.topic) + "</div></div>" +
      "</div>" +
      '<h3 class="p-h" data-proposal="FR-R03">改期目标</h3>' +
      '<label class="p-field" data-component="Field"' + changed("room", RB.roomName(c, b.room)) + '><span>目标会议室</span><select name="room">' + RB.opts(rooms, e.room) + "</select></label>" +
      '<div class="p-row">' +
        '<label class="p-field" data-component="Field"' + changed("date", b.date) + '><span>目标日期</span><input type="date" name="date" value="' + c.esc(e.date) + '"></label>' +
        '<label class="p-field" data-component="Field"' + changed("start", b.start) + '><span data-rule="FR-C02">目标开始时间</span><select name="start">' + RB.opts(RB.times(9 * 60, 17 * 60 + 30), e.start) + "</select></label>" +
        '<label class="p-field" data-component="Field"' + changed("end", b.end) + '><span data-rule="FR-C02">目标结束时间</span><select name="end">' + RB.opts(RB.times(9 * 60 + 30, 18 * 60), e.end) + "</select></label>" +
      "</div>" +
      '<p class="p-pending p-review-only" data-open="Q-03">改期是否有提前量要求待定：原型不限制</p>' +
      '<p class="p-pending p-review-only" data-open="Q-22">目标与原预约完全相同时如何处理待定：请勿用相同目标演示</p>' +
      '<p class="p-pending p-review-only" data-open="Q-06">原会议室已停用时能否改到其他会议室待定</p>' +
      '<p class="p-pending p-review-only" data-open="Q-15">改期后是否保留原会议室、原时段等变更历史待定：原型不保留</p>' +
      '<div class="p-row" data-component="ActionBar">' +
        '<button class="p-btn primary" data-proposal="FR-R05">确认改期</button>' +
        '<button type="button" class="p-btn" data-go="mine">返回我的预约</button>' +
      "</div></form>" +
      '<section class="p-card p-review-only" data-rule="FR-R03 FR-C07 FR-C06">' +
        '<h2 class="p-h">评审辅助：绕过界面直接提交</h2>' +
        "<p>界面只列出启用的会议室。下面用表单当前的日期和时段，把目标会议室改为停用的会议室 C 直接提交（不是界面设计）。</p>" +
        '<button type="button" class="p-btn" data-action="directRescheduleC" data-id="' + c.esc(b.id) + '">目标会议室改为 C 并提交</button>' +
      "</section>";
  }
});

Proto.action("startReschedule", function (c, a) {
  var b = RB.find(c, a.id);
  if (!RB.R.canModify(b, c.role.id, c.now)) return RB.say(c, "reBlocked");
  c.data.edit = { id: b.id, room: b.room, date: b.date, start: b.start, end: b.end };   // defaults to the original (proposal)
  c.go("reschedule");
});

function rbReschedule(c, id, f) {
  var b = RB.find(c, id);
  var target = { room: f.room, date: f.date, start: f.start, end: f.end };    // FR-R01: a topic in the request is ignored
  c.data.edit = { id: id, room: f.room, date: f.date, start: f.start, end: f.end };  // stay on the form with the target (proposal)
  var why = RB.R.rescheduleProblem(b, target, c.data, c.role.id, c.now);
  if (why === "blocked") return RB.say(c, "reBlocked");
  if (why === "conflict") return RB.say(c, "reConflict");
  if (why) return RB.say(c, why);       // "time" or "room": the same proposed wording as 4.2.1
  b.room = target.room; b.date = target.date; b.start = target.start; b.end = target.end;   // FR-R05
  c.data.edit = null; c.data.day = target.date;
  RB.say(c, "reOk");
  c.go("mine");
}

Proto.action("reschedule", function (c, a) { rbReschedule(c, a.id, a.fields); });

Proto.action("directRescheduleC", function (c, a, el) {
  var form = el.closest("main").querySelector("form[data-action=reschedule]"), f = {};
  new FormData(form).forEach(function (v, k) { f[k] = v; });
  f.room = "C";
  rbReschedule(c, a.id, f);
});
