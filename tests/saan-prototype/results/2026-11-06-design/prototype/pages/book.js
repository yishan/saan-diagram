/* 4.2.1 新建预约. A full page, as the profile's guide asks for create and edit. */
Proto.page("book", {
  label: "新建预约", nav: false, proposal: "FR-B01",
  render: function (c) {
    var R = RB.R, d = c.data.draft || { room: "", date: c.data.day || RB.today(c), start: "09:00", end: "09:30", topic: "" };
    var rooms = c.data.rooms.filter(function (r) { return r.enabled; })     // only enabled rooms are offered (proposal)
      .map(function (r) { return { value: r.id, label: r.name + "（容量 " + r.capacity + " 人）" }; });
    return '<form class="p-card" data-action="book">' +
      '<h2 class="p-h" data-proposal="FR-B01">新建预约</h2>' +
      '<label class="p-field" data-component="Field"><span data-proposal="FR-C07">会议室</span><select name="room">' + RB.opts(rooms, d.room) + "</select></label>" +
      '<div class="p-row">' +
        '<label class="p-field" data-component="Field"><span>日期</span><input type="date" name="date" value="' + c.esc(d.date) + '"></label>' +
        '<label class="p-field" data-component="Field"><span data-rule="FR-C02" data-proposal="FR-C03">开始时间</span><select name="start">' + RB.opts(RB.times(9 * 60, 17 * 60 + 30), d.start) + "</select></label>" +
        '<label class="p-field" data-component="Field"><span data-rule="FR-C02" data-proposal="FR-C03">结束时间</span><select name="end">' + RB.opts(RB.times(9 * 60 + 30, 18 * 60), d.end) + "</select></label>" +
      "</div>" +
      '<p class="p-pending p-review-only" data-open="Q-02 Q-04 Q-16">最小提前量、最远可预约天数、每人有效预约上限、节假日是否可约均待定：原型不限制日期</p>' +
      '<label class="p-field" data-component="Field"><span data-rule="FR-B03">会议主题 *</span><input name="topic" value="' + c.esc(d.topic) + '"></label>' +
      '<p class="p-pending p-review-only" data-open="Q-05">主题长度上限、纯空格是否算未填写待定：原型只把空字符串当作未填写</p>' +
      '<div class="p-field read" data-component="Field" data-rule="FR-B02"><span data-proposal="FR-B02">创建人</span><div>' + c.esc(c.role.label) + "</div></div>" +
      '<p class="p-pending p-review-only" data-open="Q-13">同一员工同一时段能否持有不同会议室的预约待定：原型只按同一会议室判断冲突</p>' +
      '<div class="p-row" data-component="ActionBar">' +
        '<button class="p-btn primary" data-proposal="FR-B05">提交预约</button>' +
        '<button type="button" class="p-btn" data-go="rooms">返回会议室</button>' +
      "</div>" +
      '<p class="p-pending p-review-only" data-open="Q-11">提交后防止重复点击、网络中断后重试的方式待定</p>' +
      "</form>" +
      '<section class="p-card p-review-only" data-rule="FR-C02 FR-C06 FR-C07 FR-B02 FR-C05">' +
        '<h2 class="p-h">评审辅助：绕过界面直接提交</h2>' +
        "<p>用上方表单当前的会议室、日期和主题，直接提交界面无法选择的请求（不是界面设计）。</p>" +
        '<div class="p-row">' +
          ["09:15—10:00", "08:30—09:30", "17:30—18:30", "10:00—10:00", "11:00—10:00", "17:30—18:00"].map(function (t) {
            return '<button type="button" class="p-btn" data-action="directBook" data-time="' + t + '">时段 ' + t + "</button>";
          }).join("") +
        "</div>" +
        '<div class="p-row" style="margin-top:8px">' +
          '<button type="button" class="p-btn" data-action="directBook" data-room="C">预约停用的会议室 C</button>' +
          '<button type="button" class="p-btn" data-action="directBook" data-creator="yi">请求中指定创建人为员工乙</button>' +
          '<button type="button" class="p-btn" data-action="simulateRival">模拟：另一员工同时提交同一时段，先被处理</button>' +
        "</div>" +
      "</section>";
  }
});

function rbCreate(c, req) {
  c.data.draft = { room: req.room, date: req.date, start: req.start, end: req.end, topic: req.topic };  // keep input on failure (proposal)
  var why = RB.R.bookProblem(req, c.data);
  if (why) return RB.say(c, why);
  c.data.bookings.push({ id: "n" + (c.data.bookings.length + 1), room: req.room, date: req.date, start: req.start, end: req.end,
    topic: req.topic, creator: c.role.id, status: "有效" });   // FR-B02: creator is the signed-in employee, never req.creator
  c.data.draft = null; c.data.day = req.date;
  RB.say(c, "bookOk");
  c.go("mine");
}

Proto.action("book", function (c, a) {
  rbCreate(c, { room: a.fields.room, date: a.fields.date, start: a.fields.start, end: a.fields.end, topic: a.fields.topic });
});

Proto.action("directBook", function (c, a, el) {
  var form = el.closest("main").querySelector("form[data-action=book]"), f = {};
  new FormData(form).forEach(function (v, k) { f[k] = v; });
  if (a.time) { f.start = a.time.split("—")[0]; f.end = a.time.split("—")[1]; }
  if (a.room) f.room = a.room;
  f.creator = a.creator;   // ignored by rbCreate (FR-B02)
  rbCreate(c, f);
});

Proto.action("simulateRival", function (c, a, el) {
  var form = el.closest("main").querySelector("form[data-action=book]"), f = {};
  new FormData(form).forEach(function (v, k) { f[k] = v; });
  c.data.draft = f;
  var rival = c.role.id === "yi" ? "jia" : "yi";
  var req = { room: f.room, date: f.date, start: f.start, end: f.end, topic: "（另一员工的预约）" };
  if (RB.R.bookProblem(req, c.data)) return c.flash("另一员工的提交未成功：所选时段不可预约，请先换一个空闲时段", { kind: "error", rule: "FR-C05" });
  c.data.bookings.push({ id: "r" + (c.data.bookings.length + 1), room: f.room, date: f.date, start: f.start, end: f.end,
    topic: req.topic, creator: rival, status: "有效" });
  c.flash(RB.name(rival) + "的同时段提交已先成功，现在提交本表单会得到冲突反馈", { kind: "ok", rule: "FR-C05" });
});
