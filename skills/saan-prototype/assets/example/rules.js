/* Confirmed rules only. Each function is pure and names the rule it implements. */
Proto.rules.canBorrow = function (device) {            // FR-B01, FR-B02
  return device.status === "可借";
};
Proto.rules.canReturn = function (device, roleId) {    // FR-R01
  return device.status === "已借出" && device.holder === roleId;
};
