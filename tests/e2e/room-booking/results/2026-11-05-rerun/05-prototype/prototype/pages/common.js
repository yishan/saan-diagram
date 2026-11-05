/* 共用：时间、选项、反馈文案、对话框与提交处理。每个提交都在动作里重新校验（FR-C06）。 */
var RB = (function () {
  var RB = { handlers: {} }, esc = Proto.esc;
  RB.SLOTS = [];
  for (var m = 9 * 60; m < 18 * 60; m += 30) RB.SLOTS.push(m);
  RB.hm = function (min) { return ("0" + Math.floor(min / 60)).slice(-2) + ":" + ("0" + (min % 60)).slice(-2); };
  function sh(d) { return new Date(d.getTime() + 8 * 3600000).toISOString(); }  // FR-C01 Asia/Shanghai
  RB.today = function (c) { return sh(c.now).slice(0, 10); };
  RB.stamp = function (d) { var s = sh(d); return s.slice(0, 10) + " " + s.slice(11, 16); };
  RB.day = function (c) { return c.data.day || RB.today(c); };
  RB.room = function (c, id) { return (c.data.rooms || []).filter(function (r) { return r.id === id; })[0] || null; };
  RB.roomName = function (c, id) { var r = RB.room(c, id); return r ? r.name : id; };
  RB.booking = function (c, id) { return (c.data.bookings || []).filter(function (b) { return b.id === id; })[0] || null; };
  RB.manages = function (c) { return (c.data.rooms || []).some(function (r) { return c.rules.isAdminOf(r, c.role.id); }); };
  RB.enabledRooms = function (c) { return c.data.rooms.filter(function (r) { return c.rules.roomEnabled(r); }); };

  function opts(list, cur) {
    return list.map(function (o) {
      return '<option value="' + esc(o[0]) + '"' + (o[0] === cur ? " selected" : "") + ">" + esc(o[1]) + "</option>";
    }).join("");
  }
  RB.startOptions = function (cur) { return opts(RB.SLOTS.map(function (m) { return [RB.hm(m), RB.hm(m)]; }), cur); };
  RB.endOptions = function (cur) { return opts(RB.SLOTS.map(function (m) { return [RB.hm(m + 30), RB.hm(m + 30)]; }), cur); };
  RB.roomOptions = function (c, cur) {
    return opts(RB.enabledRooms(c).map(function (r) { return [r.id, r.name + "（容量 " + r.capacity + " 人）"]; }), cur);
  };

  /* 反馈文案。来源只给出部分建议文案；其余为本原型的建议，一律标 proposal。 */
  RB.MSG = {
    book: {
      topic: { text: "请填写会议主题", kind: "error", proposal: "FR-B03" },
      time: { text: "请选择 09:00—18:00 内的半小时整点时段，且开始早于结束", kind: "error", proposal: "FR-C02" },
      room: { text: "该会议室暂不可预约", kind: "error", proposal: "FR-C07" },
      conflict: { text: "该时段已被占用，请选择其他时段", kind: "error", proposal: "FR-B06", open: "Q-12" },
      blank: { text: "会议主题只有空格时是否算未填写，尚待确认；原型不创建预约", kind: "error", open: "Q-05" }
    },
    resched: {
      cancelled: { text: "该预约当前不可操作", kind: "error", proposal: "FR-X05" },
      notOwner: { text: "该预约当前不可改期", kind: "error", proposal: "FR-R02" },
      adminOther: { text: "该预约当前不可改期", kind: "error", proposal: "FR-R02", rule: "FR-R07" },
      started: { text: "该预约当前不可改期", kind: "error", proposal: "FR-R02" },
      boundary: { text: "恰好到开始时刻是否算“已经开始”，尚待确认；原型不执行改期", kind: "error", open: "Q-07" },
      time: { text: "请选择 09:00—18:00 内的半小时整点时段，且开始早于结束", kind: "error", proposal: "FR-R03" },
      room: { text: "该会议室暂不可预约", kind: "error", proposal: "FR-C07", rule: "FR-R03" },
      conflict: { text: "目标时段已被占用，原预约保持不变", kind: "error", proposal: "FR-R06", open: "Q-12" },
      same: { text: "改期目标与原预约完全相同时如何处理，尚待确认；原型不做修改", kind: "error", open: "Q-22" }
    },
    cancel: {
      cancelled: { text: "该预约当前不可操作", kind: "error", proposal: "FR-X05" },
      notOwner: { text: "该预约当前不可取消", kind: "error", proposal: "FR-X02" },
      started: { text: "该预约当前不可取消", kind: "error", proposal: "FR-X02" },
      boundary: { text: "恰好到开始时刻是否算“已经开始”，尚待确认；原型不执行取消", kind: "error", open: "Q-07" }
    },
    admin: {
      cancelled: { text: "该预约当前不可取消", kind: "error", proposal: "FR-M02" },
      notAdmin: { text: "该预约当前不可取消", kind: "error", proposal: "FR-M02" },
      started: { text: "该预约当前不可取消", kind: "error", proposal: "FR-M02" },
      boundary: { text: "恰好到开始时刻是否算“已经开始”，尚待确认；原型不执行取消", kind: "error", open: "Q-07" },
      reason: { text: "请填写取消原因", kind: "error", proposal: "FR-M03" },
      blank: { text: "取消原因只有空格时是否算未填写，尚待确认；原型不执行取消", kind: "error", open: "Q-25" },
      own: { text: "管理员取消本人在所管会议室的预约走哪条路径，尚待确认；原型不执行此操作", kind: "error", open: "Q-26" }
    },
    done: {
      booked: { text: "预约成功", proposal: "FR-B05", open: "Q-10" },
      rescheduled: { text: "改期成功", proposal: "FR-R05", open: "Q-10" },
      cancelled: { text: "预约已取消", proposal: "FR-X03", open: "Q-10" },
      adminCancelled: { text: "预约已取消", proposal: "FR-M04", open: "Q-10" }
    }
  };
  RB.say = function (c, group, key) { var m = RB.MSG[group][key]; c.flash(m.text, m); };

  /* 评审辅助：不属于界面。演示绕过界面直接提交时的校验，以及数据层的取消记录。 */
  RB.extras = function (c) {
    var out = "", probes = c.data.probes || [];
    if (probes.length) {
      out += '<section class="p-card p-review-only"><h2 class="p-h" data-rule="FR-C06">评审辅助：绕过界面直接提交</h2>' +
        '<p>这些按钮不属于界面，用来演示提交处理时的校验，以当前角色提交。</p><div class="p-row">' +
        probes.map(function (p, i) {
          return '<button class="p-btn" data-action="probe" data-i="' + i + '">' + esc(p.label) + "</button>";
        }).join("") + "</div></section>";
    }
    var cancelled = (c.data.bookings || []).filter(function (b) { return b.status === "已取消"; });
    if (cancelled.length) {
      out += '<section class="p-card p-review-only"><h2 class="p-h" data-rule="FR-X03 FR-M04">评审辅助：取消记录（数据层）</h2>' +
        '<p class="p-pending" data-open="Q-08">界面上谁能看到操作人和原因、记录保存多久待定；此处只用于核对数据</p>' +
        '<table class="p-table"><thead><tr><th>预约</th><th>取消操作人</th><th>取消时间</th><th>取消原因</th></tr></thead><tbody>' +
        cancelled.map(function (b) {
          return "<tr><td>" + esc(RB.roomName(c, b.room) + " " + b.date + " " + b.start + "—" + b.end) + "</td><td>" +
            esc(b.cancelByLabel || b.cancelBy || "") + "</td><td>" + esc(b.cancelAt || "") + "</td><td>" +
            esc(b.cancelReason || "—") + "</td></tr>";
        }).join("") + "</tbody></table></section>";
    }
    return out;
  };

  function summary(c, b) {
    return '<table class="p-table"><tbody>' +
      "<tr><th>会议室</th><td>" + esc(RB.roomName(c, b.room)) + "</td></tr>" +
      "<tr><th>日期</th><td>" + esc(b.date) + "</td></tr>" +
      "<tr><th>时间</th><td>" + esc(b.start + "—" + b.end) + "</td></tr>" +
      '<tr><th>会议主题</th><td data-rule="FR-V02">' + esc(b.topic) + "</td></tr></tbody></table>";
  }

  // 占用块详情：只有预约人和该会议室管理员能打开（FR-V02）
  RB.detail = function (c, b) {
    var r = c.rules, me = c.role.id, room = RB.room(c, b.room);
    var own = b.owner === me, admin = r.isAdminOf(room, me), st = r.startState(b, c.now);
    var html = '<h2 class="p-h" data-proposal="FR-V02">预约详情</h2>' + summary(c, b);
    if (b.status === "有效" && st === "at") html += '<p class="p-pending p-review-only" data-open="Q-07">恰好到开始时刻，能否改期、取消待定</p>';
    if (!own && admin) html += '<p class="p-pending p-review-only" data-open="Q-19">管理员是否能看到预约人待定；原型不显示预约人</p>';
    if (own && admin) html += '<p class="p-pending p-review-only" data-open="Q-26">本人预约位于所管会议室时，取消走预约人路径还是管理员路径待定；原型按预约人路径展示</p>';
    var acts = "";
    if (own && r.canChange(b, me, c.now)) {
      acts = '<div class="p-row" style="margin-top:12px" data-rule="FR-L03">' +
        '<button class="p-btn" data-action="startEdit" data-id="' + esc(b.id) + '" data-proposal="FR-L03">改期</button>' +
        '<button class="p-btn danger" data-action="askCancel" data-id="' + esc(b.id) + '" data-proposal="FR-L03">取消预约</button>';
    } else if (!own && r.canAdminCancel(b, room, me, c.now)) {
      acts = '<div class="p-row" style="margin-top:12px" data-rule="FR-M01 FR-R07">' +
        '<button class="p-btn danger" data-action="askAdminCancel" data-id="' + esc(b.id) + '" data-proposal="FR-M01">取消预约</button>';
    } else {
      acts = '<div class="p-row" style="margin-top:12px" data-rule="FR-L03 FR-M02">';
    }
    return html + acts + '<button type="button" class="p-btn" data-action="closeDialog">关闭</button></div>';
  };

  RB.cancelDialog = function (c, b) {
    var own = b.owner === c.role.id, admin = c.rules.isAdminOf(RB.room(c, b.room), c.role.id);
    return '<h2 class="p-h" data-proposal="FR-X03">确定取消该预约？</h2>' + summary(c, b) +
      (own && admin ? '<p class="p-pending p-review-only" data-open="Q-26">管理员取消本人在所管会议室的预约是否需要填写原因待定</p>' : "") +
      '<p class="p-pending p-review-only" data-open="Q-09">员工取消时是否填写原因待定，本稿不设该输入</p>' +
      '<div class="p-row"><button class="p-btn danger" data-action="cancel" data-id="' + esc(b.id) + '" data-proposal="FR-X03">确定取消</button>' +
      '<button type="button" class="p-btn" data-action="closeDialog" data-proposal="FR-X03">不取消</button></div>';
  };

  RB.adminDialog = function (c, b, err) {
    var msg = err === "reason" ? '<div class="p-flash error" data-proposal="FR-M03">请填写取消原因</div>'
      : err === "blank" ? '<div class="p-flash error" data-open="Q-25">取消原因只有空格时是否算未填写，尚待确认；原型不执行取消</div>' : "";
    return '<h2 class="p-h" data-proposal="FR-M04">取消该预约</h2>' + summary(c, b) +
      '<form data-action="adminCancel" data-id="' + esc(b.id) + '" style="margin-top:12px">' +
      '<label class="p-field"><span data-rule="FR-M03">取消原因 *</span><textarea name="reason" rows="3"></textarea></label>' +
      '<p class="p-pending p-review-only" data-open="Q-25">原因长度上限、只有空格是否算未填写待定</p>' + msg +
      '<div class="p-row"><button class="p-btn danger" data-proposal="FR-M04">确认取消</button>' +
      '<button type="button" class="p-btn" data-action="closeDialog">返回</button></div></form>';
  };

  /* 提交处理。a.probe 为真时来自评审辅助的直接请求：不改表单草稿，不跳转。 */
  RB.handlers.book = function (c, a) {
    var f = a.fields || {};
    if (!a.probe) c.data.draft = Object.assign({}, f);
    if (f.topic && !f.topic.trim()) return RB.say(c, "book", "blank");
    var why = c.rules.bookingProblem(f, RB.room(c, f.room), c.data.bookings);
    if (why) return RB.say(c, "book", why);
    // FR-B02: the creator is the current user; any creator sent in the request (f.owner) is ignored
    c.data.bookings.push({ id: "n" + (c.data.bookings.length + 1), room: f.room, date: f.date, start: f.start, end: f.end,
      topic: f.topic, owner: c.role.id, status: "有效" });
    if (!a.probe) { c.data.draft = null; c.data.day = f.date; c.go("rooms"); }
    RB.say(c, "done", "booked");  // after c.go, which clears the message
  };

  RB.handlers.reschedule = function (c, a) {
    var b = RB.booking(c, a.id), f = a.fields || {};
    if (!a.probe) c.data.edit = Object.assign({ id: a.id }, f);
    if (!b) return RB.say(c, "resched", "notOwner");
    var why = c.rules.rescheduleProblem(b, f, RB.room(c, f.room), c.data.bookings, c.role.id, c.now);
    if (why === "notOwner" && c.rules.isAdminOf(RB.room(c, b.room), c.role.id)) why = "adminOther";
    if (!why && f.room === b.room && f.date === b.date && f.start === b.start && f.end === b.end) why = "same";
    if (why) return RB.say(c, "resched", why);
    b.room = f.room; b.date = f.date; b.start = f.start; b.end = f.end;  // FR-R05: topic and creator unchanged (FR-R01)
    if (!a.probe) { c.data.edit = null; c.data.day = f.date; c.go("mine"); }
    RB.say(c, "done", "rescheduled");
  };

  RB.handlers.cancel = function (c, a) {
    var b = RB.booking(c, a.id);
    var why = b ? c.rules.cancelProblem(b, c.role.id, c.now) : "notOwner";
    c.close();
    if (why) return RB.say(c, "cancel", why);
    b.status = "已取消"; b.cancelBy = c.role.id; b.cancelByLabel = c.role.label; b.cancelAt = RB.stamp(c.now);  // FR-X03
    RB.say(c, "done", "cancelled");
  };

  RB.handlers.adminCancel = function (c, a) {
    var b = RB.booking(c, a.id), reason = (a.fields || {}).reason || "";
    if (b && b.owner === c.role.id) { c.close(); return RB.say(c, "admin", "own"); }
    var why = b ? c.rules.adminCancelProblem(b, RB.room(c, b.room), c.role.id, c.now, reason) : "notAdmin";
    if (!why && !reason.trim()) why = "blank";
    if ((why === "reason" || why === "blank") && !a.probe) return c.dialog(RB.adminDialog(c, b, why));
    c.close();
    if (why) return RB.say(c, "admin", why);
    b.status = "已取消"; b.cancelBy = c.role.id; b.cancelByLabel = c.role.label;  // FR-M04
    b.cancelAt = RB.stamp(c.now); b.cancelReason = reason;
    RB.say(c, "done", "adminCancelled");
  };

  return RB;
})();

