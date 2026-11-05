Proto.page("spots", {
  label: "登记车位",
  proposal: "FR-1",
  render: function (c) {
    var day = c.rules.tomorrow(c.now);
    var rows = c.data.spots.map(function (s) {
      var h = c.rules.holderOf(s.id, day, c.data.regs);
      var state = !h ? '<span class="p-tag" data-proposal="FR-2">空闲</span>'
        : h.owner === c.role.id ? '<span class="p-tag" data-proposal="FR-2">我已登记</span>'
        : '<span class="p-tag" data-rule="FR-2">已登记</span>';
      // A taken spot keeps its button so the reviewer can trigger the FR-2 rejection (AC-2).
      var act = h && h.owner === c.role.id
        ? '<button class="p-btn" data-go="mine" data-proposal="FR-3">去我的登记</button>'
        : '<button class="p-btn' + (h ? "" : " primary") + '" data-action="register" data-spot="' + c.esc(s.id) +
          '" data-date="' + c.esc(day) + '" data-rule="FR-1 FR-2">登记</button>';
      return "<tr><td>" + c.esc(s.name) + "</td><td>" + state + "</td><td>" + act + "</td></tr>";
    }).join("");
    return '<section class="p-card"><h2 class="p-h" data-rule="FR-1">明天（' + c.esc(day) + '）的车位</h2>' +
      '<p data-proposal="FR-1">只能登记明天要用的车位，同一车位一天只给一人。</p>' +
      '<p class="p-pending p-review-only" data-open="Q-01">车位清单的来源和维护人待定，以下为虚构车位</p>' +
      '<table class="p-table"><thead><tr><th>车位</th><th>明天</th><th>操作</th></tr></thead><tbody>' + rows + "</tbody></table>" +
      '<p class="p-pending p-review-only" data-open="Q-05">已登记车位是否显示登记人待定，暂只显示「已登记」</p>' +
      '<p class="p-pending p-review-only" data-open="Q-02">一人一天能登记几个车位待定，原型不限制数量</p>' +
      '<p class="p-pending p-review-only" data-open="Q-04">登记的开放和截止时间待定，原型不限制时段</p>' +
      '<p class="p-pending p-review-only" data-open="Q-06">周末和节假日能否登记待定，原型不区分日期类型</p>' +
      "</section>";
  }
});
Proto.action("register", function (c, a) {
  if (!c.rules.canRegisterDate(a.date, c.now)) return c.flash("只能登记明天的车位", { kind: "error", rule: "FR-1", proposal: "FR-1" });
  if (c.rules.holderOf(a.spot, a.date, c.data.regs)) return c.flash("该车位明天已被登记，请换一个车位", { kind: "error", rule: "FR-2", proposal: "FR-2" });
  var spot = c.data.spots.filter(function (s) { return s.id === a.spot; })[0];
  c.data.regs.push({ id: "r" + (c.data.regs.length + 1) + "-" + c.now.getTime(), spot: a.spot, date: a.date,
    owner: c.role.id, createdAt: c.now.toISOString(), status: "已登记" });
  c.flash("已登记 " + spot.name + "（" + a.date + "）", { proposal: "FR-1" });
});
