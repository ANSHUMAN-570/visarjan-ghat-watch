"use strict";
// Landing page behaviour: theme, mobile menu, active nav, entrance animations, dashboard links.
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
})();
