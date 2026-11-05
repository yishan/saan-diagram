Proto.page("mine", {
  label: "我的预约",
  render: function (c) {
    var r = c.rules, me = c.role.id, esc = c.esc;
    // FR-L01: bookings created by the current user, valid and cancelled. Order: proposal (Q-21)
    var list = c.data.bookings.filter(function (b) { return b.owner === me; }).slice().sort(function (a, b) {
      return (b.date + b.start).localeCompare(a.date + a.start);
    });
    var head = '<section class="p-card"><h2 class="p-h">我的预约</h2>';
    if (!list.length) return head + '<div class="p-empty" data-proposal="FR-L01">暂无预约</div></section>' + RB.extras(c);
    var rows = list.map(function (b) {
      var st = r.startState(b, c.now), status, acts;
      if (b.status === "已取消") {
        status = '<span class="p-tag" data-rule="FR-L02">已取消</span>' +
          (b.cancelAt ? '<div data-proposal="FR-X03" style="font-size:12px;color:var(--muted)">取消时间 ' + esc(b.cancelAt) + "</div>" : "");
      } else if (st === "before") {
        status = '<span class="p-tag" data-proposal="FR-L02">已预约</span>';
      } else {
        status = '<span class="p-tag" data-proposal="FR-L02" data-open="Q-21">已预约</span>';
      }
      if (r.canChange(b, me, c.now)) {
        acts = '<button class="p-btn" data-action="startEdit" data-id="' + esc(b.id) + '" data-proposal="FR-L03">改期</button> ' +
          '<button class="p-btn danger" data-action="askCancel" data-id="' + esc(b.id) + '" data-proposal="FR-L03">取消预约</button>';
      } else if (b.status === "有效" && st === "at") {
        acts = '<span class="p-pending p-review-only" data-open="Q-07">恰好到开始时刻，能否改期、取消待定</span>';
      } else {
        acts = "—";
      }
      return "<tr><td>" + esc(RB.roomName(c, b.room)) + "</td><td>" + esc(b.date) + "</td><td>" + esc(b.start + "—" + b.end) +
        "</td><td>" + esc(b.topic) + "</td><td>" + status + '</td><td data-rule="FR-L03">' + acts + "</td></tr>";
    }).join("");
    return head +
      '<p data-proposal="FR-L01" style="margin:0 0 8px;font-size:12px;color:var(--muted)">按开始时间倒序</p>' +
      '<table class="p-table"><thead><tr><th>会议室</th><th>日期</th><th>时间</th><th>会议主题</th><th>状态</th><th>操作</th></tr></thead><tbody>' +
      rows + "</tbody></table>" +
      '<p class="p-pending p-review-only" data-open="Q-21" style="margin-top:12px">排序方式、有效预约的显示文案、已开始或已结束预约的显示方式待定</p>' +
      '<p class="p-pending p-review-only" data-open="Q-08">是否向预约人显示取消操作人和取消原因、取消记录保存多久待定</p>' +
      "</section>" + RB.extras(c);
  }
});