Proto.action("probe", function (c, a) {
  var p = c.data.probes[Number(a.i)];
  RB.handlers[p.action](c, { id: p.id, fields: Object.assign({}, p.fields), probe: true });
});
Proto.action("book", function (c, a) { RB.handlers.book(c, a); });
Proto.action("reschedule", function (c, a) { RB.handlers.reschedule(c, a); });
Proto.action("cancel", function (c, a) { RB.handlers.cancel(c, a); });
Proto.action("adminCancel", function (c, a) { RB.handlers.adminCancel(c, a); });
Proto.action("setDay", function (c, a) { c.data.day = a.value; });
Proto.action("closeDialog", function (c) { c.close(); });
Proto.action("pick", function (c, a) {
  var m = Number(a.min);
  c.data.draft = { room: a.room, date: RB.day(c), start: RB.hm(m), end: RB.hm(m + 30), topic: "" };
  c.go("book");
});
Proto.action("openBooking", function (c, a) {
  var b = RB.booking(c, a.id);
  if (b) c.dialog(RB.detail(c, b));
});
Proto.action("startEdit", function (c, a) {
  var b = RB.booking(c, a.id);
  if (!b) return;
  c.data.edit = { id: b.id, room: b.room, date: b.date, start: b.start, end: b.end };
  c.close();
  c.go("reschedule");
});
Proto.action("askCancel", function (c, a) { var b = RB.booking(c, a.id); if (b) c.dialog(RB.cancelDialog(c, b)); });
Proto.action("askAdminCancel", function (c, a) { var b = RB.booking(c, a.id); if (b) c.dialog(RB.adminDialog(c, b, null)); });
