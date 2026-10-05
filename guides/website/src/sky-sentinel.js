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
  var POWER_TICKS = { spread: 600, rapid: 600, missiles: 540, wingman: 900 };
  var DROP_CHANCE = 0.16;
  /* Seven upgrades; a kill's drop is picked from the drops stream with these weights. */
  var DROPS = [["shield", 0.2], ["weapon", 0.18], ["spread", 0.14], ["rapid", 0.14], ["missiles", 0.12], ["wingman", 0.12], ["ship", 0.1]];
  var POWER_LOOK = {
    shield: ["#60a5fa", "Shield"], weapon: ["#f472b6", "Twin"], spread: ["#fbbf24", "Spread"], rapid: ["#a3e635", "Rapid"],
    missiles: ["#fb923c", "Missiles"], wingman: ["#c084fc", "Wingman"], ship: ["#34d399", "Ship"]
  };
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
    canvas.setAttribute("role", "application");
    canvas.setAttribute("aria-roledescription", "game");
    canvas.setAttribute("aria-label", "Sky Sentinel arena");
    canvas.tabIndex = 0;
    var overlay = el("div", "ss-overlay");
    var overTitle = el("p", "ss-over-title");
    var startBtn = el("button", "ss-start", "Start game");
    startBtn.type = "button";
    var hint = el("p", "ss-hint", "Arrows or WASD move, Space or click fires, Escape pauses.");
    hint.id = "ss-hint-" + id;
    canvas.setAttribute("aria-describedby", hint.id);
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
    function arenaCap() { return Math.max(260, (window.innerHeight || 800) - 250); }
    function chooseWorld() {
      /* A hidden stage measures 0 px, so fall back to the viewport before guessing landscape. */
      var w = host.clientWidth || window.innerWidth || 960;
      if (w < 600) { world = { w: 720, h: 960 }; return; }
      /* Landscape: 600 units tall; as wide as the arena's shape, so it fills the frame edge to edge. */
      var cssH = Math.min(w * 600 / 960, arenaCap());
      world = { w: Math.max(960, Math.min(1500, Math.round(600 * w / cssH))), h: 600 };
    }
    function fit() {
      if (S && S.state === "idle") {
        var old = world;
        chooseWorld();
        if (world.w !== old.w || world.h !== old.h) { world = old; reset(); return; }
      }
      var cssW = Math.max(240, stage.clientWidth || host.clientWidth || 960);
      var cssH = cssW * world.h / world.w;
      if (cssH > arenaCap()) cssH = arenaCap();
      var dpr = Math.min(window.devicePixelRatio || 1, 3);
      canvas.style.height = Math.round(cssH) + "px";
      canvas.width = Math.round(cssW * dpr);
      canvas.height = Math.round(cssH * dpr);
      draw();
    }

    /* ---------- simulation */
    function reset() {
      var before = world.w, beforeH = world.h;
      chooseWorld();
      var reshaped = world.w !== before || world.h !== beforeH;
      var r = streams(cfg.seed);
      var level = cfg.progression ? Math.max(1, Math.min(3, cfg.level)) : 1;
      S = {
        rng: r, tick: 0, state: "idle", pausedBy: null, score: 0, level: level, levelTicks: 0,
        player: { x: world.w / 2, y: world.h - 70, r: 18, lives: START_LIVES, invuln: 0, exploding: 0, cooldown: 0, shield: 0, weapon: 0,
                  spread: 0, rapid: 0, missiles: 0, wingman: 0, missileIn: 0, wingIn: 0 },
        enemies: [], enemyShots: [], shots: [], asteroids: [], powerUps: [], effects: [],
        spawnIn: 50, rockIn: 240, firstShotTick: null, firstShotGap: null, firstHitTaken: false,
        nextExplosion: firstExplosion(r.defects), explodeTicks: [], hitTicks: [], lifeLossTicks: [],
        collected: [], levelUps: [], boss: null, bossDue: cfg.boss && level === 3 ? (cfg.bossNow ? BOSS_AFTER_JUMP : BOSS_AFTER) : null,
        overReason: null, victory: false, banner: null
      };
      acc = 0;
      sync();
      if (reshaped) fit(); else draw();
    }

    /* Four ship classes, each with its own weapon: drones fire fast aimed bolts, weavers lob
       wavering plasma orbs, lancers charge then fire a laser beam (telegraphed), and bombers
       drop mines that burst into a ring of bolts. */
    var ENEMY = {
      drone: { r: 16, hp: 1, score: 100 },
      weaver: { r: 16, hp: 1, score: 150 },
      lancer: { r: 20, hp: 3, score: 250 },
      bomber: { r: 24, hp: 4, score: 400 }
    };
    function pickType(rng) {
      var x = rng();
      if (!cfg.progression || S.level === 1) return x < 0.7 ? "drone" : "weaver";
      if (S.level === 2) return x < 0.45 ? "drone" : x < 0.8 ? "weaver" : "lancer";
      return x < 0.3 ? "drone" : x < 0.58 ? "weaver" : x < 0.82 ? "lancer" : "bomber";
    }
    function spawnEnemy() {
      var rng = S.rng.spawn;
      var type = pickType(rng);
      var spec = ENEMY[type];
      var edge = spec.r + 16;
      S.enemies.push({
        type: type, x: edge + rng() * (world.w - 2 * edge), y: -24, r: spec.r,
        vx: (rng() - 0.5) * 1.6, vy: (type === "lancer" ? 0.8 : type === "bomber" ? 0.55 : 1.1) + rng() * (type === "bomber" ? 0.4 : 1.1),
        phase: rng() * Math.PI * 2, hp: spec.hp, charge: 0,
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
    function enemyShot(x, y, vx, vy, kind, extra) {
      var o = { x: x, y: y, r: kind === "orb" ? 7 : kind === "mine" ? 9 : 5, vx: vx, vy: vy, kind: kind || "bolt", t: 0 };
      if (extra) for (var k in extra) o[k] = extra[k];
      S.enemyShots.push(o);
      if (S.firstShotTick === null) { S.firstShotTick = S.tick; S.firstShotGap = S.player.y - y; }
      return o;
    }
    function enemyFire(e) {
      var p = S.player, aim = Math.max(-2.4, Math.min(2.4, (p.x - e.x) / 110));
      if (e.type === "drone") enemyShot(e.x, e.y + e.r, aim * 0.7, 6.2, "bolt");
      else if (e.type === "weaver") enemyShot(e.x, e.y + e.r, aim * 0.5, 3.6, "orb", { wave: e.phase });
      else if (e.type === "lancer") { e.charge = 50; return 200 + Math.floor(S.rng.spawn() * 90); }
      else enemyShot(e.x, e.y + e.r, 0, 1.7, "mine", { fuse: 80 });
      return (e.type === "bomber" ? 210 : 90) + Math.floor(S.rng.spawn() * 90);
    }
    function moveEnemyShots() {
      var out = [];
      for (var i = 0; i < S.enemyShots.length; i++) {
        var o = S.enemyShots[i];
        o.t += 1;
        if (o.kind === "orb") { o.wave += 0.12; o.x += o.vx + Math.sin(o.wave) * 1.8; o.y += o.vy; }
        else if (o.kind === "beam") { o.life -= 1; if (o.owner && S.enemies.indexOf(o.owner) !== -1) { o.x = o.owner.x; o.y = o.owner.y + o.owner.r; } if (o.life <= 0) continue; }
        else if (o.kind === "mine") {
          o.x += o.vx; o.y += o.vy; o.fuse -= 1;
          if (o.fuse <= 0) {
            for (var k = 0; k < 6; k++) { var a = k / 6 * 6.283 + 0.52; S.enemyShots.push({ x: o.x, y: o.y, r: 4, vx: Math.cos(a) * 2.6, vy: Math.sin(a) * 2.6, kind: "bolt", t: 0 }); }
            boom(o.x, o.y, 0.7, "#f87171");
            continue;
          }
        } else { o.x += o.vx; o.y += o.vy; }
        out.push(o);
      }
      S.enemyShots = out;
    }
    function shotHitsPlayer(o, p) {
      if (o.kind === "beam") return o.life <= o.span - 6 && Math.abs(p.x - o.x) < 10 + p.r * 0.5 && p.y > o.y;
      return overlaps(o, p, -4);
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
      S.banner = { text: "Level " + S.level + ": the " + FORMS[S.level], t: 150 };
      emit("levelUp", { level: S.level, form: FORMS[S.level], tick: S.tick });
      say("Level " + S.level + ". The ship becomes the " + FORMS[S.level] + ".");
      if (S.level === 3 && cfg.boss) S.bossDue = BOSS_AFTER;
    }
    function collect(pu) {
      var p = S.player;
      S.collected.push({ kind: pu.kind, tick: S.tick });
      ring(pu.x, pu.y, (POWER_LOOK[pu.kind] || POWER_LOOK.ship)[0]);
      if (pu.kind === "shield") { p.shield = 1; say("Shield up: it absorbs one hit."); }
      else if (pu.kind === "weapon") { p.weapon = WEAPON_TICKS; say("Twin shot for 10 seconds."); }
      else if (pu.kind === "ship") { p.lives = Math.min(MAX_LIVES, p.lives + 1); say("Extra ship. Lives: " + p.lives + "."); }
      else if (POWER_TICKS[pu.kind]) { p[pu.kind] = POWER_TICKS[pu.kind]; say(POWER_LOOK[pu.kind][1] + " for " + Math.round(POWER_TICKS[pu.kind] / HZ) + " seconds."); }
      emit("powerUp", { kind: pu.kind, tick: S.tick });
    }
    function fire() {
      var p = S.player, form = cfg.progression ? S.level : 1;
      var twin = p.weapon > 0 || form === 3;
      var spread = p.spread > 0 || (form === 3 && p.weapon > 0);
      if (spread) {
        S.shots.push({ x: p.x, y: p.y - p.r, r: 4, vx: 0 });
        S.shots.push({ x: p.x - 10, y: p.y - p.r + 4, r: 4, vx: -2.2 });
        S.shots.push({ x: p.x + 10, y: p.y - p.r + 4, r: 4, vx: 2.2 });
        if (twin && p.spread > 0) { S.shots.push({ x: p.x - 16, y: p.y - p.r + 8, r: 4, vx: -4 }); S.shots.push({ x: p.x + 16, y: p.y - p.r + 8, r: 4, vx: 4 }); }
      } else if (twin) {
        S.shots.push({ x: p.x - 9, y: p.y - p.r + 4, r: 4, vx: 0 });
        S.shots.push({ x: p.x + 9, y: p.y - p.r + 4, r: 4, vx: 0 });
      } else {
        S.shots.push({ x: p.x, y: p.y - p.r, r: 4, vx: 0 });
      }
      p.cooldown = Math.max(4, Math.round((form >= 2 ? 8 : 10) * (p.rapid > 0 ? 0.5 : 1)));
    }
    /* Homing missiles and the wingman fire on their own while they last. */
    function autoWeapons() {
      var p = S.player;
      if (p.exploding > 0) return;
      if (p.missiles > 0 && --p.missileIn <= 0) {
        S.shots.push({ x: p.x - 14, y: p.y, r: 5, vx: -2, vy: -6, kind: "missile" });
        S.shots.push({ x: p.x + 14, y: p.y, r: 5, vx: 2, vy: -6, kind: "missile" });
        p.missileIn = 45;
      }
      if (p.wingman > 0 && --p.wingIn <= 0) {
        S.shots.push({ x: p.x - 42, y: p.y - 6, r: 4, vx: 0 });
        S.shots.push({ x: p.x + 42, y: p.y - 6, r: 4, vx: 0 });
        p.wingIn = 16;
      }
    }
    function moveShots() {
      for (var i = 0; i < S.shots.length; i++) {
        var sh = S.shots[i];
        if (sh.kind !== "missile") { sh.y -= 13; sh.x += sh.vx || 0; continue; }
        var target = null, best = 1e9;
        for (var j = 0; j < S.enemies.length; j++) { var d = Math.hypot(S.enemies[j].x - sh.x, S.enemies[j].y - sh.y); if (d < best && S.enemies[j].y < sh.y) { best = d; target = S.enemies[j]; } }
        if (target) { sh.vx += Math.max(-0.6, Math.min(0.6, (target.x - sh.x) * 0.02)); sh.vy += Math.max(-0.6, Math.min(0.6, (target.y - sh.y) * 0.02)); }
        var v = Math.hypot(sh.vx, sh.vy) || 1;
        sh.vx = sh.vx / v * 9; sh.vy = sh.vy / v * 9;
        sh.x += sh.vx; sh.y += sh.vy;
      }
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
        /* Clamp by the drawn wingspan, not the hit radius, so the ship never leaves the frame. */
        var span = PLAYER[cfg.progression ? S.level : 1].w + 2;
        p.x = Math.max(span, Math.min(world.w - span, p.x + dx * 7));
        p.y = Math.max(world.h * 0.55, Math.min(world.h - p.r - 6, p.y + dy * 6));
        if (p.invuln > 0) p.invuln -= 1;
        if (p.cooldown > 0) p.cooldown -= 1;
        if (held.fire && p.cooldown === 0) fire();
      }
      if (p.weapon > 0) p.weapon -= 1;
      ['spread', 'rapid', 'missiles', 'wingman'].forEach(function (k) { if (p[k] > 0) p[k] -= 1; });
      if (S.state === "running") autoWeapons();
      if (S.banner && --S.banner.t <= 0) S.banner = null;

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
      moveShots();
      for (i = 0; i < S.enemies.length; i++) {
        var e = S.enemies[i];
        e.phase += e.type === "weaver" ? 0.07 : 0.04;
        var sway = e.type === "weaver" ? Math.sin(e.phase) * 2.6 : Math.sin(e.phase) * 0.9;
        if (e.x + e.vx + sway < e.r || e.x + e.vx + sway > world.w - e.r) e.vx = -e.vx;
        e.x = Math.max(e.r, Math.min(world.w - e.r, e.x + e.vx + sway));
        e.y += e.charge > 0 ? e.vy * 0.25 : e.vy;
        /* A lancer's charge is its tell: the beam fires when the charge runs out. */
        if (e.charge > 0 && --e.charge === 0) enemyShot(e.x, e.y + e.r, 0, 0, "beam", { life: 40, span: 40, owner: e });
        e.fireIn -= 1;
        if (e.fireIn <= 0 && e.charge === 0) e.fireIn = enemyMayFire(e) ? enemyFire(e) : 12;
      }
      moveEnemyShots();
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
              boom(en.x, en.y, en.type === "bomber" ? 1.6 : 1, { drone: "#f472b6", weaver: "#c084fc", lancer: "#fb923c", bomber: "#4ade80" }[en.type]);
              S.enemies.splice(j, 1);
              S.score += ENEMY[en.type].score;
              if (cfg.progression && S.rng.drops() < DROP_CHANCE) {
                var k = S.rng.drops(), acc2 = 0, kind = "ship";
                for (var d = 0; d < DROPS.length; d++) { acc2 += DROPS[d][1]; if (k < acc2) { kind = DROPS[d][0]; break; } }
                spawnPowerUp(kind, en.x, en.y);
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
        if (used || s.y < -10 || s.y > world.h + 10 || s.x < -10 || s.x > world.w + 10) S.shots.splice(i, 1);
      }

      /* collisions: the player */
      if (S.state === "running" && p.exploding === 0) {
        for (i = S.enemyShots.length - 1; i >= 0; i--) {
          if (shotHitsPlayer(S.enemyShots[i], p)) { if (S.enemyShots[i].kind !== "beam") S.enemyShots.splice(i, 1); if (hitPlayer("shot")) break; }
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
      S.enemyShots = S.enemyShots.filter(function (o) { return o.kind === "beam" || (o.y < world.h + 20 && o.y > -40 && o.x > -20 && o.x < world.w + 20); });
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

    /* ---------- ships: shaded hulls with a lit left edge, a shadowed right edge, glass, panel
       lines, wingtip lights, and engine glow, so flat paths read as solid craft. */
    function path(pts) {
      ctx.beginPath();
      ctx.moveTo(pts[0][0], pts[0][1]);
      for (var k = 1; k < pts.length; k++) ctx.lineTo(pts[k][0], pts[k][1]);
      ctx.closePath();
    }
    function mirror(half) {
      var out = half.slice();
      for (var k = half.length - 1; k >= 0; k--) if (half[k][0] !== 0) out.push([-half[k][0], half[k][1]]);
      return out;
    }
    function hull(pts, w, light, mid, dark, edge) {
      var g = ctx.createLinearGradient(-w, 0, w, 0);
      g.addColorStop(0, light); g.addColorStop(0.45, mid); g.addColorStop(0.55, mid); g.addColorStop(1, dark);
      path(pts);
      ctx.fillStyle = g; ctx.fill();
      ctx.lineWidth = 1.3; ctx.strokeStyle = edge; ctx.stroke();
      /* top light: a soft vertical sheen down the spine */
      var sheen = ctx.createLinearGradient(0, -w, 0, w);
      sheen.addColorStop(0, "rgba(255,255,255,0.32)"); sheen.addColorStop(0.5, "rgba(255,255,255,0.04)"); sheen.addColorStop(1, "rgba(0,0,0,0.25)");
      path(pts); ctx.fillStyle = sheen; ctx.fill();
    }
    function glass(x, y, rx, ry, tint) {
      var g = ctx.createRadialGradient(x - rx * 0.3, y - ry * 0.4, 1, x, y, Math.max(rx, ry) * 1.2);
      g.addColorStop(0, "#e0fbff"); g.addColorStop(0.35, tint); g.addColorStop(1, "#06202b");
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, 6.283); ctx.fill();
      ctx.fillStyle = "rgba(255,255,255,0.75)";
      ctx.beginPath(); ctx.ellipse(x - rx * 0.35, y - ry * 0.35, rx * 0.25, ry * 0.18, -0.5, 0, 6.283); ctx.fill();
    }
    function engine(x, y, w, len, hot) {
      ctx.fillStyle = "#0b1d24"; ctx.fillRect(x - w / 2, y - 3, w, 6);
      var flick = REDUCED ? 1 : 0.82 + 0.18 * Math.sin(S.tick * 0.9 + x);
      var g = ctx.createLinearGradient(0, y, 0, y + len * flick);
      g.addColorStop(0, "rgba(255,255,255,0.95)"); g.addColorStop(0.25, hot); g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(x - w / 2, y + 2); ctx.quadraticCurveTo(x, y + len * 1.25 * flick, x + w / 2, y + 2); ctx.closePath(); ctx.fill();
      if (!REDUCED) { ctx.shadowColor = hot; ctx.shadowBlur = 14; ctx.fillStyle = hot; ctx.fillRect(x - w / 2 + 1, y, w - 2, 2); ctx.shadowBlur = 0; }
    }
    function lights(x, y) {
      var on = REDUCED || Math.floor(S.tick / 20) % 2 === 0;
      ctx.fillStyle = on ? "#f87171" : "#4c1d1d"; ctx.beginPath(); ctx.arc(-x, y, 2, 0, 6.283); ctx.fill();
      ctx.fillStyle = on ? "#4ade80" : "#14391f"; ctx.beginPath(); ctx.arc(x, y, 2, 0, 6.283); ctx.fill();
    }
    function panel(lines) {
      ctx.strokeStyle = "rgba(4,33,43,0.55)"; ctx.lineWidth = 1;
      ctx.beginPath();
      lines.forEach(function (l) { ctx.moveTo(l[0], l[1]); ctx.lineTo(l[2], l[3]); ctx.moveTo(-l[0], l[1]); ctx.lineTo(-l[2], l[3]); });
      ctx.stroke();
    }

    var PLAYER = {
      1: { half: [[0, -26], [6, -12], [8, 0], [24, 10], [24, 15], [9, 13], [6, 19], [0, 16]], w: 24,
           panel: [[4, -8, 6, 10], [12, 6, 22, 12]], engines: [[0, 16, 8]], glass: [0, -8, 4, 8], tips: [24, 12] },
      2: { half: [[0, -32], [5, -22], [9, -8], [14, -2], [30, 8], [32, 16], [16, 15], [12, 22], [5, 20], [0, 22]], w: 32,
           panel: [[6, -14, 8, 4], [14, 2, 28, 12], [9, 10, 12, 20]], engines: [[-7, 21, 7], [7, 21, 7]], glass: [0, -12, 4.5, 10], tips: [31, 13] },
      3: { half: [[0, -40], [6, -30], [10, -14], [18, -6], [38, 2], [42, 12], [40, 18], [22, 16], [20, 24], [12, 26], [6, 22], [0, 26]], w: 42,
           panel: [[7, -22, 9, -2], [16, -2, 36, 10], [14, 12, 20, 22], [4, 6, 9, 18]], engines: [[-15, 25, 8], [0, 26, 8], [15, 25, 8]], glass: [0, -18, 5.5, 12], tips: [41, 14] }
    };
    function drawShip(p) {
      var form = cfg.progression ? S.level : 1, spec = PLAYER[form];
      ctx.save();
      ctx.translate(p.x, p.y);
      spec.engines.forEach(function (e) { engine(e[0], e[1], e[2], 26 + form * 4, "#22d3ee"); });
      hull(mirror(spec.half), spec.w, "#e8fbff", "#67c9db", "#0c4655", "#bff4fb");
      panel(spec.panel);
      if (form >= 2) {
        /* wing pods: darker armour plates with a cyan running light */
        ctx.fillStyle = "rgba(7,40,50,0.65)";
        [-1, 1].forEach(function (sgn) { ctx.beginPath(); ctx.ellipse(sgn * spec.w * 0.55, 8, 4, 9, 0, 0, 6.283); ctx.fill(); });
        ctx.fillStyle = "#67e8f9";
        [-1, 1].forEach(function (sgn) { ctx.fillRect(sgn * spec.w * 0.55 - 1, 2, 2, 8); });
      }
      glass(spec.glass[0], spec.glass[1], spec.glass[2], spec.glass[3], "#38bdf8");
      lights(spec.tips[0], spec.tips[1]);
      if (p.shield > 0) {
        var r = spec.w + 10 + (REDUCED ? 0 : Math.sin(S.tick * 0.15) * 2);
        var sg = ctx.createRadialGradient(0, 0, r * 0.6, 0, 0, r);
        sg.addColorStop(0, "rgba(96,165,250,0)"); sg.addColorStop(1, "rgba(96,165,250,0.35)");
        ctx.fillStyle = sg; ctx.beginPath(); ctx.arc(0, 0, r, 0, 6.283); ctx.fill();
        ctx.strokeStyle = "rgba(147,197,253,0.9)"; ctx.lineWidth = 2; ctx.stroke();
      }
      ctx.restore();
      if (p.wingman > 0) [-42, 42].forEach(function (dx) { drawWingman(p.x + dx, p.y + 4); });
    }
    function drawWingman(x, y) {
      ctx.save(); ctx.translate(x, y);
      engine(0, 9, 5, 16, "#c084fc");
      hull([[0, -12], [5, -2], [12, 6], [4, 8], [0, 10], [-4, 8], [-12, 6], [-5, -2]], 12, "#f5e8ff", "#b48be6", "#4a2a72", "#e9d5ff");
      glass(0, -3, 2.5, 4, "#a78bfa");
      ctx.restore();
    }

    function drawEnemy(e) {
      ctx.save();
      ctx.translate(e.x, e.y);
      if (e.type === "drone") {
        /* a saucer: metallic disc, glass dome, a ring of turning lights */
        engine(0, 8, 8, 12, "#f472b6");
        var g = ctx.createLinearGradient(-e.r, 0, e.r, 0);
        g.addColorStop(0, "#fbcfe8"); g.addColorStop(0.5, "#db2777"); g.addColorStop(1, "#500724");
        ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(0, 2, e.r, e.r * 0.45, 0, 0, 6.283); ctx.fill();
        ctx.strokeStyle = "#fce7f3"; ctx.lineWidth = 1; ctx.stroke();
        glass(0, -3, e.r * 0.45, e.r * 0.4, "#f472b6");
        for (var k = 0; k < 5; k++) {
          var a = (S.tick * 0.06 + k * 1.2566) % 6.283;
          ctx.fillStyle = Math.cos(a) > 0 ? "#fde68a" : "rgba(253,230,138,0.3)";
          ctx.beginPath(); ctx.arc(Math.sin(a) * e.r * 0.8, 4, 1.8, 0, 6.283); ctx.fill();
        }
      } else if (e.type === "weaver") {
        /* a living crescent: ribbed shell around a glowing core */
        ctx.rotate(Math.sin(e.phase) * 0.35);
        var core = ctx.createRadialGradient(0, 2, 1, 0, 2, e.r * 0.6);
        core.addColorStop(0, "#fdf4ff"); core.addColorStop(0.5, "#d946ef"); core.addColorStop(1, "rgba(217,70,239,0)");
        ctx.fillStyle = core; ctx.beginPath(); ctx.arc(0, 2, e.r * 0.65, 0, 6.283); ctx.fill();
        var sg = ctx.createLinearGradient(-e.r, 0, e.r, 0);
        sg.addColorStop(0, "#e9d5ff"); sg.addColorStop(0.5, "#7e22ce"); sg.addColorStop(1, "#2e1065");
        ctx.fillStyle = sg;
        ctx.beginPath(); ctx.arc(0, 0, e.r, 0.15, Math.PI - 0.15); ctx.arc(0, -6, e.r * 0.78, Math.PI - 0.35, 0.35, true); ctx.closePath(); ctx.fill();
        ctx.strokeStyle = "rgba(46,16,101,0.7)"; ctx.lineWidth = 1.2;
        for (var r2 = -2; r2 <= 2; r2++) { ctx.beginPath(); ctx.moveTo(r2 * 5, e.r * 0.25); ctx.lineTo(r2 * 6.5, e.r * 0.9); ctx.stroke(); }
      } else if (e.type === "lancer") {
        /* a heavy gunship: armoured hull, twin pods, a cannon that glows while charging */
        engine(-9, -e.r + 2, 6, 12, "#fb923c"); engine(9, -e.r + 2, 6, 12, "#fb923c");
        ctx.scale(1, -1);
        hull(mirror([[0, -24], [6, -12], [10, -4], [22, 0], [22, 8], [10, 10], [6, 18], [0, 16]]), 22, "#fed7aa", "#c2410c", "#431407", "#ffedd5");
        ctx.scale(1, -1);
        var heat = e.charge > 0 ? 1 - e.charge / 50 : 0.15;
        var cg = ctx.createRadialGradient(0, 22, 1, 0, 22, 8 + heat * 10);
        cg.addColorStop(0, "rgba(255,247,237," + (0.5 + heat * 0.5) + ")"); cg.addColorStop(1, "rgba(251,146,60,0)");
        ctx.fillStyle = cg; ctx.beginPath(); ctx.arc(0, 22, 8 + heat * 10, 0, 6.283); ctx.fill();
        glass(0, -6, 3.5, 6, "#fdba74");
      } else {
        /* a bomber: a wide flying wing with an open bay */
        engine(-14, -14, 7, 14, "#4ade80"); engine(14, -14, 7, 14, "#4ade80");
        ctx.scale(1, -1);
        hull(mirror([[0, -18], [10, -12], [30, -2], [34, 6], [16, 8], [8, 14], [0, 12]]), 34, "#d9f99d", "#15803d", "#052e16", "#dcfce7");
        ctx.scale(1, -1);
        ctx.fillStyle = "#052e16"; ctx.fillRect(-7, 2, 14, 7);
        ctx.fillStyle = REDUCED || Math.floor(S.tick / 15) % 2 ? "#f87171" : "#7f1d1d"; ctx.fillRect(-3, 4, 6, 3);
        glass(0, -8, 4, 4, "#86efac");
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
      var look = POWER_LOOK[pu.kind] || POWER_LOOK.ship, color = look[0];
      var bob = REDUCED ? 0 : Math.sin(pu.t * 0.12) * 2;
      ctx.save();
      ctx.translate(pu.x, pu.y + bob);
      /* a glass capsule with the upgrade's colour, icon, and initial */
      var g = ctx.createRadialGradient(-4, -5, 1, 0, 0, pu.r + 2);
      g.addColorStop(0, "rgba(255,255,255,0.55)"); g.addColorStop(0.4, "rgba(2,6,23,0.75)"); g.addColorStop(1, "rgba(2,6,23,0.9)");
      ctx.fillStyle = g;
      if (!REDUCED) { ctx.shadowColor = color; ctx.shadowBlur = 14; }
      ctx.strokeStyle = color; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(0, 0, pu.r, 0, 6.283); ctx.fill(); ctx.stroke();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 2;
      if (pu.kind === "shield") { ctx.beginPath(); ctx.moveTo(0, -7); ctx.lineTo(6, -4); ctx.lineTo(5, 3); ctx.lineTo(0, 7); ctx.lineTo(-5, 3); ctx.lineTo(-6, -4); ctx.closePath(); ctx.stroke(); }
      else if (pu.kind === "weapon") { ctx.fillRect(-5, -6, 3, 12); ctx.fillRect(2, -6, 3, 12); }
      else if (pu.kind === "spread") { [-0.5, 0, 0.5].forEach(function (a) { ctx.save(); ctx.rotate(a); ctx.fillRect(-1.2, -8, 2.4, 9); ctx.restore(); }); }
      else if (pu.kind === "rapid") { ctx.beginPath(); ctx.moveTo(2, -8); ctx.lineTo(-4, 1); ctx.lineTo(0, 1); ctx.lineTo(-2, 8); ctx.lineTo(4, -1); ctx.lineTo(0, -1); ctx.closePath(); ctx.fill(); }
      else if (pu.kind === "missiles") { ctx.beginPath(); ctx.moveTo(0, -8); ctx.lineTo(3, -3); ctx.lineTo(3, 5); ctx.lineTo(5, 8); ctx.lineTo(-5, 8); ctx.lineTo(-3, 5); ctx.lineTo(-3, -3); ctx.closePath(); ctx.fill(); }
      else if (pu.kind === "wingman") { ctx.beginPath(); ctx.moveTo(0, -6); ctx.lineTo(4, 4); ctx.lineTo(0, 2); ctx.lineTo(-4, 4); ctx.closePath(); ctx.fill(); ctx.fillRect(-9, 0, 3, 5); ctx.fillRect(6, 0, 3, 5); }
      else { ctx.beginPath(); ctx.moveTo(0, -7); ctx.lineTo(6, 6); ctx.lineTo(-6, 6); ctx.closePath(); ctx.fill(); ctx.fillRect(-1, -2, 2, 2); }
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
      var sky = ctx.createLinearGradient(0, 0, 0, ch);
      sky.addColorStop(0, "#030a10"); sky.addColorStop(1, "#071a22");
      ctx.fillStyle = sky;
      ctx.fillRect(0, 0, cw, ch);
      ctx.setTransform(scale, 0, 0, scale, ox, oy);
      drawBackground();
      var i;
      for (i = 0; i < S.asteroids.length; i++) drawRock(S.asteroids[i]);
      if (S.boss) drawBoss(S.boss);
      for (i = 0; i < S.enemies.length; i++) drawEnemy(S.enemies[i]);
      for (i = 0; i < S.powerUps.length; i++) drawPowerUp(S.powerUps[i]);
      for (i = 0; i < S.enemyShots.length; i++) drawEnemyShot(S.enemyShots[i]);
      for (i = 0; i < S.shots.length; i++) drawShot(S.shots[i]);
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
      drawHud();
    }

    function drawEnemyShot(o) {
      if (o.kind === "beam") {
        var k = o.life / o.span, w = 6 + 8 * Math.min(1, (o.span - o.life) / 6);
        var g = ctx.createLinearGradient(o.x - w, 0, o.x + w, 0);
        g.addColorStop(0, "rgba(251,146,60,0)"); g.addColorStop(0.35, "rgba(251,146,60," + (0.6 * k + 0.3) + ")"); g.addColorStop(0.5, "rgba(255,247,237,0.95)"); g.addColorStop(0.65, "rgba(251,146,60," + (0.6 * k + 0.3) + ")"); g.addColorStop(1, "rgba(251,146,60,0)");
        ctx.fillStyle = g; ctx.fillRect(o.x - w, o.y, w * 2, world.h - o.y);
        return;
      }
      ctx.save();
      ctx.translate(o.x, o.y);
      if (o.kind === "orb") {
        var r = o.r + (REDUCED ? 0 : Math.sin(o.t * 0.3) * 1.5);
        var og = ctx.createRadialGradient(0, 0, 1, 0, 0, r * 1.8);
        og.addColorStop(0, "#fdf4ff"); og.addColorStop(0.4, "#d946ef"); og.addColorStop(1, "rgba(217,70,239,0)");
        ctx.fillStyle = og; ctx.beginPath(); ctx.arc(0, 0, r * 1.8, 0, 6.283); ctx.fill();
      } else if (o.kind === "mine") {
        ctx.rotate(o.t * 0.05);
        ctx.fillStyle = "#1f2937"; ctx.strokeStyle = "#f87171"; ctx.lineWidth = 1.5;
        ctx.beginPath(); for (var k2 = 0; k2 < 8; k2++) { var a = k2 / 8 * 6.283; ctx.moveTo(Math.cos(a) * 6, Math.sin(a) * 6); ctx.lineTo(Math.cos(a) * 12, Math.sin(a) * 12); } ctx.stroke();
        ctx.beginPath(); ctx.arc(0, 0, 7, 0, 6.283); ctx.fill(); ctx.stroke();
        ctx.fillStyle = o.fuse < 25 && Math.floor(o.t / 4) % 2 ? "#fde68a" : "#ef4444"; ctx.beginPath(); ctx.arc(0, 0, 2.6, 0, 6.283); ctx.fill();
      } else {
        ctx.rotate(Math.atan2(o.vy, o.vx) - Math.PI / 2);
        if (!REDUCED) { ctx.shadowColor = "#f87171"; ctx.shadowBlur = 10; }
        var bg = ctx.createLinearGradient(0, -10, 0, 6);
        bg.addColorStop(0, "rgba(248,113,113,0)"); bg.addColorStop(1, "#fecaca");
        ctx.fillStyle = bg; ctx.beginPath(); ctx.ellipse(0, -2, 3, 9, 0, 0, 6.283); ctx.fill();
        ctx.shadowBlur = 0;
      }
      ctx.restore();
    }
    function drawShot(sh) {
      ctx.save();
      ctx.translate(sh.x, sh.y);
      if (sh.kind === "missile") {
        ctx.rotate(Math.atan2(sh.vy, sh.vx) + Math.PI / 2);
        engine(0, 6, 3, 10, "#fb923c");
        ctx.fillStyle = "#e5e7eb"; ctx.beginPath(); ctx.moveTo(0, -7); ctx.lineTo(2.5, -2); ctx.lineTo(2.5, 6); ctx.lineTo(-2.5, 6); ctx.lineTo(-2.5, -2); ctx.closePath(); ctx.fill();
        ctx.fillStyle = "#ef4444"; ctx.fillRect(-2.5, -3, 5, 2);
      } else {
        if (!REDUCED) { ctx.shadowColor = "#22d3ee"; ctx.shadowBlur = 12; }
        var g = ctx.createLinearGradient(0, -12, 0, 8);
        g.addColorStop(0, "#ffffff"); g.addColorStop(0.5, "#a5f3fc"); g.addColorStop(1, "rgba(34,211,238,0)");
        ctx.fillStyle = g; ctx.beginPath(); ctx.ellipse(0, -2, 2.6, 10, Math.atan2(sh.vx || 0, 13), 0, 6.283); ctx.fill();
        ctx.shadowBlur = 0;
      }
      ctx.restore();
    }

    /* ---------- the HUD, drawn in the arena at screen size: lives, score, level and its goal, upgrades */
    var hudFont = null;
    function goal() {
      if (!S) return null;
      if (S.boss) return { text: S.boss.entered ? (nodesAlive(S.boss) ? "Break the " + nodesAlive(S.boss) + " glowing nodes, then the core" : "The core is open: destroy it") : "The Nexus megaship is arriving", k: S.boss.entered ? 1 - nodesAlive(S.boss) / 4 : 0 };
      if (!cfg.progression) return { text: "Survive: " + clock(S.tick), k: null };
      if (S.level < 3) { var need = LEVEL_TICKS[S.level]; return { text: "Survive " + clock(need - S.levelTicks) + " to reach level " + (S.level + 1), k: S.levelTicks / need }; }
      if (cfg.boss && S.bossDue !== null) return { text: "Something big arrives in " + clock(S.bossDue), k: 1 - S.bossDue / BOSS_AFTER };
      return { text: "Final level: survive", k: null };
    }
    function clock(t) { var sec = Math.max(0, Math.ceil(t / HZ)); return Math.floor(sec / 60) + ":" + (sec % 60 < 10 ? "0" : "") + (sec % 60); }
    function drawHud() {
      if (!S) return;
      var dpr = canvas.width / Math.max(1, canvas.clientWidth || canvas.width);
      var W = canvas.width / dpr, H = canvas.height / dpr, small = W < 520;
      if (!hudFont) hudFont = (window.getComputedStyle && getComputedStyle(host).fontFamily) || "system-ui, sans-serif";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var bar = ctx.createLinearGradient(0, 0, 0, small ? 58 : 50);
      bar.addColorStop(0, "rgba(2,8,12,0.88)"); bar.addColorStop(1, "rgba(2,8,12,0)");
      ctx.fillStyle = bar; ctx.fillRect(0, 0, W, small ? 64 : 56);
      var p = S.player;
      /* lives: one small ship per life */
      for (var k = 0; k < Math.max(0, p.lives); k++) {
        ctx.save(); ctx.translate(16 + k * 18, 18); ctx.scale(0.42, 0.42);
        hull(mirror(PLAYER[1].half), 24, "#e8fbff", "#67c9db", "#0c4655", "#bff4fb");
        ctx.restore();
      }
      if (p.shield > 0) { ctx.strokeStyle = "#93c5fd"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(16 + Math.max(0, p.lives) * 18 + 4, 18, 7, 0, 6.283); ctx.stroke(); }
      ctx.textBaseline = "middle";
      ctx.font = "800 " + (small ? 13 : 15) + "px " + hudFont;
      ctx.fillStyle = "#e6f6f8"; ctx.textAlign = "right";
      ctx.fillText("Score " + S.score.toLocaleString("en-US"), W - 14, 18);
      /* level, its goal, and progress toward it */
      var g = goal();
      ctx.textAlign = "center";
      ctx.font = "800 " + (small ? 12 : 13) + "px " + hudFont;
      ctx.fillStyle = "#5eead4";
      var title = S.boss ? "Final boss" : cfg.progression ? "Level " + S.level + ": " + FORMS[S.level] : "Level 1";
      ctx.fillText(title.toUpperCase(), W / 2, small ? 40 : 14);
      if (g) {
        ctx.font = "600 " + (small ? 11.5 : 12.5) + "px " + hudFont;
        ctx.fillStyle = "#c7dde2";
        ctx.fillText(g.text, W / 2, small ? 54 : 30);
        if (g.k !== null) {
          var bw = Math.min(260, W * 0.36), bx = W / 2 - bw / 2, by = small ? 62 : 40;
          ctx.fillStyle = "rgba(148,163,184,0.25)"; ctx.fillRect(bx, by, bw, 4);
          ctx.fillStyle = S.boss ? "#f2feff" : "#2dd4bf"; ctx.fillRect(bx, by, bw * Math.max(0, Math.min(1, g.k)), 4);
        }
      }
      /* active upgrades with what is left of each */
      var chips = [];
      if (p.weapon > 0) chips.push(["weapon", p.weapon / WEAPON_TICKS]);
      ["spread", "rapid", "missiles", "wingman"].forEach(function (kk) { if (p[kk] > 0) chips.push([kk, p[kk] / POWER_TICKS[kk]]); });
      ctx.textAlign = "left";
      ctx.font = "700 11.5px " + hudFont;
      chips.forEach(function (c, i) {
        var look = POWER_LOOK[c[0]], x = 12 + i * 92, y = H - 26;
        ctx.fillStyle = "rgba(2,8,12,0.72)"; ctx.fillRect(x, y, 84, 18);
        ctx.fillStyle = look[0]; ctx.fillRect(x, y + 15, 84 * c[1], 3);
        ctx.fillText(look[1], x + 6, y + 8);
      });
      /* a level-up or event banner */
      if (S.banner) {
        var a = Math.min(1, S.banner.t / 30);
        ctx.globalAlpha = a;
        ctx.font = "900 " + (small ? 18 : 24) + "px " + hudFont;
        ctx.textAlign = "center";
        ctx.fillStyle = "#f2feff";
        if (!REDUCED) { ctx.shadowColor = "#22d3ee"; ctx.shadowBlur = 18; }
        ctx.fillText(S.banner.text.toUpperCase(), W / 2, H * 0.4);
        ctx.shadowBlur = 0; ctx.globalAlpha = 1;
      }
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
      startBtn.textContent = S.state === "paused" ? "Resume" : S.state === "over" ? "Play again" : "Start game";
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
      wake();
      canvas.focus({ preventScroll: true });
      /* The banner and callout can push the arena below the fold; bring the whole game into view. */
      if (host.offsetParent !== null && host.scrollIntoView) host.scrollIntoView({ block: "nearest", behavior: REDUCED ? "auto" : "smooth" });
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
      wake();
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
      running: function () { return !!S && S.state === "running"; },
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
        if (!S || !Object.prototype.hasOwnProperty.call(POWER_LOOK, kind)) return false;
        spawnPowerUp(kind, S.player.x, S.player.y);
        return true;
      },
      spawn: function (type, x, y) {
        if (!S || !ENEMY[type]) return false;
        var spec = ENEMY[type];
        S.enemies.push({ type: type, x: x, y: y, r: spec.r, vx: 0, vy: 0, phase: 0, hp: spec.hp, charge: 0, fireIn: 1, burst: 0 });
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
        /* A beam, and a lancer charging one, threaten a whole column below the emitter: show it
           as a column of falling points, the way a player reads the glow and the tell. */
        var columns = [];
        function column(x, y0) { for (var y = y0; y < world.h; y += 36) columns.push({ x: x, y: y, r: 14, vx: 0, vy: 8 }); }
        S.enemyShots.forEach(function (o) { if (o.kind === "beam") column(o.x, o.y); });
        S.enemies.forEach(function (e) { if (e.charge > 0) column(e.x, e.y + e.r); });
        return {
          player: { x: S.player.x, y: S.player.y, r: S.player.r },
          threats: S.enemyShots.filter(function (o) { return o.kind !== "beam"; }).map(pick).concat(columns, S.enemies.map(pick), S.asteroids.map(pick)),
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
          player: { x: p.x, y: p.y, invuln: p.invuln, exploding: p.exploding, shield: p.shield, weapon: p.weapon,
            spread: p.spread || 0, rapid: p.rapid || 0, missiles: p.missiles || 0, wingman: p.wingman || 0 },
          shotKinds: S.enemyShots.map(function (o) { return o.kind; }), goal: goal(),
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
  /* The loop asks for a frame only while some game is running, so an idle, paused, or hidden game
     costs a reading tab nothing. start and resume wake it; one pending request at most, so waking
     twice can never start a second loop. */
  var scheduled = false;
  function anyRunning() {
    for (var k in instances) if (instances[k].running()) return true;
    return false;
  }
  function wake() {
    if (scheduled || manual) return;
    scheduled = true;
    window.requestAnimationFrame(loop);
  }
  function loop(now) {
    scheduled = false;
    if (manual) return;
    for (var k in instances) instances[k].frame(now);
    if (anyRunning()) wake();
  }
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") for (var k in instances) instances[k].pause("hidden");
  });
  window.addEventListener("blur", function () { for (var k in instances) instances[k].pause("blur"); });

  window.SkySentinel = {
    create: create,
    get: function (id) { return instances[id] || null; },
    ids: function () { return Object.keys(instances); },
    manual: function (on) { manual = !!on; if (!manual && anyRunning()) wake(); },
    defectSchedule: defectSchedule,
    constants: {
      HZ: HZ, GRACE_TICKS: GRACE_TICKS, FIRST_SHOT_CLEARANCE: FIRST_SHOT_CLEARANCE, EARLIEST_EXPLOSION: EARLIEST_EXPLOSION,
      EXPLOSION_GAP: EXPLOSION_GAP, INVULNERABLE_TICKS: INVULNERABLE_TICKS, START_LIVES: START_LIVES, MAX_LIVES: MAX_LIVES,
      LEVEL_TICKS: LEVEL_TICKS, BOSS_AFTER: BOSS_AFTER, WEAPON_TICKS: WEAPON_TICKS
    }
  };
})();
