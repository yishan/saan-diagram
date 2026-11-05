/* Confirmed rules only (source.md 第 4 章). Each function is pure and names the rule it implements.
   Dates are "YYYY-MM-DD", times "HH:mm", all in Asia/Shanghai (FR-C01).
   Open questions are not decided here: startState "at" (Q-07) comes back as the code "boundary",
   and pages handle whitespace-only text (Q-05, Q-25) before calling; both end in a pending message. */
(function (R) {
  function toMin(t) {
    var m = /^(\d{2}):(\d{2})$/.exec(t || "");
    return m ? Number(m[1]) * 60 + Number(m[2]) : NaN;
  }
  R.toMin = toMin;

  // FR-C01: a booking's start instant, read in Asia/Shanghai (+08:00)
  R.startsAt = function (b) { return new Date(b.date + "T" + b.start + ":00+08:00"); };

  // FR-C02 (FR-C03 boundaries follow): one date per booking (FR-B01), half-hour ticks,
  // start >= 09:00, end <= 18:00, start earlier than end
  R.timeValid = function (f) {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(f.date || "")) return false;
    var s = toMin(f.start), e = toMin(f.end);
    if (isNaN(s) || isNaN(e)) return false;
    return s % 30 === 0 && e % 30 === 0 && s >= 9 * 60 && e <= 18 * 60 && s < e;
  };

  // FR-C04: occupancy is [start, end); same room and same date; touching ends do not overlap
  R.overlaps = function (a, b) {
    return a.room === b.room && a.date === b.date &&
      toMin(a.start) < toMin(b.end) && toMin(b.start) < toMin(a.end);
  };
  // FR-C04, FR-R04: only valid ("有效") bookings count; the booking being rescheduled is ignored
  R.conflict = function (bookings, target, ignoreId) {
    return bookings.some(function (b) { return b.status === "有效" && b.id !== ignoreId && R.overlaps(b, target); });
  };

  // FR-C07: only enabled rooms can be booked or used as a reschedule target
  R.roomEnabled = function (room) { return !!room && room.enabled === true; };

  // 4.3: room administrator. Where this mapping comes from is Q-01; the prototype reads room.admins
  R.isAdminOf = function (room, roleId) { return !!room && (room.admins || []).indexOf(roleId) >= 0; };

  // FR-V02: the booker and the room's administrator see the topic; everyone else sees 「已占用」
  R.canSeeTopic = function (b, room, roleId) { return b.owner === roleId || R.isAdminOf(room, roleId); };

  // FR-R02, FR-X02, FR-M02: "before" | "at" | "after" the start time. Whether "at" counts as started is Q-07.
  R.startState = function (b, now) {
    var d = R.startsAt(b).getTime() - now.getTime();
    return d > 0 ? "before" : d === 0 ? "at" : "after";
  };

  // FR-L03 (FR-R02, FR-X01): own, valid, not yet started
  R.canChange = function (b, roleId, now) {
    return b.owner === roleId && b.status === "有效" && R.startState(b, now) === "before";
  };

  // FR-M01: another person's booking in a room this admin manages, valid, not yet started (own bookings: FR-M05)
  R.canAdminCancel = function (b, room, roleId, now) {
    return b.owner !== roleId && R.isAdminOf(room, roleId) && b.status === "有效" && R.startState(b, now) === "before";
  };

  // FR-B03, FR-B04 (FR-C02, FR-C07), FR-B06 (FR-C04). Returns a problem code or null.
  R.bookingProblem = function (f, room, bookings) {
    if (!f.topic) return "topic";
    if (!R.timeValid(f)) return "time";
    if (!R.roomEnabled(room)) return "room";
    if (R.conflict(bookings, f, null)) return "conflict";
    return null;
  };

  // FR-X05, FR-R02, FR-R03, FR-R04, FR-R06. Returns a problem code or null.
  R.rescheduleProblem = function (b, f, targetRoom, bookings, roleId, now) {
    if (b.status === "已取消") return "cancelled";
    if (b.owner !== roleId) return "notOwner";
    var st = R.startState(b, now);
    if (st === "at") return "boundary";
    if (st === "after") return "started";
    if (!R.timeValid(f)) return "time";
    if (!R.roomEnabled(targetRoom)) return "room";
    if (R.conflict(bookings, f, b.id)) return "conflict";
    return null;
  };

  // FR-X01, FR-X02, FR-X05. Returns a problem code or null.
  R.cancelProblem = function (b, roleId, now) {
    if (b.status === "已取消") return "cancelled";
    if (b.owner !== roleId) return "notOwner";
    var st = R.startState(b, now);
    if (st === "at") return "boundary";
    if (st === "after") return "started";
    return null;
  };

  // FR-M01, FR-M02, FR-M03. Returns a problem code or null.
  R.adminCancelProblem = function (b, room, roleId, now, reason) {
    if (b.status === "已取消") return "cancelled";
    if (!R.isAdminOf(room, roleId)) return "notAdmin";
    var st = R.startState(b, now);
    if (st === "at") return "boundary";
    if (st === "after") return "started";
    if (!reason) return "reason";
    return null;
  };
})(Proto.rules);
