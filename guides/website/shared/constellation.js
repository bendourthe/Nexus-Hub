  /* -------------------------------------------------- constellation */
  var canvas = document.getElementById("constellation");
  var constel = null;
  function syncConstellation() {
    if (!constel || !canvas) return;
    var dark = currentTheme() === "dark";
    var hidden = document.hidden;
    if (!dark || hidden) {
      canvas.style.opacity = "0";
      constel.stop();
      return;
    }
    canvas.style.opacity = current === "home" ? "0.55" : "0.16";
    constel.start();
  }
  if (canvas && canvas.getContext) {
    constel = (function () {
      var ctx = canvas.getContext("2d");
      var w, h, dpr, nodes, raf = null, running = false;
      function resize() {
        dpr = Math.min(window.devicePixelRatio || 1, 2);
        w = canvas.width = Math.floor(window.innerWidth * dpr);
        h = canvas.height = Math.floor(window.innerHeight * dpr);
        canvas.style.width = window.innerWidth + "px";
        canvas.style.height = window.innerHeight + "px";
      }
      function build() {
        var count = Math.max(18, Math.min(46, Math.floor(window.innerWidth / 34)));
        nodes = [];
        for (var i = 0; i < count; i++) {
          nodes.push({
            x: Math.random() * w, y: Math.random() * h,
            vx: (Math.random() - 0.5) * 0.16 * dpr,
            vy: (Math.random() - 0.5) * 0.16 * dpr
          });
        }
      }
      function frame(advance) {
        ctx.clearRect(0, 0, w, h);
        var maxd = 150 * dpr;
        for (var i = 0; i < nodes.length; i++) {
          var n = nodes[i];
          if (advance) {
            n.x += n.vx; n.y += n.vy;
            if (n.x < 0 || n.x > w) n.vx *= -1;
            if (n.y < 0 || n.y > h) n.vy *= -1;
          }
          for (var j = i + 1; j < nodes.length; j++) {
            var m = nodes[j], dx = n.x - m.x, dy = n.y - m.y, d = Math.sqrt(dx * dx + dy * dy);
            if (d < maxd) {
              ctx.globalAlpha = (1 - d / maxd) * 0.45;
              ctx.strokeStyle = "#2dd4bf";
              ctx.lineWidth = 0.6 * dpr;
              ctx.beginPath(); ctx.moveTo(n.x, n.y); ctx.lineTo(m.x, m.y); ctx.stroke();
            }
          }
        }
        ctx.globalAlpha = 0.85;
        for (var k = 0; k < nodes.length; k++) {
          ctx.fillStyle = "#5eead4";
          ctx.beginPath(); ctx.arc(nodes[k].x, nodes[k].y, 1.5 * dpr, 0, 6.2832); ctx.fill();
        }
        ctx.globalAlpha = 1;
      }
      function loop() {
        if (!running) return;
        frame(true);
        raf = window.requestAnimationFrame(loop);
      }
      resize(); build();
      window.addEventListener("resize", function () {
        resize();
        build();
        if (running && REDUCE) frame(false);
      });
      document.addEventListener("visibilitychange", function () { syncConstellation(); });
      return {
        start: function () {
          if (currentTheme() !== "dark" || document.hidden) return;
          if (REDUCE) {
            running = false;
            if (raf) { window.cancelAnimationFrame(raf); raf = null; }
            frame(false);
            return;
          }
          if (running) return;
          running = true;
          loop();
        },
        stop: function () {
          running = false;
          if (raf) { window.cancelAnimationFrame(raf); raf = null; }
        }
      };
    })();
  }
