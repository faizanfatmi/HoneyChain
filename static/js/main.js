(function () {
  "use strict";

  var hasGSAP = typeof window.gsap !== "undefined";
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  function renderIcons() {
    if (window.lucide && typeof window.lucide.createIcons === "function") {
      window.lucide.createIcons();
    }
  }

  function renderQRCodes() {
    if (typeof window.QRCode === "undefined") return;
    document.querySelectorAll("[data-qr]").forEach(function (el) {
      if (el.dataset.qrDone) return;
      el.dataset.qrDone = "1";
      var size = el.clientWidth || 166;
      new window.QRCode(el, {
        text: el.getAttribute("data-qr"),
        width: size, height: size,
        colorDark: "#17110a", colorLight: "#ffffff",
        correctLevel: window.QRCode.CorrectLevel.H,
      });
    });
  }

  function initNav() {
    var nav = document.getElementById("nav");
    var toggle = document.getElementById("navToggle");
    var links = document.getElementById("navLinks");
    function onScroll() { if (nav) nav.classList.toggle("scrolled", window.scrollY > 12); }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
    if (toggle && links) {
      toggle.addEventListener("click", function () { links.classList.toggle("open"); });
      links.querySelectorAll("a").forEach(function (a) {
        a.addEventListener("click", function () { links.classList.remove("open"); });
      });
    }
  }

  function animateCounter(el) {
    var raw = el.getAttribute("data-count") || "0";
    var target = parseFloat(raw) || 0;
    var decimals = (raw.split(".")[1] || "").length;
    function fmt(v) { return v.toLocaleString(undefined, { minimumFractionDigits: decimals, maximumFractionDigits: decimals }); }
    if (reduceMotion || !hasGSAP) { el.textContent = fmt(target); return; }
    var obj = { v: 0 };
    window.gsap.to(obj, { v: target, duration: 1.5, ease: "power2.out", onUpdate: function () { el.textContent = fmt(obj.v); } });
  }

  function initToasts() {
    document.querySelectorAll(".toast").forEach(function (t) {
      setTimeout(function () {
        if (hasGSAP && !reduceMotion) {
          window.gsap.to(t, { opacity: 0, x: 20, duration: 0.4, onComplete: function () { t.remove(); } });
        } else { t.remove(); }
      }, 4500);
    });
  }

  function initAnimations() {
    var gsap = window.gsap;
    if (window.ScrollTrigger) gsap.registerPlugin(window.ScrollTrigger);

    var mm = gsap.matchMedia();
    mm.add(
      { reduce: "(prefers-reduced-motion: reduce)", ok: "(prefers-reduced-motion: no-preference)" },
      function (ctx) {
        if (ctx.conditions.reduce) {
          gsap.set(".comb-cell-fill", { opacity: 0.9 });
          gsap.set(".comb-seal", { opacity: 1 });
          startCounters();
          return;
        }

        if (document.querySelector(".comb-cell-fill")) {
          var tl = gsap.timeline({ delay: 0.55 });
          tl.to(".comb-cell-fill", { opacity: 0.9, duration: 0.4, ease: "power2.out", stagger: 0.11 });
          tl.fromTo(".comb-seal",
            { opacity: 0, scale: 0, transformOrigin: "50% 50%" },
            { opacity: 1, scale: 1, duration: 0.6, ease: "back.out(1.8)" }, "-=0.05");
        }

        startCounters();
        return function () {};
      }
    );
  }

  function startCounters() {
    var els = window.gsap.utils.toArray("[data-count]");
    if (reduceMotion || !window.ScrollTrigger) {
      els.forEach(animateCounter);
      return;
    }
    els.forEach(function (el) {
      window.ScrollTrigger.create({ trigger: el, start: "top 92%", once: true, onEnter: function () { animateCounter(el); } });
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    renderQRCodes();
    renderIcons();
    initNav();
    initToasts();
    if (hasGSAP) { initAnimations(); }
  });
})();
