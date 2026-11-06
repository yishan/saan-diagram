/* Confirmed rules only (source.md §4). Each function is pure and names the rule it implements.
   Times are "HH:mm" strings and dates "YYYY-MM-DD", read in Asia/Shanghai (FR-C01). */
(function (R) {
  function min(t) {                                        // "09:30" -> 570; null when not HH:mm
    var m = /^(\d{2}):(\d{2})$/.exec(String(t || ""));
    return m ? Number(m[1]) * 60 + Number(m[2]) : null;
  }
  R.min = min;
  R.roomById = function (rooms, id) {
    return rooms.filter(function (r) { return r.id === id; })[0] || null;
  };
  R.startAt = function (b) {                               // FR-C01: Asia/Shanghai is UTC+8 with no DST
    return new Date(b.date + "T" + b.start + ":00+08:00");
  };

  // FR-C02: same day, half-hour marks, start >= 09:00, end <= 18:00, start before end.
  // The form has one date field, so ① holds by construction.
  R.timeValid = function (date, start, end) {
    var s = min(start), e = min(end);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(String(date || ""))) return false;
    if (s === null || e === null) return false;
    if (s % 30 !== 0 || e % 30 !== 0) return false;
    if (s < 9 * 60 || e > 18 * 60) return false;
    return s < e;
  };

  // FR-C04: [start, end) on the same room; touching ends do not conflict; 已取消 is ignored.
  // FR-R04: the booking being rescheduled (exceptId) does not count. Q-13 (cross-room per person) is not checked.
  R.overlaps = function (a, b) {
    return a.room === b.room && a.date === b.date && min(a.start) < min(b.end) && min(b.start) < min(a.end);
  };
  R.conflict = function (bookings, target, exceptId) {
    return bookings.filter(function (b) {
      return b.status === "有效" && b.id !== exceptId && R.overlaps(b, target);
    })[0] || null;
  };

  // Room administrator: the prototype reads rooms[].admins from sample data; the real source is Q-01.
  R.isAdmin = function (rooms, roomId, roleId) {
    var r = R.roomById(rooms, roomId);
    return !!(r && (r.admins || []).indexOf(roleId) >= 0);
  };

  // FR-V02: topic is visible to the booker and to the room's administrator; everyone else sees 已占用.
  R.canSeeTopic = function (b, roleId, rooms) {
    return b.creator === roleId || R.isAdmin(rooms, b.room, roleId);
  };

  // FR-R02, FR-X02, FR-M02: "already started" compares the start time with now at submission.
  // The prototype reads "now >= start" as started; the exact boundary is Q-07.
  R.hasStarted = function (b, now) {
    return now.getTime() >= R.startAt(b).getTime();
  };

  // FR-L03: only the booker's own 有效 booking that has not started can be rescheduled or cancelled.
  R.canModify = function (b, roleId, now) {
    return b.creator === roleId && b.status === "有效" && !R.hasStarted(b, now);
  };

  // FR-B02—FR-B06, FR-C02, FR-C05, FR-C06, FR-C07: returns null when the new booking can be created,
  // otherwise "topic" | "time" | "room" | "conflict". The creator is never taken from the request (FR-B02).
  // Q-05: only an empty string counts as empty; whether spaces count is open.
  R.bookProblem = function (req, data) {
    if (!req.topic) return "topic";                                     // FR-B03
    if (!R.timeValid(req.date, req.start, req.end)) return "time";      // FR-C02
    var room = R.roomById(data.rooms, req.room);
    if (!room || !room.enabled) return "room";                          // FR-C07
    if (R.conflict(data.bookings, req, null)) return "conflict";        // FR-C04, FR-B06
    return null;
  };

  // FR-R01—FR-R07, FR-X05, FR-C06: returns null, or "blocked" | "time" | "room" | "conflict".
  // Q-22 (target identical to the original) is not decided and not handled.
  R.rescheduleProblem = function (b, target, data, roleId, now) {
    if (!b || !R.canModify(b, roleId, now)) return "blocked";          // FR-R02, FR-R07, FR-X05
    if (!R.timeValid(target.date, target.start, target.end)) return "time";   // FR-R03, FR-C02
    var room = R.roomById(data.rooms, target.room);
    if (!room || !room.enabled) return "room";                          // FR-R03, FR-C07
    if (R.conflict(data.bookings, target, b.id)) return "conflict";     // FR-R04, FR-R06
    return null;
  };

  // FR-X01, FR-X02, FR-X05: the booker cancels their own 有效 booking that has not started.
  R.cancelProblem = function (b, roleId, now) {
    return b && R.canModify(b, roleId, now) ? null : "blocked";
  };

  // FR-M01: the administrator's room, 有效, not started. Used to decide whether to offer the action.
  R.adminCanCancel = function (b, roleId, rooms, now) {
    return !!b && b.status === "有效" && R.isAdmin(rooms, b.room, roleId) && !R.hasStarted(b, now);
  };
  // FR-M01—FR-M03: returns null, or "blocked" | "reason". Q-25: only an empty string counts as empty.
  R.adminCancelProblem = function (b, roleId, rooms, reason, now) {
    if (!R.adminCanCancel(b, roleId, rooms, now)) return "blocked";     // FR-M02
    if (!reason) return "reason";                                       // FR-M03
    return null;
  };
})(Proto.rules);
