  /* mobile nav */
  var navToggle = document.getElementById("navToggle");
  if (navToggle) {
    navToggle.addEventListener("click", function () {
      var links = document.getElementById("navLinks");
      var open = links.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }
