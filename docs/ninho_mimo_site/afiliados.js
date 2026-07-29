// =============================================
// NINHO & MIMO TRENDS — AFILIADOS · afiliados.js
// =============================================

/* ── HAMBURGER MENU ── */
const hamburger = document.getElementById("hamburger");
const mobileNav = document.getElementById("mobileNav");

if (hamburger && mobileNav) {
  hamburger.addEventListener("click", () => {
    const isOpen = mobileNav.classList.toggle("open");
    hamburger.setAttribute("aria-expanded", isOpen.toString());
  });
}

/* ── BILLING TOGGLE ── */
const billingToggle = document.getElementById("billingToggle");
const amounts = document.querySelectorAll(".plan-amount");
const toggleLabelMonth = document.getElementById("toggleLabelMonth");
const toggleLabelYear  = document.getElementById("toggleLabelYear");
const starterNote = document.getElementById("starterNote");
const proNote     = document.getElementById("proNote");
const eliteNote   = document.getElementById("eliteNote");

let isYearly = false;

if (billingToggle) {
  billingToggle.addEventListener("click", () => {
    isYearly = !isYearly;
    billingToggle.setAttribute("aria-checked", isYearly.toString());

    toggleLabelMonth.classList.toggle("toggle-label--active", !isYearly);
    toggleLabelYear.classList.toggle("toggle-label--active",  isYearly);

    amounts.forEach(el => {
      const target = isYearly ? el.dataset.yearly : el.dataset.monthly;
      animateNumber(el, target);
    });

    const note = isYearly ? "cobrado anualmente (economize 20%)" : "cobrado mensalmente";
    [starterNote, proNote, eliteNote].forEach(el => { if (el) el.textContent = note; });
  });
}

function animateNumber(el, target) {
  const start = parseInt(el.textContent, 10);
  const end   = parseInt(target, 10);
  const dur   = 350;
  const t0    = performance.now();

  function step(now) {
    const p   = Math.min((now - t0) / dur, 1);
    const val = Math.round(start + (end - start) * easeOut(p));
    el.textContent = val;
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function easeOut(t) { return 1 - Math.pow(1 - t, 3); }

/* ── REVEAL ON SCROLL ── */
const revealEls = document.querySelectorAll(".reveal, .reveal-delay");

function checkReveal() {
  revealEls.forEach(el => {
    const rect = el.getBoundingClientRect();
    if (rect.top < window.innerHeight - 80) {
      el.classList.add("visible");
    }
  });
  animateBars();
}

const io = new IntersectionObserver(
  entries => entries.forEach(e => { if (e.isIntersecting) e.target.classList.add("visible"); }),
  { threshold: 0.12 }
);
revealEls.forEach(el => io.observe(el));

window.addEventListener("scroll", checkReveal, { passive: true });
checkReveal();

/* ── SCORE BAR ANIMATION ── */
function animateBars() {
  document.querySelectorAll(".score-bar__fill[data-width]").forEach(bar => {
    const rect = bar.getBoundingClientRect();
    if (rect.top < window.innerHeight - 40 && !bar.dataset.animated) {
      bar.dataset.animated = "1";
      const w = bar.dataset.width + "%";
      requestAnimationFrame(() => { bar.style.width = w; });
    }
  });
}

/* ── NAV SCROLL EFFECT ── */
const nav = document.querySelector(".nav");
window.addEventListener("scroll", () => {
  if (nav) {
    nav.style.boxShadow = window.scrollY > 20
      ? "0 4px 24px rgba(0,0,0,.35)"
      : "none";
  }
}, { passive: true });

/* ── SMOOTH NAV LINKS ── */
document.querySelectorAll("a[href^=\"#\"]").forEach(link => {
  link.addEventListener("click", e => {
    const id = link.getAttribute("href");
    if (id === "#") return;
    const target = document.querySelector(id);
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      if (mobileNav) mobileNav.classList.remove("open");
    }
  });
});

/* ── DASHBOARD CARD HOVER GLOW ── */
document.querySelectorAll(".dash-card").forEach(card => {
  card.addEventListener("mouseenter", () => {
    card.style.background = "rgba(143,174,139,0.08)";
    card.style.borderColor = "rgba(143,174,139,0.3)";
    card.style.transform = "translateX(4px)";
    card.style.transition = "all 0.2s ease";
  });
  card.addEventListener("mouseleave", () => {
    if (card.classList.contains("dash-card--hot")) {
      card.style.background = "rgba(143,174,139,0.1)";
      card.style.borderColor = "rgba(143,174,139,0.25)";
    } else {
      card.style.background = "rgba(255,255,255,0.04)";
      card.style.borderColor = "rgba(143,174,139,0.12)";
    }
    card.style.transform = "translateX(0)";
  });
});

/* ── COUNTER ANIMATION FOR METRICS ── */
function animateCounter(el) {
  const text = el.textContent;
  const match = text.match(/[\d,.]+/);
  if (!match) return;

  const numStr = match[0].replace(/\./g, "").replace(",", ".");
  const num = parseFloat(numStr);
  if (isNaN(num)) return;

  const prefix = text.substring(0, text.indexOf(match[0]));
  const suffix = text.substring(text.indexOf(match[0]) + match[0].length);
  const isDecimal = match[0].includes(",");

  const dur = 1800;
  const t0  = performance.now();

  function step(now) {
    const p   = Math.min((now - t0) / dur, 1);
    const val = num * easeOut(p);
    let display;
    if (isDecimal) {
      display = val.toFixed(1).replace(".", ",");
    } else if (num >= 1000) {
      display = Math.round(val).toLocaleString("pt-BR");
    } else {
      display = Math.round(val).toString();
    }
    el.textContent = prefix + display + suffix;
    if (p < 1) requestAnimationFrame(step);
  }

  el.textContent = prefix + (isDecimal ? "0,0" : "0") + suffix;
  requestAnimationFrame(step);
}

const metricObserver = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if (e.isIntersecting) {
      animateCounter(e.target);
      metricObserver.unobserve(e.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll(".metric-num").forEach(el => metricObserver.observe(el));
