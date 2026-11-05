/* Shared dialogs and actions: 新建预约、改期、取消预约、管理员取消预约, and the booking detail opened from 会议室.
   All wording here is 〔建议〕 from the specification unless listed in manifest.confirmed_text. */
window.RB = (function () {
  var MSG = {
    "FR-B03": "请填写会议主题",
    "FR-C02": "请选择 09:00—18:00 内的半小时整点时段，且开始早于结束",
    "FR-C07": "该会议室暂不可预约",
    "FR-B06": "该时段已被占用，请选择其他时段",
    "FR-R06": "目标时段已被占用，原预约保持不变",
    "FR-R02": "该预约当前不可改期",
    "FR-X02": "该预约当前不可取消",
    "FR-X05": "该预约已取消，不可操作",
    "FR-M02": "该预约当前不可取消",
    "FR-M03": "请填写取消原因",
    "Q-07": "恰好到开始时刻是否算“已经开始”尚未确定，原型不作判断",
    "Q-22": "改期目标与原预约完全相同时如何处理尚未确定，原型不作判断",
    "Q-26": "管理员本人预约位于所管会议室时走哪条取消路径尚未确定"
  };
  var CONFLICT = { "FR-B06": 1, "FR-R06": 1 };

  /* A rejected action: text from the specification's proposed wording, annotated with the rule it comes from. */
  function problemOpts(p) {
    if (p.open) return { text: MSG[p.open], opt: { kind: "error", open: p.open } };
    var shown = p.why || p.rule;
    var rule = p.why ? p.rule + " " + p.why : p.rule;
    var opt = { kind: "error", rule: rule, proposal: shown };
    if (CONFLICT[p.rule]) opt.open = "Q-12";              // 冲突反馈文案未定稿
    return { text: MSG[shown], opt: opt };
  }
  function fail(c, p) { var x = problemOpts(p); c.flash(x.text, x.opt); }
  function errorHtml(c, p) {
    if (!p) return "";
    var x = problemOpts(p), a = "";
    ["proposal", "open", "rule"].forEach(function (k) { if (x.opt[k]) a += " data-" + k + '="' + c.esc(x.opt[k]) + '"'; });
    return '<div class="p-flash error"' + a + ">" + c.esc(x.text) + "</div>";
  }

  function roomName(c, id) { var r = c.rules.room(c.data, id); return r ? r.name : id; }
  function roleLabel(id) {
    var labels = { jia: "员工甲", yi: "员工乙", bing: "员工丙", m: "管理员 M" };
    return labels[id] || id;
  }
  function find(c, id) { return c.data.bookings.filter(function (b) { return b.id === id; })[0]; }

  function opt(v, label, cur) {
    return '<option value="' + Proto.esc(v) + '"' + (v === cur ? " selected" : "") + ">" + Proto.esc(label) + "</option>";
  }
  /* FR-C03〔建议〕：选项只提供半小时刻度；开始 09:00—17:30，结束 09:30—18:00 */
  function timeOptions(c, from, to, cur) {
    var out = opt("", "请选择", cur);
    for (var m = from; m <= to; m += 30) out += opt(c.rules.hhmm(m), c.rules.hhmm(m), cur);
    return out;
  }
  /* 4.2.1〔建议〕：只可选择启用的会议室；服务端仍按 FR-C07 校验 */
  function roomOptions(c, cur) {
    return c.data.rooms.filter(function (r) { return c.rules.roomEnabled(r); })
      .map(function (r) { return opt(r.id, r.name + "（容量 " + r.capacity + "）", cur); }).join("");
  }
  function slotFields(c, v) {
    return '<label class="p-field" data-proposal="FR-C07"><span>会议室</span><select name="room">' + roomOptions(c, v.room) + "</select></label>" +
      '<label class="p-field"><span>日期</span><input type="date" name="date" value="' + c.esc(v.date) + '"></label>' +
      '<div class="p-row">' +
      '<label class="p-field" data-proposal="FR-C03"><span>开始时间</span><select name="start">' + timeOptions(c, 9 * 60, 17 * 60 + 30, v.start) + "</select></label>" +
      '<label class="p-field" data-proposal="FR-C03"><span>结束时间</span><select name="end">' + timeOptions(c, 9 * 60 + 30, 18 * 60, v.end) + "</select></label>" +
      "</div>";
  }

  /* ---------- 新建预约 4.2.1 ---------- */
  function bookDialog(c, v, p) {
    return '<h2 class="p-h" data-proposal="FR-B05">新建预约</h2>' + errorHtml(c, p) +
      '<form data-action="book">' + slotFields(c, v) +
      '<label class="p-field" data-rule="FR-B03"><span>会议主题 *</span><input name="topic" value="' + c.esc(v.topic || "") + '"></label>' +
      '<p class="p-pending p-review-only" data-open="Q-05">主题长度上限、纯空格是否算未填写待定，原型不限制长度、不去除空格</p>' +
      '<div class="p-field" data-rule="FR-B02"><span data-proposal="FR-B02">创建人</span><div>' + c.esc(c.role.label) + "</div></div>" +
      '<p class="p-pending p-review-only" data-open="Q-02 Q-04 Q-16">最小提前量、最远可预约天数、人均有效预约上限、节假日限制待定，原型不做这些校验（也不拦截当前时刻之前的时段）</p>' +
      '<p class="p-pending p-review-only" data-open="Q-13">同一员工能否同时段持有不同会议室的预约待定，原型只按同一会议室判断冲突（FR-C04）</p>' +
      '<p class="p-pending p-review-only" data-open="Q-14">是否填写参会人数并按容量校验待定，原型只展示容量</p>' +
      '<div class="p-row"><button class="p-btn primary" data-proposal="FR-B05">提交预约</button>' +
      '<button type="button" class="p-btn" data-action="closeDialog" data-proposal="FR-B05">返回</button></div>' +
      '<p class="p-pending p-review-only" data-open="Q-11">防止重复点击、超时重试的方式待定，原型不模拟</p>' +
      '<p class="p-pending p-review-only" data-open="Q-12">冲突反馈及各项提示的正式文案未定稿，原型使用规格中的建议文案</p>' +
      "</form>";
  }
  Proto.action("pick", function (c, a) {               // 4.2.1〔建议〕从空闲格进入，预填会议室、日期、开始时间
    c.dialog(bookDialog(c, { room: a.room, date: a.date, start: a.start, end: "", topic: "" }));
  });
  Proto.action("book", function (c, a) {
    var f = a.fields;
    var p = c.rules.bookProblem(f, c.data);
    if (p) return c.dialog(bookDialog(c, f, p));        // 失败时保留已填写内容〔建议〕
    c.data.bookings.push(c.rules.newBooking(f, c.role.id, "n" + (c.data.bookings.length + 1)));
    c.close();
    c.data.viewDate = f.date;
    c.flash("预约成功", { proposal: "FR-B05", rule: "FR-B05", open: "Q-10" });
  });

  /* ---------- 改期 4.2.3 ---------- */
  function rescheduleDialog(c, b, v, p) {
    return '<h2 class="p-h" data-proposal="FR-R05">改期</h2>' + errorHtml(c, p) +
      '<table class="p-table" data-rule="FR-R01"><tbody>' +
      "<tr><th>原会议室</th><td>" + c.esc(roomName(c, b.room)) + "</td></tr>" +
      "<tr><th>原时间</th><td>" + c.esc(b.date + " " + b.start + "—" + b.end) + "</td></tr>" +
      "<tr><th>会议主题</th><td>" + c.esc(b.topic) + "</td></tr></tbody></table>" +
      '<form data-action="reschedule" data-id="' + c.esc(b.id) + '" style="margin-top:12px">' +
      '<p data-proposal="FR-R03">目标默认为原预约的值</p>' + slotFields(c, v) +
      '<p class="p-pending p-review-only" data-open="Q-03">改期是否有提前量要求待定，原型不校验</p>' +
      '<p class="p-pending p-review-only" data-open="Q-22">目标与原预约完全相同时如何处理待定，原型提交后只提示待确认</p>' +
      '<p class="p-pending p-review-only" data-open="Q-06">原会议室已停用时能否改期到其他会议室待定，示例数据中没有这种预约</p>' +
      '<p class="p-pending p-review-only" data-open="Q-15">改期是否保留原会议室、原时段的变更历史待定，原型不保存历史</p>' +
      '<div class="p-row"><button class="p-btn primary" data-proposal="FR-R05">确认改期</button>' +
      '<button type="button" class="p-btn" data-action="closeDialog" data-proposal="FR-R05">返回</button></div></form>';
  }
  Proto.action("askReschedule", function (c, a) {
    var b = find(c, a.id);
    var p = c.rules.ownerProblem(b, c.role.id, c.now, "reschedule");
    if (p) { c.close(); return fail(c, p); }
    c.dialog(rescheduleDialog(c, b, { room: b.room, date: b.date, start: b.start, end: b.end }));
  });
  Proto.action("reschedule", function (c, a) {
    var b = find(c, a.id), t = a.fields;
    var p = c.rules.rescheduleProblem(b, t, c.data, c.role.id, c.now);
    if (p) return c.dialog(rescheduleDialog(c, b, t, p));   // FR-R06：原预约不变；停留在改期界面〔建议〕
    c.rules.applyReschedule(b, t);
    c.close();
    c.flash("改期成功", { proposal: "FR-R05", rule: "FR-R05", open: "Q-10" });
  });

  /* ---------- 预约人取消 4.2.4 ---------- */
  Proto.action("askCancel", function (c, a) {
    var b = find(c, a.id);
    var p = c.rules.ownerProblem(b, c.role.id, c.now, "cancel");
    if (p) { c.close(); return fail(c, p); }
    c.dialog('<h2 class="p-h" data-proposal="FR-X03">确定取消该预约？</h2>' +
      "<p>" + c.esc(roomName(c, b.room) + " · " + b.date + " " + b.start + "—" + b.end + " · " + b.topic) + "</p>" +
      '<p class="p-pending p-review-only" data-open="Q-09">员工自己取消时是否填写原因待定，原型不设原因输入</p>' +
      '<div class="p-row"><button class="p-btn danger" data-action="cancel" data-id="' + c.esc(b.id) + '" data-proposal="FR-X03">确定取消</button>' +
      '<button class="p-btn" data-action="closeDialog" data-proposal="FR-X03">不取消</button></div>');
  });
  Proto.action("cancel", function (c, a) {
    var b = find(c, a.id);
    var p = c.rules.ownerProblem(b, c.role.id, c.now, "cancel");   // FR-X01、FR-X02、FR-X05
    c.close();
    if (p) return fail(c, p);
    c.rules.cancel(b, c.role.id, c.now);
    c.flash("预约已取消", { proposal: "FR-X03", rule: "FR-X03", open: "Q-10" });
  });

  /* ---------- 管理员取消 4.3.1 ---------- */
  function adminCancelDialog(c, b, reason, p) {
    return '<h2 class="p-h" data-proposal="FR-M04">取消预约</h2>' + errorHtml(c, p) +
      "<p>" + c.esc(roomName(c, b.room) + " · " + b.date + " " + b.start + "—" + b.end + " · " + b.topic) + "</p>" +
      '<form data-action="adminCancel" data-id="' + c.esc(b.id) + '">' +
      '<label class="p-field" data-rule="FR-M03"><span>取消原因 *</span><textarea name="reason">' + c.esc(reason || "") + "</textarea></label>" +
      '<p class="p-pending p-review-only" data-open="Q-25">原因长度上限、纯空格是否算未填写待定，原型不限制长度、不去除空格</p>' +
      '<div class="p-row"><button class="p-btn danger" data-proposal="FR-M04">确认取消</button>' +
      '<button type="button" class="p-btn" data-action="closeDialog" data-proposal="FR-M04">返回</button></div></form>';
  }
  Proto.action("askAdminCancel", function (c, a) {
    var b = find(c, a.id), room = c.rules.room(c.data, b.room);
    var p = c.rules.adminProblem(b, room, c.role.id, c.now);
    if (p) { c.close(); return fail(c, p); }
    c.dialog(adminCancelDialog(c, b, ""));
  });
  Proto.action("adminCancel", function (c, a) {
    var b = find(c, a.id), room = c.rules.room(c.data, b.room), reason = a.fields.reason;
    var p = c.rules.adminCancelProblem(b, room, c.role.id, c.now, reason);
    if (p && p.rule === "FR-M03") return c.dialog(adminCancelDialog(c, b, reason, p));
    c.close();
    if (p) return fail(c, p);
    c.rules.cancel(b, c.role.id, c.now, reason);
    c.flash("预约已取消", { proposal: "FR-M04", rule: "FR-M04", open: "Q-10" });
  });

  /* ---------- 从「会议室」占用块打开的预约详情 ---------- */
  function ownerButtons(c, b) {
    var room = c.rules.room(c.data, b.room), out = "";
    var pr = c.rules.ownerProblem(b, c.role.id, c.now, "reschedule");
    var pc = c.rules.ownerProblem(b, c.role.id, c.now, "cancel");
    if (pr && pr.open) return '<p class="p-pending p-review-only" data-open="Q-07">该预约恰好到开始时刻，能否改期、取消待定</p>';
    if (!pr) out += '<button class="p-btn" data-action="askReschedule" data-id="' + c.esc(b.id) + '" data-rule="FR-L03" data-proposal="FR-L03">改期</button>';
    if (!pc && c.rules.isRoomAdmin(room, c.role.id))
      out += '<p class="p-pending p-review-only" data-open="Q-26">本人预约位于所管会议室：取消走预约人路径还是管理员路径（是否必填原因）待定，原型暂不提供取消</p>';
    else if (!pc) out += '<button class="p-btn danger" data-action="askCancel" data-id="' + c.esc(b.id) + '" data-rule="FR-L03" data-proposal="FR-L03">取消预约</button>';
    return out;
  }
  Proto.action("openBooking", function (c, a) {
    var b = find(c, a.id), room = c.rules.room(c.data, b.room);
    if (!b || !c.rules.canSeeTopic(b, room, c.role.id)) return;   // FR-V02：其他员工没有详情入口
    var mine = b.creator === c.role.id, acts = "";
    if (mine) acts = ownerButtons(c, b);
    else if (!c.rules.adminProblem(b, room, c.role.id, c.now))
      acts = '<button class="p-btn danger" data-action="askAdminCancel" data-id="' + c.esc(b.id) + '" data-rule="FR-M01" data-proposal="FR-M01">取消预约</button>';
    c.dialog('<h2 class="p-h" data-rule="FR-V02">' + c.esc(b.topic) + "</h2>" +
      '<table class="p-table"><tbody>' +
      "<tr><th>会议室</th><td>" + c.esc(room.name) + "</td></tr>" +
      "<tr><th>时间</th><td>" + c.esc(b.date + " " + b.start + "—" + b.end) + "</td></tr>" +
      (mine ? "" : '<tr><th>预约人</th><td><span class="p-pending p-review-only" data-open="Q-19">管理员是否能看到预约人待定，原型不显示</span></td></tr>') +
      "</tbody></table>" +
      (mine ? "" : '<p class="p-review-only" data-rule="FR-R07">评审说明：管理员不能改期他人预约，此处不提供改期</p>') +
      '<div class="p-row" style="margin-top:12px">' + acts +
      '<button class="p-btn" data-action="closeDialog" data-proposal="FR-V01">关闭</button></div>');
  });

  Proto.action("closeDialog", function (c) { c.close(); });

  return { MSG: MSG, fail: fail, roomName: roomName, roleLabel: roleLabel, ownerButtons: ownerButtons };
})();
