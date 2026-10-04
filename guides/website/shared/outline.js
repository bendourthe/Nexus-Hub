  /* -------------------------------------------------- NexusOutline (v4.13.10, shared)
     NexusOutline.mount(host, items, opts) renders an "On this page" bar into host.
     items: [{ id, label, href, target }]. In "scroll" mode, target is the element id
     to bring into view, the current entry follows scrolling, and a click scrolls
     without changing the page (the hash is updated with replaceState). In "route"
     mode, a click follows href and opts.current() names the current entry.
     Phones collapse the list to one line naming the current entry. */
  window.NexusOutline = (function () {
    var instances = [];
    var wide = window.matchMedia ? window.matchMedia("(min-width: 721px)") : null;
    function el(tag, cls, text) {
      var node = document.createElement(tag);
      if (cls) node.className = cls;
      if (text != null) node.textContent = text;
      return node;
    }
    function setCurrent(inst, id) {
      if (inst.currentId === id) return;
      inst.currentId = id;
      for (var i = 0; i < inst.links.length; i++) {
        var on = inst.links[i].getAttribute("data-outline-id") === id;
        if (on) inst.links[i].setAttribute("aria-current", "true"); else inst.links[i].removeAttribute("aria-current");
        if (on) inst.now.textContent = inst.links[i].textContent;
      }
    }
    function fromScroll(inst) {
      if (!inst.host.offsetParent) return;
      var line = 150, best = inst.items.length ? inst.items[0].id : null;
      for (var i = 0; i < inst.items.length; i++) {
        var t = document.getElementById(inst.items[i].target);
        if (t && t.getBoundingClientRect().top <= line) best = inst.items[i].id;
      }
      setCurrent(inst, best);
    }
    function syncOpen(inst) {
      if (wide && wide.matches) inst.details.setAttribute("open", "");
      else if (!inst.userOpened) inst.details.removeAttribute("open");
    }
    function mount(host, items, opts) {
      opts = opts || {};
      var inst = { host: host, items: items, mode: opts.mode || "scroll", current: opts.current, links: [], currentId: null, userOpened: false };
      host.textContent = "";
      var nav = el("nav", "pg-outline");
      nav.setAttribute("aria-label", opts.label || "On this page");
      var details = el("details");
      var summary = el("summary");
      summary.appendChild(document.createTextNode((opts.label || "On this page") + ": "));
      inst.now = el("small");
      summary.appendChild(inst.now);
      var list = el("ol");
      var lab = el("li", "pg-outline-label", opts.label || "On this page");
      lab.setAttribute("aria-hidden", "true");
      list.appendChild(lab);
      items.forEach(function (item) {
        var li = el("li");
        var a = el("a", null, item.label);
        a.href = item.href;
        a.setAttribute("data-outline-id", item.id);
        if (inst.mode === "scroll") {
          var target = document.getElementById(item.target);
          if (target) target.setAttribute("data-outline-target", "");
          a.addEventListener("click", function (ev) {
            var t = document.getElementById(item.target);
            if (!t) return;
            ev.preventDefault();
            t.scrollIntoView({ block: "start", behavior: REDUCE ? "auto" : "smooth" });
            var heading = t.querySelector("h1, h2, h3") || t;
            if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
            heading.focus({ preventScroll: true });
            try { window.history.replaceState(null, "", item.href); } catch (err) {}
            setCurrent(inst, item.id);
            if (!(wide && wide.matches)) details.removeAttribute("open");
          });
        } else {
          a.addEventListener("click", function () { if (!(wide && wide.matches)) details.removeAttribute("open"); });
        }
        li.appendChild(a);
        list.appendChild(li);
        inst.links.push(a);
      });
      details.appendChild(summary);
      details.appendChild(list);
      details.addEventListener("toggle", function () { if (!(wide && wide.matches)) inst.userOpened = details.open; });
      nav.appendChild(details);
      host.appendChild(nav);
      inst.details = details;
      syncOpen(inst);
      if (inst.mode === "scroll") fromScroll(inst);
      else if (inst.current) setCurrent(inst, inst.current());
      instances.push(inst);
      return {
        refresh: function () { if (inst.mode === "scroll") fromScroll(inst); else if (inst.current) setCurrent(inst, inst.current()); },
        current: function () { return inst.currentId; }
      };
    }
    var ticking = false;
    window.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () {
        ticking = false;
        for (var i = 0; i < instances.length; i++) if (instances[i].mode === "scroll") fromScroll(instances[i]);
      });
    }, { passive: true });
    window.addEventListener("hashchange", function () {
      window.requestAnimationFrame(function () {
        for (var i = 0; i < instances.length; i++) {
          if (instances[i].mode === "scroll") fromScroll(instances[i]);
          else if (instances[i].current) setCurrent(instances[i], instances[i].current());
        }
      });
    });
    if (wide) {
      var onWide = function () { for (var i = 0; i < instances.length; i++) syncOpen(instances[i]); };
      if (wide.addEventListener) wide.addEventListener("change", onWide); else if (wide.addListener) wide.addListener(onWide);
    }
    return { mount: mount };
  })();
