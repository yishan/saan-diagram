/* Confirmed rules only (as restated in source.md). Each function is pure and names the rule it implements. */
// Calendar date (YYYY-MM-DD) in Asia/Shanghai (UTC+8, no daylight saving) for a Date or ISO string.
Proto.rules.dayOf = function (t) {
  var d = t instanceof Date ? t : new Date(t);
  return new Date(d.getTime() + 8 * 3600 * 1000).toISOString().slice(0, 10);
};
Proto.rules.tomorrow = function (now) {                  // FR-1
  return Proto.rules.dayOf(new Date(now.getTime() + 24 * 3600 * 1000));
};
Proto.rules.canRegisterDate = function (date, now) {     // FR-1
  return date === Proto.rules.tomorrow(now);
};
Proto.rules.holderOf = function (spotId, date, regs) {   // FR-2
  return regs.filter(function (r) {
    return r.spot === spotId && r.date === date && r.status === "已登记";
  })[0] || null;
};
Proto.rules.isOwnActive = function (reg, roleId) {       // FR-3
  return !!reg && reg.owner === roleId && reg.status === "已登记";
};
Proto.rules.withinCancelDay = function (reg, now) {      // FR-3
  return Proto.rules.dayOf(reg.createdAt) === Proto.rules.dayOf(now);
};
