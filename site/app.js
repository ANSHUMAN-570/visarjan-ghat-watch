"use strict";
// Landing page behaviour: theme, mobile menu, active nav, entrance animations, dashboard links, login demo.
(function () {
  const root = document.documentElement;
  const $ = (sel) => document.querySelector(sel);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // ---- theme ------------------------------------------------------------------------------------
  const toggle = $("#theme-toggle");
  function applyTheme(theme, persist) {
    root.setAttribute("data-theme", theme);
    const dark = theme === "dark";
    toggle.setAttribute("aria-pressed", String(dark));
    toggle.setAttribute("aria-label", dark ? "Switch to light mode" : "Switch to dark mode");
    if (persist) {
      try { localStorage.setItem("vgw-theme", theme); } catch (e) { /* storage blocked: theme still applies */ }
    }
  }
  applyTheme(root.getAttribute("data-theme") === "dark" ? "dark" : "light", false);
  toggle.addEventListener("click", () => applyTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark", true));
  // follow the OS setting until the user has chosen explicitly
  const mq = window.matchMedia("(prefers-color-scheme: dark)");
  mq.addEventListener("change", (e) => {
    let saved = null;
    try { saved = localStorage.getItem("vgw-theme"); } catch (err) {}
    if (!saved) applyTheme(e.matches ? "dark" : "light", false);
  });

  // ---- dashboard links (one place to configure) -------------------------------------------------
  const meta = document.querySelector('meta[name="dashboard-url"]');
  const dashboardUrl = meta ? meta.content : "";
  document.querySelectorAll("[data-dashboard]").forEach((a) => {
    a.href = dashboardUrl;
    a.target = "_blank";
    a.rel = "noopener";
  });

  // ---- mobile menu ------------------------------------------------------------------------------
  const burger = $("#burger");
  const menu = $("#menu");
  function setMenu(open) {
    menu.classList.toggle("open", open);
    burger.setAttribute("aria-expanded", String(open));
    burger.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  }
  burger.addEventListener("click", () => setMenu(!menu.classList.contains("open")));
  menu.addEventListener("click", (e) => { if (e.target.closest("a")) setMenu(false); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && menu.classList.contains("open")) { setMenu(false); burger.focus(); } });

  // ---- nav border on scroll + active section ----------------------------------------------------
  const nav = $(".nav");
  const onScroll = () => nav.classList.toggle("scrolled", window.scrollY > 8);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const links = new Map([...document.querySelectorAll("[data-nav]")].map((a) => [a.dataset.nav, a]));
  if ("IntersectionObserver" in window) {
    const spy = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting && links.has(en.target.id)) {
          links.forEach((a) => { a.classList.remove("active"); a.removeAttribute("aria-current"); });
          links.get(en.target.id).classList.add("active");
          links.get(en.target.id).setAttribute("aria-current", "true");
        }
      });
    }, { rootMargin: "-45% 0px -50% 0px" });
    links.forEach((_, id) => { const s = document.getElementById(id); if (s) spy.observe(s); });
  }

  // ---- entrance animations ----------------------------------------------------------------------
  const reveals = document.querySelectorAll(".reveal");
  if (reduceMotion || !("IntersectionObserver" in window)) {
    reveals.forEach((el) => el.classList.add("in"));
  } else {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); } });
    }, { threshold: 0.12 });
    reveals.forEach((el) => io.observe(el));
  }

  $("#year").textContent = String(new Date().getFullYear());

  // ---- login (frontend-only demo: validates, sends nothing, stores nothing) ----------------------
  const dialog = $("#login-dialog");
  const form = $("#login-form");
  const email = $("#email");
  const password = $("#password");
  const submit = $("#login-submit");
  const msg = $("#login-msg");
  const pwToggle = $("#pw-toggle");
  let opener = null;

  function setError(input, text) {
    const err = document.getElementById(input.id + "-err");
    err.textContent = text || "";
    err.hidden = !text;
    input.setAttribute("aria-invalid", text ? "true" : "false");
  }
  function validate() {
    let ok = true;
    const e = email.value.trim();
    if (!e) { setError(email, "Enter your email address."); ok = false; }
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(e)) { setError(email, "Enter a valid email address, like name@example.com."); ok = false; }
    else setError(email, "");
    if (!password.value) { setError(password, "Enter your password."); ok = false; }
    else if (password.value.length < 8) { setError(password, "Password must be at least 8 characters."); ok = false; }
    else setError(password, "");
    return ok;
  }
  function resetForm() {
    form.reset();
    [email, password].forEach((i) => setError(i, ""));
    msg.hidden = true;
    submit.classList.remove("loading");
    pwToggle.setAttribute("aria-pressed", "false");
    pwToggle.setAttribute("aria-label", "Show password");
    password.type = "password";
  }

  $("#login-open").addEventListener("click", (e) => {
    opener = e.currentTarget;
    resetForm();
    dialog.showModal();
    email.focus();
  });
  $("#login-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (e) => { if (e.target === dialog) dialog.close(); }); // backdrop click
  dialog.addEventListener("close", () => { password.value = ""; if (opener) opener.focus(); });

  pwToggle.addEventListener("click", () => {
    const show = password.type === "password";
    password.type = show ? "text" : "password";
    pwToggle.setAttribute("aria-pressed", String(show));
    pwToggle.setAttribute("aria-label", show ? "Hide password" : "Show password");
  });
  [email, password].forEach((i) => i.addEventListener("input", () => {
    if (i.getAttribute("aria-invalid") === "true") validate();
  }));

  form.addEventListener("submit", (e) => {
    e.preventDefault(); // never let the dialog form submit anywhere
    msg.hidden = true;
    if (!validate()) {
      (email.getAttribute("aria-invalid") === "true" ? email : password).focus();
      return;
    }
    submit.classList.add("loading");
    submit.querySelector(".lbl").textContent = "Checking…";
    setTimeout(() => {
      submit.classList.remove("loading");
      submit.querySelector(".lbl").textContent = "Log in";
      password.value = ""; // the password is never kept, sent or stored
      msg.textContent = "Form is valid. This is a frontend-only demo: no account exists and nothing was sent or stored. "
        + "The dashboard itself needs no login.";
      msg.hidden = false;
    }, reduceMotion ? 0 : 600);
  });
})();
