  /* -------------------------------------------------- NexusOutline (v4.13.10 R1, shared)
     NexusOutline.mount(host, items, opts) renders page navigation that follows the reader.
     items: [{ id, label, href, target }]. In "scroll" mode, target is the element id to bring
     into view and the current entry follows scrolling; in "route" mode a click follows href and
     opts.current() names the current entry. opts.column names the content column to measure
     (default: the host's closest .container).
     Placement never takes width from the content: when the left margin beside the centred
     content column has room, the navigation is a fixed rail inside that margin (labels when the
     margin is wide, the current label only when it is slim); otherwise it is a compact sticky bar
     under the header with a progress line and a section menu. The layout is re-measured on
     resize, so any screen size or aspect ratio picks the form that fits. */
  window.NexusOutline = (function () {
    var instances = [];
    var FULL = 184, SLIM = 56;
    function el(tag, cls, text) {
      var node = document.createElement(tag);
      if (cls) node.className = cls;
      if (text != null) node.textContent = text;
      return node;
    }
    function reduced() { return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches); }
    function headerBottom() {
      var h = document.querySelector(".site-header");
      return h ? Math.max(0, h.getBoundingClientRect().bottom) : 0;
    }
    function setCurrent(inst, id) {
      if (inst.currentId === id) return;
      inst.currentId = id;
      for (var i = 0; i < inst.links.length; i++) {
        var on = inst.links[i].getAttribute("data-outline-id") === id;
        if (on) inst.links[i].setAttribute("aria-current", "true"); else inst.links[i].removeAttribute("aria-current");
        inst.links[i].parentNode.classList.toggle("is-current", on);
        if (on) { inst.now.textContent = inst.items[i].label; inst.index = i; }
      }
      inst.nav.style.setProperty("--pg-step", inst.items.length > 1 ? String(inst.index / (inst.items.length - 1)) : "0");
    }
    function progress(inst) {
      var first = document.getElementById(inst.items[0] && inst.items[0].target);
      var last = document.getElementById(inst.items.length ? inst.items[inst.items.length - 1].target : "");
      if (!first || !last) return 0;
      var top = first.getBoundingClientRect().top + window.scrollY - headerBottom();
      var end = last.getBoundingClientRect().bottom + window.scrollY - window.innerHeight;
      if (end <= top) return 1;
      return Math.max(0, Math.min(1, (window.scrollY - top) / (end - top)));
    }
    function shown(inst) {
      var column = inst.column;
      return !!column && column.getClientRects().length > 0;
    }
    function fromScroll(inst) {
      if (!shown(inst)) return;
      /* A page that was hidden when the navigation mounted is measured the first time it shows. */
      if (!inst.measured) { place(inst); return; }
      if (inst.mode === "scroll") {
        var line = headerBottom() + Math.min(160, window.innerHeight * 0.3), best = inst.items.length ? inst.items[0].id : null;
        for (var i = 0; i < inst.items.length; i++) {
          var t = document.getElementById(inst.items[i].target);
          if (t && t.offsetParent && t.getBoundingClientRect().top <= line) best = inst.items[i].id;
        }
        setCurrent(inst, best);
      } else if (inst.current) {
        setCurrent(inst, inst.current());
      }
      inst.nav.style.setProperty("--pg-progress", String(progress(inst)));
    }
    /* Measure the free margin left of the content column and choose the form that fits. */
    function place(inst) {
      var column = inst.column;
      var visible = !!column && column.getClientRects().length > 0;
      var free = 0;
      if (visible) {
        var r = column.getBoundingClientRect();
        free = r.left + parseFloat(getComputedStyle(column).paddingLeft || "0");
      }
      inst.measured = visible;
      var layout = !visible ? inst.layout || "bar" : free >= FULL ? "rail" : free >= SLIM ? "rail slim" : "bar";
      inst.layout = layout.split(" ")[0];
      inst.nav.className = "pg-outline pg-outline--" + layout.replace(" ", " pg-outline--");
      if (inst.layout === "rail") {
        /* Centered in the free margin, so it is never flush with the window edge. */
        var width = Math.min(232, free - 48);
        inst.nav.style.left = Math.round((free - width) / 2) + "px";
        inst.nav.style.width = width + "px";
        inst.nav.style.top = headerBottom() + 28 + "px";
        inst.menu.hidden = false;
        inst.toggle.setAttribute("aria-expanded", "true");
      } else {
        inst.nav.style.left = inst.nav.style.width = inst.nav.style.top = "";
        inst.menu.hidden = !inst.open;
        inst.toggle.setAttribute("aria-expanded", inst.open ? "true" : "false");
      }
      fromScroll(inst);
    }
    function close(inst) {
      if (inst.layout === "rail") return;
      inst.open = false;
      inst.menu.hidden = true;
      inst.toggle.setAttribute("aria-expanded", "false");
    }
    function mount(host, items, opts) {
      opts = opts || {};
      var label = opts.label || "On this page";
      var inst = { host: host, column: opts.column || host.closest(".container") || host.parentNode, items: items, mode: opts.mode || "scroll", current: opts.current, links: [], currentId: null, index: 0, open: false, layout: null };
      host.textContent = "";
      /* The mount point steps out of layout so the compact bar can stick for the whole column. */
      host.style.display = "contents";
      var nav = el("nav", "pg-outline");
      nav.setAttribute("aria-label", label);
      inst.nav = nav;
      var toggle = el("button", "pg-outline-toggle");
      toggle.type = "button";
      toggle.appendChild(el("span", "pg-outline-label", label));
      toggle.lastChild.setAttribute("data-ty", "eyebrow");
      inst.now = el("span", "pg-outline-now");
      inst.now.setAttribute("data-ty", "body-sm");
      toggle.appendChild(inst.now);
      toggle.appendChild(el("span", "pg-outline-chev"));
      toggle.lastChild.setAttribute("aria-hidden", "true");
      inst.toggle = toggle;
      var menu = el("ol", "pg-outline-list");
      menu.id = "pg-outline-" + (instances.length + 1);
      toggle.setAttribute("aria-controls", menu.id);
      inst.menu = menu;
      items.forEach(function (item) {
        var li = el("li");
        var a = el("a");
        a.href = item.href;
        a.setAttribute("data-outline-id", item.id);
        a.setAttribute("title", item.label);
        a.appendChild(el("span", "pg-outline-node"));
        a.lastChild.setAttribute("aria-hidden", "true");
        a.appendChild(el("span", "pg-outline-text", item.label));
        a.lastChild.setAttribute("data-ty", "body-sm");
        if (inst.mode === "scroll") {
          var target = document.getElementById(item.target);
          if (target) target.setAttribute("data-outline-target", "");
          a.addEventListener("click", function (ev) {
            var t = document.getElementById(item.target);
            if (!t) return;
            ev.preventDefault();
            t.scrollIntoView({ block: "start", behavior: reduced() ? "auto" : "smooth" });
            var heading = t.querySelector("h1, h2, h3") || t;
            if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
            heading.focus({ preventScroll: true });
            try { window.history.replaceState(null, "", item.href); } catch (err) {}
            setCurrent(inst, item.id);
            close(inst);
          });
        } else {
          a.addEventListener("click", function () { close(inst); });
        }
        li.appendChild(a);
        menu.appendChild(li);
        inst.links.push(a);
      });
      toggle.addEventListener("click", function () {
        if (inst.layout === "rail") return;
        inst.open = !inst.open;
        menu.hidden = !inst.open;
        toggle.setAttribute("aria-expanded", inst.open ? "true" : "false");
      });
      nav.addEventListener("keydown", function (ev) {
        if (ev.key === "Escape" && inst.open) { close(inst); toggle.focus(); }
      });
      document.addEventListener("click", function (ev) { if (inst.open && !nav.contains(ev.target)) close(inst); });
      var track = el("span", "pg-outline-track");
      track.setAttribute("aria-hidden", "true");
      track.appendChild(el("span", "pg-outline-fill"));
      nav.appendChild(toggle);
      nav.appendChild(track);
      nav.appendChild(menu);
      host.appendChild(nav);
      instances.push(inst);
      place(inst);
      /* A hidden page's column goes from no size to its real size when it shows; measure then. */
      var column = inst.column;
      if (column && window.ResizeObserver) new ResizeObserver(function () { place(inst); }).observe(column);
      if (inst.mode !== "scroll" && inst.current) setCurrent(inst, inst.current());
      return {
        refresh: function () { place(inst); },
        current: function () { return inst.currentId; },
        layout: function () { return inst.layout; }
      };
    }
    var ticking = false;
    function all(fn) { for (var i = 0; i < instances.length; i++) fn(instances[i]); }
    window.addEventListener("scroll", function () {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () { ticking = false; all(fromScroll); });
    }, { passive: true });
    var resizing = null;
    window.addEventListener("resize", function () {
      window.clearTimeout(resizing);
      resizing = window.setTimeout(function () { all(place); }, 80);
    });
    window.addEventListener("hashchange", function () { window.requestAnimationFrame(function () { all(place); }); });
    return { mount: mount };
  })();
