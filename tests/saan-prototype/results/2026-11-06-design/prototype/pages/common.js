/* Shared helpers for the pages. Wording here is proposed (〔建议〕 in source.md) unless it is in confirmed_text. */
var RB = (function () {
  var R = Proto.rules;
  var NAMES = { jia: "员工甲", yi: "员工乙", bing: "员工丙", m: "管理员 M" };
  var TONE = { "有效": "success", "已取消": "neutral" };

  // Feedback for rule results. Each entry carries its own annotation IDs, written literally.
  var MSG = {
    bookOk:      { text: "预约成功", kind: "ok", proposal: "FR-B05", open: "Q-10" },
    topic:       { text: "请填写会议主题", kind: "error", proposal: "FR-B03", rule: "FR-B03" },
    time:        { text: "请选择 09:00—18:00 内的半小时整点时段，且开始早于结束", kind: "error", proposal: "FR-C02", rule: "FR-C02" },
    room:        { text: "该会议室暂不可预约", kind: "error", proposal: "FR-C07", rule: "FR-C07" },
    conflict:    { text: "该时段已被占用，请选择其他时段", kind: "error", proposal: "FR-B06", open: "Q-12" },
    reOk:        { text: "改期成功", kind: "ok", proposal: "FR-R05", open: "Q-10" },
    reConflict:  { text: "目标时段已被占用，原预约保持不变", kind: "error", proposal: "FR-R06", open: "Q-12" },
    reBlocked:   { text: "该预约当前不可改期", kind: "error", proposal: "FR-R02", rule: "FR-R02 FR-R07 FR-X05" },
    xBlocked:    { text: "该预约当前不可取消", kind: "error", proposal: "FR-X02", rule: "FR-X02 FR-X05" },
    xOk:         { text: "预约已取消", kind: "ok", proposal: "FR-X03", open: "Q-10" },
    mBlocked:    { text: "该预约当前不可取消", kind: "error", proposal: "FR-M02", rule: "FR-M02" },
    mReason:     { text: "请填写取消原因", kind: "error", proposal: "FR-M03", rule: "FR-M03", open: "Q-25" },
    mOk:         { text: "预约已取消", kind: "ok", proposal: "FR-M04", open: "Q-10" }
  };

  function say(c, key) { var m = MSG[key]; c.flash(m.text, m); }
  function name(id) { return NAMES[id] || id; }
  function roomName(c, id) { var r = R.roomById(c.data.rooms, id); return r ? r.name : id; }
  function find(c, id) { return c.data.bookings.filter(function (b) { return b.id === String(id); })[0]; }
  function today(c) {                                     // FR-C01: the date in Asia/Shanghai
    return new Date(c.now.getTime() + 8 * 3600 * 1000).toISOString().slice(0, 10);
  }
  function hhmm(m) { return ("0" + Math.floor(m / 60)).slice(-2) + ":" + ("0" + (m % 60)).slice(-2); }
  function times(from, to) { var out = []; for (var m = from; m <= to; m += 30) out.push(hhmm(m)); return out; }
  function opts(list, current) {
    return list.map(function (v) {
      var val = typeof v === "string" ? v : v.value, label = typeof v === "string" ? v : v.label;
      return '<option value="' + Proto.esc(val) + '"' + (val === current ? " selected" : "") + ">" + Proto.esc(label) + "</option>";
    }).join("");
  }
  function nowText(c) {
    return new Date(c.now.getTime() + 8 * 3600 * 1000).toISOString().slice(0, 16).replace("T", " ");
  }
  // Status text: 已取消 is confirmed; the wording for 有效 is the proposal 「已预约」 (Q-21).
  function status(c, b) {
    var text = b.status === "已取消" ? "已取消" : "已预约";
    return '<span class="p-status" data-component="StatusBadge" data-tone="' + (TONE[b.status] || "neutral") + '"' +
      (b.status === "已取消" ? ' data-rule="FR-L02"' : ' data-proposal="FR-L02" data-open="Q-21"') + ">" + c.esc(text) + "</span>";
  }

  // Review aid: submit directly, bypassing the interface, for actions the interface does not offer (FR-C06).
  function directPanel(c) {
    var rows = c.data.bookings.map(function (b) {
      var btns = [];
      if (!R.canModify(b, c.role.id, c.now)) {
        btns.push('<button class="p-btn" data-action="directReschedule" data-id="' + c.esc(b.id) + '">直接提交：改期</button>');
        btns.push('<button class="p-btn" data-action="directCancel" data-id="' + c.esc(b.id) + '">直接提交：取消</button>');
      }
      if (c.role.id === "m" && !R.adminCanCancel(b, c.role.id, c.data.rooms, c.now)) {
        btns.push('<button class="p-btn" data-action="directAdminCancel" data-id="' + c.esc(b.id) + '">直接提交：管理员取消</button>');
      }
      if (!btns.length) return "";
      return "<tr><td>" + c.esc(roomName(c, b.room)) + '<span class="p-cell-sub">' + c.esc(b.date + " " + b.start + "—" + b.end) +
        "</span></td><td>" + c.esc(name(b.creator)) + '<span class="p-cell-sub">' + c.esc(b.status) + "</span></td><td>" +
        '<div class="p-row">' + btns.join("") + "</div></td></tr>";
    }).join("");
    if (!rows) return "";
    return '<section class="p-card p-review-only" data-rule="FR-C06">' +
      '<h2 class="p-h">评审辅助：绕过界面直接提交</h2>' +
      "<p>以下请求界面不提供，用于演示服务端仍然校验（不是界面设计）。改期请求的目标沿用原时段，只看归属、状态与开始时间的拒绝。</p>" +
      '<table class="p-table"><thead><tr><th>预约</th><th>预约人</th><th>请求</th></tr></thead><tbody>' + rows + "</tbody></table></section>";
  }

  return { R: R, MSG: MSG, say: say, name: name, roomName: roomName, find: find, today: today, hhmm: hhmm,
           times: times, opts: opts, nowText: nowText, status: status, directPanel: directPanel };
})();

Proto.action("directReschedule", function (c, a) {
  var b = RB.find(c, a.id);
  var target = { room: b.room, date: b.date, start: b.start, end: b.end };
  // The panel lists only bookings that FR-L03 does not offer, so the rule rejects at its first check.
  if (RB.R.rescheduleProblem(b, target, c.data, c.role.id, c.now)) return RB.say(c, "reBlocked");
});
Proto.action("directCancel", function (c, a) {
  var b = RB.find(c, a.id);
  if (RB.R.cancelProblem(b, c.role.id, c.now)) return RB.say(c, "xBlocked");
});
Proto.action("directAdminCancel", function (c, a) {
  var b = RB.find(c, a.id);
  if (RB.R.adminCancelProblem(b, c.role.id, c.data.rooms, "场地临时检修", c.now)) return RB.say(c, "mBlocked");
});
