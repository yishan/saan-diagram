Proto.page("register", {
  label: "登记车位",
  proposal: "FR-1",
  render: function (c) {
    var day = c.rules.tomorrow(c.now);
    var regs = c.data.registrations;
    var rows = c.data.spots.map(function (s) {
      var r = c.rules.activeFor(regs, s.id, day);
      var status = !r
        ? '<span class="p-tag" data-proposal="FR-2">空闲</span>'
        : r.by === c.role.id
          ? '<span class="p-tag" data-proposal="FR-2">已登记（我）</span>'
          : '<span class="p-tag" data-rule="FR-2">已登记</span>';
      var act = !r
        ? '<button class="p-btn primary" data-action="register" data-id="' + c.esc(s.id) + '" data-rule="FR-1 FR-2"><span data-proposal="FR-1">登记</span></button>'
        : r.by === c.role.id
          ? '<button class="p-btn" data-go="mine"><span data-proposal="FR-3">去我的登记</span></button>'
          : '<button class="p-btn" data-action="register" data-id="' + c.esc(s.id) + '" data-rule="FR-2"><span data-proposal="FR-1">登记</span></button>';
      return "<tr><td>" + c.esc(s.name) + "</td><td>" + status + "</td><td>" + act + "</td></tr>";
    }).join("");
    return '<section class="p-card"><h2 class="p-h" data-proposal="FR-1">登记明天的车位：' + c.esc(day) + "</h2>" +
      '<table class="p-table"><thead><tr><th>车位</th><th>明天状态</th><th>操作</th></tr></thead><tbody>' + rows + "</tbody></table>" +
      '<p class="p-pending p-review-only" data-open="Q-6">已被他人登记的车位是否显示登记人待定，原型只显示「已登记」</p>' +
      '<p class="p-pending p-review-only" data-open="Q-2">每人每天能登记几个车位待定，原型不做限制</p>' +
      '<p class="p-pending p-review-only" data-open="Q-3">登记截止时间待定，原型全天可登记</p>' +
      "</section>";
  }
});
Proto.action("register", function (c, a) {
  var day = c.rules.tomorrow(c.now);
  var spot = c.data.spots.filter(function (s) { return s.id === a.id; })[0];
  if (!c.rules.canRegister(c.data.registrations, a.id, day, c.now))
    return c.flash("该车位明天已被登记，请选择其他车位", { kind: "error", proposal: "FR-2" });
  c.data.registrations.push({ id: "r" + (c.data.registrations.length + 1), spot: a.id, date: day, by: c.role.id,
    createdOn: c.rules.dateKey(c.now), status: "已登记" });
  c.flash("登记成功：" + spot.name + "，" + day, { proposal: "FR-1" });
});
