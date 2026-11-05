Proto.page("devices", {
  label: "设备",
  render: function (c) {
    var rows = c.data.devices.map(function (d) {
      var act = c.rules.canBorrow(d)
        ? '<button class="p-btn primary" data-action="borrow" data-id="' + c.esc(d.id) + '" data-rule="FR-B01">借用</button>'
        : c.rules.canReturn(d, c.role.id)
          ? '<button class="p-btn" data-action="return" data-id="' + c.esc(d.id) + '" data-rule="FR-R01">归还</button>'
          : '<button class="p-btn" data-action="borrow" data-id="' + c.esc(d.id) + '" data-rule="FR-B02">借用</button>';
      return "<tr><td>" + c.esc(d.name) + '</td><td><span class="p-tag">' + c.esc(d.status) + "</span></td><td>" + act + "</td></tr>";
    }).join("");
    return '<section class="p-card"><h2 class="p-h">设备</h2>' +
      '<table class="p-table"><thead><tr><th>名称</th><th>状态</th><th>操作</th></tr></thead><tbody>' + rows + "</tbody></table>" +
      '<p class="p-pending p-review-only" data-open="Q-01">借用期限待定，表单暂不收集期限</p></section>';
  }
});
Proto.action("borrow", function (c, a) {
  var d = c.data.devices.filter(function (x) { return x.id === a.id; })[0];
  if (!c.rules.canBorrow(d)) return c.flash("该设备已被借出", { kind: "error", proposal: "FR-B02" });
  d.status = "已借出"; d.holder = c.role.id;
  c.flash("借用成功", { proposal: "FR-B01" });
});
Proto.action("return", function (c, a) {
  var d = c.data.devices.filter(function (x) { return x.id === a.id; })[0];
  if (!c.rules.canReturn(d, c.role.id)) return c.flash("只能归还自己借出的设备", { kind: "error", proposal: "FR-R01" });
  d.status = "可借"; d.holder = null;
  c.flash("已归还", { proposal: "FR-R01" });
});
