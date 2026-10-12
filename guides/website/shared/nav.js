  /* skip link: both pages route on the hash, so focus main directly instead of following #app */
  var skipLink = document.querySelector(".skip-link"), mainEl = document.getElementById("app");
  if (skipLink && mainEl) {
    skipLink.addEventListener("click", function (e) {
      e.preventDefault();
      mainEl.setAttribute("tabindex", "-1");
      mainEl.focus();
    });
  }
  /* mobile nav: the open menu covers the top of the page, so Escape closes it and returns focus to
     the toggle, and focus leaving the menu closes it rather than reaching the content underneath */
  var navToggle = document.getElementById("navToggle");
  if (navToggle) {
    var navMenu = document.getElementById("navLinks");
    var closeNav = function () {
      navMenu.classList.remove("open");
      navToggle.setAttribute("aria-expanded", "false");
    };
    navToggle.addEventListener("click", function () {
      var open = navMenu.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key !== "Escape" || !navMenu.classList.contains("open")) return;
      e.preventDefault();
      closeNav();
      navToggle.focus();
    });
    document.addEventListener("focusin", function (e) {
      if (navMenu.classList.contains("open") && e.target !== navToggle && !navMenu.contains(e.target)) closeNav();
    });
  }
