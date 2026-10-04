/* ===================================================================== Sky Sentinel (v4.13.10)
   The Training page's game engine. Design and test rules:
   docs/releases/v4/v4.13/development/v4.13.10-game-design.md
   Fixed 60 Hz simulation separated from canvas rendering; three seeded random
   streams (spawn, drops, defects); every timing rule counted in ticks; the two
   seeded defects are independent flags. Inlined into training.html by
   scripts/stamp_guide_shared.py: edit this file, not the page.
   ===================================================================== */
(function () {
  "use strict";

  var HZ = 60;
  var MAX_STEPS_PER_FRAME = 5;
  var GRACE_TICKS = 180;            /* no enemy fires in the first 3 s */
  var FIRST_SHOT_CLEARANCE = 300;   /* the first shot leaves from at least this far above the ship */
  var EARLIEST_EXPLOSION = 1200;    /* never before 20 s of play */
  var EXPLOSION_GAP = 900;          /* never twice within 15 s */
  var EXPLOSION_JITTER = 600;
  var INVULNERABLE_TICKS = 120;
  var RESPAWN_TICKS = 90;
  var START_LIVES = 3;
  var DEFECT_NAMES = ["firstHitFatal", "randomExplosion"];
  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  var instances = {};
  var manual = false;

  /* -------------------------------------------------- seeded randomness */
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  function streams(seed) {
    var s = seed >>> 0;
    return {
      spawn: mulberry32(s ^ 0x51ED270B),
      drops: mulberry32(s ^ 0x2545F491),
      defects: mulberry32(s ^ 0x6A09E667)
    };
  }
  function firstExplosion(rng) { return EARLIEST_EXPLOSION + Math.floor(rng() * EXPLOSION_JITTER); }
  function nextExplosion(rng, at) { return at + EXPLOSION_GAP + Math.floor(rng() * EXPLOSION_JITTER); }

  /* The pure scheduler: the nominal explosion ticks for a seed, with no deferrals. */
  function defectSchedule(seed, untilTick) {
    var rng = streams(seed).defects, out = [], t = firstExplosion(rng);
    while (t <= untilTick) { out.push(t); t = nextExplosion(rng, t); }
    return out;
  }

  function normDefects(d) {
    var out = { firstHitFatal: false, randomExplosion: false };
    if (!d) return out;
    for (var k in d) {
      if (!Object.prototype.hasOwnProperty.call(d, k)) continue;
      if (DEFECT_NAMES.indexOf(k) === -1) return null;
      out[k] = !!d[k];
    }
    return out;
  }

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  /* -------------------------------------------------- one game */
  function create(host, opts) {
    opts = opts || {};
    var id = opts.id || host.getAttribute("data-ss-id") || ("game" + Object.keys(instances).length);
    if (instances[id]) throw new Error("SkySentinel: duplicate game id " + id);

    var cfg = { defects: normDefects(opts.defects) || normDefects(null), level: opts.level || 1, seed: opts.seed >>> 0 || 1, threats: true };
    var listeners = {};
    var held = { left: false, right: false, up: false, down: false, fire: false };
    var world = { w: 960, h: 600 };
    var S = null;                      /* simulation state */
    var acc = 0, last = 0;

    /* ---------- DOM */
    host.textContent = "";
    host.classList.add("ss");
    var stage = el("div", "ss-stage");
    var canvas = el("canvas", "ss-canvas");
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-label", "Sky Sentinel arena");
    canvas.tabIndex = 0;
    var overlay = el("div", "ss-overlay");
    var startBtn = el("button", "ss-start", "Click to start");
    startBtn.type = "button";
    var hint = el("p", "ss-hint", "Arrows or WASD move, Space or click fires, Escape pauses.");
    overlay.appendChild(startBtn);
    overlay.appendChild(hint);
    stage.appendChild(canvas);
    stage.appendChild(overlay);
    var hud = el("div", "ss-hud");
    var hudScore = el("span", "ss-hud-item"), hudLives = el("span", "ss-hud-item"), hudLevel = el("span", "ss-hud-item"), hudState = el("span", "ss-hud-item");
    hud.appendChild(hudScore); hud.appendChild(hudLives); hud.appendChild(hudLevel); hud.appendChild(hudState);
    var touch = el("div", "ss-touch");
    touch.setAttribute("aria-label", "Touch controls");
    var touchButtons = {};
    [["left", "Left"], ["up", "Up"], ["down", "Down"], ["right", "Right"], ["fire", "Fire"]].forEach(function (b) {
      var btn = el("button", "ss-touch-btn ss-touch-" + b[0], b[1]);
      btn.type = "button";
      btn.setAttribute("aria-label", b[1]);
      touchButtons[b[0]] = btn;
      touch.appendChild(btn);
    });
    var live = el("p", "ss-live");
    live.setAttribute("aria-live", "polite");
    var fallback = el("p", "ss-fallback", "This browser cannot draw the game. The story still works: each stage describes what the game would show.");
    fallback.hidden = true;
    host.appendChild(stage);
    host.appendChild(hud);
    host.appendChild(touch);
    host.appendChild(live);
    host.appendChild(fallback);

    var ctx = null;
    try { ctx = canvas.getContext("2d"); } catch (err) { ctx = null; }
    if (!ctx) { fallback.hidden = false; stage.hidden = true; }

    function emit(name, detail) {
      var fns = listeners[name] || [];
      for (var i = 0; i < fns.length; i++) { try { fns[i](detail || {}); } catch (err) { if (window.console) console.error(err); } }
    }
    function say(text) { live.textContent = text; }

    /* ---------- sizing */
    function chooseWorld() {
      /* A hidden stage measures 0 px, so fall back to the viewport before guessing landscape. */
      var w = host.clientWidth || window.innerWidth || 960;
      world = w < 600 ? { w: 720, h: 960 } : { w: 960, h: 600 };
    }
    function fit() {
      if (S && S.state === "idle") {
        var old = world;
        chooseWorld();
        if (world.w !== old.w) { world = old; reset(); return; }
      }
      var cssW = Math.max(240, stage.clientWidth || host.clientWidth || 960);
      var cssH = cssW * world.h / world.w;
      /* Leave room for the sticky header, the outline bar, and the HUD row below the arena. */
      var cap = Math.max(260, (window.innerHeight || 800) - 250);
      if (cssH > cap) cssH = cap;
      var dpr = Math.min(window.devicePixelRatio || 1, 3);
      canvas.style.height = Math.round(cssH) + "px";
      canvas.width = Math.round(cssW * dpr);
      canvas.height = Math.round(cssH * dpr);
      draw();
    }

    /* ---------- simulation */
    function reset() {
      var before = world.w;
      chooseWorld();
      var reshaped = world.w !== before;
      var r = streams(cfg.seed);
      S = {
        rng: r, tick: 0, state: "idle", pausedBy: null, score: 0, level: cfg.level,
        player: { x: world.w / 2, y: world.h - 70, r: 18, lives: START_LIVES, invuln: 0, exploding: 0, cooldown: 0 },
        enemies: [], enemyShots: [], shots: [], asteroids: [], effects: [],
        spawnIn: 50, rockIn: 240, firstShotTick: null, firstShotGap: null, firstHitTaken: false,
        nextExplosion: firstExplosion(r.defects), explodeTicks: [], hitTicks: [], lifeLossTicks: [],
        overReason: null
      };
      acc = 0;
      sync();
      if (reshaped) fit(); else draw();
    }

    function spawnEnemy() {
      var rng = S.rng.spawn;
      S.enemies.push({
        x: 40 + rng() * (world.w - 80), y: -24, r: 16,
        vx: (rng() - 0.5) * 1.6, vy: 1.1 + rng() * 1.1,
        phase: rng() * Math.PI * 2, hp: 1,
        fireIn: 50 + Math.floor(rng() * 110)
      });
    }
    function spawnRock() {
      var rng = S.rng.spawn;
      var r = 16 + Math.floor(rng() * 16);
      S.asteroids.push({ x: r + rng() * (world.w - 2 * r), y: -r, r: r, vx: (rng() - 0.5) * 1.2, vy: 1.3 + rng() * 1.2, hp: r > 24 ? 2 : 1, spin: rng() * 6.28 });
    }

    function enemyMayFire(e) {
      if (S.tick < GRACE_TICKS) return false;
      if (S.firstShotTick === null && S.player.y - e.y < FIRST_SHOT_CLEARANCE) return false;
      return e.y > 0 && e.y < world.h * 0.75;
    }

    function hitPlayer(source) {
      var p = S.player;
      if (S.state !== "running" || p.invuln > 0 || p.exploding > 0) return false;
      S.hitTicks.push(S.tick);
      emit("hit", { source: source, tick: S.tick });
      if (cfg.defects.firstHitFatal && !S.firstHitTaken) {
        S.firstHitTaken = true;
        p.lives = 0;
        boom(p.x, p.y, 2);
        gameOver("first-hit");
        return true;
      }
      S.firstHitTaken = true;
      loseLife("hit");
      return true;
    }

    function loseLife(reason) {
      var p = S.player;
      p.lives -= 1;
      S.lifeLossTicks.push(S.tick);
      boom(p.x, p.y, 1.6);
      emit("lifeLost", { reason: reason, lives: p.lives, tick: S.tick });
      if (p.lives <= 0) { gameOver(reason); return; }
      p.exploding = RESPAWN_TICKS;
      say(reason === "explode" ? "The ship exploded with no hit. Lives left: " + p.lives + "." : "Hit. Lives left: " + p.lives + ".");
    }

    function gameOver(reason) {
      S.state = "over";
      S.overReason = reason;
      held.left = held.right = held.up = held.down = held.fire = false;
      emit("destroyed", { reason: reason, tick: S.tick, score: S.score });
      say(reason === "first-hit" ? "Destroyed by the first hit, with lives still left. That is the bug." : "Game over. Score " + S.score + ".");
      sync();
    }

    function boom(x, y, size) { S.effects.push({ x: x, y: y, t: 0, size: size || 1 }); }

    function overlaps(a, b, extra) { var dx = a.x - b.x, dy = a.y - b.y, r = a.r + b.r + (extra || 0); return dx * dx + dy * dy < r * r; }

    function tick() {
      var p = S.player, i, j;
      S.tick += 1;

      /* player */
      if (p.exploding > 0) {
        p.exploding -= 1;
        if (p.exploding === 0) { p.x = world.w / 2; p.y = world.h - 70; p.invuln = INVULNERABLE_TICKS; }
      } else {
        var dx = (held.right ? 1 : 0) - (held.left ? 1 : 0);
        var dy = (held.down ? 1 : 0) - (held.up ? 1 : 0);
        p.x = Math.max(p.r, Math.min(world.w - p.r, p.x + dx * 7));
        p.y = Math.max(world.h * 0.55, Math.min(world.h - p.r - 6, p.y + dy * 6));
        if (p.invuln > 0) p.invuln -= 1;
        if (p.cooldown > 0) p.cooldown -= 1;
        if (held.fire && p.cooldown === 0) { S.shots.push({ x: p.x, y: p.y - p.r, r: 4 }); p.cooldown = 10; }
      }

      /* spawning (the test layer can switch threats off to watch the defect schedule alone) */
      if (cfg.threats) {
        S.spawnIn -= 1;
        if (S.spawnIn <= 0) { spawnEnemy(); S.spawnIn = Math.max(28, 70 - Math.floor(S.tick / 600) * 6) + Math.floor(S.rng.spawn() * 30); }
        S.rockIn -= 1;
        if (S.rockIn <= 0) { spawnRock(); S.rockIn = 220 + Math.floor(S.rng.spawn() * 200); }
      }

      /* movement */
      for (i = 0; i < S.shots.length; i++) S.shots[i].y -= 13;
      for (i = 0; i < S.enemies.length; i++) {
        var e = S.enemies[i];
        e.phase += 0.04;
        e.x = Math.max(e.r, Math.min(world.w - e.r, e.x + e.vx + Math.sin(e.phase) * 0.9));
        e.y += e.vy;
        e.fireIn -= 1;
        if (e.fireIn <= 0) {
          if (enemyMayFire(e)) {
            var aim = Math.max(-2, Math.min(2, (p.x - e.x) / 120));
            S.enemyShots.push({ x: e.x, y: e.y + e.r, r: 5, vx: aim, vy: 5.2 });
            if (S.firstShotTick === null) { S.firstShotTick = S.tick; S.firstShotGap = p.y - e.y; }
            e.fireIn = 90 + Math.floor(S.rng.spawn() * 90);
          } else {
            e.fireIn = 12;
          }
        }
      }
      for (i = 0; i < S.enemyShots.length; i++) { S.enemyShots[i].x += S.enemyShots[i].vx; S.enemyShots[i].y += S.enemyShots[i].vy; }
      for (i = 0; i < S.asteroids.length; i++) { var a = S.asteroids[i]; a.x += a.vx; a.y += a.vy; a.spin += 0.01; }
      for (i = 0; i < S.effects.length; i++) S.effects[i].t += 1;

      /* collisions: player shots */
      for (i = S.shots.length - 1; i >= 0; i--) {
        var s = S.shots[i], used = false;
        for (j = S.enemies.length - 1; j >= 0 && !used; j--) {
          if (overlaps(s, S.enemies[j])) { boom(S.enemies[j].x, S.enemies[j].y, 1); S.enemies.splice(j, 1); S.score += 100; used = true; }
        }
        for (j = S.asteroids.length - 1; j >= 0 && !used; j--) {
          if (overlaps(s, S.asteroids[j])) {
            used = true;
            S.asteroids[j].hp -= 1;
            if (S.asteroids[j].hp <= 0) { boom(S.asteroids[j].x, S.asteroids[j].y, 1.2); S.asteroids.splice(j, 1); S.score += 50; }
          }
        }
        if (used || s.y < -10) S.shots.splice(i, 1);
      }

      /* collisions: the player */
      if (S.state === "running" && p.exploding === 0) {
        for (i = S.enemyShots.length - 1; i >= 0; i--) {
          if (overlaps(S.enemyShots[i], p, -4)) { S.enemyShots.splice(i, 1); if (hitPlayer("shot")) break; }
        }
      }
      if (S.state === "running" && p.exploding === 0) {
        for (i = S.enemies.length - 1; i >= 0; i--) {
          if (overlaps(S.enemies[i], p, -4)) { boom(S.enemies[i].x, S.enemies[i].y, 1); S.enemies.splice(i, 1); if (hitPlayer("enemy")) break; }
        }
      }
      if (S.state === "running" && p.exploding === 0) {
        for (i = S.asteroids.length - 1; i >= 0; i--) {
          if (overlaps(S.asteroids[i], p, -6)) { if (hitPlayer("asteroid")) break; }
        }
      }

      /* the seeded random explosion */
      if (S.state === "running" && cfg.defects.randomExplosion && S.tick >= S.nextExplosion) {
        if (p.exploding === 0 && p.invuln === 0) {
          S.explodeTicks.push(S.tick);
          emit("explode", { tick: S.tick });
          loseLife("explode");
          S.nextExplosion = nextExplosion(S.rng.defects, S.tick);
        }
      }

      /* cleanup */
      S.enemies = S.enemies.filter(function (o) { return o.y < world.h + 40; });
      S.enemyShots = S.enemyShots.filter(function (o) { return o.y < world.h + 20 && o.x > -20 && o.x < world.w + 20; });
      S.asteroids = S.asteroids.filter(function (o) { return o.y < world.h + o.r + 10; });
      S.effects = S.effects.filter(function (o) { return o.t < 40; });
    }

    /* ---------- rendering (Phase 3: simple shapes) */
    var stars = (function () {
      var r = mulberry32(7), out = [];
      for (var k = 0; k < 90; k++) out.push({ x: r(), y: r(), s: 0.6 + r() * 1.4 });
      return out;
    })();
    function draw() {
      if (!ctx || !S) return;
      var cw = canvas.width, ch = canvas.height;
      var scale = Math.min(cw / world.w, ch / world.h);
      var ox = (cw - world.w * scale) / 2, oy = (ch - world.h * scale) / 2;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.fillStyle = "#040c11";
      ctx.fillRect(0, 0, cw, ch);
      ctx.setTransform(scale, 0, 0, scale, ox, oy);
      ctx.fillStyle = "#06141b";
      ctx.fillRect(0, 0, world.w, world.h);
      ctx.fillStyle = "rgba(186,230,253,.55)";
      for (var k = 0; k < stars.length; k++) {
        var sy = (stars[k].y * world.h + (S.tick * stars[k].s * 0.4)) % world.h;
        ctx.fillRect(stars[k].x * world.w, sy, stars[k].s, stars[k].s);
      }
      var i;
      ctx.fillStyle = "#94a3b8";
      for (i = 0; i < S.asteroids.length; i++) { var a = S.asteroids[i]; ctx.beginPath(); ctx.arc(a.x, a.y, a.r, 0, 6.283); ctx.fill(); }
      ctx.fillStyle = "#f472b6";
      for (i = 0; i < S.enemies.length; i++) {
        var e = S.enemies[i];
        ctx.beginPath(); ctx.moveTo(e.x, e.y + e.r); ctx.lineTo(e.x - e.r, e.y - e.r * 0.6); ctx.lineTo(e.x + e.r, e.y - e.r * 0.6); ctx.closePath(); ctx.fill();
      }
      ctx.fillStyle = "#fbbf24";
      for (i = 0; i < S.enemyShots.length; i++) { var es = S.enemyShots[i]; ctx.beginPath(); ctx.arc(es.x, es.y, es.r, 0, 6.283); ctx.fill(); }
      ctx.fillStyle = "#5eead4";
      for (i = 0; i < S.shots.length; i++) ctx.fillRect(S.shots[i].x - 2, S.shots[i].y - 8, 4, 12);
      var p = S.player;
      var blink = p.invuln > 0 && !REDUCED && Math.floor(p.invuln / 6) % 2 === 0;
      if (p.exploding === 0 && S.overReason !== "first-hit" && !(S.state === "over" && p.lives <= 0) && !blink) {
        ctx.fillStyle = "#22d3ee";
        ctx.beginPath(); ctx.moveTo(p.x, p.y - p.r); ctx.lineTo(p.x - p.r, p.y + p.r); ctx.lineTo(p.x + p.r, p.y + p.r); ctx.closePath(); ctx.fill();
      }
      for (i = 0; i < S.effects.length; i++) {
        var f = S.effects[i], grow = f.t / 40;
        ctx.strokeStyle = "rgba(251,191,36," + (1 - grow).toFixed(2) + ")";
        ctx.lineWidth = 3;
        ctx.beginPath(); ctx.arc(f.x, f.y, (10 + grow * 34) * f.size, 0, 6.283); ctx.stroke();
      }
    }

    function sync() {
      if (!S) return;
      hudScore.textContent = "Score " + S.score;
      hudLives.textContent = "Lives " + Math.max(0, S.player.lives);
      hudLevel.textContent = "Level " + S.level;
      hudState.textContent = S.state === "idle" ? "Ready" : S.state === "running" ? "Playing" : S.state === "paused" ? "Paused" : "Game over";
      overlay.hidden = S.state === "running";
      startBtn.textContent = S.state === "paused" ? "Resume" : S.state === "over" ? "Play again" : "Click to start";
      host.setAttribute("data-ss-state", S.state);
    }

    /* ---------- control */
    function releaseKeys() { held.left = held.right = held.up = held.down = held.fire = false; }
    function start() {
      if (!S || S.state === "over") reset();
      if (S.state === "paused") { resume(); return; }
      if (S.state === "running") return;
      S.state = "running";
      S.pausedBy = null;
      last = 0; acc = 0;
      emit("start", { tick: S.tick });
      sync();
      canvas.focus({ preventScroll: true });
    }
    function pause(reason) {
      if (!S || S.state !== "running") return;
      S.state = "paused";
      S.pausedBy = reason || "user";
      releaseKeys();
      emit("pause", { reason: S.pausedBy });
      sync();
      draw();
    }
    function resume() {
      if (!S || S.state !== "paused") return;
      S.state = "running";
      S.pausedBy = null;
      last = 0; acc = 0;
      emit("resume", {});
      sync();
    }

    var api = {
      id: id,
      configure: function (next) {
        next = next || {};
        if (next.defects) {
          var d = normDefects(next.defects);
          if (!d) { if (window.console) console.warn("SkySentinel: unknown defect in " + JSON.stringify(next.defects) + "; nothing changed"); return false; }
          cfg.defects = d;
        }
        if (next.level) cfg.level = next.level;
        if (next.seed != null) cfg.seed = next.seed >>> 0;
        if (next.threats != null) cfg.threats = !!next.threats;
        if (next.reset !== false) reset();
        return true;
      },
      start: start,
      pause: pause,
      resume: resume,
      reset: function () { reset(); },
      on: function (name, fn) { (listeners[name] = listeners[name] || []).push(fn); return api; },
      /* test layer */
      step: function (n) {
        if (!S) reset();
        var wasPaused = S.state !== "running";
        var saved = S.state;
        if (wasPaused && S.state !== "over") S.state = "running";
        for (var k = 0; k < (n || 1) && S.state === "running"; k++) tick();
        if (wasPaused && S.state === "running") S.state = saved;
        sync();
        draw();
        return api.state();
      },
      input: function (keys) { for (var k in keys) if (Object.prototype.hasOwnProperty.call(held, k)) held[k] = !!keys[k]; },
      forceHit: function (source) {
        if (!S || S.state === "over" || S.state === "idle") return false;
        var saved = S.state;
        S.state = "running";
        var hit = hitPlayer(source || "test");
        if (S.state === "running") S.state = saved;
        sync();
        return hit;
      },
      state: function () {
        return {
          id: id, tick: S.tick, state: S.state, pausedBy: S.pausedBy, score: S.score, level: S.level,
          lives: S.player.lives, defects: { firstHitFatal: cfg.defects.firstHitFatal, randomExplosion: cfg.defects.randomExplosion },
          seed: cfg.seed, world: { w: world.w, h: world.h },
          player: { x: S.player.x, y: S.player.y, invuln: S.player.invuln, exploding: S.player.exploding },
          enemies: S.enemies.length, enemyShots: S.enemyShots.length, asteroids: S.asteroids.length, shots: S.shots.length,
          firstShotTick: S.firstShotTick, firstShotGap: S.firstShotGap,
          explodeTicks: S.explodeTicks.slice(), hitTicks: S.hitTicks.slice(), lifeLossTicks: S.lifeLossTicks.slice(),
          nextExplosion: S.nextExplosion, overReason: S.overReason,
          canvas: { cssWidth: canvas.clientWidth, cssHeight: canvas.clientHeight, width: canvas.width, height: canvas.height }
        };
      },
      frame: function (now) {
        if (!S || S.state !== "running") { last = 0; return; }
        if (!last) last = now;
        acc += Math.min(250, now - last) / 1000;
        last = now;
        var steps = 0;
        while (acc >= 1 / HZ && steps < MAX_STEPS_PER_FRAME && S.state === "running") { tick(); acc -= 1 / HZ; steps += 1; }
        if (steps === MAX_STEPS_PER_FRAME) acc = 0;
        if (steps) { sync(); draw(); }
      },
      destroy: function () { delete instances[id]; if (io) io.disconnect(); if (ro) ro.disconnect(); }
    };

    /* ---------- input wiring */
    var KEYS = { ArrowLeft: "left", a: "left", A: "left", ArrowRight: "right", d: "right", D: "right", ArrowUp: "up", w: "up", W: "up", ArrowDown: "down", s: "down", S: "down", " ": "fire" };
    function owns() { return S && S.state === "running" && host.offsetParent !== null; }
    window.addEventListener("keydown", function (ev) {
      if (ev.ctrlKey || ev.metaKey || ev.altKey) return;
      if (ev.key === "Escape" && owns()) { pause("escape"); ev.preventDefault(); return; }
      if (ev.key === "Enter" && document.activeElement === canvas && S && S.state !== "running") { start(); ev.preventDefault(); return; }
      var k = KEYS[ev.key];
      if (k && owns()) { held[k] = true; ev.preventDefault(); }
    });
    window.addEventListener("keyup", function (ev) { var k = KEYS[ev.key]; if (k) held[k] = false; });
    startBtn.addEventListener("click", function () { start(); });
    canvas.addEventListener("mousedown", function (ev) {
      if (ev.button !== 0) return;
      if (!S || S.state !== "running") { start(); return; }
      held.fire = true;
    });
    window.addEventListener("mouseup", function () { held.fire = false; });
    canvas.addEventListener("contextmenu", function (ev) { ev.preventDefault(); });
    Object.keys(touchButtons).forEach(function (k) {
      var btn = touchButtons[k];
      btn.addEventListener("pointerdown", function (ev) { ev.preventDefault(); if (!S || S.state !== "running") start(); held[k] = true; });
      ["pointerup", "pointercancel", "pointerleave"].forEach(function (t) { btn.addEventListener(t, function () { held[k] = false; }); });
    });
    var io = null, ro = null;
    if ("IntersectionObserver" in window) {
      io = new IntersectionObserver(function (entries) {
        for (var k = 0; k < entries.length; k++) if (entries[k].intersectionRatio < 0.3) pause("offscreen");
      }, { threshold: [0, 0.3, 0.6, 1] });
      io.observe(stage);
    }
    if ("ResizeObserver" in window) { ro = new ResizeObserver(function () { fit(); }); ro.observe(host); }
    else window.addEventListener("resize", fit);

    instances[id] = api;
    reset();
    fit();
    if (opts.autoStart) start();
    return api;
  }

  /* -------------------------------------------------- shared loop and page events */
  function loop(now) {
    if (!manual) for (var k in instances) instances[k].frame(now);
    window.requestAnimationFrame(loop);
  }
  window.requestAnimationFrame(loop);
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") for (var k in instances) instances[k].pause("hidden");
  });
  window.addEventListener("blur", function () { for (var k in instances) instances[k].pause("blur"); });

  window.SkySentinel = {
    create: create,
    get: function (id) { return instances[id] || null; },
    ids: function () { return Object.keys(instances); },
    manual: function (on) { manual = !!on; },
    defectSchedule: defectSchedule,
    constants: { HZ: HZ, GRACE_TICKS: GRACE_TICKS, FIRST_SHOT_CLEARANCE: FIRST_SHOT_CLEARANCE, EARLIEST_EXPLOSION: EARLIEST_EXPLOSION, EXPLOSION_GAP: EXPLOSION_GAP, INVULNERABLE_TICKS: INVULNERABLE_TICKS, START_LIVES: START_LIVES }
  };
})();
