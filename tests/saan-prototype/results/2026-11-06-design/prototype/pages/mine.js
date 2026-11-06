/* 4.2.2 我的预约 and 4.2.4 取消预约. */
Proto.page("mine", {
  label: "我的预约",
  render: function (c) {
    var R = RB.R;
    var own = c.data.bookings.filter(function (b) { return b.creator === c.role.id; })   // FR-L01
      .slice().sort(function (x, y) { return R.startAt(y) - R.startAt(x); });           // newest first is a proposal (Q-21)
    var isAdminRole = c.data.rooms.some(function (r) { return R.isAdmin(c.data.rooms, r.id, c.role.id); });

    function actions(b) {
      if (!R.canModify(b, c.role.id, c.now)) return "";    // FR-L03: not offered; the source proposes hiding them
      return '<div class="p-row" data-component="ActionBar" data-rule="FR-L03">' +
        '<button class="p-btn" data-action="startReschedule" data-id="' + c.esc(b.id) + '" data-proposal="FR-R01">改期</button>' +
        '<button class="p-btn danger" data-action="askCancel" data-id="' + c.esc(b.id) + '" data-proposal="FR-X01">取消预约</button>' +
        "</div>";
    }
    function cancelInfo(b) {
      if (b.status !== "已取消") return "";
      return '<span class="p-cell-sub" data-proposal="FR-X03">取消时间 ' + c.esc(b.cancelAt || "—") + "</span>";
    }

    var body = own.length
      ? '<table class="p-table" data-component="DataTable"><thead><tr><th>会议室</th><th>时间</th><th>会议主题</th><th>状态</th><th>操作</th></tr></thead><tbody>' +
        own.map(function (b) {
          return "<tr><td>" + c.esc(RB.roomName(c, b.room)) + "</td><td>" + c.esc(b.date) + '<span class="p-cell-sub">' +
            c.esc(b.start + "—" + b.end) + "</span></td><td>" + c.esc(b.topic) + "</td><td>" + RB.status(c, b) + cancelInfo(b) +
            "</td><td>" + actions(b) + "</td></tr>";
        }).join("") + "</tbody></table>"
      : '<div class="p-empty" data-proposal="FR-L01">暂无预约</div>';

    return '<section class="p-card"><h2 class="p-h">我的预约</h2>' + body +
      '<p class="p-pending p-review-only" data-open="Q-21">排序方式、有效预约的显示文案，以及已开始、已结束的预约如何显示待定：原型按开始时间倒序，有效预约暂显示「已预约」</p>' +
      '<p class="p-pending p-review-only" data-open="Q-07">恰好到开始时刻是否算已经开始待定：原型按“到达开始时刻即已开始”判断，示例不使用该边界</p>' +
      '<p class="p-pending p-review-only" data-open="Q-08">被取消的预约是否向预约人显示操作人和取消原因待定：原型只显示取消时间</p>' +
      (isAdminRole ? '<p class="p-pending p-review-only" data-open="Q-26">管理员本人在所管会议室的预约，取消时走预约人路径还是管理员路径（原因必填）待定：原型走预约人路径</p>' : "") +
      "</section>" + RB.directPanel(c);
  }
});

Proto.action("askCancel", function (c, a) {
  var b = RB.find(c, a.id);
  c.confirm({
    title: "确定取消该预约？", proposal: "FR-X03", component: "ChangeConfirm",
    body: '<div class="p-field read" data-component="Field"><span>预约</span><div>' +
      c.esc(RB.roomName(c, b.room) + " " + b.date + " " + b.start + "—" + b.end + " " + b.topic) + "</div></div>",
    changes: [{ label: "状态", from: "有效", to: "已取消" }],
    effects: [
      { text: "释放该时段的占用，其他人可预约", rule: "FR-X03" },
      { text: "记录保留在「我的预约」中", rule: "FR-X04" },
      { text: "是否需要填写取消原因待定，原型不设该输入", open: "Q-09" },
      { text: "是否发送通知待定", open: "Q-10" }
    ],
    confirm: { text: "确认取消", proposal: "FR-X03" }, danger: true, data: { id: b.id }
  }, "cancel");
});

Proto.action("cancel", function (c, a) {
  var b = RB.find(c, a.id);
  if (RB.R.cancelProblem(b, c.role.id, c.now)) { c.close(); return RB.say(c, "xBlocked"); }
  b.status = "已取消"; b.cancelBy = c.role.id; b.cancelAt = RB.nowText(c);   // FR-X03: operator and time are kept
  c.close();
  RB.say(c, "xOk");
});
