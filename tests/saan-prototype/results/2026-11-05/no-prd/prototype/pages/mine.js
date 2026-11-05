Proto.page("mine", {
  label: "我的登记",
  proposal: "FR-3",
  render: function (c) {
    var names = {};
    c.data.spots.forEach(function (s) { names[s.id] = s.name; });
    var mine = c.data.registrations.filter(function (r) { return r.by === c.role.id; });
    var rows = mine.map(function (r) {
      var act = c.rules.canCancel(r, c.role.id, c.now)
        ? '<button class="p-btn danger" data-action="askCancel" data-id="' + c.esc(r.id) + '" data-rule="FR-3"><span data-proposal="FR-3">取消登记</span></button>'
        : r.status === "已登记"
          ? '<span data-rule="FR-3"><span data-proposal="FR-3">仅可在登记当天取消</span></span>'
          : "";
      return "<tr><td>" + c.esc(names[r.spot] || r.spot) + "</td><td>" + c.esc(r.date) + "</td><td>" + c.esc(r.createdOn) +
        '</td><td><span class="p-tag">' + c.esc(r.status) + "</span></td><td>" + act + "</td></tr>";
    }).join("");
    return '<section class="p-card"><h2 class="p-h" data-proposal="FR-3">我的登记</h2>' +
      (mine.length
        ? '<table class="p-table"><thead><tr><th>车位</th><th>使用日期</th><th>登记日期</th><th>状态</th><th>操作</th></tr></thead><tbody>' + rows + "</tbody></table>"
        : '<div class="p-empty" data-proposal="FR-1">暂无登记</div>') +
      '<p class="p-pending p-review-only" data-open="Q-1">「当天取消」的“当天”待定：原型按登记当天理解，若指使用当天，取消按钮的出现时间会变</p>' +
      "</section>";
  }
});
Proto.action("askCancel", function (c, a) {
  c.dialog('<h2 class="p-h" data-proposal="FR-3">取消这条车位登记？</h2>' +
    '<p data-proposal="FR-3">取消后该车位当天可被其他人登记。</p>' +
    '<div class="p-row"><button class="p-btn danger" data-action="cancel" data-id="' + c.esc(a.id) + '">确认取消</button>' +
    '<button type="button" class="p-btn" data-action="closeDialog">返回</button></div>');
});
Proto.action("closeDialog", function (c) { c.close(); });
Proto.action("cancel", function (c, a) {
  var r = c.data.registrations.filter(function (x) { return x.id === a.id; })[0];
  c.close();
  if (!r || !c.rules.canCancel(r, c.role.id, c.now))
    return c.flash("只能在登记当天取消自己的登记", { kind: "error", proposal: "FR-3" });
  r.status = "已取消";
  c.flash("已取消登记", { proposal: "FR-3" });
});
