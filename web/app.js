"use strict";
// Front end for Visarjan Ghat Watch. All scoring happens in Python (visarjan/); this page only renders data.json.

const MARK = { ok: "✅", violation: "❌", missing: "⬜" };
const LIMIT_TEXT = { "pH": "6.5–8.5", "Dissolved oxygen": "≥ 5 mg/l", "BOD": "≤ 3 mg/l" };
const PARAMS = ["pH", "Dissolved oxygen", "BOD"];
const PHASES = ["pre", "during", "after"];

const state = { data: null, lang: "en", withGanesh: false };
const $ = (id) => document.getElementById(id);

// Build DOM with textContent only (data is never parsed as HTML).
function el(tag, props = {}, ...kids) {
  const n = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") n.className = v;
    else if (v !== null && v !== undefined) n.setAttribute(k, v);
  }
  for (const k of kids.flat()) n.append(k instanceof Node ? k : document.createTextNode(String(k)));
  return n;
}

function table(headers, rows) {
  return el("table", {},
    el("thead", {}, el("tr", {}, headers.map((h) => el("th", {}, h)))),
    el("tbody", {}, rows.map((r) => el("tr", {}, r.map((c) => (c instanceof Node ? c : el("td", {}, c)))))));
}

const shortName = (s) => s.split(" (")[0].split(" /")[0];

function render() {
  const { data, lang } = state;
  const ui = data.ui[lang], app = data.app[lang];
  const key = state.withGanesh ? "all" : "durga";
  const results = data.variants[key];

  document.documentElement.lang = lang;
  $("title").textContent = ui.title;
  $("tagline").textContent = app.tagline;
  $("ganesh-label").textContent = app.incl_ganesh;
  $("worklist-title").textContent = app.dispatch_title;
  $("ranking-title").textContent = app.ranking_title;
  $("footer").textContent = app.footer;
  document.querySelectorAll(".lang button").forEach((b) => b.classList.toggle("on", b.dataset.lang === lang));

  const days = Math.ceil((new Date(data.visarjan_date + "T00:00:00") - new Date().setHours(0, 0, 0, 0)) / 864e5);
  const cd = $("countdown");
  cd.hidden = days < 0;
  cd.textContent = "⏳ " + (days === 0 ? app.days_today : app.days_left.replace("{n}", days));

  const link = $("brief-link");
  link.textContent = "⬇ " + app.download;
  link.href = `brief_${key}.html`;

  // work list: what to dispatch where
  const wl = $("worklist");
  wl.replaceChildren(...["clean", "aerate", "retest"].map((action) => {
    const names = results.filter((g) => g.actions.includes(action))
      .map((g) => `${g.rank}. ${shortName(g.site)}${action === "retest" && g.low_confidence ? " ⚠️" : ""}`);
    return el("div", { class: "box" }, el("h3", {}, app.list[action]),
      names.length ? el("ul", {}, names.map((n) => el("li", {}, n))) : el("div", { class: "none" }, app.none));
  }));
  wl.append(el("div", { class: "note", style: "grid-column:1/-1" }, "⚠️ = " + app.gap_mark));

  $("ghats").replaceChildren(...results.map((g) => card(g, ui, app)));
}

function card(g, ui, app) {
  const { lang, data } = state;
  const reasons = g.reasons_text[lang];
  const latest = data.latest[g.site];

  const kids = [
    el("div", { class: "card-head" },
      el("div", {}, el("h3", {}, `${g.rank}. ${g.site}`), el("div", { class: "sub" }, g.water_body),
        g.low_confidence ? el("span", { class: "conf" }, "⚠️ " + ui.conf_low) : ""),
      el("div", { class: `badge ${g.tier}` }, ui.tier[g.tier],
        el("small", {}, `${ui.score}: ${Math.round(g.score)}/100`))),
    el("ul", {}, reasons.map((r) => el("li", {}, r))),
    el("div", { class: "acts" }, ui.actions + ": " + g.actions.map((a) => ui.action[a].replace(/[.।]$/, "")).join(" · ")),
  ];

  if (latest.year === null) {
    kids.push(el("div", { class: "note" }, app.latest_none.replace("{festival}", ui.festival.Durga)));
  } else {
    kids.push(el("div", { class: "tbl-title" },
      app.latest_title.replace("{festival}", ui.festival.Durga).replace("{year}", latest.year)));
    const rows = PARAMS.map((p) => [ui.param[p], LIMIT_TEXT[p], ...PHASES.map((ph) => {
      const [text, st] = latest.table[p][ph];
      const label = text === "missing" ? "—" : text === "below detection" ? app.state.very_low : text;
      return el("td", st === "missing" ? { class: "missing" } : {}, `${MARK[st]} ${label}`);
    })]);
    kids.push(table([app.col_param, app.limit_row, ...PHASES.map((ph) => ui.phase[ph])], rows));
  }

  // every reading with its report page
  const raw = data.readings[g.site].filter((r) => state.withGanesh || r.festival === "Durga");
  kids.push(el("details", {}, el("summary", {}, app.all_readings),
    table([app.col_param, app.col_festival, app.col_year, app.col_phase, app.col_value, app.col_state, app.col_page],
      raw.map((r) => [ui.param[r.parameter], ui.festival[r.festival], r.year, ui.phase[r.phase],
        r.printed ?? "-", el("td", r.status === "missing" ? { class: "missing" } : {}, app.state[r.status]),
        r.page ?? "-"]))));

  return el("article", { class: `card ${g.tier}` }, kids);
}

async function init() {
  try {
    const res = await fetch("data.json");
    if (!res.ok) throw new Error(res.status);
    state.data = await res.json();
  } catch (e) {
    $("tagline").textContent = "Could not load data.json. Serve this folder over HTTP: python -m http.server -d web 8000";
    return;
  }
  document.querySelectorAll(".lang button").forEach((b) =>
    b.addEventListener("click", () => { state.lang = b.dataset.lang; render(); }));
  $("ganesh").addEventListener("change", (e) => { state.withGanesh = e.target.checked; render(); });
  render();
}

init();
