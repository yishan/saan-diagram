/* 4.2.2 我的预约；改期、取消入口（4.2.3、4.2.4） */
Proto.page("mine", {
  label: "我的预约",
  render: function (c) {
    var R = c.rules;
    var rows = c.data.bookings.filter(function (b) { return b.creator === c.role.id; });   // FR-L01
    if (!rows.length)
      return '<section class="p-card"><h2 class="p-h">我的预约</h2><div class="p-empty" data-proposal="FR-L01">暂无预约</div></section>';
    var body = rows.map(function (b) {
      var status, acts;
      if (b.status === "已取消") {                                                         // FR-L02、FR-X04
        status = '<span class="p-tag" data-rule="FR-L02">已取消</span>' +
          '<div style="font-size:12px;color:var(--muted)" data-proposal="FR-X03">取消时间 ' + c.esc(b.cancelledAt || "") + "</div>";
        acts = "";                                                                            // FR-L03、FR-X05
      } else {
        var started = R.startState(b, c.now) !== "not_started";
        status = started
          ? '<span class="p-tag" data-proposal="FR-L02" data-open="Q-21">已预约</span>'
          : '<span class="p-tag" data-proposal="FR-L02">已预约</span>';
        acts = RB.ownerButtons(c, b);
      }
      return "<tr><td>" + c.esc(RB.roomName(c, b.room)) + "</td><td>" + c.esc(b.date) + "</td><td>" + c.esc(b.start + "—" + b.end) +
        "</td><td>" + c.esc(b.topic) + "</td><td>" + status + '</td><td><div class="p-row">' + (acts || "—") + "</div></td></tr>";
    }).join("");
    return '<section class="p-card"><h2 class="p-h">我的预约</h2>' +
      '<table class="p-table"><thead><tr><th>会议室</th><th>日期</th><th>时间</th><th>会议主题</th><th>状态</th><th>操作</th></tr></thead><tbody>' +
      body + "</tbody></table>" +
      '<p class="p-pending p-review-only" data-open="Q-21" style="margin-top:12px">排序方式、有效预约的正式显示文案、已开始或已结束的有效预约如何显示待定；原型按数据顺序列出，有效预约暂用建议文案「已预约」</p>' +
      '<p class="p-pending p-review-only" data-open="Q-08">取消记录保存多久、是否向预约人显示取消操作人和原因待定，原型只显示取消时间</p>' +
      "</section>";
  }
});
