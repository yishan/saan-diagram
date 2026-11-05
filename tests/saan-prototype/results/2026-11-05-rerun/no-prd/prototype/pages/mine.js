Proto.page("mine", {
  label: "我的登记",
  proposal: "FR-3",
  render: function (c) {
    var spotName = function (id) {
      var s = c.data.spots.filter(function (x) { return x.id === id; })[0];
      return s ? s.name : id;
    };
    var rows = c.data.regs.filter(function (r) { return r.owner === c.role.id; });
    // An active registration outside its cancel day keeps the button, so the reviewer can trigger the FR-3 rejection (AC-5).
    var act = function (r) {
      return c.rules.isOwnActive(r, c.role.id)
        ? '<button class="p-btn danger" data-action="cancel" data-id="' + c.esc(r.id) + '" data-rule="FR-3">取消</button>'
        : "";
    };
    return '<section class="p-card"><h2 class="p-h" data-proposal="FR-3">我的登记</h2>' +
      (rows.length ? '<table class="p-table"><thead><tr><th>车位</th><th>使用日期</th><th>登记日期</th><th>状态</th><th>操作</th></tr></thead><tbody>' +
        rows.map(function (r) {
          return "<tr><td>" + c.esc(spotName(r.spot)) + "</td><td>" + c.esc(r.date) + "</td><td>" + c.esc(c.rules.dayOf(r.createdAt)) +
            '</td><td><span class="p-tag">' + c.esc(r.status) + "</span></td><td>" + act(r) + "</td></tr>";
        }).join("") + "</tbody></table>"
       : '<div class="p-empty" data-proposal="FR-1">还没有登记，去「登记车位」登记明天的车位</div>') +
      '<p class="p-review-only" data-rule="FR-3">登记当天可以取消自己的登记。</p>' +
      '<p class="p-pending p-review-only" data-open="Q-03">「当天取消」按登记当天理解，是否改为使用当天、截止到几点待定</p>' +
      "</section>";
  }
});
Proto.action("cancel", function (c, a) {
  var r = c.data.regs.filter(function (x) { return x.id === a.id; })[0];
  if (!c.rules.isOwnActive(r, c.role.id)) return c.flash("只能取消自己的有效登记", { kind: "error", rule: "FR-3", proposal: "FR-3" });
  if (!c.rules.withinCancelDay(r, c.now)) return c.flash("只能在登记当天取消，这条登记已不能取消", { kind: "error", rule: "FR-3", proposal: "FR-3", open: "Q-03" });
  r.status = "已取消";
  c.flash("已取消，车位已释放", { proposal: "FR-3" });
});
