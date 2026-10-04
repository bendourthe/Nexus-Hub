  /* -------------------------------------------------- theme */
  function currentTheme() {
    var t = document.documentElement.getAttribute("data-theme");
    return t === "light" ? "light" : "dark";
  }
  function applyTheme(theme) {
    if (theme !== "light" && theme !== "dark") return;
    document.documentElement.setAttribute("data-theme", theme);
    document.documentElement.style.colorScheme = theme;
    try { window.localStorage.setItem(THEME_KEY, theme); } catch (err) {}
    var meta = document.getElementById("themeColorMeta");
    if (meta) meta.setAttribute("content", theme === "light" ? "#f3f1ea" : "#07141a");
    var btn = document.getElementById("themeToggle");
    if (btn) {
      btn.setAttribute("aria-pressed", theme === "dark" ? "true" : "false");
      btn.setAttribute("aria-label", theme === "dark" ? "Switch to light theme" : "Switch to dark theme");
    }
    syncConstellation();
  }
  applyTheme(currentTheme());
  var themeBtn = document.getElementById("themeToggle");
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      applyTheme(currentTheme() === "dark" ? "light" : "dark");
    });
  }
