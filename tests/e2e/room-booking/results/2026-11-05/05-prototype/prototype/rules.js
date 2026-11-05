/* Confirmed rules only (需求规格说明书 V0.1 第 4 章). Each function is pure and names the rule it implements.
   Open questions are never decided here: where a rule depends on one, the function returns {open: "Q-…"}
   and the page shows a pending message instead of an answer. */
(function (R) {
  var TZ = "+08:00";                                    // FR-C01：以 Asia/Shanghai 为准

  R.toMin = function (hhmm) {                           // "09:30" -> 570；格式不对返回 NaN
    var m = /^(\d{2}):(\d{2})$/.exec(hhmm || "");
    return m ? Number(m[1]) * 60 + Number(m[2]) : NaN;
  };
  R.hhmm = function (min) {
    return String(Math.floor(min / 60)).padStart(2, "0") + ":" + String(min % 60).padStart(2, "0");
  };
  R.at = function (date, hhmm) {                        // FR-C01
    return new Date(date + "T" + hhmm + ":00" + TZ);
  };
  R.today = function (now) {                            // FR-C01：当前日期按 Asia/Shanghai
    return new Date(now.getTime() + 8 * 3600 * 1000).toISOString().slice(0, 10);
  };
  R.stamp = function (now) {                            // FR-C01：记录时间按 Asia/Shanghai 展示
    return new Date(now.getTime() + 8 * 3600 * 1000).toISOString().slice(0, 16).replace("T", " ");
  };

  R.timeProblem = function (date, start, end) {         // FR-C02
    var s = R.toMin(start), e = R.toMin(end);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(date || "") || isNaN(s) || isNaN(e)) return "FR-C02";
    if (s % 30 || e % 30) return "FR-C02";              // ② 半小时刻度
    if (s < 9 * 60 || e > 18 * 60) return "FR-C02";     // ③ 09:00—18:00
    if (s >= e) return "FR-C02";                         // ④ 开始早于结束（① 同一日：表单只有一个日期）
    return null;
  };

  R.room = function (data, id) {
    return data.rooms.filter(function (r) { return r.id === id; })[0] || null;
  };
  R.roomEnabled = function (room) {                     // FR-C07
    return !!(room && room.enabled);
  };

  R.overlaps = function (a, b) {                        // FR-C04：[开始, 结束) 左闭右开，首尾相接不冲突
    return a.room === b.room && a.date === b.date &&
      R.toMin(a.start) < R.toMin(b.end) && R.toMin(b.start) < R.toMin(a.end);
  };
  R.conflict = function (data, target, exceptId) {      // FR-C04；FR-R04 原预约自身不计入
    return data.bookings.filter(function (b) {
      return b.status === "有效" && b.id !== exceptId && R.overlaps(b, target);   // 「已取消」不参与
    })[0] || null;
  };

  R.startState = function (b, now) {                   // 尚未开始／已经开始；恰好等于开始时刻见 Q-07
    var t = R.at(b.date, b.start).getTime(), n = now.getTime();
    return n < t ? "not_started" : n > t ? "started" : "boundary";
  };

  R.isRoomAdmin = function (room, roleId) {             // 4.3；对应关系来源未定（Q-01），原型取示例数据
    return !!(room && (room.admins || []).indexOf(roleId) >= 0);
  };
  R.canSeeTopic = function (b, room, roleId) {          // FR-V02
    return b.creator === roleId || R.isRoomAdmin(room, roleId);
  };

  R.bookProblem = function (f, data) {                  // FR-B03、FR-B04（FR-C02、FR-C07）、FR-B06（FR-C04）
    if (!f.topic) return { rule: "FR-B03" };            // 纯空格是否视为空未定（Q-05），原型不判断
    if (R.timeProblem(f.date, f.start, f.end)) return { rule: "FR-C02" };
    if (!R.roomEnabled(R.room(data, f.room))) return { rule: "FR-C07" };
    if (R.conflict(data, f)) return { rule: "FR-B06" };
    return null;
  };
  R.newBooking = function (f, roleId, id) {             // FR-B02 创建人取当前登录员工；FR-B05 成为有效预约
    return { id: id, room: f.room, date: f.date, start: f.start, end: f.end, topic: f.topic,
             creator: roleId, status: "有效" };
  };

  R.ownerProblem = function (b, roleId, now, kind) {    // FR-L03；改期 FR-R02，取消 FR-X01/FR-X02；已取消 FR-X05
    if (b.status === "已取消") return { rule: "FR-X05" };
    if (b.creator !== roleId) return { rule: kind === "cancel" ? "FR-X02" : "FR-R02" };
    var st = R.startState(b, now);
    if (st === "boundary") return { open: "Q-07" };
    if (st === "started") return { rule: kind === "cancel" ? "FR-X02" : "FR-R02" };
    return null;
  };

  R.rescheduleProblem = function (b, t, data, roleId, now) {   // FR-R01—FR-R06、FR-R07
    var p = R.ownerProblem(b, roleId, now, "reschedule");
    if (p) return p;
    if (R.timeProblem(t.date, t.start, t.end)) return { rule: "FR-R03", why: "FR-C02" };
    if (!R.roomEnabled(R.room(data, t.room))) return { rule: "FR-R03", why: "FR-C07" };
    if (t.room === b.room && t.date === b.date && t.start === b.start && t.end === b.end) return { open: "Q-22" };
    if (R.conflict(data, t, b.id)) return { rule: "FR-R06" };
    return null;
  };
  R.applyReschedule = function (b, t) {                 // FR-R05；FR-R01 主题、创建人不变
    b.room = t.room; b.date = t.date; b.start = t.start; b.end = t.end;
  };

  R.cancel = function (b, roleId, now, reason) {        // FR-X03 / FR-M04：状态变为「已取消」，保存操作人与时间
    b.status = "已取消"; b.cancelledBy = roleId; b.cancelledAt = R.stamp(now);
    if (reason !== undefined) b.cancelReason = reason;
  };

  R.adminProblem = function (b, room, roleId, now) {    // FR-M01、FR-M02、FR-M05
    if (b.creator === roleId) return { open: "Q-26" };  // 本人预约走哪条取消路径未定
    if (!R.isRoomAdmin(room, roleId) || b.status !== "有效") return { rule: "FR-M02" };
    var st = R.startState(b, now);
    if (st === "boundary") return { open: "Q-07" };
    if (st === "started") return { rule: "FR-M02" };
    return null;
  };
  R.adminCancelProblem = function (b, room, roleId, now, reason) {   // FR-M01—FR-M03
    var p = R.adminProblem(b, room, roleId, now);
    if (p) return p;
    if (!reason) return { rule: "FR-M03" };             // 纯空格是否视为空未定（Q-25），原型不判断
    return null;
  };
})(Proto.rules);
