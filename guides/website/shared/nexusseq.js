  /* -------------------------------------------------- NexusSeq: declarative step timelines
     One shared engine for every choreographed scene, so motion is consistent, testable, and
     cheap. Contract: a [data-seq-root] holds [data-seq=N] steps (optional data-seq-dur ms);
     steps gain .is-on in order; data-seq-loop repeats after data-seq-hold ms. Starts at 40%
     visibility, pauses offscreen and on a hidden tab, and under reduced motion play() applies
     the terminal state synchronously and schedules nothing. */
  window.NexusSeq = (function () {
    var roots = [];
    function warn(msg) { if (window.console && console.warn) { console.warn("NexusSeq: " + msg); } }
    function parseSteps(root) {
      var nodes = root.querySelectorAll("[data-seq]"), byStep = {}, order = [], steps = [];
      for (var i = 0; i < nodes.length; i++) {
        var n = parseInt(nodes[i].getAttribute("data-seq"), 10);
        var raw = nodes[i].getAttribute("data-seq-dur");
        var dur = raw === null ? 700 : parseInt(raw, 10);
        if (isNaN(n) || n < 0 || isNaN(dur) || dur < 0) {
          warn("skipping malformed step on #" + (nodes[i].id || "(no id)") + " in #" + (root.id || "(no id)"));
          continue;
        }
        if (!byStep[n]) { byStep[n] = { n: n, els: [], dur: dur }; order.push(n); }
        byStep[n].els.push(nodes[i]);
        if (dur > byStep[n].dur) { byStep[n].dur = dur; }
      }
      order.sort(function (a, b) { return a - b; });
      for (var k = 0; k < order.length; k++) { steps.push(byStep[order[k]]); }
      return steps;
    }
    function entry(root) {
      for (var i = 0; i < roots.length; i++) { if (roots[i].root === root) { return roots[i]; } }
      return null;
    }
    function setAll(e, on) {
      for (var i = 0; i < e.steps.length; i++) {
        for (var j = 0; j < e.steps[i].els.length; j++) { e.steps[i].els[j].classList.toggle("is-on", on); }
      }
    }
    function finish(e) { setAll(e, true); e.idx = e.steps.length; e.running = false; e.root.classList.add("seq-done"); }
    function schedule(e) {
      if (!e.running) { return; }
      var gen = e.gen;
      if (e.idx >= e.steps.length) {
        e.root.classList.add("seq-done");
        if (!e.loop) { e.running = false; return; }
        e.timer = setTimeout(function () {
          if (e.gen !== gen || !e.running) { return; }
          setAll(e, false); e.idx = 0; e.root.classList.remove("seq-done"); schedule(e);
        }, e.hold);
        return;
      }
      var step = e.steps[e.idx];
      for (var j = 0; j < step.els.length; j++) { step.els[j].classList.add("is-on"); }
      e.idx += 1;
      e.timer = setTimeout(function () { if (e.gen === gen) { schedule(e); } }, step.dur);
    }
    function play(root) {
      var e = entry(root);
      if (!e) { return; }
      if (REDUCE) { finish(e); return; }
      if (e.running) { return; }           /* a second start while running is ignored */
      e.running = true; e.gen += 1; schedule(e);
    }
    function pause(root) {
      var e = entry(root);
      if (!e) { return; }
      e.running = false; e.gen += 1; clearTimeout(e.timer);   /* resumes from the same step */
    }
    function reset(root) {
      var e = entry(root);
      if (!e) { return; }
      pause(root); setAll(e, false); e.idx = 0; e.root.classList.remove("seq-done");
    }
    function state(root) {
      var e = entry(root);
      return e ? { step: e.idx, total: e.steps.length, running: e.running, reduced: !!REDUCE, loop: e.loop } : null;
    }
    function register(root) {
      if (!root || entry(root)) { return; }
      roots.push({
        root: root, steps: parseSteps(root), idx: 0, timer: null, running: false, visible: false, gen: 0,
        loop: root.hasAttribute("data-seq-loop"),
        hold: parseInt(root.getAttribute("data-seq-hold") || "1500", 10) || 1500
      });
    }
    function init() {
      var all = document.querySelectorAll("[data-seq-root]");
      for (var i = 0; i < all.length; i++) { register(all[i]); }
      if (!("IntersectionObserver" in window)) {
        for (var k = 0; k < roots.length; k++) { play(roots[k].root); }   /* never "never": start now */
        return;
      }
      var io = new IntersectionObserver(function (entries) {
        for (var i = 0; i < entries.length; i++) {
          var e = entry(entries[i].target);
          if (!e) { continue; }
          e.visible = entries[i].isIntersecting;
          if (e.visible && !document.hidden) { play(e.root); } else { pause(e.root); }
        }
      }, { threshold: 0.4 });
      for (var r = 0; r < roots.length; r++) { io.observe(roots[r].root); }
      document.addEventListener("visibilitychange", function () {
        for (var r = 0; r < roots.length; r++) {
          if (document.hidden) { pause(roots[r].root); } else if (roots[r].visible) { play(roots[r].root); }
        }
      });
    }
    return { init: init, register: register, play: play, pause: pause, reset: reset, state: state };
  })();
  window.NexusSeq.init();
