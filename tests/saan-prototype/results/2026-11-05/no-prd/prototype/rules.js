/* Confirmed rules only (from the author's restatement in source.md). Each function is pure and names its rule. */
Proto.rules.dateKey = function (d) {                        // FR-1, FR-3: dates are Asia/Shanghai calendar days
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Shanghai", year: "numeric", month: "2-digit", day: "2-digit" }).format(d);
};
Proto.rules.tomorrow = function (now) {                     // FR-1: only tomorrow can be registered
  return Proto.rules.dateKey(new Date(now.getTime() + 24 * 3600 * 1000));
};
Proto.rules.activeFor = function (regs, spotId, date) {     // FR-2: one active registration per spot per day
  return regs.filter(function (r) { return r.spot === spotId && r.date === date && r.status === "已登记"; })[0] || null;
};
Proto.rules.canRegister = function (regs, spotId, date, now) {  // FR-1, FR-2
  return date === Proto.rules.tomorrow(now) && !Proto.rules.activeFor(regs, spotId, date);
};
Proto.rules.canCancel = function (reg, roleId, now) {       // FR-3: own, active, cancelled on the day it was made
  return reg.by === roleId && reg.status === "已登记" && reg.createdOn === Proto.rules.dateKey(now);
};
