/* Saan Prototype runtime: review bar, annotations, roles, scenarios, themes. */
(function () {
  "use strict";
  var D = JSON.parse(document.getElementById("p-data").textContent);
  var pages = [], actions = {};
  var S = { scenario: null, role: null, now: null, data: null, page: null, flash: null, dialog: null,
            review: true, components: false, theme: D.theme };
  var KIND = { proposal: "建议", open: "待确认", rule: "规则" };

  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function role() { return D.roles.filter(function (r) { return r.id === S.role; })[0] || D.roles[0]; }
  function visible() {
    return pages.filter(function (p) { return !p.roles || p.roles.indexOf(S.role) >= 0; });
  }
  function inNav(p) { return p.nav !== false; }
  function ctx() {
    return {
      data: S.data, role: role(), now: S.now, rules: Proto.rules, scenario: S.scenario, esc: esc,
      go: function (id) { S.page = id; },  // keeps a message set in the same action; run() clears old ones
      flash: function (text, opt) { S.flash = Object.assign({ text: text, kind: "ok" }, opt || {}); },
      dialog: function (html) { S.dialog = html; },
      confirm: function (opt, name) { S.dialog = confirmHtml(opt, name); },
      close: function () { S.dialog = null; }
    };
  }
  function attrs(opt) {
    var out = "";
    ["proposal", "open", "rule"].forEach(function (k) { if (opt && opt[k]) out += " data-" + k + '="' + esc(opt[k]) + '"'; });
    return out;
  }
  function confirmHtml(opt, name) {
    var data = opt.data || {};
    var dattrs = Object.keys(data).map(function (k) {
      return " data-" + esc(k.replace(/[A-Z]/g, "-$&").toLowerCase()) + '="' + esc(data[k]) + '"';  // dataset gives back k
    }).join("");
    var changes = (opt.changes || []).map(function (ch) {
      return "<tr><th>" + esc(ch.label) + "</th><td>" + esc(ch.from) + '</td><td aria-hidden="true">→</td><td>' + esc(ch.to) + "</td></tr>";
    }).join("");
    var effects = (opt.effects || []).map(function (ef) {
      ef = typeof ef === "string" ? { text: ef } : ef;
      return "<li" + (ef.open ? ' class="p-pending p-review-only"' : "") + attrs(ef) + ">" + esc(ef.text) + "</li>";
    }).join("");
    var btn = opt.confirm || { text: "确认" };
    return '<form class="p-confirm" data-action="' + esc(name) + '"' + dattrs + ">" +
      '<h2 class="p-h"' + attrs(opt) + ">" + esc(opt.title) + "</h2>" + (opt.body || "") +
      (changes ? '<table class="p-table p-changes"><tbody>' + changes + "</tbody></table>" : "") +
      (effects ? '<ul class="p-effects">' + effects + "</ul>" : "") +
      '<div class="p-row"><button class="p-btn ' + (opt.danger ? "danger" : "primary") + '"' + attrs(btn) + ">" + esc(btn.text) + "</button>" +
      '<button type="button" class="p-btn" data-p-close>返回</button></div></form>';
  }
  function applyTheme() {
    var t = D.themes[S.theme] || D.themes[Object.keys(D.themes)[0]];
    ["success"].forEach(function (k) { if (!(k in t)) document.documentElement.style.removeProperty("--" + k); });
    Object.keys(t).forEach(function (k) { if (k !== "label") document.documentElement.style.setProperty("--" + k, t[k]); });
  }
  function option(value, label, current) {
    return '<option value="' + esc(value) + '"' + (value === current ? " selected" : "") + ">" + esc(label) + "</option>";
  }
  function bar() {
    var sc = D.scenarios.map(function (s) {
      return option(s.id, s.label + (s.acceptance && s.acceptance.length ? "（" + s.acceptance.join("、") + "）" : ""), S.scenario.id);
    }).join("");
    var ro = D.roles.map(function (r) { return option(r.id, r.label, S.role); }).join("");
    var th = Object.keys(D.themes).map(function (k) { return option(k, D.themes[k].label || k, S.theme); }).join("");
    document.getElementById("p-bar").innerHTML =
      '<span class="p-tag-review">评审原型 · 示例数据为虚构' +
      (D.design ? " · 按《" + esc(D.design.name) + (D.design.version ? " " + esc(D.design.version) : "") + "》" : "") + "</span>" +
      '<label>场景 <select data-bar="scenario">' + sc + "</select></label>" +
      '<label>角色 <select data-bar="role">' + ro + "</select></label>" +
      '<label>主题 <select data-bar="theme">' + th + "</select></label>" +
      '<label><input type="checkbox" data-bar="review"' + (S.review ? " checked" : "") + "> 标注</label>" +
      (D.design ? '<label><input type="checkbox" data-bar="components"' + (S.components ? " checked" : "") + "> 组件名</label>" : "") +
      "<span>当前时间 " + esc(new Intl.DateTimeFormat(D.language, { timeZone: D.timezone, dateStyle: "medium", timeStyle: "short" }).format(S.now)) +
      "（" + esc(D.timezone) + "）</span>";
  }
  function decorate(root) {
    ["proposal", "open", "rule"].forEach(function (k) {
      root.querySelectorAll("[data-" + k + "]").forEach(function (el) {
        var done = el.__badged || (el.__badged = {});
        el.getAttribute("data-" + k).split(/\s+/).filter(Boolean).forEach(function (id) {
          if (done[id]) return;  // the same ID as proposal and rule gets one badge
          done[id] = true;
          var b = document.createElement("span");
          b.className = "p-badge " + k;
          b.textContent = (k === "proposal" ? "建议 " : "") + id;
          b.setAttribute("data-def", id);
          b.title = KIND[k] + " · " + id + "\n" + (D.defs[id] || "来源中未找到该编号");
          el.appendChild(b);
        });
      });
    });
    root.querySelectorAll("[data-disabled-reason]").forEach(function (el) {
      if (el.__reason) return;
      el.__reason = true;
      var s = document.createElement("span");
      s.className = "p-reason";
      s.textContent = el.getAttribute("data-disabled-reason");
      el.insertAdjacentElement("afterend", s);
    });
    if (D.design) root.querySelectorAll("[data-component]").forEach(function (el) {
      if (el.__comp) return;
      el.__comp = true;
      var name = el.getAttribute("data-component"), def = D.design.components[name];
      var b = document.createElement("span");
      b.className = "p-badge component";
      b.textContent = name;
      b.title = "组件 · " + name + "\n" + (def ? def.rule || "" : "规范中没有该组件");
      if (/^(TABLE|UL|OL|SELECT|INPUT|TEXTAREA)$/.test(el.tagName)) el.insertAdjacentElement("beforebegin", b);
      else if (/^(THEAD|TBODY|TR)$/.test(el.tagName)) (el.querySelector("th,td") || el).appendChild(b);
      else el.appendChild(b);
    });
  }
  function render() {
    document.getElementById("p-pop").hidden = true;  // its badge is about to be replaced
    applyTheme();
    document.body.classList.toggle("p-review-off", !S.review);
    document.body.classList.toggle("p-components-on", S.components);
    bar();
    var vis = visible();
    if (!vis.some(function (p) { return p.id === S.page; })) {
      var first = vis.filter(inNav)[0] || vis[0];
      S.page = first ? first.id : null;
    }
    document.getElementById("p-nav").innerHTML = vis.filter(inNav).map(function (p) {
      return '<button data-go="' + esc(p.id) + '"' + (p.id === S.page ? ' aria-current="page"' : "") + attrs(p) + ">" + esc(p.label) + "</button>";
    }).join("");
    var page = vis.filter(function (p) { return p.id === S.page; })[0];
    var flash = S.flash ? '<div class="p-flash ' + esc(S.flash.kind) + '"' + attrs(S.flash) + ">" + esc(S.flash.text) + "</div>" : "";
    var html = (S.dialog ? "" : flash) + (page ? page.render(ctx()) : '<div class="p-empty">当前角色没有可见页面</div>');
    if (S.dialog) html += '<div class="p-dialog"><div>' + flash + S.dialog + "</div></div>";  // keep the message visible above the overlay
    var main = document.getElementById("p-main");
    main.innerHTML = html;
    decorate(document.getElementById("p-nav"));
    decorate(main);
  }
  function load(id) {
    var sc = D.scenarios.filter(function (s) { return s.id === id; })[0] || D.scenarios[0];
    S.scenario = sc; S.role = sc.role || D.roles[0].id; S.now = new Date(sc.now || Date.now());
    S.data = JSON.parse(JSON.stringify(sc.data || {})); S.flash = null; S.dialog = null;
    if (sc.page) S.page = sc.page;
    render();
  }
  function popover(badge) {
    var pop = document.getElementById("p-pop"), r = badge.getBoundingClientRect(), id = badge.getAttribute("data-def");
    pop.innerHTML = "<strong>" + esc(id) + "</strong><br>" + esc(D.defs[id] || "来源中未找到该编号");
    pop.style.left = Math.min(r.left, innerWidth - 380) + "px";
    pop.style.top = (r.bottom + 6) + "px";
    pop.hidden = false;
  }
  function run(name, el, extra) {
    var fn = actions[name];
    if (!fn) { S.flash = { text: "原型未实现动作：" + name, kind: "error" }; return render(); }
    S.flash = null;  // a new action replaces the previous message
    fn(ctx(), Object.assign({}, el.dataset, extra || {}), el);
    render();
  }

  document.addEventListener("click", function (e) {
    var pop = document.getElementById("p-pop");
    var badge = e.target.closest(".p-badge.open");
    if (badge) { e.preventDefault(); e.stopPropagation(); return popover(badge); }
    pop.hidden = true;
    if (e.target.closest("[data-p-close]")) { S.dialog = null; S.flash = null; return render(); }
    var go = e.target.closest("[data-go]");
    if (go) { S.page = go.getAttribute("data-go"); S.flash = null; S.dialog = null; return render(); }
    var act = e.target.closest("button[data-action], a[data-action]");
    if (act && !act.disabled) { e.preventDefault(); run(act.getAttribute("data-action"), act); }
  });
  document.addEventListener("submit", function (e) {
    var form = e.target.closest("form[data-action]");
    if (!form) return;
    e.preventDefault();
    var fields = {};
    new FormData(form).forEach(function (v, k) { fields[k] = v; });
    run(form.getAttribute("data-action"), form, { fields: fields });
  });
  document.addEventListener("change", function (e) {
    var k = e.target.getAttribute("data-bar");
    if (!k) {
      var field = e.target.closest("input[data-action], select[data-action]");
      if (field) run(field.getAttribute("data-action"), field, { value: field.type === "checkbox" ? field.checked : field.value });
      return;
    }
    if (k === "scenario") return load(e.target.value);
    if (k === "role") { S.role = e.target.value; S.flash = null; S.dialog = null; }
    if (k === "theme") S.theme = e.target.value;
    if (k === "review") S.review = e.target.checked;
    if (k === "components") S.components = e.target.checked;
    render();
  });

  window.Proto = {
    rules: {},
    page: function (id, def) { pages.push(Object.assign({ id: id }, def)); },
    action: function (name, fn) { actions[name] = fn; },
    start: function () { load(D.scenarios[0] && D.scenarios[0].id); },
    esc: esc
  };
})();
