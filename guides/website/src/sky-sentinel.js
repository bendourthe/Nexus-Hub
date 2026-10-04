/* ===================================================================== Sky Sentinel (v4.13.10)
   The Training page's game engine. Design and test rules:
   docs/releases/v4/v4.13/development/v4.13.10-game-design.md
   Fixed 60 Hz simulation separated from canvas rendering; seeded random streams
   (spawn, drops, defects, and a render-only fx stream); every timing rule counted in
   ticks; the two seeded defects are independent flags. Progression (levels, ship
   forms, power-ups) and the Nexus megaship boss are switched on per game.
   Inlined into training.html by scripts/stamp_guide_shared.py: edit this file, not the page.
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
  var MAX_LIVES = 5;
  var LEVEL_TICKS = { 1: 5400, 2: 6600 };   /* level 2 at 90 s, level 3 at 200 s */
  var BOSS_AFTER = 3600;                    /* the boss arrives 60 s into level 3: 260 s from the start */
  var BOSS_AFTER_JUMP = 150;
  var WEAPON_TICKS = 600;
  var DROP_CHANCE = 0.14;
  var FORMS = { 1: "Scout", 2: "Fighter", 3: "Sentinel" };
  var DEFECT_NAMES = ["firstHitFatal", "randomExplosion"];
  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* The Nexus Hub mark in its own 512-unit space (the guide's shared nexus-mark symbol):
     two crossing bars, four end nodes, a white core, two side plates, and two blades. */
  var LOGO = {
    centre: [258, 246],
    nodes: [[106, 97], [410, 97], [106, 395], [410, 395]],
    nodeR: 34, coreR: 30, barW: 26,
    plates: [[[89, 144], [196, 250], [89, 356]], [[425, 144], [320, 250], [425, 355]]],
    blades: [[[164, 102], [285, 179], [270, 196]], [[352, 398], [231, 321], [246, 304]]]
  };

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
      defects: mulberry32(s ^ 0x6A09E667),
      fx: mulberry32(s ^ 0x1F83D9AB)
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

  function inTriangle(px, py, t) {
    var a = t[0], b = t[1], c = t[2];
    var d1 = (px - b[0]) * (a[1] - b[1]) - (a[0] - b[0]) * (py - b[1]);
    var d2 = (px - c[0]) * (b[1] - c[1]) - (b[0] - c[0]) * (py - c[1]);
    var d3 = (px - a[0]) * (c[1] - a[1]) - (c[0] - a[0]) * (py - a[1]);
    var neg = d1 < 0 || d2 < 0 || d3 < 0, pos = d1 > 0 || d2 > 0 || d3 > 0;
    return !(neg && pos);
  }
  function segDist(px, py, ax, ay, bx, by) {
    var dx = bx - ax, dy = by - ay, t = ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy);
    t = Math.max(0, Math.min(1, t));
    var x = ax + t * dx - px, y = ay + t * dy - py;
    return Math.sqrt(x * x + y * y);
  }

  /* -------------------------------------------------- one game */
  function create(host, opts) {
    opts = opts || {};
    var id = opts.id || host.getAttribute("data-ss-id") || ("game" + Object.keys(instances).length);
    if (instances[id]) throw new Error("SkySentinel: duplicate game id " + id);

    var cfg = {
      defects: normDefects(opts.defects) || normDefects(null), level: opts.level || 1, seed: opts.seed >>> 0 || 1,
      threats: true, progression: !!opts.progression, boss: !!opts.boss, bossNow: false
    };
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
    var overTitle = el("p", "ss-over-title");
    var startBtn = el("button", "ss-start", "Click to start");
    startBtn.type = "button";
    var hint = el("p", "ss-hint", "Arrows or WASD move, Space or click fires, Escape pauses.");
    overlay.appendChild(overTitle);
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
      var level = cfg.progression ? Math.max(1, Math.min(3, cfg.level)) : 1;
      S = {
        rng: r, tick: 0, state: "idle", pausedBy: null, score: 0, level: level, levelTicks: 0,
        player: { x: world.w / 2, y: world.h - 70, r: 18, lives: START_LIVES, invuln: 0, exploding: 0, cooldown: 0, shield: 0, weapon: 0 },
        enemies: [], enemyShots: [], shots: [], asteroids: [], powerUps: [], effects: [],
        spawnIn: 50, rockIn: 240, firstShotTick: null, firstShotGap: null, firstHitTaken: false,
        nextExplosion: firstExplosion(r.defects), explodeTicks: [], hitTicks: [], lifeLossTicks: [],
        collected: [], levelUps: [], boss: null, bossDue: cfg.boss && level === 3 ? (cfg.bossNow ? BOSS_AFTER_JUMP : BOSS_AFTER) : null,
        overReason: null, victory: false
      };
      acc = 0;
      sync();
      if (reshaped) fit(); else draw();
    }

    var ENEMY = {
      drone: { r: 16, hp: 1, score: 100 },
      weaver: { r: 15, hp: 1, score: 150 },
      lancer: { r: 19, hp: 2, score: 250 }
    };
    function pickType(rng) {
      var x = rng();
      if (!cfg.progression || S.level === 1) return x < 0.7 ? "drone" : "weaver";
      if (S.level === 2) return x < 0.45 ? "drone" : x < 0.8 ? "weaver" : "lancer";
      return x < 0.35 ? "drone" : x < 0.7 ? "weaver" : "lancer";
    }
    function spawnEnemy() {
      var rng = S.rng.spawn;
      var type = pickType(rng);
      var spec = ENEMY[type];
      S.enemies.push({
        type: type, x: 40 + rng() * (world.w - 80), y: -24, r: spec.r,
        vx: (rng() - 0.5) * 1.6, vy: (type === "lancer" ? 0.8 : 1.1) + rng() * 1.1,
        phase: rng() * Math.PI * 2, hp: spec.hp,
        fireIn: 50 + Math.floor(rng() * 110), burst: 0
      });
    }
    function spawnRock() {
      var rng = S.rng.spawn;
      var r = 16 + Math.floor(rng() * 16);
      S.asteroids.push({ x: r + rng() * (world.w - 2 * r), y: -r, r: r, vx: (rng() - 0.5) * 1.2, vy: 1.3 + rng() * 1.2, hp: r > 24 ? 2 : 1, spin: rng() * 6.28, look: Math.floor(rng() * 1e9) });
    }
    function spawnPowerUp(kind, x, y) { S.powerUps.push({ kind: kind, x: x, y: y, r: 14, t: 0 }); }

    function enemyMayFire(e) {
      if (S.tick < GRACE_TICKS) return false;
      if (S.firstShotTick === null && S.player.y - e.y < FIRST_SHOT_CLEARANCE) return false;
      return e.y > 0 && e.y < world.h * 0.75;
    }
    function enemyShot(x, y, vx, vy) {
      S.enemyShots.push({ x: x, y: y, r: 5, vx: vx, vy: vy });
      if (S.firstShotTick === null) { S.firstShotTick = S.tick; S.firstShotGap = S.player.y - y; }
    }

    function hitPlayer(source) {
      var p = S.player;
      if (S.state !== "running" || p.invuln > 0 || p.exploding > 0) return false;
      S.hitTicks.push(S.tick);
      emit("hit", { source: source, tick: S.tick });
      if (cfg.defects.firstHitFatal && !S.firstHitTaken) {
        S.firstHitTaken = true;
        p.lives = 0;
        boom(p.x, p.y, 2.2, "#fbbf24");
        gameOver("first-hit");
        return true;
      }
      S.firstHitTaken = true;
      if (p.shield > 0) {
        p.shield = 0;
        p.invuln = 60;
        ring(p.x, p.y, "#60a5fa");
        say("The shield took the hit.");
        return true;
      }
      loseLife("hit");
      return true;
    }

    function loseLife(reason) {
      var p = S.player;
      p.lives -= 1;
      p.weapon = 0;
      S.lifeLossTicks.push(S.tick);
      boom(p.x, p.y, 1.8, "#fbbf24");
      emit("lifeLost", { reason: reason, lives: p.lives, tick: S.tick });
      if (p.lives <= 0) { gameOver(reason); return; }
      p.exploding = RESPAWN_TICKS;
      say(reason === "explode" ? "The ship exploded with no hit. Lives left: " + p.lives + "." : "Hit. Lives left: " + p.lives + ".");
    }

    function gameOver(reason) {
      S.state = "over";
      S.overReason = reason;
      held.left = held.right = held.up = held.down = held.fire = false;
      if (reason === "victory") {
        say("The Nexus megaship is down. Score " + S.score + ".");
      } else {
        emit("destroyed", { reason: reason, tick: S.tick, score: S.score });
        say(reason === "first-hit" ? "Destroyed by the first hit, with lives still left. That is the bug." : "Game over. Score " + S.score + ".");
      }
      sync();
    }

    function boom(x, y, size, color) {
      var n = REDUCED ? 6 : 16, fx = S.rng.fx;
      S.effects.push({ kind: "ring", x: x, y: y, t: 0, size: size || 1, color: color || "#fbbf24", life: 40 });
      for (var k = 0; k < n; k++) {
        var a = fx() * 6.283, v = (0.8 + fx() * 3.2) * (size || 1);
        S.effects.push({ kind: "spark", x: x, y: y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, t: 0, life: 26 + Math.floor(fx() * 20), color: color || "#fbbf24" });
      }
    }
    function ring(x, y, color) { S.effects.push({ kind: "ring", x: x, y: y, t: 0, size: 1.4, color: color, life: 36 }); }

    function overlaps(a, b, extra) { var dx = a.x - b.x, dy = a.y - b.y, r = a.r + b.r + (extra || 0); return dx * dx + dy * dy < r * r; }

    /* ---------- progression */
    function levelUp() {
      S.level += 1;
      S.levelTicks = 0;
      S.levelUps.push(S.tick);
      var p = S.player;
      ring(p.x, p.y, "#5eead4");
      ring(p.x, p.y - 10, "#22d3ee");
      emit("levelUp", { level: S.level, form: FORMS[S.level], tick: S.tick });
      say("Level " + S.level + ". The ship becomes the " + FORMS[S.level] + ".");
      if (S.level === 3 && cfg.boss) S.bossDue = BOSS_AFTER;
    }
    function collect(pu) {
      var p = S.player;
      S.collected.push({ kind: pu.kind, tick: S.tick });
      ring(pu.x, pu.y, pu.kind === "shield" ? "#60a5fa" : pu.kind === "weapon" ? "#f472b6" : "#34d399");
      if (pu.kind === "shield") { p.shield = 1; say("Shield up: it absorbs one hit."); }
      else if (pu.kind === "weapon") { p.weapon = WEAPON_TICKS; say("Twin shot for 10 seconds."); }
      else { p.lives = Math.min(MAX_LIVES, p.lives + 1); say("Extra ship. Lives: " + p.lives + "."); }
      emit("powerUp", { kind: pu.kind, tick: S.tick });
    }
    function fire() {
      var p = S.player, form = cfg.progression ? S.level : 1;
      var twin = p.weapon > 0 || form === 3;
      if (form === 3 && p.weapon > 0) {
        S.shots.push({ x: p.x, y: p.y - p.r, r: 4, vx: 0 });
        S.shots.push({ x: p.x - 10, y: p.y - p.r + 4, r: 4, vx: -2.2 });
        S.shots.push({ x: p.x + 10, y: p.y - p.r + 4, r: 4, vx: 2.2 });
      } else if (twin) {
        S.shots.push({ x: p.x - 9, y: p.y - p.r + 4, r: 4, vx: 0 });
        S.shots.push({ x: p.x + 9, y: p.y - p.r + 4, r: 4, vx: 0 });
      } else {
        S.shots.push({ x: p.x, y: p.y - p.r, r: 4, vx: 0 });
      }
      p.cooldown = form >= 2 ? 8 : 10;
    }

    /* ---------- the boss */
    function bossScale() { return world.w < 800 ? 0.5 : 0.62; }
    function spawnBoss() {
      var s = bossScale();
      S.boss = {
        x: world.w / 2, y: -260 * s, targetY: world.h * 0.25, s: s, t: 0, entered: false,
        nodes: LOGO.nodes.map(function (n, i) { return { i: i, hp: 8, alive: true, fireIn: 90 + i * 19, flash: 0 }; }),
        coreHp: 24, coreFlash: 0, fireIn: 120
      };
      S.enemies = [];
      emit("bossArrive", { tick: S.tick });
      say("The Nexus megaship is coming. Destroy its four nodes, then its core.");
    }
    function bossPoint(b, lx, ly) { return [b.x + (lx - LOGO.centre[0]) * b.s, b.y + (ly - LOGO.centre[1]) * b.s]; }
    function nodesAlive(b) { return b.nodes.filter(function (n) { return n.alive; }).length; }
    function bossTick() {
      var b = S.boss, p = S.player;
      b.t += 1;
      if (!b.entered) {
        b.y += (b.targetY - b.y) * 0.03 + 0.6;
        if (b.y >= b.targetY - 1) { b.y = b.targetY; b.entered = true; }
      } else {
        b.x = world.w / 2 + Math.sin(b.t * 0.008) * world.w * 0.22;
      }
      if (b.coreFlash > 0) b.coreFlash -= 1;
      b.nodes.forEach(function (n) {
        if (n.flash > 0) n.flash -= 1;
        if (!n.alive || !b.entered) return;
        n.fireIn -= 1;
        if (n.fireIn <= 0) {
          var at = bossPoint(b, LOGO.nodes[n.i][0], LOGO.nodes[n.i][1]);
          var dx = p.x - at[0], dy = p.y - at[1], d = Math.sqrt(dx * dx + dy * dy) || 1;
          enemyShot(at[0], at[1], dx / d * 4.2, dy / d * 4.2);
          n.fireIn = 84;
        }
      });
      if (b.entered && nodesAlive(b) === 0) {
        b.fireIn -= 1;
        if (b.fireIn <= 0) {
          for (var k = -2; k <= 2; k++) enemyShot(b.x, b.y + LOGO.coreR * b.s, k * 1.3, 4.4);
          b.fireIn = 80;
        }
      }
    }
    /* Returns true when the shot is used up by the boss. */
    function shotHitsBoss(s) {
      var b = S.boss;
      if (!b) return false;
      for (var i = 0; i < b.nodes.length; i++) {
        var n = b.nodes[i];
        if (!n.alive) continue;
        var at = bossPoint(b, LOGO.nodes[i][0], LOGO.nodes[i][1]);
        if (Math.hypot(s.x - at[0], s.y - at[1]) < LOGO.nodeR * b.s + s.r) { damageNode(i, 1); return true; }
      }
      if (Math.hypot(s.x - b.x, s.y - b.y) < LOGO.coreR * b.s + s.r) {
        if (nodesAlive(b) === 0) damageCore(1); else ring(s.x, s.y, "#93c5fd");
        return true;
      }
      var lx = (s.x - b.x) / b.s + LOGO.centre[0], ly = (s.y - b.y) / b.s + LOGO.centre[1];
      var shapes = LOGO.plates.concat(LOGO.blades);
      for (var k = 0; k < shapes.length; k++) if (inTriangle(lx, ly, shapes[k])) return true;
      if (segDist(lx, ly, 106, 97, 410, 395) < LOGO.barW / 2 || segDist(lx, ly, 410, 97, 106, 395) < LOGO.barW / 2) return true;
      return false;
    }
    function damageNode(i, n) {
      var node = S.boss.nodes[i];
      if (!node.alive) return;
      node.hp -= n;
      node.flash = 6;
      S.score += 25;
      if (node.hp <= 0) {
        node.alive = false;
        var at = bossPoint(S.boss, LOGO.nodes[i][0], LOGO.nodes[i][1]);
        boom(at[0], at[1], 1.6, "#22d3ee");
        S.score += 750;
        say(nodesAlive(S.boss) ? nodesAlive(S.boss) + " nodes left." : "Every node is down. The core is exposed.");
      }
    }
    function damageCore(n) {
      var b = S.boss;
      b.coreHp -= n;
      b.coreFlash = 6;
      S.score += 40;
      if (b.coreHp <= 0) {
        boom(b.x, b.y, 3.2, "#f2feff");
        boom(b.x, b.y, 2.2, "#22d3ee");
        S.score += 5000;
        S.victory = true;
        S.boss = null;
        emit("bossDefeated", { tick: S.tick, score: S.score });
        gameOver("victory");
      }
    }

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
        if (held.fire && p.cooldown === 0) fire();
      }
      if (p.weapon > 0) p.weapon -= 1;

      /* progression */
      if (cfg.progression) {
        /* The countdown runs before the level check, so a boss due 3,600 ticks after
           level 3 begins arrives on exactly that tick, not one tick early. */
        if (S.bossDue !== null && !S.boss) {
          S.bossDue -= 1;
          if (S.bossDue <= 0) { S.bossDue = null; spawnBoss(); }
        }
        S.levelTicks += 1;
        if (S.level < 3 && S.levelTicks >= LEVEL_TICKS[S.level]) levelUp();
      }

      /* spawning (the test layer can switch threats off to watch the defect schedule alone) */
      if (cfg.threats && !S.boss) {
        S.spawnIn -= 1;
        if (S.spawnIn <= 0) {
          spawnEnemy();
          var pace = 70 - Math.floor(S.tick / 600) * 6 - (cfg.progression ? (S.level - 1) * 8 : 0);
          S.spawnIn = Math.max(24, pace) + Math.floor(S.rng.spawn() * 30);
        }
        S.rockIn -= 1;
        if (S.rockIn <= 0) { spawnRock(); S.rockIn = 220 + Math.floor(S.rng.spawn() * 200); }
      }
      if (S.boss) bossTick();

      /* movement */
      for (i = 0; i < S.shots.length; i++) { S.shots[i].y -= 13; S.shots[i].x += S.shots[i].vx || 0; }
      for (i = 0; i < S.enemies.length; i++) {
        var e = S.enemies[i];
        e.phase += e.type === "weaver" ? 0.07 : 0.04;
        var sway = e.type === "weaver" ? Math.sin(e.phase) * 2.6 : Math.sin(e.phase) * 0.9;
        e.x = Math.max(e.r, Math.min(world.w - e.r, e.x + e.vx + sway));
        e.y += e.vy;
        e.fireIn -= 1;
        if (e.fireIn <= 0) {
          if (enemyMayFire(e)) {
            var aim = Math.max(-2, Math.min(2, (p.x - e.x) / 120));
            if (e.type === "drone") enemyShot(e.x, e.y + e.r, aim * 0.5, 5.2);
            else if (e.type === "weaver") enemyShot(e.x, e.y + e.r, aim, 5.2);
            else { enemyShot(e.x, e.y + e.r, aim - 1, 4.6); enemyShot(e.x, e.y + e.r, aim, 4.8); enemyShot(e.x, e.y + e.r, aim + 1, 4.6); }
            e.fireIn = (e.type === "lancer" ? 130 : 90) + Math.floor(S.rng.spawn() * 90);
          } else {
            e.fireIn = 12;
          }
        }
      }
      for (i = 0; i < S.enemyShots.length; i++) { S.enemyShots[i].x += S.enemyShots[i].vx; S.enemyShots[i].y += S.enemyShots[i].vy; }
      for (i = 0; i < S.asteroids.length; i++) { var a = S.asteroids[i]; a.x += a.vx; a.y += a.vy; a.spin += 0.01; }
      for (i = 0; i < S.powerUps.length; i++) { S.powerUps[i].y += 1.8; S.powerUps[i].t += 1; }
      for (i = 0; i < S.effects.length; i++) {
        var f = S.effects[i];
        f.t += 1;
        if (f.kind === "spark") { f.x += f.vx; f.y += f.vy; f.vx *= 0.95; f.vy *= 0.95; }
      }

      /* collisions: player shots */
      for (i = S.shots.length - 1; i >= 0; i--) {
        var s = S.shots[i], used = shotHitsBoss(s);
        if (!S.boss && S.state === "over") return;
        for (j = S.enemies.length - 1; j >= 0 && !used; j--) {
          var en = S.enemies[j];
          if (overlaps(s, en)) {
            used = true;
            en.hp -= 1;
            if (en.hp <= 0) {
              boom(en.x, en.y, 1, en.type === "lancer" ? "#fb923c" : "#f472b6");
              S.enemies.splice(j, 1);
              S.score += ENEMY[en.type].score;
              if (cfg.progression && S.rng.drops() < DROP_CHANCE) {
                var k = S.rng.drops();
                spawnPowerUp(k < 0.4 ? "shield" : k < 0.8 ? "weapon" : "ship", en.x, en.y);
              }
            }
          }
        }
        for (j = S.asteroids.length - 1; j >= 0 && !used; j--) {
          if (overlaps(s, S.asteroids[j])) {
            used = true;
            S.asteroids[j].hp -= 1;
            if (S.asteroids[j].hp <= 0) { boom(S.asteroids[j].x, S.asteroids[j].y, 1.2, "#cbd5e1"); S.asteroids.splice(j, 1); S.score += 50; }
          }
        }
        if (used || s.y < -10 || s.x < -10 || s.x > world.w + 10) S.shots.splice(i, 1);
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
      if (S.state === "running" && p.exploding === 0 && S.boss && S.boss.entered) {
        if (Math.hypot(p.x - S.boss.x, p.y - S.boss.y) < (LOGO.coreR + 120) * S.boss.s) hitPlayer("boss");
      }
      if (S.state === "running" && p.exploding === 0) {
        for (i = S.powerUps.length - 1; i >= 0; i--) {
          if (overlaps(S.powerUps[i], p, 6)) { collect(S.powerUps[i]); S.powerUps.splice(i, 1); }
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
      S.enemyShots = S.enemyShots.filter(function (o) { return o.y < world.h + 20 && o.y > -40 && o.x > -20 && o.x < world.w + 20; });
      S.asteroids = S.asteroids.filter(function (o) { return o.y < world.h + o.r + 10; });
      S.powerUps = S.powerUps.filter(function (o) { return o.y < world.h + 20; });
      S.effects = S.effects.filter(function (o) { return o.t < o.life; });
    }

    /* ---------- rendering */
    var starLayers = (function () {
      var r = mulberry32(7), out = [];
      [[70, 0.12, 0.8, 0.35], [45, 0.32, 1.2, 0.55], [22, 0.75, 1.8, 0.85]].forEach(function (spec) {
        var layer = { speed: spec[1], size: spec[2], alpha: spec[3], stars: [] };
        for (var k = 0; k < spec[0]; k++) layer.stars.push({ x: r(), y: r(), tw: r() * 6.28 });
        out.push(layer);
      });
      return out;
    })();

    function drawBackground() {
      var g = ctx.createLinearGradient(0, 0, 0, world.h);
      g.addColorStop(0, "#030a10");
      g.addColorStop(1, "#071a22");
      ctx.fillStyle = g;
      ctx.fillRect(0, 0, world.w, world.h);
      var neb = [[0.18, 0.28, 0.32, "rgba(34,211,238,0.06)"], [0.82, 0.62, 0.4, "rgba(168,85,247,0.05)"]];
      neb.forEach(function (n) {
        var rg = ctx.createRadialGradient(n[0] * world.w, n[1] * world.h, 0, n[0] * world.w, n[1] * world.h, n[2] * world.w);
        rg.addColorStop(0, n[3]);
        rg.addColorStop(1, "rgba(0,0,0,0)");
        ctx.fillStyle = rg;
        ctx.fillRect(0, 0, world.w, world.h);
      });
      starLayers.forEach(function (layer) {
        var drift = REDUCED ? layer.speed * 0.2 : layer.speed;
        for (var k = 0; k < layer.stars.length; k++) {
          var st = layer.stars[k];
          var y = (st.y * world.h + S.tick * drift) % world.h;
          var a = layer.alpha * (REDUCED ? 1 : 0.75 + 0.25 * Math.sin(st.tw + S.tick * 0.05));
          ctx.fillStyle = "rgba(205,240,255," + a.toFixed(2) + ")";
          ctx.fillRect(st.x * world.w, y, layer.size, layer.size);
        }
      });
    }

    function drawShip(p) {
      var form = cfg.progression ? S.level : 1, x = p.x, y = p.y;
      ctx.save();
      ctx.translate(x, y);
      var flame = REDUCED ? 1 : 0.8 + 0.2 * Math.sin(S.tick * 0.6);
      var fl = ctx.createLinearGradient(0, 10, 0, 34);
      fl.addColorStop(0, "rgba(253,224,71,0.95)");
      fl.addColorStop(1, "rgba(249,115,22,0)");
      ctx.fillStyle = fl;
      var engines = form === 3 ? [-9, 9] : [0];
      engines.forEach(function (ex) {
        ctx.beginPath(); ctx.moveTo(ex - 5, 12); ctx.lineTo(ex, 12 + 22 * flame); ctx.lineTo(ex + 5, 12); ctx.closePath(); ctx.fill();
      });
      var hull = ctx.createLinearGradient(-20, -20, 20, 20);
      hull.addColorStop(0, "#a5f3fc");
      hull.addColorStop(1, form === 3 ? "#0e7490" : "#0891b2");
      ctx.fillStyle = hull;
      ctx.strokeStyle = "#ecfeff";
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      if (form === 1) {
        ctx.moveTo(0, -20); ctx.lineTo(14, 14); ctx.lineTo(0, 8); ctx.lineTo(-14, 14);
      } else if (form === 2) {
        ctx.moveTo(0, -24); ctx.lineTo(8, -4); ctx.lineTo(24, 10); ctx.lineTo(24, 16); ctx.lineTo(6, 12); ctx.lineTo(0, 16);
        ctx.lineTo(-6, 12); ctx.lineTo(-24, 16); ctx.lineTo(-24, 10); ctx.lineTo(-8, -4);
      } else {
        ctx.moveTo(0, -30); ctx.lineTo(9, -8); ctx.lineTo(30, 4); ctx.lineTo(30, 14); ctx.lineTo(14, 12); ctx.lineTo(13, 18);
        ctx.lineTo(4, 14); ctx.lineTo(0, 18); ctx.lineTo(-4, 14); ctx.lineTo(-13, 18); ctx.lineTo(-14, 12); ctx.lineTo(-30, 14); ctx.lineTo(-30, 4); ctx.lineTo(-9, -8);
      }
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
      ctx.fillStyle = "#082f49";
      ctx.beginPath(); ctx.ellipse(0, -6, 3.5, 7, 0, 0, 6.283); ctx.fill();
      if (p.shield > 0) {
        ctx.strokeStyle = "rgba(96,165,250,0.85)";
        ctx.lineWidth = 2.5;
        ctx.beginPath(); ctx.arc(0, -2, 30 + (REDUCED ? 0 : Math.sin(S.tick * 0.15) * 2), 0, 6.283); ctx.stroke();
      }
      ctx.restore();
    }

    function drawEnemy(e) {
      ctx.save();
      ctx.translate(e.x, e.y);
      if (e.type === "drone") {
        var g = ctx.createLinearGradient(0, -e.r, 0, e.r);
        g.addColorStop(0, "#f9a8d4"); g.addColorStop(1, "#be185d");
        ctx.fillStyle = g;
        ctx.beginPath(); ctx.moveTo(0, e.r); ctx.lineTo(-e.r, -e.r * 0.4); ctx.lineTo(-e.r * 0.4, -e.r); ctx.lineTo(e.r * 0.4, -e.r); ctx.lineTo(e.r, -e.r * 0.4); ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#fdf2f8"; ctx.beginPath(); ctx.arc(0, -2, 3, 0, 6.283); ctx.fill();
      } else if (e.type === "weaver") {
        ctx.rotate(Math.sin(e.phase) * 0.4);
        ctx.fillStyle = "#c084fc";
        ctx.beginPath(); ctx.arc(0, 0, e.r, 0.2, Math.PI - 0.2); ctx.arc(0, -5, e.r * 0.75, Math.PI - 0.4, 0.4, true); ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#f5d0fe"; ctx.beginPath(); ctx.arc(0, 4, 3, 0, 6.283); ctx.fill();
      } else {
        var warm = e.fireIn < 25 ? 1 : 0.4;
        ctx.fillStyle = "#fb923c";
        ctx.beginPath(); ctx.moveTo(0, e.r + 6); ctx.lineTo(-7, -e.r); ctx.lineTo(0, -e.r + 6); ctx.lineTo(7, -e.r); ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#7c2d12";
        ctx.fillRect(-e.r, -4, e.r * 2, 6);
        ctx.fillStyle = "rgba(254,215,170," + warm + ")";
        ctx.beginPath(); ctx.arc(0, e.r + 2, 4 + warm * 2, 0, 6.283); ctx.fill();
      }
      ctx.restore();
    }

    function drawRock(a) {
      var r = mulberry32(a.look), n = 9;
      ctx.save();
      ctx.translate(a.x, a.y);
      ctx.rotate(a.spin);
      var g = ctx.createRadialGradient(-a.r * 0.35, -a.r * 0.35, a.r * 0.2, 0, 0, a.r * 1.1);
      g.addColorStop(0, "#cbd5e1"); g.addColorStop(1, "#334155");
      ctx.fillStyle = g;
      ctx.beginPath();
      for (var k = 0; k < n; k++) {
        var ang = k / n * 6.283, rad = a.r * (0.78 + r() * 0.3);
        if (k === 0) ctx.moveTo(Math.cos(ang) * rad, Math.sin(ang) * rad); else ctx.lineTo(Math.cos(ang) * rad, Math.sin(ang) * rad);
      }
      ctx.closePath(); ctx.fill();
      ctx.fillStyle = "rgba(15,23,42,0.35)";
      ctx.beginPath(); ctx.arc(a.r * 0.25, a.r * 0.1, a.r * 0.22, 0, 6.283); ctx.fill();
      ctx.restore();
    }

    function drawPowerUp(pu) {
      var color = pu.kind === "shield" ? "#60a5fa" : pu.kind === "weapon" ? "#f472b6" : "#34d399";
      var bob = REDUCED ? 0 : Math.sin(pu.t * 0.12) * 2;
      ctx.save();
      ctx.translate(pu.x, pu.y + bob);
      ctx.fillStyle = "rgba(2,6,23,0.75)";
      ctx.strokeStyle = color;
      ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(0, 0, pu.r, 0, 6.283); ctx.fill(); ctx.stroke();
      ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 2;
      if (pu.kind === "shield") { ctx.beginPath(); ctx.arc(0, 0, 6, 3.6, 5.8); ctx.stroke(); ctx.beginPath(); ctx.arc(0, 2, 6, 0.4, 2.7); ctx.stroke(); }
      else if (pu.kind === "weapon") { ctx.fillRect(-5, -6, 3, 12); ctx.fillRect(2, -6, 3, 12); }
      else { ctx.beginPath(); ctx.moveTo(0, -7); ctx.lineTo(6, 6); ctx.lineTo(-6, 6); ctx.closePath(); ctx.fill(); }
      ctx.restore();
    }

    function drawBoss(b) {
      ctx.save();
      ctx.translate(b.x, b.y);
      ctx.scale(b.s, b.s);
      ctx.translate(-LOGO.centre[0], -LOGO.centre[1]);
      function tri(t, fill) { ctx.fillStyle = fill; ctx.beginPath(); ctx.moveTo(t[0][0], t[0][1]); ctx.lineTo(t[1][0], t[1][1]); ctx.lineTo(t[2][0], t[2][1]); ctx.closePath(); ctx.fill(); }
      var gl = ctx.createLinearGradient(89, 0, 196, 0); gl.addColorStop(0, "#00647f"); gl.addColorStop(1, "#00cbe8");
      var gr = ctx.createLinearGradient(425, 0, 320, 0); gr.addColorStop(0, "#00647f"); gr.addColorStop(1, "#00cbe8");
      tri(LOGO.plates[0], gl);
      tri(LOGO.plates[1], gr);
      var gw = ctx.createLinearGradient(164, 102, 285, 196); gw.addColorStop(0, "#8ff8fb"); gw.addColorStop(1, "#0d8fa6");
      tri(LOGO.blades[0], gw);
      tri(LOGO.blades[1], gw);
      ctx.lineCap = "round";
      if (!REDUCED) { ctx.shadowColor = "#25f4ff"; ctx.shadowBlur = 24; }
      ctx.strokeStyle = "#25f4ff";
      ctx.lineWidth = LOGO.barW;
      ctx.beginPath(); ctx.moveTo(106, 97); ctx.lineTo(410, 395); ctx.moveTo(410, 97); ctx.lineTo(106, 395); ctx.stroke();
      ctx.shadowBlur = 0;
      b.nodes.forEach(function (n, i) {
        var c = LOGO.nodes[i];
        ctx.fillStyle = !n.alive ? "#164e63" : n.flash > 0 ? "#ffffff" : "#3ff7ff";
        ctx.beginPath(); ctx.arc(c[0], c[1], LOGO.nodeR, 0, 6.283); ctx.fill();
        if (n.alive) {
          ctx.strokeStyle = "rgba(255,255,255,0.6)"; ctx.lineWidth = 4;
          ctx.beginPath(); ctx.arc(c[0], c[1], LOGO.nodeR * (n.hp / 8), 0, 6.283); ctx.stroke();
        } else {
          ctx.strokeStyle = "#0e7490"; ctx.lineWidth = 6;
          ctx.beginPath(); ctx.moveTo(c[0] - 18, c[1] - 18); ctx.lineTo(c[0] + 18, c[1] + 18); ctx.moveTo(c[0] + 18, c[1] - 18); ctx.lineTo(c[0] - 18, c[1] + 18); ctx.stroke();
        }
      });
      var exposed = nodesAlive(b) === 0;
      var pulse = REDUCED ? 1 : 0.85 + 0.15 * Math.sin(b.t * 0.12);
      ctx.fillStyle = b.coreFlash > 0 ? "#fde68a" : exposed ? "#f2feff" : "rgba(242,254,255,0.55)";
      if (exposed && !REDUCED) { ctx.shadowColor = "#f2feff"; ctx.shadowBlur = 30; }
      ctx.beginPath(); ctx.arc(LOGO.centre[0], LOGO.centre[1], LOGO.coreR * pulse, 0, 6.283); ctx.fill();
      ctx.shadowBlur = 0;
      if (!exposed) {
        ctx.strokeStyle = "rgba(147,197,253,0.8)"; ctx.lineWidth = 5;
        ctx.beginPath(); ctx.arc(LOGO.centre[0], LOGO.centre[1], LOGO.coreR + 12, 0, 6.283); ctx.stroke();
      }
      ctx.restore();
      if (exposed) {
        var w = 160, x0 = b.x - w / 2, y0 = b.y - 150 * b.s - 24;
        ctx.fillStyle = "rgba(2,6,23,0.7)"; ctx.fillRect(x0, y0, w, 8);
        ctx.fillStyle = "#f2feff"; ctx.fillRect(x0, y0, w * Math.max(0, b.coreHp) / 24, 8);
      }
    }

    function draw() {
      if (!ctx || !S) return;
      var cw = canvas.width, ch = canvas.height;
      var scale = Math.min(cw / world.w, ch / world.h);
      var ox = (cw - world.w * scale) / 2, oy = (ch - world.h * scale) / 2;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.fillStyle = "#02070b";
      ctx.fillRect(0, 0, cw, ch);
      ctx.setTransform(scale, 0, 0, scale, ox, oy);
      drawBackground();
      var i;
      for (i = 0; i < S.asteroids.length; i++) drawRock(S.asteroids[i]);
      if (S.boss) drawBoss(S.boss);
      for (i = 0; i < S.enemies.length; i++) drawEnemy(S.enemies[i]);
      for (i = 0; i < S.powerUps.length; i++) drawPowerUp(S.powerUps[i]);
      if (!REDUCED) { ctx.shadowColor = "#fbbf24"; ctx.shadowBlur = 10; }
      ctx.fillStyle = "#fcd34d";
      for (i = 0; i < S.enemyShots.length; i++) { var es = S.enemyShots[i]; ctx.beginPath(); ctx.arc(es.x, es.y, es.r, 0, 6.283); ctx.fill(); }
      if (!REDUCED) ctx.shadowColor = "#22d3ee";
      ctx.fillStyle = "#a5f3fc";
      for (i = 0; i < S.shots.length; i++) { var sh = S.shots[i]; ctx.beginPath(); ctx.ellipse(sh.x, sh.y - 4, 2.5, 8, 0, 0, 6.283); ctx.fill(); }
      ctx.shadowBlur = 0;
      var p = S.player;
      var blink = p.invuln > 0 && !REDUCED && Math.floor(p.invuln / 6) % 2 === 0;
      if (p.exploding === 0 && S.overReason !== "first-hit" && !(S.state === "over" && p.lives <= 0) && !blink) drawShip(p);
      for (i = 0; i < S.effects.length; i++) {
        var f = S.effects[i], k = f.t / f.life;
        if (f.kind === "ring") {
          ctx.strokeStyle = f.color; ctx.globalAlpha = Math.max(0, 1 - k); ctx.lineWidth = 3;
          ctx.beginPath(); ctx.arc(f.x, f.y, (10 + k * 34) * f.size, 0, 6.283); ctx.stroke();
        } else {
          ctx.fillStyle = f.color; ctx.globalAlpha = Math.max(0, 1 - k);
          ctx.fillRect(f.x - 1.5, f.y - 1.5, 3, 3);
        }
      }
      ctx.globalAlpha = 1;
    }

    function sync() {
      if (!S) return;
      var p = S.player;
      hudScore.textContent = "Score " + S.score;
      hudLives.textContent = "Lives " + Math.max(0, p.lives);
      hudLevel.textContent = cfg.progression ? "Level " + S.level + ": " + FORMS[S.level] : "Level 1";
      var extras = [];
      if (p.shield > 0) extras.push("shield");
      if (p.weapon > 0) extras.push("twin shot " + Math.ceil(p.weapon / HZ) + "s");
      if (S.boss) extras.push("boss");
      var base = S.state === "idle" ? "Ready" : S.state === "running" ? "Playing" : S.state === "paused" ? "Paused" : S.victory ? "Victory" : "Game over";
      hudState.textContent = extras.length && S.state === "running" ? base + ": " + extras.join(", ") : base;
      overlay.hidden = S.state === "running";
      overTitle.textContent = S.victory ? "The Nexus megaship is down" : S.state === "over" ? (S.overReason === "first-hit" ? "Destroyed by the first hit" : "Game over") : "";
      overTitle.hidden = !overTitle.textContent;
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
    function withRunning(fn) {
      if (!S || S.state === "over") return false;
      var saved = S.state;
      S.state = "running";
      var out = fn();
      if (S.state === "running") S.state = saved;
      sync();
      return out;
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
        if (next.progression != null) cfg.progression = !!next.progression;
        if (next.boss != null) cfg.boss = !!next.boss;
        cfg.bossNow = !!next.bossNow;
        if (next.reset !== false) reset();
        return true;
      },
      start: start,
      pause: pause,
      resume: resume,
      reset: function () { reset(); },
      jumpToBoss: function () {
        if (!cfg.boss) return false;
        api.configure({ level: 3, bossNow: true });
        start();
        return true;
      },
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
        if (!S || S.state === "idle") return false;
        return withRunning(function () { return hitPlayer(source || "test"); });
      },
      dropPowerUp: function (kind) {
        if (!S || ["shield", "weapon", "ship"].indexOf(kind) === -1) return false;
        spawnPowerUp(kind, S.player.x, S.player.y);
        return true;
      },
      hitBoss: function (part, n) {
        if (!S || !S.boss) return false;
        return withRunning(function () {
          if (part === "core") { if (nodesAlive(S.boss) > 0) return false; damageCore(n || 1); return true; }
          var i = parseInt(String(part).replace("node", ""), 10);
          if (!(i >= 0 && i < 4) || !S.boss.nodes[i].alive) return false;
          damageNode(i, n || 1);
          return true;
        });
      },
      shotAt: function (x, y) {
        if (!S) return false;
        return shotHitsBoss({ x: x, y: y, r: 4 });
      },
      view: function () {
        if (!S) return null;
        function pick(o) { return { x: o.x, y: o.y, r: o.r, vx: o.vx || 0, vy: o.vy || 0 }; }
        return {
          player: { x: S.player.x, y: S.player.y, r: S.player.r },
          threats: S.enemyShots.map(pick).concat(S.enemies.map(pick), S.asteroids.map(pick)),
          powerUps: S.powerUps.map(pick), world: { w: world.w, h: world.h }
        };
      },
      bossGeometry: function () {
        if (!S || !S.boss) return null;
        var b = S.boss;
        return {
          centre: [b.x, b.y], scale: b.s,
          nodes: LOGO.nodes.map(function (c) { return bossPoint(b, c[0], c[1]); }),
          plates: LOGO.plates.map(function (t) { return t.map(function (c) { return bossPoint(b, c[0], c[1]); }); })
        };
      },
      state: function () {
        var p = S.player, b = S.boss;
        return {
          id: id, tick: S.tick, state: S.state, pausedBy: S.pausedBy, score: S.score, level: S.level,
          form: cfg.progression ? FORMS[S.level] : FORMS[1], levelUps: S.levelUps.slice(),
          lives: p.lives, defects: { firstHitFatal: cfg.defects.firstHitFatal, randomExplosion: cfg.defects.randomExplosion },
          progression: cfg.progression, bossEnabled: cfg.boss,
          seed: cfg.seed, world: { w: world.w, h: world.h },
          player: { x: p.x, y: p.y, invuln: p.invuln, exploding: p.exploding, shield: p.shield, weapon: p.weapon },
          enemies: S.enemies.length, enemyShots: S.enemyShots.length, asteroids: S.asteroids.length, shots: S.shots.length,
          enemyTypes: S.enemies.map(function (e) { return e.type; }),
          powerUps: S.powerUps.length, collected: S.collected.slice(),
          firstShotTick: S.firstShotTick, firstShotGap: S.firstShotGap,
          explodeTicks: S.explodeTicks.slice(), hitTicks: S.hitTicks.slice(), lifeLossTicks: S.lifeLossTicks.slice(),
          nextExplosion: S.nextExplosion, overReason: S.overReason, victory: S.victory,
          boss: b ? { entered: b.entered, nodesAlive: nodesAlive(b), coreHp: b.coreHp } : null, bossDue: S.bossDue,
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
    constants: {
      HZ: HZ, GRACE_TICKS: GRACE_TICKS, FIRST_SHOT_CLEARANCE: FIRST_SHOT_CLEARANCE, EARLIEST_EXPLOSION: EARLIEST_EXPLOSION,
      EXPLOSION_GAP: EXPLOSION_GAP, INVULNERABLE_TICKS: INVULNERABLE_TICKS, START_LIVES: START_LIVES, MAX_LIVES: MAX_LIVES,
      LEVEL_TICKS: LEVEL_TICKS, BOSS_AFTER: BOSS_AFTER, WEAPON_TICKS: WEAPON_TICKS
    }
  };
})();
