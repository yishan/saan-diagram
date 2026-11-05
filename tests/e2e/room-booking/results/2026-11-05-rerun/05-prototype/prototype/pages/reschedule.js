Proto.page("reschedule", {
  label: "改期", nav: false, proposal: "FR-R05",
  render: function (c) {
    var esc = c.esc, e = c.data.edit, b = e && RB.booking(c, e.id);
    if (!b) {
      return '<section class="p-card"><div class="p-empty" data-proposal="FR-R02">未选择要改期的预约</div>' +
        '<button type="button" class="p-btn" data-go="mine" data-proposal="FR-L03">返回我的预约</button></section>' + RB.extras(c);
    }
    var original = '<section class="p-card"><h2 class="p-h" data-proposal="FR-R01">原预约</h2><table class="p-table"><tbody>' +
      "<tr><th>会议室</th><td>" + esc(RB.roomName(c, b.room)) + "</td></tr>" +
      "<tr><th>日期</th><td>" + esc(b.date) + "</td></tr>" +
      "<tr><th>时间</th><td>" + esc(b.start + "—" + b.end) + "</td></tr>" +
      '<tr><th>会议主题</th><td data-rule="FR-R01">' + esc(b.topic) + "（不可修改）</td></tr></tbody></table></section>";
    var form = '<form class="p-card" data-action="reschedule" data-id="' + esc(b.id) + '"><h2 class="p-h" data-proposal="FR-R05">改期到</h2>' +
      '<label class="p-field"><span data-rule="FR-R03">目标会议室</span><select name="room">' + RB.roomOptions(c, e.room) + "</select></label>" +
      '<label class="p-field"><span>目标日期</span><input type="date" name="date" value="' + esc(e.date) + '"></label>' +
      '<p class="p-pending p-review-only" data-open="Q-03">改期是否有提前量要求、是否与新预约相同待定；原型不做此校验</p>' +
      '<div class="p-row">' +
      '<label class="p-field"><span data-rule="FR-C02">目标开始时间</span><select name="start">' + RB.startOptions(e.start) + "</select></label>" +
      '<label class="p-field"><span data-rule="FR-C02">目标结束时间</span><select name="end">' + RB.endOptions(e.end) + "</select></label>" +
      "</div>" +
      '<p data-rule="FR-R04" style="margin:-6px 0 12px;font-size:12px;color:var(--muted)">原预约自身的占用不计入冲突</p>' +
      '<div class="p-row"><button class="p-btn primary" data-proposal="FR-R05">确认改期</button>' +
      '<button type="button" class="p-btn" data-go="mine" data-proposal="FR-L03">返回我的预约</button></div>' +
      '<p class="p-pending p-review-only" data-open="Q-15" style="margin-top:12px">改期后是否保留原会议室、原时段等变更历史待定</p>' +
      "</form>";
    return original + form + RB.extras(c);
  }
});
