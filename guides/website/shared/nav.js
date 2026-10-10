  /* skip link: both pages route on the hash, so focus main directly instead of following #app */
  var skipLink = document.querySelector(".skip-link"), mainEl = document.getElementById("app");
  if (skipLink && mainEl) {
    skipLink.addEventListener("click", function (e) {
      e.preventDefault();
      mainEl.setAttribute("tabindex", "-1");
      mainEl.focus();
    });
  }
  /* mobile nav */
  var navToggle = document.getElementById("navToggle");
  if (navToggle) {
    navToggle.addEventListener("click", function () {
      var links = document.getElementById("navLinks");
      var open = links.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
