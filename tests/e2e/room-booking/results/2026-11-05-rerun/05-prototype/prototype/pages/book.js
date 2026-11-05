Proto.page("book", {
  label: "新建预约", nav: false, proposal: "FR-B05",
  render: function (c) {
    var esc = c.esc, first = RB.enabledRooms(c)[0];
    var d = c.data.draft || { room: first ? first.id : "", date: RB.day(c), start: "09:00", end: "09:30", topic: "" };
    return '<form class="p-card" data-action="book"><h2 class="p-h" data-proposal="FR-B01">新建预约</h2>' +
      '<label class="p-field"><span data-rule="FR-C07">会议室</span><select name="room">' + RB.roomOptions(c, d.room) + "</select></label>" +
      '<p data-proposal="FR-C07" style="margin:-6px 0 12px;font-size:12px;color:var(--muted)">仅列出启用的会议室</p>' +
      '<p class="p-pending p-review-only" data-open="Q-14">容量仅作展示，还是需要填写人数并校验，待定</p>' +
      '<label class="p-field"><span>日期</span><input type="date" name="date" value="' + esc(d.date) + '"></label>' +
      '<p class="p-pending p-review-only" data-open="Q-02 Q-04 Q-16">最小提前量、最远可预约天数、人均上限、节假日限制待定；原型不做这些校验</p>' +
      '<div class="p-row">' +
      '<label class="p-field"><span data-rule="FR-C02">开始时间</span><select name="start">' + RB.startOptions(d.start) + "</select></label>" +
      '<label class="p-field"><span data-rule="FR-C02">结束时间</span><select name="end">' + RB.endOptions(d.end) + "</select></label>" +
      "</div>" +
      '<p data-proposal="FR-C03" style="margin:-6px 0 12px;font-size:12px;color:var(--muted)">时间选项仅提供 09:00—18:00 内的半小时刻度</p>' +
      '<label class="p-field"><span data-rule="FR-B03">会议主题 *</span><input name="topic" value="' + esc(d.topic) + '"></label>' +
      '<p class="p-pending p-review-only" data-open="Q-05">主题长度上限、只有空格是否算未填写待定</p>' +
      '<div class="p-field"><span>创建人</span><div data-proposal="FR-B02">' + esc(c.role.label) + "</div></div>" +
      '<p class="p-pending p-review-only" data-open="Q-13">同一员工同一时段能否持有不同会议室的预约待定；原型按同一会议室判断冲突</p>' +
      '<div class="p-row"><button class="p-btn primary" data-proposal="FR-B05">提交预约</button>' +
      '<button type="button" class="p-btn" data-go="rooms" data-proposal="FR-V01">返回会议室</button></div>' +
      '<p class="p-pending p-review-only" data-open="Q-11" style="margin-top:12px">防止重复点击、超时重试的方式待定</p>' +
      "</form>" + RB.extras(c);
  }
});
