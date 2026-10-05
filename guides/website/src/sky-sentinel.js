/* ===================================================================== Sky Sentinel (v4.13.10)
   The Training page's game engine. Design and test rules:
   docs/releases/v4/v4.13/development/v4.13.10-game-design.md
   Fixed 60 Hz simulation separated from rendering; seeded random streams (spawn, drops,
   defects, rocks, and a render-only fx stream); every timing rule counted in ticks; the two
   seeded defects are independent flags. Progression (levels, difficulty, ship forms,
   power-ups) and the Nexus megaship boss are switched on per game.
   Rendering: a hand-written WebGL 1 renderer draws lit 3D meshes built in code (lofted hulls,
   swept wings, canopies, nacelles, noisy icosphere rocks) under a tilted orthographic camera,
   with additive glow sprites and particles; a 2D overlay canvas carries the HUD. Where WebGL
   is missing the same game draws on a 2D canvas. Force the 2D path with
   data-ss-renderer="2d" on the host, the create option { renderer: "2d" }, or
   window.SKY_SENTINEL_RENDERER = "2d" set before the page script runs (the tests use this).
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
  var HIT_INVULN = 60;              /* a short window after each hit, so one beam or rock counts once */
  var HEALTH_MAX = 100;
  var SHIELD_MAX = 50;              /* the shield is a second bar that takes damage first */
  var REPAIR = 35;                  /* the repair kit replaces the old extra ship */
  var EXPLOSION_DAMAGE = 40;        /* the leftover self-test: internal, so the shield does not stop it */
  var BLAST_RADIUS = 84;
  var BOMB_ARM = 34;                /* ticks between a bomb arming (its ring shows) and the blast */
  var LEVEL_TICKS = { 1: 5400, 2: 6600 };   /* level 2 at 90 s, level 3 at 200 s */
  var BOSS_AFTER = 3600;                    /* the boss arrives 60 s into level 3: 260 s from the start */
  var BOSS_AFTER_JUMP = 150;
  var WEAPON_TICKS = 600;
  var POWER_TICKS = { spread: 600, rapid: 600, missiles: 540, wingman: 900 };
  var DROP_CHANCE = 0.18;

  /* Damage at Easy; each level multiplies it (DIFFICULTY.damage). A bomb's blast falls off
     with distance from DAMAGE.blast at the centre to a fifth of it at the rim. */
  var DAMAGE = {
    needle: 6, shot: 10, beam: 32, blast: 34, bossShot: 14, test: 10,
    collision: { interceptor: 14, gunship: 22, lancer: 26, bomber: 30, boss: 45 },
    asteroid: { large: 28, medium: 16, small: 7 }
  };
  var DIFFICULTY = {
    1: { name: "Easy", pace: 80, rocks: 260, fire: 1, damage: 1, cap: 6, burst: 1,
         mix: [["gunship", 0.6], ["interceptor", 0.4]], note: "Gunships and interceptors" },
    2: { name: "Medium", pace: 64, rocks: 220, fire: 0.82, damage: 1.15, cap: 8, burst: 1,
         mix: [["gunship", 0.36], ["interceptor", 0.3], ["lancer", 0.24], ["bomber", 0.1]], note: "Lancers and bombers join" },
    3: { name: "Hard", pace: 50, rocks: 180, fire: 0.68, damage: 1.3, cap: 10, burst: 2,
         mix: [["gunship", 0.28], ["interceptor", 0.27], ["lancer", 0.25], ["bomber", 0.2]], note: "Every class, faster fire, heavier hits" }
  };
  /* Four ship classes, each with its own weapon: gunships fire aimed bolts, interceptors dive
     in swarms firing darts, lancers charge (a visible tell) then fire a laser beam down their
     column, and bombers lob bombs that arm near the ship and burst with a blast radius. */
  var ENEMY = {
    gunship: { r: 22, hp: 2, score: 150, weapon: "shot" },
    interceptor: { r: 14, hp: 1, score: 100, weapon: "needle" },
    lancer: { r: 20, hp: 4, score: 250, weapon: "beam" },
    bomber: { r: 28, hp: 5, score: 400, weapon: "bomb" }
  };
  var ROCK = {
    large: { r: [34, 40], hp: 4, score: 80, into: "medium" },
    medium: { r: [19, 23], hp: 2, score: 50, into: "small" },
    small: { r: [10, 13], hp: 1, score: 25, into: null }
  };
  /* Eight upgrades; a kill's drop is picked from the drops stream with these weights. */
  var DROPS = [["shield", 0.18], ["weapon", 0.15], ["spread", 0.12], ["rapid", 0.12], ["missiles", 0.11], ["wingman", 0.1], ["repair", 0.22]];
  var POWER_LOOK = {
    shield: ["#60a5fa", "Shield"], weapon: ["#f472b6", "Twin"], spread: ["#fbbf24", "Spread"], rapid: ["#a3e635", "Rapid"],
    missiles: ["#fb923c", "Missiles"], wingman: ["#c084fc", "Wingman"], repair: ["#34d399", "Repair"]
  };
  var FORMS = { 1: "Scout", 2: "Fighter", 3: "Sentinel" };
  var DEFECT_NAMES = ["firstHitFatal", "randomExplosion"];
  var REDUCED = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var SOURCE_TEXT = {
    shot: "a gunship bolt", needle: "an interceptor dart", beam: "a laser beam", blast: "a bomb blast",
    bossShot: "a megaship bolt", boss: "the megaship", test: "a test hit", explode: "its own self-test"
  };

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
      rocks: mulberry32(s ^ 0x3C6EF372),
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
  function clamp(v, lo, hi) { return v < lo ? lo : v > hi ? hi : v; }

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

  /* ==================================================================== meshes
     Built once in code and uploaded to each WebGL context. A vertex is 12 floats: position,
     normal, colour, and material (metalness, emission, surface: 0 paint, 1 panelled metal,
     2 rock, 3 glass). Local axes match the world: x right, y up out of the play plane, z down
     the screen; every craft is modelled with its nose toward -z. */
  var M_PANEL = [0.78, 0, 1], M_METAL = [0.9, 0, 0], M_PAINT = [0.35, 0, 1], M_DARK = [0.55, 0, 0];
  var M_GLASS = [0.9, 0, 3], M_EMIT = [0, 1, 0], M_ROCK = [0, 0, 2], M_HALF = [0.4, 0.55, 0];
  function v3sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
  function v3cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
  function v3dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
  function v3norm(a) { var l = Math.sqrt(v3dot(a, a)) || 1; return [a[0] / l, a[1] / l, a[2] / l]; }

  function Mesh() { this.v = []; }
  Mesh.prototype.vert = function (p, n, c, m) { this.v.push(p[0], p[1], p[2], n[0], n[1], n[2], c[0], c[1], c[2], m[0], m[1], m[2]); };
  /* A flat triangle; `out` is a direction the face should point along, to orient its normal. */
  Mesh.prototype.tri = function (a, b, c, col, mat, out) {
    var n = v3norm(v3cross(v3sub(b, a), v3sub(c, a)));
    if (out && v3dot(n, out) < 0) n = [-n[0], -n[1], -n[2]];
    this.vert(a, n, col, mat); this.vert(b, n, col, mat); this.vert(c, n, col, mat);
  };
  /* Append another mesh through an affine map: m is a 3x3 row-major matrix, t a translation. */
  Mesh.prototype.add = function (src, m, t) {
    var v = src.v;
    for (var i = 0; i < v.length; i += 12) {
      var x = v[i], y = v[i + 1], z = v[i + 2], nx = v[i + 3], ny = v[i + 4], nz = v[i + 5];
      this.v.push(m[0] * x + m[1] * y + m[2] * z + t[0], m[3] * x + m[4] * y + m[5] * z + t[1], m[6] * x + m[7] * y + m[8] * z + t[2]);
      var n = v3norm([m[0] * nx + m[1] * ny + m[2] * nz, m[3] * nx + m[4] * ny + m[5] * nz, m[6] * nx + m[7] * ny + m[8] * nz]);
      this.v.push(n[0], n[1], n[2], v[i + 6], v[i + 7], v[i + 8], v[i + 9], v[i + 10], v[i + 11]);
    }
    return this;
  };
  var IDENT = [1, 0, 0, 0, 1, 0, 0, 0, 1], MIRROR_X = [-1, 0, 0, 0, 1, 0, 0, 0, 1];
  function both(dst, part) { dst.add(part, IDENT, [0, 0, 0]); dst.add(part, MIRROR_X, [0, 0, 0]); }
  function rotZ(a) { var c = Math.cos(a), s = Math.sin(a); return [c, -s, 0, s, c, 0, 0, 0, 1]; }
  function rotX(a) { var c = Math.cos(a), s = Math.sin(a); return [1, 0, 0, 0, c, -s, 0, s, c]; }

  /* A smooth loft through rings of equal length (closed around each ring). Normals come from
     central differences, turned outward from each ring's centre. */
  function loft(m, rings, col, mat, capCol, capMat) {
    var nr = rings.length, nv = rings[0].length, i, j;
    var cen = rings.map(function (r) {
      var c = [0, 0, 0];
      r.forEach(function (p) { c[0] += p[0]; c[1] += p[1]; c[2] += p[2]; });
      return [c[0] / r.length, c[1] / r.length, c[2] / r.length];
    });
    var nor = [];
    for (i = 0; i < nr; i++) {
      nor.push([]);
      for (j = 0; j < nv; j++) {
        var du = v3sub(rings[i][(j + 1) % nv], rings[i][(j + nv - 1) % nv]);
        var dv = v3sub(rings[Math.min(nr - 1, i + 1)][j], rings[Math.max(0, i - 1)][j]);
        var n = v3norm(v3cross(du, dv));
        if (v3dot(n, v3sub(rings[i][j], cen[i])) < 0) n = [-n[0], -n[1], -n[2]];
        nor[i].push(n);
      }
    }
    var c = typeof col === "function" ? col : function () { return col; };
    for (i = 0; i < nr - 1; i++) {
      for (j = 0; j < nv; j++) {
        var j2 = (j + 1) % nv, k = c(i, j);
        m.vert(rings[i][j], nor[i][j], k, mat); m.vert(rings[i + 1][j], nor[i + 1][j], k, mat); m.vert(rings[i + 1][j2], nor[i + 1][j2], k, mat);
        m.vert(rings[i][j], nor[i][j], k, mat); m.vert(rings[i + 1][j2], nor[i + 1][j2], k, mat); m.vert(rings[i][j2], nor[i][j2], k, mat);
      }
    }
    if (capCol) {
      var last = rings[nr - 1], lc = cen[nr - 1], axis = v3norm(v3sub(lc, cen[nr - 2]));
      for (j = 0; j < nv; j++) m.tri(lc, last[j], last[(j + 1) % nv], capCol, capMat || mat, axis);
    }
    return m;
  }
  /* A superellipse ring in the xy plane at depth z; the underside is flattened. */
  function sring(z, hw, hh, yo, e, n, under) {
    var out = [];
    for (var k = 0; k < n; k++) {
      var a = k / n * Math.PI * 2, c = Math.cos(a), s = Math.sin(a);
      var x = hw * (c < 0 ? -1 : 1) * Math.pow(Math.abs(c), 2 / e);
      var y = hh * (s < 0 ? -1 : 1) * Math.pow(Math.abs(s), 2 / e);
      out.push([x, (y < 0 ? y * under : y) + yo, z]);
    }
    return out;
  }
  function body(m, sections, e, col, mat, capCol) {
    return loft(m, sections.map(function (b) { return sring(b[0], b[1], b[2], b[3], e, 18, 0.62); }), col, mat, capCol, M_DARK);
  }
  function ellipsoid(m, cx, cy, cz, rx, ry, rz, col, mat, n) {
    var rings = [];
    n = n || 12;
    for (var i = 0; i <= n; i++) {
      var t = -1 + 2 * i / n, k = Math.sqrt(Math.max(0.0004, 1 - t * t));
      rings.push(sring(cz + t * rz, rx * k, ry * k, cy, 2, 14, 1).map(function (p) { return [p[0] + cx, p[1], p[2]]; }));
    }
    return loft(m, rings, col, mat);
  }
  /* A nacelle along z: radius r0 at z0 to r1 at z1, then a darker nozzle lip and a glowing
     exhaust disc at the back. */
  function nacelle(m, cx, cy, z0, z1, r0, r1, col, glowCol) {
    var rings = [], steps = [[0, 0.55], [0.12, 1], [0.8, 1], [1, r1 / r0]];
    steps.forEach(function (s) { rings.push(sring(z0 + (z1 - z0) * s[0], r0 * s[1], r0 * s[1], 0, 2, 14, 1)); });
    rings = rings.map(function (r) { return r.map(function (p) { return [p[0] + cx, p[1] + cy, p[2]]; }); });
    loft(m, rings, col, M_METAL);
    var lip = [sring(z1, r1, r1, cy, 2, 14, 1), sring(z1 + 1.2, r1 * 1.08, r1 * 1.08, cy, 2, 14, 1)].map(function (r) { return r.map(function (p) { return [p[0] + cx, p[1], p[2]]; }); });
    loft(m, lip, [0.16, 0.17, 0.19], M_DARK, glowCol, M_EMIT);
    return m;
  }
  /* Polygon helpers in the (x, z) plane. */
  function area2(poly) { var a = 0; for (var i = 0; i < poly.length; i++) { var p = poly[i], q = poly[(i + 1) % poly.length]; a += p[0] * q[1] - q[0] * p[1]; } return a / 2; }
  function triangulate(poly) {
    var idx = poly.map(function (_, i) { return i; }), out = [], sgn = area2(poly) > 0 ? 1 : -1, guard = 0;
    while (idx.length > 3 && guard++ < 400) {
      var cut = false;
      for (var i = 0; i < idx.length && !cut; i++) {
        var a = idx[(i + idx.length - 1) % idx.length], b = idx[i], c = idx[(i + 1) % idx.length];
        var pa = poly[a], pb = poly[b], pc = poly[c];
        var cr = (pb[0] - pa[0]) * (pc[1] - pa[1]) - (pb[1] - pa[1]) * (pc[0] - pa[0]);
        if (cr * sgn <= 0) continue;
        var inside = false;
        for (var k = 0; k < idx.length && !inside; k++) {
          var q = idx[k];
          if (q === a || q === b || q === c) continue;
          inside = inTriangle(poly[q][0], poly[q][1], [pa, pb, pc]);
        }
        if (inside) continue;
        out.push([a, b, c]); idx.splice(i, 1); cut = true;
      }
      if (!cut) break;
    }
    if (idx.length === 3) out.push(idx);
    return out;
  }
  function inset(poly, d) {
    var sgn = area2(poly) > 0 ? 1 : -1, n = poly.length, out = [];
    for (var i = 0; i < n; i++) {
      var p0 = poly[(i + n - 1) % n], p1 = poly[i], p2 = poly[(i + 1) % n];
      var e1 = v3norm([p1[0] - p0[0], 0, p1[1] - p0[1]]), e2 = v3norm([p2[0] - p1[0], 0, p2[1] - p1[1]]);
      var n1 = [-e1[2] * sgn, e1[0] * sgn], n2 = [-e2[2] * sgn, e2[0] * sgn];   /* inward normals */
      var b = [n1[0] + n2[0], n1[1] + n2[1]], bl = Math.sqrt(b[0] * b[0] + b[1] * b[1]) || 1;
      b = [b[0] / bl, b[1] / bl];
      var miter = Math.min(2.5, 1 / Math.max(0.3, b[0] * n1[0] + b[1] * n1[1]));
      out.push([p1[0] + b[0] * d * miter, p1[1] + b[1] * d * miter]);
    }
    return out;
  }
  /* A bevelled slab: the polygon's outline sits at y0, the top face is inset and raised by
     th / 2, the bottom inset and lowered, so the edge reads as a chamfered blade. */
  function slab(m, poly, y0, th, bevel, col, mat, topCol) {
    var top = inset(poly, bevel), bot = top, n = poly.length, tris = triangulate(poly);
    var yt = y0 + th / 2, yb = y0 - th * 0.35;
    tris.forEach(function (t) {
      m.tri([top[t[0]][0], yt, top[t[0]][1]], [top[t[1]][0], yt, top[t[1]][1]], [top[t[2]][0], yt, top[t[2]][1]], topCol || col, mat, [0, 1, 0]);
      m.tri([bot[t[0]][0], yb, bot[t[0]][1]], [bot[t[1]][0], yb, bot[t[1]][1]], [bot[t[2]][0], yb, bot[t[2]][1]], col, mat, [0, -1, 0]);
    });
    var sgn = area2(poly) > 0 ? 1 : -1;
    for (var i = 0; i < n; i++) {
      var j = (i + 1) % n, p = poly[i], q = poly[j];
      var e = v3norm([q[0] - p[0], 0, q[1] - p[1]]), outward = [e[2] * sgn, 0, -e[0] * sgn];
      var a = [p[0], y0, p[1]], b = [q[0], y0, q[1]];
      var ta = [top[i][0], yt, top[i][1]], tb = [top[j][0], yt, top[j][1]];
      var ba = [bot[i][0], yb, bot[i][1]], bb = [bot[j][0], yb, bot[j][1]];
      var up = [outward[0], 0.9, outward[2]], dn = [outward[0], -0.9, outward[2]];
      m.tri(a, b, tb, col, mat, up); m.tri(a, tb, ta, col, mat, up);
      m.tri(a, bb, b, col, mat, dn); m.tri(a, ba, bb, col, mat, dn);
    }
    return m;
  }
  /* A canted fin: a slab in the (height, z) plane stood up at x, leaning outward by `cant`. */
  function fin(m, x, y, poly, th, cant, col) {
    var f = slab(new Mesh(), poly, 0, th, Math.min(0.5, th * 0.4), col, M_PANEL);
    var swap = [0, 1, 0, 1, 0, 0, 0, 0, 1];   /* the slab's x becomes height, its y the thickness */
    var stood = new Mesh().add(f, swap, [0, 0, 0]);
    m.add(stood, rotZ(-cant), [x, y, 0]);
    return m;
  }
  /* A box from its two corners, flat shaded. */
  function box(m, x0, y0, z0, x1, y1, z1, col, mat) {
    var p = [[x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0], [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]];
    var faces = [[0, 1, 2, 3, [0, 0, -1]], [5, 4, 7, 6, [0, 0, 1]], [4, 0, 3, 7, [-1, 0, 0]], [1, 5, 6, 2, [1, 0, 0]], [3, 2, 6, 7, [0, 1, 0]], [4, 5, 1, 0, [0, -1, 0]]];
    faces.forEach(function (f) { m.tri(p[f[0]], p[f[1]], p[f[2]], col, mat, f[4]); m.tri(p[f[0]], p[f[2]], p[f[3]], col, mat, f[4]); });
    return m;
  }
  function icosphere(sub) {
    var t = (1 + Math.sqrt(5)) / 2;
    var v = [[-1, t, 0], [1, t, 0], [-1, -t, 0], [1, -t, 0], [0, -1, t], [0, 1, t], [0, -1, -t], [0, 1, -t], [t, 0, -1], [t, 0, 1], [-t, 0, -1], [-t, 0, 1]].map(v3norm);
    var f = [[0, 11, 5], [0, 5, 1], [0, 1, 7], [0, 7, 10], [0, 10, 11], [1, 5, 9], [5, 11, 4], [11, 10, 2], [10, 7, 6], [7, 1, 8],
             [3, 9, 4], [3, 4, 2], [3, 2, 6], [3, 6, 8], [3, 8, 9], [4, 9, 5], [2, 4, 11], [6, 2, 10], [8, 6, 7], [9, 8, 1]];
    for (var s = 0; s < sub; s++) {
      var cache = {}, nf = [];
      var mid = function (a, b) {
        var key = a < b ? a + "_" + b : b + "_" + a;
        if (cache[key] == null) { v.push(v3norm([(v[a][0] + v[b][0]) / 2, (v[a][1] + v[b][1]) / 2, (v[a][2] + v[b][2]) / 2])); cache[key] = v.length - 1; }
        return cache[key];
      };
      f.forEach(function (tr) { var a = mid(tr[0], tr[1]), b = mid(tr[1], tr[2]), c = mid(tr[2], tr[0]); nf.push([tr[0], a, c], [tr[1], b, a], [tr[2], c, b], [a, b, c]); });
      f = nf;
    }
    return { v: v, f: f };
  }
  /* A rock: an icosphere pushed out by lumps and pressed in by craters, flat shaded so every
     facet catches the light, darker in its hollows. Unit radius; the draw call scales it. */
  function rockMesh(seed) {
    var r = mulberry32(seed), ico = icosphere(2), m = new Mesh();
    var bumps = [];
    for (var k = 0; k < 14; k++) bumps.push({ d: v3norm([r() - 0.5, r() - 0.5, r() - 0.5]), w: 0.25 + r() * 0.5, h: (k < 6 ? -1 : 1) * (0.08 + r() * 0.16), crater: k < 6 });
    var squash = [0.82 + r() * 0.3, 0.78 + r() * 0.25, 0.85 + r() * 0.3], ph = [r() * 6, r() * 6, r() * 6];
    var pts = ico.v.map(function (p) {
      var rad = 1 + 0.07 * Math.sin(p[0] * 5 + ph[0]) * Math.sin(p[1] * 4 + ph[1]) * Math.sin(p[2] * 6 + ph[2]);
      bumps.forEach(function (b) {
        var ang = Math.acos(clamp(v3dot(p, b.d), -1, 1));
        if (ang > b.w) return;
        var x = ang / b.w;
        rad += b.crater ? b.h * (1 - x * x) - b.h * 0.6 * Math.exp(-Math.pow((x - 1) * 4, 2)) : b.h * (1 - x * x) * (1 - x * x);
      });
      return [p[0] * rad * squash[0], p[1] * rad * squash[1], p[2] * rad * squash[2]];
    });
    var warm = [0.5, 0.45, 0.4], cool = [0.33, 0.32, 0.33];
    ico.f.forEach(function (t) {
      var a = pts[t[0]], b = pts[t[1]], c = pts[t[2]];
      var cen = [(a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3, (a[2] + b[2] + c[2]) / 3];
      var depth = Math.sqrt(v3dot(cen, cen)), mix = r(), shade = clamp(0.62 + (depth - 0.85) * 1.2, 0.45, 1.1);
      var col = [(warm[0] * mix + cool[0] * (1 - mix)) * shade, (warm[1] * mix + cool[1] * (1 - mix)) * shade, (warm[2] * mix + cool[2] * (1 - mix)) * shade];
      m.tri(a, b, c, col, M_ROCK, cen);
    });
    return m;
  }

  var C = {
    white: [0.82, 0.85, 0.88], steel: [0.56, 0.6, 0.65], gun: [0.3, 0.32, 0.36], dark: [0.12, 0.13, 0.15],
    cyan: [0.12, 0.78, 0.95], cyanHot: [0.55, 0.95, 1.0], glass: [0.05, 0.22, 0.32]
  };
  /* The player's fighter, parameterised so its three forms share one design language. */
  function fighter(s) {
    var m = new Mesh();
    body(m, s.body, 2.7, s.hull, M_PANEL, C.dark);
    /* a dark dorsal spine and intake cheeks break up the hull */
    if (s.spine) body(m, s.spine, 3, C.gun, M_METAL);
    ellipsoid(m, 0, s.canopy[1], s.canopy[0], s.canopy[2], s.canopy[3], s.canopy[4], C.glass, M_GLASS);
    var side = new Mesh();
    slab(side, s.wing, s.wingY, s.wingTh, 0.9, s.wingCol || s.hull, M_PANEL);
    if (s.stripe) slab(side, s.stripe, s.wingY + s.wingTh / 2 + 0.05, 0.25, 0.05, s.accent, M_PAINT);
    if (s.canard) slab(side, s.canard, s.wingY + 0.6, s.wingTh * 0.8, 0.5, s.hull, M_PANEL);
    if (s.intake) box(side, s.intake[0], s.intake[1], s.intake[2], s.intake[3], s.intake[4], s.intake[5], C.dark, M_DARK);
    (s.fins || []).forEach(function (f) { fin(side, f[0], f[1], f[2], 0.9, f[3], s.hull); });
    (s.pods || []).forEach(function (p) {
      nacelle(side, p[0], p[1], p[2], p[3], p[4], p[4] * 0.7, C.gun, s.accent);
      box(side, p[0] - 0.35, p[1] - 0.35, p[2] - 4, p[0] + 0.35, p[1] + 0.35, p[2], C.dark, M_METAL);
    });
    ellipsoid(side, s.tip[0], s.tip[1], s.tip[2], 0.7, 0.5, 1.2, [1, 0.25, 0.2], M_EMIT, 6);
    both(m, side);
    var engines = [];
    s.engines.forEach(function (e) {
      nacelle(m, e[0], e[1], e[2], e[3], e[4], e[4] * 0.86, C.steel, C.cyanHot);
      engines.push([e[0], e[1], e[3] + 1.4, e[4]]);
    });
    return { mesh: m, engines: engines };
  }
  function playerForm(form) {
    if (form === 1) return fighter({
      hull: C.white, accent: C.cyan,
      body: [[-27, 0.25, 0.2, 0.5], [-23, 1.7, 1.2, 0.7], [-17, 3.1, 2.2, 0.9], [-10, 4.3, 2.9, 1.1], [-3, 5.1, 3.3, 1.2], [5, 5.5, 3.2, 1.1], [13, 5.3, 2.9, 0.9], [19, 4.5, 2.5, 0.7], [23, 3.8, 2.1, 0.6]],
      spine: [[-6, 0.3, 0.3, 3.4], [0, 1.4, 1.2, 3.4], [10, 1.7, 1.2, 3.1], [18, 1.2, 0.8, 2.6], [21, 0.3, 0.3, 2.3]],
      canopy: [-11, 3.4, 2.2, 1.9, 6.5],
      wing: [[4.5, -6], [23, 9.5], [24, 13.5], [21, 15], [5, 16]], wingY: 0.3, wingTh: 1.5,
      stripe: [[9, 1.5], [21.5, 11], [22, 12.6], [9, 4]],
      canard: [[3.8, -17], [8.5, -11], [8.5, -9.5], [3.8, -10]],
      fins: [[3.6, 2.4, [[0, 13], [6.5, 18], [6.5, 21], [0, 22]], 0.38]],
      tip: [23.6, 0.6, 12.8],
      engines: [[0, 0.7, 14, 24.5, 3.1]]
    });
    if (form === 2) return fighter({
      hull: C.white, accent: C.cyan,
      body: [[-33, 0.25, 0.2, 0.5], [-28, 1.9, 1.3, 0.7], [-21, 3.5, 2.4, 1.0], [-12, 4.9, 3.2, 1.3], [-3, 6.3, 3.6, 1.3], [6, 7.5, 3.6, 1.1], [15, 8.1, 3.4, 0.9], [23, 7.5, 3.0, 0.7], [28, 6.7, 2.6, 0.6]],
      spine: [[-8, 0.3, 0.3, 3.8], [0, 1.6, 1.3, 3.9], [14, 2.1, 1.3, 3.6], [24, 1.4, 0.9, 3.0], [27, 0.3, 0.3, 2.7]],
      canopy: [-14, 3.8, 2.5, 2.1, 8],
      wing: [[6.5, -5], [30, 12], [32, 16], [27.5, 18], [7.5, 19]], wingY: 0.2, wingTh: 1.7,
      stripe: [[12, 2.5], [29.5, 13], [30, 14.8], [12, 5.2]],
      canard: [[4.5, -21], [11.5, -14.5], [11.5, -12.8], [4.5, -13]],
      intake: [4.6, -1.2, -10, 6.8, 2.2, -2],
      fins: [[5.6, 2.6, [[0, 16], [8.5, 22], [8.5, 26], [0, 27.5]], 0.4]],
      pods: [[17, -0.4, -4, 13, 1.5]],
      tip: [31.5, 0.6, 15.2],
      engines: [[-3.7, 0.5, 18, 30.5, 3.0], [3.7, 0.5, 18, 30.5, 3.0]]
    });
    return fighter({
      hull: C.white, accent: C.cyan, wingCol: [0.74, 0.78, 0.82],
      body: [[-41, 0.25, 0.2, 0.6], [-35, 2.1, 1.4, 0.8], [-27, 4.0, 2.6, 1.1], [-17, 5.6, 3.4, 1.4], [-6, 7.2, 3.9, 1.5], [6, 8.8, 4.0, 1.3], [17, 9.6, 3.8, 1.1], [27, 9.0, 3.3, 0.9], [34, 8.0, 2.8, 0.7]],
      spine: [[-12, 0.3, 0.3, 4.4], [-2, 2.0, 1.6, 4.6], [16, 2.6, 1.6, 4.4], [29, 1.8, 1.1, 3.7], [33, 0.3, 0.3, 3.3]],
      canopy: [-19, 4.4, 2.8, 2.3, 9.5],
      wing: [[7.5, -12], [22, 2], [40, 11], [42, 16], [36.5, 19.5], [8.5, 23]], wingY: 0.2, wingTh: 1.9,
      stripe: [[14, -2], [39.5, 12.5], [40, 14.5], [14, 1.4]],
      canard: [[5, -27], [13.5, -19], [13.5, -17], [5, -17.5]],
      intake: [5.4, -1.3, -14, 8, 2.4, -4],
      fins: [[6.8, 2.8, [[0, 19], [10, 26], [10, 31], [0, 33]], 0.42]],
      pods: [[40.5, -0.2, -8, 14, 1.4], [20, -0.6, -6, 12, 1.6]],
      tip: [41.6, 0.6, 15.5],
      engines: [[0, 2.2, 22, 37, 2.8], [-7.2, 0.3, 21, 36, 3.1], [7.2, 0.3, 21, 36, 3.1]]
    });
  }
  function wingmanMesh() {
    var m = new Mesh(), side = new Mesh();
    body(m, [[-12, 0.2, 0.2, 0.4], [-8, 1.4, 1.0, 0.5], [-1, 2.2, 1.5, 0.6], [6, 2.2, 1.3, 0.5], [10, 1.6, 1.0, 0.4]], 2.6, [0.78, 0.74, 0.86], M_PANEL, C.dark);
    ellipsoid(m, 0, 1.6, -4, 1.1, 0.9, 3, C.glass, M_GLASS);
    slab(side, [[2, -3], [12, 4], [12.5, 6.5], [2.5, 8]], 0.2, 1, 0.5, [0.7, 0.66, 0.8], M_PANEL);
    slab(side, [[6, 1.5], [11.5, 5], [11.6, 5.8], [6, 2.8]], 0.75, 0.2, 0.05, [0.75, 0.45, 1], M_PAINT);
    both(m, side);
    nacelle(m, 0, 0.4, 7, 12, 1.6, 1.4, C.steel, [0.85, 0.6, 1]);
    return { mesh: m, engines: [[0, 0.4, 13.2, 1.6]] };
  }
  function gunshipMesh() {
    var m = new Mesh(), side = new Mesh(), red = [0.78, 0.12, 0.09];
    body(m, [[-23, 0.4, 0.3, 0.2], [-19, 3.4, 2.0, 0.4], [-12, 6.2, 3.2, 0.7], [-3, 7.6, 3.8, 0.9], [7, 7.9, 3.6, 0.8], [15, 6.6, 3.0, 0.6], [21, 5.2, 2.4, 0.5]], 3.6, C.gun, M_PANEL, C.dark);
    body(m, [[-14, 0.3, 0.3, 3.1], [-8, 2.6, 1.0, 3.6], [6, 3.0, 1.1, 3.5], [14, 2.0, 0.6, 3.0]], 3, [0.22, 0.23, 0.26], M_METAL);
    ellipsoid(m, 0, 3.1, -13, 2.8, 1.1, 3.8, [0.45, 0.05, 0.04], M_GLASS);
    slab(side, [[6.5, 2], [21, -6.5], [24, -4], [23, 0], [7, 14]], 0.4, 1.8, 1, [0.36, 0.37, 0.41], M_PANEL);
    slab(side, [[12, -1], [21.5, -5.5], [22.4, -4.4], [12.4, 1.6]], 1.36, 0.25, 0.05, red, M_PAINT);
    nacelle(side, 3.6, -2.1, -27, -9, 1.1, 1.1, C.dark, [1, 0.35, 0.15]);
    nacelle(side, 4.6, 0.5, 13, 23, 2.7, 2.3, C.steel, [1, 0.42, 0.18]);
    fin(side, 3.2, 3, [[0, 10], [5, 15], [5, 18], [0, 19]], 0.8, 0.5, C.gun);
    ellipsoid(side, 23.4, 0.6, -4, 0.8, 0.6, 1.2, [1, 0.2, 0.15], M_EMIT, 6);
    both(m, side);
    return { mesh: m, engines: [[-4.6, 0.5, 24.2, 2.7], [4.6, 0.5, 24.2, 2.7]], muzzles: [[-3.6, -2.1, -27.5], [3.6, -2.1, -27.5]] };
  }
  function interceptorMesh() {
    var m = new Mesh(), side = new Mesh(), mag = [0.85, 0.2, 0.72];
    body(m, [[-15, 0.2, 0.2, 0.3], [-10, 1.6, 1.3, 0.5], [-3, 2.6, 2.0, 0.6], [5, 3.0, 2.0, 0.6], [12, 2.4, 1.6, 0.5]], 2.8, [0.24, 0.22, 0.3], M_PANEL, C.dark);
    ellipsoid(m, 0, 1.9, -5, 1.2, 1.0, 3.2, [0.35, 0.05, 0.3], M_GLASS);
    slab(side, [[2, 4], [14, -4], [15.2, -2.2], [13.5, 1], [3, 10]], 0.2, 1.1, 0.5, [0.3, 0.27, 0.37], M_PANEL);
    slab(side, [[8, 1], [14.2, -3.2], [14.8, -2.4], [8.4, 2.6]], 0.8, 0.2, 0.05, mag, M_PAINT);
    fin(side, 2.1, 1.8, [[0, 4], [4, 8.5], [4, 10.5], [0, 11]], 0.6, 0.55, [0.3, 0.27, 0.37]);
    both(m, side);
    nacelle(m, 0, 0.4, 9, 14, 1.8, 1.5, C.gun, [1, 0.4, 0.95]);
    return { mesh: m, engines: [[0, 0.4, 15.2, 1.8]] };
  }
  function lancerMesh() {
    var m = new Mesh(), side = new Mesh(), ceramic = [0.8, 0.76, 0.7], orange = [1, 0.55, 0.15];
    body(m, [[-20, 0.4, 0.4, 0.6], [-15, 2.6, 2.2, 0.8], [-6, 4.1, 3.0, 1.0], [6, 4.7, 3.2, 1.0], [16, 4.3, 2.8, 0.8], [24, 3.4, 2.2, 0.6]], 2.4, ceramic, M_PANEL, C.dark);
    ellipsoid(m, 0, 3.4, -6, 1.6, 1.3, 4.4, [0.35, 0.18, 0.04], M_GLASS);
    box(side, 2.4, -0.3, -33, 3.6, 1.6, -8, C.dark, M_METAL);
    box(side, 1.4, 0.2, -31, 2.4, 1.1, -10, orange, M_HALF);
    slab(side, [[3.5, 3], [16, 15], [17, 18.5], [4, 20]], 0.4, 1.3, 0.6, [0.72, 0.68, 0.62], M_PANEL);
    slab(side, [[8, 8.5], [15.8, 15.6], [16.2, 17], [8, 10.5]], 1.1, 0.2, 0.05, orange, M_PAINT);
    fin(side, 3.4, 1.4, [[0, 6], [5, 11], [5, 13], [0, 14]], 0.8, 1.0, ceramic);
    nacelle(side, 4.3, 0.2, 14, 24, 1.6, 1.4, C.steel, [1, 0.6, 0.25]);
    both(m, side);
    nacelle(m, 0, 0.8, 18, 29, 2.5, 2.1, C.steel, [1, 0.6, 0.25]);
    ellipsoid(m, 0, 0.7, -25, 1.5, 1.5, 1.5, [1, 0.7, 0.3], M_EMIT, 8);
    return { mesh: m, engines: [[0, 0.8, 30.2, 2.5], [-4.3, 0.2, 25.2, 1.6], [4.3, 0.2, 25.2, 1.6]], emitter: [0, 0.7, -27] };
  }
  function bomberMesh() {
    var m = new Mesh(), olive = [0.27, 0.31, 0.25], yellow = [0.9, 0.78, 0.22];
    var half = [[0, -17], [30, 4], [32, 8], [26, 9], [21, 6], [15, 11], [9, 8], [3.5, 12.5], [0, 10]];
    var poly = half.concat(half.slice(1, half.length - 1).reverse().map(function (p) { return [-p[0], p[1]]; }));
    slab(m, poly, 0, 3.6, 1.6, olive, M_PANEL);
    body(m, [[-15, 0.4, 0.3, 1.2], [-10, 4.2, 2.3, 1.5], [0, 6.4, 3.2, 1.7], [8, 5.2, 2.6, 1.3], [12, 3.6, 1.8, 1.0]], 2.4, [0.3, 0.34, 0.28], M_PANEL, C.dark);
    ellipsoid(m, 0, 3.8, -6, 2.6, 0.9, 3, [0.3, 0.3, 0.05], M_GLASS);
    var side = new Mesh();
    slab(side, [[20, 0.5], [30.5, 5], [30.8, 6.6], [20, 2.4]], 1.85, 0.2, 0.05, yellow, M_PAINT);
    box(side, 5, 1.2, 3, 9, 2.6, 9, C.dark, M_DARK);
    box(side, 5.3, 1.2, 9, 8.7, 2.3, 9.6, [1, 0.85, 0.3], M_EMIT);
    ellipsoid(side, 31, 0.4, 7, 0.8, 0.6, 1.0, [1, 0.85, 0.3], M_EMIT, 6);
    both(m, side);
    return { mesh: m, engines: [[-7, 1.8, 10, 1.9], [7, 1.8, 10, 1.9]] };
  }
  function bombMesh() {
    var m = new Mesh();
    ellipsoid(m, 0, 0, 0, 4.2, 4.2, 4.2, [0.2, 0.21, 0.23], M_PANEL, 10);
    loft(m, [sring(-0.9, 4.5, 4.5, 0, 2, 16, 1), sring(0.9, 4.5, 4.5, 0, 2, 16, 1)], [0.7, 0.16, 0.12], M_PAINT);
    [[1, 0, 0], [-1, 0, 0], [0, 0, 1], [0, 0, -1], [0, 1, 0]].forEach(function (d) {
      box(m, d[0] * 4 - 0.6, d[1] * 4 - 0.6, d[2] * 4 - 0.6, d[0] * 6 + 0.6, d[1] * 6 + 0.6, d[2] * 6 + 0.6, C.steel, M_METAL);
    });
    ellipsoid(m, 0, 3.6, 0, 1.2, 1.0, 1.2, [1, 0.25, 0.15], M_EMIT, 6);
    return { mesh: m };
  }
  function missileMesh() {
    var m = new Mesh();
    loft(m, [sring(-6, 0.1, 0.1, 0, 2, 10, 1), sring(-4, 0.8, 0.8, 0, 2, 10, 1), sring(4, 0.9, 0.9, 0, 2, 10, 1), sring(5, 0.7, 0.7, 0, 2, 10, 1)], [0.88, 0.88, 0.9], M_PAINT, C.dark);
    [0, 1, 2, 3].forEach(function (k) { var f = box(new Mesh(), -0.15, 0, 2, 0.15, 2.1, 5, [0.75, 0.2, 0.18], M_PAINT); m.add(f, rotZ(k * Math.PI / 2 + 0.785), [0, 0, 0]); });
    return { mesh: m, engines: [[0, 0, 5.4, 0.8]] };
  }
  function gemMesh() {
    var m = new Mesh(), p = [[0, 6.5, 0], [0, -6.5, 0], [5, 0, 0], [-5, 0, 0], [0, 0, 5], [0, 0, -5]];
    var f = [[0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2], [1, 4, 2], [1, 3, 4], [1, 5, 3], [1, 2, 5]];
    f.forEach(function (t) { var a = p[t[0]], b = p[t[1]], c = p[t[2]]; m.tri(a, b, c, [0.85, 0.9, 0.95], M_GLASS, [(a[0] + b[0] + c[0]) / 3, (a[1] + b[1] + c[1]) / 3, (a[2] + b[2] + c[2]) / 3]); });
    loft(m, [sring(-0.6, 5.4, 5.4, 0, 2, 16, 1).map(function (q) { return [q[0], q[2], q[1]]; }), sring(0.6, 5.4, 5.4, 0, 2, 16, 1).map(function (q) { return [q[0], q[2], q[1]]; })], [0.9, 0.9, 0.9], M_METAL);
    return { mesh: m };
  }
  function shardMesh() {
    var m = new Mesh(), p = [[0, 1.4, 0], [1.2, -0.6, 0.8], [-1.1, -0.5, 0.9], [0.1, -0.6, -1.3]];
    [[0, 1, 2], [0, 2, 3], [0, 3, 1], [1, 3, 2]].forEach(function (t) { m.tri(p[t[0]], p[t[1]], p[t[2]], [0.5, 0.52, 0.56], M_METAL, [(p[t[0]][0] + p[t[1]][0] + p[t[2]][0]), (p[t[0]][1] + p[t[1]][1] + p[t[2]][1]), (p[t[0]][2] + p[t[1]][2] + p[t[2]][2])]); });
    return { mesh: m };
  }
  /* The megaship in the logo's own 512-unit space, centred on the logo centre: the side plates
     and blades become bevelled armour, the bars glowing struts. The logo outline is unchanged. */
  function bossMeshes() {
    var cx = LOGO.centre[0], cy = LOGO.centre[1], hullM = new Mesh();
    function loc(t) { return t.map(function (p) { return [p[0] - cx, p[1] - cy]; }); }
    LOGO.plates.forEach(function (t) { slab(hullM, loc(t), 0, 26, 7, [0.04, 0.42, 0.5], M_PANEL, [0.08, 0.55, 0.64]); });
    LOGO.blades.forEach(function (t) { slab(hullM, loc(t), 4, 18, 4, [0.4, 0.86, 0.9], M_METAL); });
    [[[106, 97], [410, 395]], [[410, 97], [106, 395]]].forEach(function (b) {
      var a = b[0], c = b[1], dx = c[0] - a[0], dy = c[1] - a[1], l = Math.sqrt(dx * dx + dy * dy), nx = -dy / l * LOGO.barW / 2, ny = dx / l * LOGO.barW / 2;
      slab(hullM, loc([[a[0] + nx, a[1] + ny], [c[0] + nx, c[1] + ny], [c[0] - nx, c[1] - ny], [a[0] - nx, a[1] - ny]]), 8, 14, 3, [0.15, 0.95, 1.0], M_HALF);
    });
    var node = new Mesh();
    loft(node, [sring(0, LOGO.nodeR * 0.9, LOGO.nodeR * 0.9, 0, 2, 24, 1), sring(0, LOGO.nodeR, LOGO.nodeR, 0, 2, 24, 1)].map(function (r, i) { return r.map(function (p) { return [p[0], i * 4 - 8, p[1]]; }); }), [0.1, 0.5, 0.58], M_METAL);
    ellipsoid(node, 0, 2, 0, LOGO.nodeR * 0.92, 14, LOGO.nodeR * 0.92, [0.25, 0.97, 1.0], M_HALF, 10);
    var core = new Mesh();
    ellipsoid(core, 0, 6, 0, LOGO.coreR, LOGO.coreR * 0.8, LOGO.coreR, [0.95, 1, 1], M_EMIT, 12);
    return { hull: { mesh: hullM }, node: { mesh: node }, core: { mesh: core } };
  }

  var MESHES = null;
  function meshes() {
    if (MESHES) return MESHES;
    var b = bossMeshes();
    MESHES = {
      form1: playerForm(1), form2: playerForm(2), form3: playerForm(3), wingman: wingmanMesh(),
      gunship: gunshipMesh(), interceptor: interceptorMesh(), lancer: lancerMesh(), bomber: bomberMesh(),
      bomb: bombMesh(), missile: missileMesh(), gem: gemMesh(), shard: shardMesh(),
      bossHull: b.hull, bossNode: b.node, bossCore: b.core, rocks: []
    };
    for (var k = 0; k < 6; k++) MESHES.rocks.push({ mesh: rockMesh(1013 + k * 7919) });
    return MESHES;
  }

  /* ==================================================================== WebGL
     The camera is orthographic and tilted toward the viewer by TILT, so the tops and backs of
     the craft show; the play plane still maps exactly onto the frame, so the game keeps its 2D
     rules and hit tests. Depth runs along the view direction. */
  var TILT = 0.5;
  var VIS = 1.15;   /* craft are drawn a little larger than their hit circles */
  var GLSL_HEAD = "#ifdef GL_FRAGMENT_PRECISION_HIGH\nprecision highp float;\n#else\nprecision mediump float;\n#endif\n";
  var PROJECT = "uniform vec3 uWorld; uniform vec2 uCS; uniform vec2 uDepth; uniform vec2 uShake;\n" +
    "vec4 project(vec3 w) { float d = w.y * uCS.x + w.z * uCS.y;\n" +
    "  return vec4(2.0 * w.x / uWorld.x - 1.0 + uShake.x, 1.0 - 2.0 * (w.z - w.y * uWorld.z) / uWorld.y + uShake.y, 1.0 - 2.0 * (d - uDepth.x) * uDepth.y, 1.0); }\n";
  var MESH_VS = "attribute vec3 aPos; attribute vec3 aNor; attribute vec3 aCol; attribute vec3 aMat;\n" +
    "uniform mat4 uModel;\n" + PROJECT +
    "varying vec3 vN; varying vec3 vCol; varying vec3 vMat; varying vec3 vObj;\n" +
    "void main() { vec4 w = uModel * vec4(aPos, 1.0); vN = (uModel * vec4(aNor, 0.0)).xyz; vCol = aCol; vMat = aMat; vObj = aPos; gl_Position = project(w.xyz); }\n";
  var MESH_FS = GLSL_HEAD +
    "uniform vec3 uLight; uniform vec3 uFill; uniform vec3 uView; uniform vec3 uTint; uniform vec3 uGlowCol; uniform float uFlash; uniform float uGlow; uniform vec3 uEnv;\n" +
    "varying vec3 vN; varying vec3 vCol; varying vec3 vMat; varying vec3 vObj;\n" +
    "float h3(vec3 p) { p = fract(p * 0.3183099 + 0.1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }\n" +
    "float n3(vec3 x) { vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3.0 - 2.0 * f);\n" +
    "  return mix(mix(mix(h3(i), h3(i + vec3(1.0, 0.0, 0.0)), f.x), mix(h3(i + vec3(0.0, 1.0, 0.0)), h3(i + vec3(1.0, 1.0, 0.0)), f.x), f.y),\n" +
    "             mix(mix(h3(i + vec3(0.0, 0.0, 1.0)), h3(i + vec3(1.0, 0.0, 1.0)), f.x), mix(h3(i + vec3(0.0, 1.0, 1.0)), h3(i + vec3(1.0, 1.0, 1.0)), f.x), f.y), f.z); }\n" +
    "void main() {\n" +
    "  vec3 n = normalize(vN); vec3 base = vCol * uTint; float metal = vMat.x; float emis = vMat.y; float kind = vMat.z; float rough = 0.6 - metal * 0.4; float seam = 1.0;\n" +
    "  if (kind > 1.5 && kind < 2.5) { float g = n3(vObj * 3.0) * 0.6 + n3(vObj * 9.0) * 0.4; base *= 0.62 + 0.75 * g; rough = 0.95; n = normalize(n + (vec3(n3(vObj * 7.0), n3(vObj * 7.0 + 3.1), n3(vObj * 7.0 + 6.2)) - 0.5) * 0.5); }\n" +
    "  if (kind > 0.5 && kind < 1.5) { vec2 gp = vObj.xz * vec2(0.16, 0.12); gp.x += h3(vec3(floor(gp.y), 2.0, 5.0)) * 0.7; vec2 id = floor(gp); vec2 q = abs(fract(gp) - 0.5);\n" +
    "    seam = 1.0 - 0.32 * smoothstep(0.462, 0.49, q.y) - 0.22 * smoothstep(0.47, 0.495, q.x); base *= 0.93 + 0.14 * h3(vec3(id, 1.0)); rough -= 0.12 * h3(vec3(id, 4.0)); }\n" +
    "  float ndl = max(dot(n, uLight), 0.0); float fill = max(dot(n, uFill), 0.0);\n" +
    "  vec3 hv = normalize(uLight + uView); float sp = pow(max(dot(n, hv), 0.0), mix(12.0, 140.0, 1.0 - rough)) * (0.2 + 1.8 * metal) * (1.0 - rough * 0.6);\n" +
    "  float fres = pow(1.0 - max(dot(n, uView), 0.0), 3.0); vec3 r = reflect(-uView, n);\n" +
    "  vec3 env = mix(vec3(0.012, 0.02, 0.035), uEnv, smoothstep(-0.3, 0.95, r.y)) + vec3(0.9, 0.85, 0.75) * pow(max(dot(r, uLight), 0.0), 24.0) * 0.6;\n" +
    "  vec3 diff = base * (vec3(0.045, 0.055, 0.075) + vec3(1.0, 0.95, 0.88) * ndl * 1.2 + vec3(0.25, 0.42, 0.65) * fill * 0.5);\n" +
    "  vec3 col = mix(diff, diff * 0.35 + base * env * 1.7, metal * 0.7) + sp * vec3(1.0, 0.97, 0.9) + fres * (vec3(0.25, 0.5, 0.75) * 0.4 + env * metal * 0.6) * (kind > 1.5 && kind < 2.5 ? 0.3 : 1.0);\n" +
    "  if (kind > 2.5) col = base * (0.25 + ndl * 0.6) + env * (0.35 + fres * 1.2) + sp * 1.6 + base * 0.5;\n" +
    "  col *= seam; col = mix(col, base * 1.6 + vec3(0.18), emis); col += uGlowCol * uGlow * (emis * 1.4 + 0.12);\n" +
    "  col = mix(col, vec3(1.0, 0.55, 0.45), uFlash * 0.65);\n" +
    "  gl_FragColor = vec4(vec3(1.0) - exp(-col * 1.35), 1.0); }\n";
  var FX_VS = "attribute vec3 aPos; attribute vec2 aUV; attribute vec4 aCol; attribute float aMode;\n" + PROJECT +
    "varying vec2 vUV; varying vec4 vCol; varying float vMode;\n" +
    "void main() { vUV = aUV; vCol = aCol; vMode = aMode; gl_Position = project(aPos); gl_Position.z = 0.0; }\n";
  var FX_FS = GLSL_HEAD + "varying vec2 vUV; varying vec4 vCol; varying float vMode;\n" +
    "void main() { float r2 = dot(vUV, vUV); float r = sqrt(r2); float a = 0.0; float hot = 0.0;\n" +
    "  if (vMode < 0.5) { a = exp(-r2 * 3.6) * 0.8 + exp(-r2 * 26.0) * 0.7; hot = exp(-r2 * 40.0); }\n" +
    "  else if (vMode < 1.5) { a = exp(-pow((r - 0.84) * 10.0, 2.0)) + exp(-pow((r - 0.84) * 34.0, 2.0)) * 0.6; }\n" +
    "  else if (vMode < 2.5) { float u = vUV.x; a = (exp(-u * u * 5.0) * 0.6 + exp(-u * u * 70.0)) * (0.8 + 0.2 * sin(vUV.y * 60.0)); hot = exp(-u * u * 90.0); }\n" +
    "  else if (vMode < 3.5) { a = exp(-(vUV.x * vUV.x * 5.0 + vUV.y * vUV.y * 1.3)) * 0.7 + exp(-(vUV.x * vUV.x * 40.0 + vUV.y * vUV.y * 3.0)); hot = exp(-(vUV.x * vUV.x * 60.0 + vUV.y * vUV.y * 6.0)); }\n" +
    "  else if (vMode < 4.5) { a = step(r, 1.0) * (0.1 + 0.9 * pow(r, 8.0)) + exp(-pow((r - 1.0) * 30.0, 2.0)) * 0.5; }\n" +
    "  else { a = step(r, 1.0) * (pow(r, 6.0) * 0.85 + 0.05) + exp(-pow((r - 1.0) * 25.0, 2.0)) * 0.4; }\n" +
    "  gl_FragColor = vec4(vCol.rgb * a * vCol.a + vec3(hot) * vCol.a * 0.55, 0.0); }\n";
  var BG_VS = "attribute vec2 aPos; uniform vec3 uWorld; varying vec2 vW;\n" +
    "void main() { vW = vec2((aPos.x + 1.0) * 0.5 * uWorld.x, (1.0 - aPos.y) * 0.5 * uWorld.y); gl_Position = vec4(aPos, 0.999, 1.0); }\n";
  var BG_FS = GLSL_HEAD +
    "uniform vec3 uWorld; uniform vec3 uScroll; uniform vec3 uNebA; uniform vec3 uNebB; uniform vec4 uPlanet; uniform vec3 uPlanetA; uniform vec3 uPlanetB; uniform float uT;\n" +
    "varying vec2 vW;\n" +
    "float h2(vec2 p) { p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }\n" +
    "float n2(vec2 x) { vec2 i = floor(x); vec2 f = fract(x); f = f * f * (3.0 - 2.0 * f); return mix(mix(h2(i), h2(i + vec2(1.0, 0.0)), f.x), mix(h2(i + vec2(0.0, 1.0)), h2(i + vec2(1.0, 1.0)), f.x), f.y); }\n" +
    "float fbm(vec2 p) { float s = 0.0; float a = 0.5; for (int i = 0; i < 4; i++) { s += a * n2(p); p = p * 2.03 + vec2(1.7, 9.2); a *= 0.5; } return s; }\n" +
    "float stars(vec2 p, float cell, float off, float dens) { vec2 g = vec2(p.x, p.y - off) / cell; vec2 id = floor(g); vec2 f = fract(g); float h = h2(id);\n" +
    "  if (h < 1.0 - dens) return 0.0; vec2 o = vec2(h2(id + 3.7), h2(id + 9.1)) * 0.8 + 0.1; float d = length((f - o) * cell);\n" +
    "  return (0.4 + 0.6 * h2(id + 1.3)) * (exp(-d * d * 0.9) + exp(-d * 0.9) * 0.08); }\n" +
    "void main() {\n" +
    "  vec2 p = vW; vec2 q = vec2(p.x, p.y - uScroll.x * 0.35) / 520.0;\n" +
    "  float w = fbm(q * 1.4 + 3.0); float n = fbm(q + w * 0.9); float m = fbm(q * 2.6 + 7.0 + w);\n" +
    "  vec3 col = mix(vec3(0.006, 0.012, 0.024), vec3(0.012, 0.03, 0.05), p.y / uWorld.y);\n" +
    "  col += uNebA * pow(n, 2.6) * 0.75 + uNebB * pow(m, 3.2) * 0.6;\n" +
    "  col += vec3(0.9, 0.95, 1.0) * (stars(p, 26.0, uScroll.x, 0.12) * 0.5 + stars(p, 44.0, uScroll.y, 0.16) * 0.75 + stars(p, 82.0, uScroll.z, 0.22));\n" +
    "  vec2 d = (p - uPlanet.xy) / uPlanet.z; float r2 = dot(d, d);\n" +
    "  vec3 L = normalize(vec3(-0.65, 0.55, -0.55));\n" +
    "  if (r2 < 1.0) { vec3 nn = vec3(d.x, sqrt(1.0 - r2), d.y); float lit = max(dot(nn, L), 0.0);\n" +
    "    float band = fbm(vec2(d.x * 2.2 + uT * 0.0002, d.y * 7.0) + fbm(d * 4.0) * 1.4);\n" +
    "    vec3 surf = mix(uPlanetA, uPlanetB, band); float rim = pow(1.0 - nn.y, 2.5);\n" +
    "    col = mix(col, surf * (0.04 + lit * 0.9) + uPlanetB * rim * (0.2 + lit) * 0.6, uPlanet.w); }\n" +
    "  else { float e = sqrt(r2) - 1.0; col += uPlanetB * exp(-e * 22.0) * 0.45 * uPlanet.w * max(dot(normalize(vec3(d.x, 0.2, d.y)), L) + 0.3, 0.0); }\n" +
    "  gl_FragColor = vec4(col, 1.0); }\n";
  var LEVEL_SKY = {
    1: { a: [0.03, 0.2, 0.26], b: [0.08, 0.06, 0.2], planet: [0.13, 1.06, 0.46], pa: [0.03, 0.12, 0.22], pb: [0.25, 0.65, 0.9], env: [0.32, 0.5, 0.62] },
    2: { a: [0.14, 0.06, 0.24], b: [0.02, 0.14, 0.2], planet: [0.9, 1.0, 0.52], pa: [0.24, 0.12, 0.3], pb: [0.75, 0.5, 0.95], env: [0.42, 0.4, 0.62] },
    3: { a: [0.26, 0.07, 0.05], b: [0.16, 0.03, 0.12], planet: [0.15, 1.04, 0.48], pa: [0.25, 0.06, 0.03], pb: [1.0, 0.45, 0.2], env: [0.6, 0.42, 0.38] }
  };

  function glCompile(gl, type, src) {
    var s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS) && !gl.isContextLost()) throw new Error("SkySentinel shader: " + gl.getShaderInfoLog(s));
    return s;
  }
  function glProgram(gl, vs, fs, attrs) {
    var p = gl.createProgram();
    gl.attachShader(p, glCompile(gl, gl.VERTEX_SHADER, vs));
    gl.attachShader(p, glCompile(gl, gl.FRAGMENT_SHADER, fs));
    attrs.forEach(function (a, i) { gl.bindAttribLocation(p, i, a); });
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS) && !gl.isContextLost()) throw new Error("SkySentinel link: " + gl.getProgramInfoLog(p));
    var u = {}, n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS) || 0;
    for (var i = 0; i < n; i++) { var info = gl.getActiveUniform(p, i); u[info.name] = gl.getUniformLocation(p, info.name); }
    return { p: p, u: u, attrs: attrs.length };
  }
  var MAX_QUADS = 3000;
  /* Shader programs, mesh buffers, and the sprite buffer for one context. */
  function glSetup(gl) {
    var R = { gl: gl, mesh: glProgram(gl, MESH_VS, MESH_FS, ["aPos", "aNor", "aCol", "aMat"]),
      fx: glProgram(gl, FX_VS, FX_FS, ["aPos", "aUV", "aCol", "aMode"]), bg: glProgram(gl, BG_VS, BG_FS, ["aPos"]), buf: {} };
    var all = meshes();
    function upload(name, def) {
      var b = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, b);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(def.mesh.v), gl.STATIC_DRAW);
      R.buf[name] = { b: b, n: def.mesh.v.length / 12 };
    }
    Object.keys(all).forEach(function (k) { if (k !== "rocks") upload(k, all[k]); });
    all.rocks.forEach(function (r, i) { upload("rock" + i, r); });
    R.bgBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, R.bgBuf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, 1, 1, -1, -1, 1, 1, -1, 1]), gl.STATIC_DRAW);
    R.fxData = new Float32Array(MAX_QUADS * 6 * 10);
    R.fxBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, R.fxBuf);
    gl.bufferData(gl.ARRAY_BUFFER, R.fxData.byteLength, gl.DYNAMIC_DRAW);
    return R;
  }
  /* A model matrix (column-major) from position, yaw (about y), pitch (about x), roll (about z),
     and a uniform scale: M = T * Ry * Rx * Rz * S. */
  function modelMat(out, x, y, z, yaw, pitch, roll, s) {
    var cy = Math.cos(yaw), sy = Math.sin(yaw), cp = Math.cos(pitch), sp = Math.sin(pitch), cr = Math.cos(roll), sr = Math.sin(roll);
    var a = [cy, sy * sp, sy * cp, 0, cp, -sp, -sy, cy * sp, cy * cp];   /* Ry * Rx, row-major */
    var m = [a[0] * cr + a[1] * sr, -a[0] * sr + a[1] * cr, a[2], a[3] * cr + a[4] * sr, -a[3] * sr + a[4] * cr, a[5], a[6] * cr + a[7] * sr, -a[6] * sr + a[7] * cr, a[8]];
    out[0] = m[0] * s; out[1] = m[3] * s; out[2] = m[6] * s; out[3] = 0;
    out[4] = m[1] * s; out[5] = m[4] * s; out[6] = m[7] * s; out[7] = 0;
    out[8] = m[2] * s; out[9] = m[5] * s; out[10] = m[8] * s; out[11] = 0;
    out[12] = x; out[13] = y; out[14] = z; out[15] = 1;
    return out;
  }
  function xform(m, p) { return [m[0] * p[0] + m[4] * p[1] + m[8] * p[2] + m[12], m[1] * p[0] + m[5] * p[1] + m[9] * p[2] + m[13], m[2] * p[0] + m[6] * p[1] + m[10] * p[2] + m[14]]; }
  function hexRgb(h) { var n = parseInt(h.slice(1), 16); return [(n >> 16 & 255) / 255, (n >> 8 & 255) / 255, (n & 255) / 255]; }

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
    function newCanvas() {
      var c = el("canvas", "ss-canvas");
      c.setAttribute("role", "application");
      c.setAttribute("aria-roledescription", "game");
      c.setAttribute("aria-label", "Sky Sentinel arena");
      c.tabIndex = 0;
      return c;
    }
    var canvas = newCanvas();
    /* Pick the renderer before any listener binds to the canvas: a canvas that gave out a WebGL
       context can never give a 2D one, so a failed WebGL setup swaps in a fresh canvas. */
    var want2d = opts.renderer === "2d" || host.getAttribute("data-ss-renderer") === "2d" || window.SKY_SENTINEL_RENDERER === "2d";
    var glr = null, ctx = null, hudCanvas = null, renderer = "none";
    function startGL(c) {
      var gl = null;
      try { gl = c.getContext("webgl", { alpha: false, antialias: true, premultipliedAlpha: false }) || c.getContext("experimental-webgl", { alpha: false, antialias: true }); } catch (err) { gl = null; }
      if (!gl) return null;
      try { return glSetup(gl); } catch (err) { if (window.console) console.warn(String(err && err.message || err)); return false; }
    }
    if (!want2d) {
      glr = startGL(canvas);
      if (glr === false) { glr = null; canvas = newCanvas(); }
    }
    if (glr) {
      renderer = "webgl";
      hudCanvas = el("canvas", "ss-hudcanvas");
      hudCanvas.setAttribute("aria-hidden", "true");
      hudCanvas.style.cssText = "position:absolute;left:0;top:0;width:100%;height:100%;pointer-events:none;";
      try { ctx = hudCanvas.getContext("2d"); } catch (err) { ctx = null; }
    } else {
      try { ctx = canvas.getContext("2d"); } catch (err) { ctx = null; }
      if (ctx) renderer = "2d";
    }
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
    if (hudCanvas) stage.appendChild(hudCanvas);
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
    host.setAttribute("data-ss-renderer-active", renderer);
    if (renderer === "none") { fallback.hidden = false; stage.hidden = true; }
    if (glr) {
      canvas.addEventListener("webglcontextlost", function (ev) { ev.preventDefault(); glr.lost = true; });
      canvas.addEventListener("webglcontextrestored", function () { try { var g = glr.gl; glr = glSetup(g); draw(); } catch (err) { if (window.console) console.warn(err); } });
    }

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
      if (hudCanvas) { hudCanvas.width = canvas.width; hudCanvas.height = canvas.height; }
      draw();
    }

    /* ---------- simulation */
    function diff() { return DIFFICULTY[cfg.progression ? S.level : 1]; }
    function reset() {
      var before = world.w, beforeH = world.h;
      chooseWorld();
      var reshaped = world.w !== before || world.h !== beforeH;
      var r = streams(cfg.seed);
      var level = cfg.progression ? Math.max(1, Math.min(3, cfg.level)) : 1;
      S = {
        rng: r, tick: 0, state: "idle", pausedBy: null, score: 0, level: level, levelTicks: 0,
        player: { x: world.w / 2, y: world.h - 70, r: 18, health: HEALTH_MAX, shieldHp: 0, invuln: 0, cooldown: 0, weapon: 0,
                  spread: 0, rapid: 0, missiles: 0, wingman: 0, missileIn: 0, wingIn: 0, bank: 0, hurt: 0 },
        enemies: [], enemyShots: [], shots: [], asteroids: [], powerUps: [], effects: [], popups: [],
        spawnIn: 50, rockIn: 240, firstShotTick: null, firstShotGap: null, spawned: 0,
        nextExplosion: firstExplosion(r.defects), explodeTicks: [], hitTicks: [], damageLog: [], lastDamage: null, damageTaken: 0,
        breaks: [], collected: [], levelUps: [], boss: null, bossDue: cfg.boss && level === 3 ? (cfg.bossNow ? BOSS_AFTER_JUMP : BOSS_AFTER) : null,
        overReason: null, overText: null, victory: false, banner: null, shake: 0
      };
      acc = 0;
      sync();
      if (reshaped) fit(); else draw();
    }

    function pickType(rng) {
      var x = rng(), mix = diff().mix, a = 0;
      for (var k = 0; k < mix.length; k++) { a += mix[k][1]; if (x < a) return mix[k][0]; }
      return mix[mix.length - 1][0];
    }
    function makeEnemy(type, x, y) {
      var spec = ENEMY[type];
      return { type: type, x: x, y: y, r: spec.r, vx: 0, vy: 0, phase: 0, hp: spec.hp, charge: 0, beamT: 0, cycles: 0,
               fireIn: 1, mode: "enter", holdY: 0, flash: 0, bank: 0, pinned: false };
    }
    function spawnEnemy() {
      var rng = S.rng.spawn, d = diff();
      var type = pickType(rng);
      var spec = ENEMY[type];
      var edge = spec.r + 30;
      var x = edge + rng() * (world.w - 2 * edge);
      /* interceptors come as a swarm: one at Easy, two at Medium, three at Hard */
      var n = type === "interceptor" ? (cfg.progression ? S.level : 1) : 1;
      for (var k = 0; k < n; k++) {
        var e = makeEnemy(type, clamp(x + (k - (n - 1) / 2) * 38, spec.r, world.w - spec.r), -26 - k * 22);
        e.vx = (rng() - 0.5) * (type === "interceptor" ? 1.2 : 1.4);
        e.vy = type === "interceptor" ? 2.6 : type === "lancer" ? 0.9 : type === "bomber" ? 0.45 + rng() * 0.3 : 0.7 + rng() * 0.6;
        e.phase = rng() * Math.PI * 2;
        e.fireIn = 50 + Math.floor(rng() * 110);
        e.holdY = world.h * (type === "lancer" ? 0.12 + rng() * 0.16 : 0.18 + rng() * 0.12);
        S.enemies.push(e);
        S.spawned += 1;
      }
    }
    function makeRock(size, x, y, vx, vy, rng) {
      var spec = ROCK[size];
      return { size: size, x: x, y: y, r: spec.r[0] + Math.floor(rng() * (spec.r[1] - spec.r[0] + 1)), vx: vx, vy: vy, hp: spec.hp,
               spin: rng() * 6.28, rx: rng() * 6.28, spinV: (rng() - 0.5) * 0.04, rxV: (rng() - 0.5) * 0.03, look: Math.floor(rng() * 6), flash: 0 };
    }
    function spawnRock() {
      var rng = S.rng.spawn, size = rng() < 0.5 ? "large" : "medium";
      var r = ROCK[size].r[1];
      S.asteroids.push(makeRock(size, r + rng() * (world.w - 2 * r), -r, (rng() - 0.5) * 1.2, 1.0 + rng() * 1.1, rng));
    }
    /* A destroyed rock splits into two or three of the next size, flung outward; a small one
       turns to dust. The rocks stream drives it, so shooting never shifts the spawns. */
    function breakRock(j) {
      var a = S.asteroids[j], spec = ROCK[a.size], rng = S.rng.rocks;
      S.asteroids.splice(j, 1);
      S.score += spec.score;
      var into = spec.into, n = into ? 2 + (rng() < 0.5 ? 1 : 0) : 0;
      dust(a.x, a.y, a.r);
      for (var k = 0; k < n; k++) {
        var ang = rng() * 6.283 / n + k * 6.283 / n, sp = 1.1 + rng() * 1.1;
        var c = makeRock(into, a.x + Math.cos(ang) * a.r * 0.4, a.y + Math.sin(ang) * a.r * 0.4, a.vx * 0.6 + Math.cos(ang) * sp, Math.max(0.4, a.vy * 0.7 + Math.sin(ang) * sp), rng);
        S.asteroids.push(c);
      }
      S.breaks.push({ size: a.size, into: n, tick: S.tick });
      emit("asteroidBreak", { size: a.size, into: n, tick: S.tick });
    }
    function spawnPowerUp(kind, x, y) { S.powerUps.push({ kind: kind, x: x, y: y, r: 14, t: 0 }); }

    function enemyMayFire(e) {
      if (S.tick < GRACE_TICKS) return false;
      if (S.firstShotTick === null && S.player.y - e.y < FIRST_SHOT_CLEARANCE) return false;
      return e.y > 0 && e.y < world.h * 0.75;
    }
    function enemyShot(x, y, vx, vy, kind, extra) {
      var o = { x: x, y: y, r: kind === "bomb" ? 8 : kind === "needle" ? 3.5 : 5, vx: vx, vy: vy, kind: kind || "bolt", t: 0, src: "shot" };
      if (extra) for (var k in extra) o[k] = extra[k];
      S.enemyShots.push(o);
      if (S.firstShotTick === null) { S.firstShotTick = S.tick; S.firstShotGap = S.player.y - y; }
      return o;
    }
    /* Fire an enemy's weapon; returns the ticks until it may fire again, scaled by difficulty. */
    function enemyFire(e) {
      var p = S.player, d = diff(), rng = S.rng.spawn;
      var dx = p.x - e.x, dy = Math.max(60, p.y - e.y), len = Math.sqrt(dx * dx + dy * dy);
      if (e.type === "gunship") {
        /* aimed loosely, as a pilot leads a target, so a moving ship can slip out of the line */
        var aim = clamp(dx / 110, -2.4, 2.4) * 0.75;
        for (var b = 0; b < d.burst; b++) enemyShot(e.x + (b ? 7 : -7) * (d.burst - 1), e.y + e.r, aim + (b ? 0.5 : -0.5) * (d.burst - 1), 5.8, "bolt");
        return Math.round((100 + Math.floor(rng() * 70)) * d.fire);
      }
      if (e.type === "interceptor") {
        enemyShot(e.x - 4, e.y + e.r, dx / len * 1.6, 7.4, "needle", { src: "needle" });
        enemyShot(e.x + 4, e.y + e.r, dx / len * 1.6, 7.4, "needle", { src: "needle" });
        return Math.round((130 + Math.floor(rng() * 60)) * d.fire);
      }
      if (e.type === "lancer") { e.charge = 50; return Math.round((220 + Math.floor(rng() * 90)) * d.fire); }
      /* a bomb never aims closer to a wall than its blast reaches, so it cannot pin a ship there */
      var wall = PLAYER[cfg.progression ? S.level : 1].w * VIS + BLAST_RADIUS + 28;
      var tx = clamp(p.x, wall, world.w - wall), ty = p.y, bl = Math.sqrt((tx - e.x) * (tx - e.x) + (ty - e.y) * (ty - e.y)) || 1;
      enemyShot(e.x, e.y + e.r * 0.4, (tx - e.x) / bl * 2.8, (ty - e.y) / bl * 2.8, "bomb", { tx: tx, ty: ty, fuse: 260, arm: 0, src: "blast" });
      return Math.round((250 + Math.floor(rng() * 90)) * d.fire);
    }
    function moveEnemy(e) {
      var p = S.player;
      if (e.flash > 0) e.flash -= 1;
      var before = e.x;
      if (e.pinned) { /* a test placed it: it stays put */ }
      else if (e.type === "interceptor") {
        if (e.mode === "enter") { e.x += e.vx; e.y += e.vy; if (e.y > e.holdY) e.mode = "dive"; }
        else {
          e.vx = clamp(e.vx + clamp((p.x - e.x) * 0.004, -0.13, 0.13), -3, 3);
          e.vy = Math.min(4.2, e.vy + 0.06);
          e.x += e.vx; e.y += e.vy;
        }
      } else if (e.type === "lancer") {
        if (e.mode === "leave") e.y += 1.3;
        else if (e.y < e.holdY) e.y += e.vy;
        /* while it is not charging or firing, a lancer slides toward the ship's column */
        if (e.charge === 0 && e.beamT === 0 && e.mode !== "leave") e.x += clamp(p.x - e.x, -0.8, 0.8);
      } else {
        e.phase += 0.04;
        var sway = Math.sin(e.phase) * (e.type === "bomber" ? 0.5 : 0.9);
        if (e.x + e.vx + sway < e.r || e.x + e.vx + sway > world.w - e.r) e.vx = -e.vx;
        e.x = clamp(e.x + e.vx + sway, e.r, world.w - e.r);
        e.y += e.vy;
      }
      e.bank = e.bank * 0.85 + clamp((e.x - before) * 0.25, -0.6, 0.6) * 0.15;
      /* A lancer's charge is its tell: the beam fires when the charge runs out. */
      if (e.charge > 0 && --e.charge === 0) {
        enemyShot(e.x, e.y + e.r, 0, 0, "beam", { life: 40, span: 40, owner: e, src: "beam" });
        e.beamT = 40;
        e.cycles += 1;
        if (e.cycles >= 3 && !e.pinned) e.mode = "leave";
      }
      if (e.beamT > 0) e.beamT -= 1;
      e.fireIn -= 1;
      if (e.fireIn <= 0 && e.charge === 0 && e.beamT === 0) e.fireIn = enemyMayFire(e) ? enemyFire(e) : 12;
    }
    function detonate(o) {
      var p = S.player, d = Math.hypot(p.x - o.x, p.y - o.y);
      boom(o.x, o.y, 1.5, "#fb923c");
      S.effects.push({ kind: "blast", x: o.x, y: o.y, t: 0, life: 30, size: BLAST_RADIUS, color: "#fdba74" });
      if (d < BLAST_RADIUS && S.state === "running") hitPlayer("blast", "bomber", d);
    }
    function moveEnemyShots() {
      var out = [], p = S.player;
      for (var i = 0; i < S.enemyShots.length; i++) {
        var o = S.enemyShots[i];
        o.t += 1;
        if (o.kind === "beam") { o.life -= 1; if (o.owner && S.enemies.indexOf(o.owner) !== -1) { o.x = o.owner.x; o.y = o.owner.y + o.owner.r; } if (o.life <= 0) continue; }
        else if (o.kind === "bomb") {
          if (o.arm === 0) {
            o.x += o.vx; o.y += o.vy; o.fuse -= 1;
            /* proximity fuse: it arms near the ship, at its aim point, or when the fuse runs out */
            if (Math.hypot(p.x - o.x, p.y - o.y) < 56 || Math.hypot(o.tx - o.x, o.ty - o.y) < 6 || o.fuse <= 0) o.arm = BOMB_ARM;
          } else if (--o.arm === 0) { detonate(o); continue; }
        } else { o.x += o.vx; o.y += o.vy; }
        out.push(o);
      }
      S.enemyShots = out;
    }
    function shotHitsPlayer(o, p) {
      if (o.kind === "bomb") return false;
      if (o.kind === "beam") return o.life <= o.span - 6 && Math.abs(p.x - o.x) < 10 + p.r * 0.5 && p.y > o.y;
      return overlaps(o, p, -4);
    }

    /* ---------- health and damage */
    function damageFor(source, detail, dist) {
      var k = diff().damage, base;
      if (source === "asteroid") base = DAMAGE.asteroid[detail] || DAMAGE.asteroid.large;
      else if (source === "collision") base = DAMAGE.collision[detail] || DAMAGE.collision.gunship;
      else if (source === "blast") {
        var dd = typeof dist === "number" ? dist : typeof detail === "number" ? detail : 0;
        if (dd >= BLAST_RADIUS) return 0;
        base = DAMAGE.blast * (1 - 0.8 * Math.max(0, dd) / BLAST_RADIUS);
      } else base = DAMAGE[source] != null && typeof DAMAGE[source] === "number" ? DAMAGE[source] : DAMAGE.test;
      return Math.max(1, Math.round(base * k));
    }
    function sourceText(source, detail) {
      if (source === "asteroid") return detail === "small" ? "a small asteroid chunk" : "a " + (detail || "large") + " asteroid";
      if (source === "collision") return detail === "boss" ? SOURCE_TEXT.boss : "a collision with " + (detail === "interceptor" ? "an " : "a ") + (detail || "gunship");
      return SOURCE_TEXT[source] || "a hit";
    }
    function popup(x, y, text, color) { S.popups.push({ x: x, y: y, text: text, color: color, t: 0, life: 60 }); }
    function hitPlayer(source, detail, dist) {
      var p = S.player;
      if (S.state !== "running" || p.health <= 0) return false;
      if (p.invuln > 0) return false;
      var amount = damageFor(source, detail, dist);
      if (amount <= 0) return false;
      S.hitTicks.push(S.tick);
      emit("hit", { source: source, detail: detail, tick: S.tick });
      if (cfg.defects.firstHitFatal) {
        /* the defect: any hit, from any source, destroys the ship outright. The bars keep what
           the hit should have left, so the end screen shows a ship destroyed with health to spare. */
        S.lastDamage = { source: source, detail: detail == null ? null : detail, amount: amount, absorbed: 0, tick: S.tick, fatal: true };
        S.damageLog.push(S.lastDamage);
        S.damageTaken += amount;
        boom(p.x, p.y, 2.4, "#fbbf24");
        shards(p.x, p.y, 10);
        S.overText = "Destroyed by a single hit: " + sourceText(source, detail);
        gameOver("first-hit");
        return true;
      }
      applyDamage(amount, source, detail);
      if (S.state === "running") p.invuln = HIT_INVULN;
      return true;
    }
    function applyDamage(amount, source, detail) {
      var p = S.player, absorbed = source === "explode" ? 0 : Math.min(p.shieldHp, amount);
      p.shieldHp -= absorbed;
      p.health = Math.max(0, p.health - (amount - absorbed));
      p.hurt = 14;
      S.shake = Math.min(12, 3 + amount * 0.25);
      S.lastDamage = { source: source, detail: detail == null ? null : detail, amount: amount, absorbed: absorbed, tick: S.tick };
      S.damageLog.push(S.lastDamage);
      if (S.damageLog.length > 40) S.damageLog.shift();
      S.damageTaken += amount;
      if (absorbed) ring(p.x, p.y, "#60a5fa");
      popup(p.x, p.y - 30, "-" + amount, absorbed === amount ? "#93c5fd" : "#fca5a5");
      emit("damage", { source: source, detail: detail, amount: amount, absorbed: absorbed, health: p.health, shield: p.shieldHp, tick: S.tick });
      if (p.health <= 0) {
        boom(p.x, p.y, 2.4, "#fbbf24");
        shards(p.x, p.y, 10);
        S.overText = source === "explode" ? "The ship blew itself up, with no hit" : "Hull destroyed by " + sourceText(source, detail);
        gameOver(source === "explode" ? "explode" : "hit");
        return;
      }
      say(source === "explode" ? "The ship exploded with no hit. Hull " + p.health + "." :
        "Hit by " + sourceText(source, detail) + ": " + amount + " damage. Hull " + p.health + (p.shieldHp ? ", shield " + p.shieldHp : "") + ".");
    }

    function gameOver(reason) {
      S.state = "over";
      /* The explosion plays out for a moment after the run ends instead of freezing on its first frame. */
      S.afterglow = REDUCED ? 0 : 90;
      S.overReason = reason;
      held.left = held.right = held.up = held.down = held.fire = false;
      if (reason === "victory") {
        say("The Nexus megaship is down. Score " + S.score + ".");
      } else {
        emit("destroyed", { reason: reason, tick: S.tick, score: S.score, text: S.overText });
        say(reason === "first-hit" ? S.overText + ", with the hull still full. That is the bug." : (S.overText || "Game over") + ". Score " + S.score + ".");
      }
      sync();
    }

    /* Explosions: a white flash, a shock ring, fireballs, sparks, and tumbling shards. */
    function boom(x, y, size, color) {
      var fx = S.rng.fx, s = size || 1, nFire = REDUCED ? 3 : 9, nSpark = REDUCED ? 4 : 12;
      S.effects.push({ kind: "flash", x: x, y: y, t: 0, life: 12, size: s, color: "#fff7e0" });
      S.effects.push({ kind: "ring", x: x, y: y, t: 0, size: s, color: color || "#fbbf24", life: 36 });
      for (var k = 0; k < nFire; k++) {
        var a = fx() * 6.283, v = (0.3 + fx() * 1.3) * s;
        S.effects.push({ kind: "fire", x: x + Math.cos(a) * 4 * s, y: y + Math.sin(a) * 4 * s, vx: Math.cos(a) * v, vy: Math.sin(a) * v, t: 0, life: 28 + Math.floor(fx() * 26), size: (8 + fx() * 10) * s, color: color || "#fbbf24" });
      }
      for (k = 0; k < nSpark; k++) {
        var b = fx() * 6.283, w = (2 + fx() * 4) * s;
        S.effects.push({ kind: "spark", x: x, y: y, vx: Math.cos(b) * w, vy: Math.sin(b) * w, t: 0, life: 18 + Math.floor(fx() * 18), color: color || "#fbbf24" });
      }
    }
    function shards(x, y, n) {
      var fx = S.rng.fx;
      for (var k = 0; k < (REDUCED ? 3 : n); k++) {
        var a = fx() * 6.283, v = 1 + fx() * 3;
        S.effects.push({ kind: "debris", x: x, y: y, vx: Math.cos(a) * v, vy: Math.sin(a) * v, t: 0, life: 40 + Math.floor(fx() * 30), size: 2 + fx() * 3, spin: fx() * 6, color: "#94a3b8" });
      }
    }
    function dust(x, y, r) {
      var fx = S.rng.fx;
      S.effects.push({ kind: "flash", x: x, y: y, t: 0, life: 10, size: r / 28, color: "#ffe9c7" });
      for (var k = 0; k < (REDUCED ? 3 : 8); k++) {
        var a = fx() * 6.283, v = 0.4 + fx() * 1.4;
        S.effects.push({ kind: "dust", x: x + Math.cos(a) * r * 0.5, y: y + Math.sin(a) * r * 0.5, vx: Math.cos(a) * v, vy: Math.sin(a) * v, t: 0, life: 30 + Math.floor(fx() * 24), size: r * (0.5 + fx() * 0.5), color: "#b8a48c" });
      }
      for (k = 0; k < (REDUCED ? 2 : 5); k++) {
        var c = fx() * 6.283, w = 1 + fx() * 2.5;
        S.effects.push({ kind: "debris", x: x, y: y, vx: Math.cos(c) * w, vy: Math.sin(c) * w, t: 0, life: 36 + Math.floor(fx() * 20), size: 1.5 + fx() * 2.5, spin: fx() * 6, color: "#8a7d70", rock: true });
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
      var d = DIFFICULTY[S.level];
      S.banner = { text: "Level " + S.level + ": " + d.name, sub: "The " + FORMS[S.level] + ". " + d.note, t: 170 };
      emit("levelUp", { level: S.level, form: FORMS[S.level], difficulty: d.name, tick: S.tick });
      say("Level " + S.level + ", " + d.name + ". The ship becomes the " + FORMS[S.level] + ". " + d.note + ".");
      if (S.level === 3 && cfg.boss) S.bossDue = BOSS_AFTER;
    }
    function collect(pu) {
      var p = S.player;
      S.collected.push({ kind: pu.kind, tick: S.tick });
      ring(pu.x, pu.y, (POWER_LOOK[pu.kind] || POWER_LOOK.repair)[0]);
      if (pu.kind === "shield") { p.shieldHp = SHIELD_MAX; say("Shield up: a second bar of " + SHIELD_MAX + " that takes damage first."); }
      else if (pu.kind === "weapon") { p.weapon = WEAPON_TICKS; say("Twin shot for 10 seconds."); }
      else if (pu.kind === "repair") { var before = p.health; p.health = Math.min(HEALTH_MAX, p.health + REPAIR); popup(p.x, p.y - 30, "+" + (p.health - before), "#6ee7b7"); say("Repaired. Hull " + p.health + "."); }
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
          enemyShot(at[0], at[1], dx / d * 4.2, dy / d * 4.2, "bolt", { src: "bossShot" });
          n.fireIn = 84;
        }
      });
      if (b.entered && nodesAlive(b) === 0) {
        b.fireIn -= 1;
        if (b.fireIn <= 0) {
          for (var k = -2; k <= 2; k++) enemyShot(b.x, b.y + LOGO.coreR * b.s, k * 1.3, 4.4, "bolt", { src: "bossShot" });
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

    function dropFrom(en) {
      if (!cfg.progression || S.rng.drops() >= DROP_CHANCE) return;
      var k = S.rng.drops(), acc2 = 0, kind = "repair";
      for (var d = 0; d < DROPS.length; d++) { acc2 += DROPS[d][1]; if (k < acc2) { kind = DROPS[d][0]; break; } }
      spawnPowerUp(kind, en.x, en.y);
    }

    function tick() {
      var p = S.player, i, j;
      S.tick += 1;

      /* player */
      var dx = (held.right ? 1 : 0) - (held.left ? 1 : 0);
      var dy = (held.down ? 1 : 0) - (held.up ? 1 : 0);
      /* Clamp by the drawn wingspan, not the hit radius, so the ship never leaves the frame. */
      var span = PLAYER[cfg.progression ? S.level : 1].w * VIS + 2;
      p.x = Math.max(span, Math.min(world.w - span, p.x + dx * 7));
      p.y = Math.max(world.h * 0.55, Math.min(world.h - p.r - 6, p.y + dy * 6));
      p.bank = p.bank * 0.82 + dx * 0.55 * 0.18;
      if (p.invuln > 0) p.invuln -= 1;
      if (p.hurt > 0) p.hurt -= 1;
      if (S.shake > 0) S.shake = Math.max(0, S.shake - 0.8);
      if (p.cooldown > 0) p.cooldown -= 1;
      if (held.fire && p.cooldown === 0) fire();
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
        var d = diff(), t = cfg.progression ? S.levelTicks : S.tick;
        S.spawnIn -= 1;
        if (S.spawnIn <= 0) {
          if (S.enemies.length < d.cap) spawnEnemy();
          var pace = d.pace - Math.floor(t / 900) * 3;
          S.spawnIn = Math.max(Math.round(d.pace * 0.6), pace) + Math.floor(S.rng.spawn() * 30);
        }
        S.rockIn -= 1;
        if (S.rockIn <= 0) { spawnRock(); S.rockIn = d.rocks + Math.floor(S.rng.spawn() * 160); }
      }
      if (S.boss) bossTick();

      /* movement */
      moveShots();
      for (i = 0; i < S.enemies.length; i++) moveEnemy(S.enemies[i]);
      moveEnemyShots();
      if (S.state !== "running") return;
      for (i = 0; i < S.asteroids.length; i++) {
        var a = S.asteroids[i];
        a.x += a.vx; a.y += a.vy; a.spin += a.spinV; a.rx += a.rxV;
        if (a.flash > 0) a.flash -= 1;
      }
      for (i = 0; i < S.powerUps.length; i++) { S.powerUps[i].y += 1.8; S.powerUps[i].t += 1; }
      for (i = 0; i < S.effects.length; i++) {
        var f = S.effects[i];
        f.t += 1;
        if (f.vx != null) { f.x += f.vx; f.y += f.vy; var drag = f.kind === "spark" ? 0.93 : f.kind === "debris" ? 0.97 : 0.94; f.vx *= drag; f.vy *= drag; }
      }
      for (i = 0; i < S.popups.length; i++) { S.popups[i].t += 1; S.popups[i].y -= 0.6; }

      /* collisions: player shots */
      for (i = S.shots.length - 1; i >= 0; i--) {
        var s = S.shots[i], used = shotHitsBoss(s);
        if (!S.boss && S.state === "over") return;
        for (j = S.enemies.length - 1; j >= 0 && !used; j--) {
          var en = S.enemies[j];
          if (overlaps(s, en)) {
            used = true;
            en.hp -= 1;
            en.flash = 5;
            if (en.hp <= 0) {
              boom(en.x, en.y, en.type === "bomber" ? 1.6 : en.type === "interceptor" ? 0.8 : 1.15, { gunship: "#fb7185", interceptor: "#e879f9", lancer: "#fb923c", bomber: "#facc15" }[en.type]);
              shards(en.x, en.y, 6);
              S.enemies.splice(j, 1);
              S.score += ENEMY[en.type].score;
              dropFrom(en);
            }
          }
        }
        for (j = S.enemyShots.length - 1; j >= 0 && !used; j--) {
          var bomb = S.enemyShots[j];
          if (bomb.kind === "bomb" && bomb.arm === 0 && overlaps(s, bomb, 4)) { used = true; S.enemyShots.splice(j, 1); detonate(bomb); S.score += 20; }
        }
        for (j = S.asteroids.length - 1; j >= 0 && !used; j--) {
          if (overlaps(s, S.asteroids[j])) {
            used = true;
            S.asteroids[j].hp -= 1;
            S.asteroids[j].flash = 4;
            if (S.asteroids[j].hp <= 0) breakRock(j);
          }
        }
        if (used || s.y < -10 || s.y > world.h + 10 || s.x < -10 || s.x > world.w + 10) S.shots.splice(i, 1);
      }

      /* collisions: the player */
      if (S.state === "running") {
        for (i = S.enemyShots.length - 1; i >= 0; i--) {
          var o = S.enemyShots[i];
          if (shotHitsPlayer(o, p)) { if (o.kind !== "beam") S.enemyShots.splice(i, 1); if (hitPlayer(o.src === "shot" ? "shot" : o.src, o.kind === "beam" ? "lancer" : null)) break; }
        }
      }
      if (S.state === "running") {
        for (i = S.enemies.length - 1; i >= 0; i--) {
          var e = S.enemies[i];
          if (overlaps(e, p, -4)) { boom(e.x, e.y, 1, "#fb923c"); shards(e.x, e.y, 5); S.enemies.splice(i, 1); if (hitPlayer("collision", e.type)) break; }
        }
      }
      if (S.state === "running") {
        for (i = S.asteroids.length - 1; i >= 0; i--) {
          var rk = S.asteroids[i];
          if (overlaps(rk, p, -6) && p.invuln === 0) { var size = rk.size; breakRock(i); if (hitPlayer("asteroid", size)) break; }
        }
      }
      if (S.state === "running" && S.boss && S.boss.entered) {
        if (Math.hypot(p.x - S.boss.x, p.y - S.boss.y) < (LOGO.coreR + 120) * S.boss.s) hitPlayer("collision", "boss");
      }
      if (S.state === "running") {
        for (i = S.powerUps.length - 1; i >= 0; i--) {
          if (overlaps(S.powerUps[i], p, 6)) { collect(S.powerUps[i]); S.powerUps.splice(i, 1); }
        }
      }

      /* the seeded random explosion */
      if (S.state === "running" && cfg.defects.randomExplosion && S.tick >= S.nextExplosion) {
        if (p.invuln === 0) {
          S.explodeTicks.push(S.tick);
          emit("explode", { tick: S.tick });
          boom(p.x, p.y, 1.8, "#fbbf24");
          applyDamage(EXPLOSION_DAMAGE, "explode", null);
          if (S.state === "running") p.invuln = HIT_INVULN;
          S.nextExplosion = nextExplosion(S.rng.defects, S.tick);
        }
      }

      /* cleanup */
      S.enemies = S.enemies.filter(function (o) { return o.y < world.h + 40 && o.y > -200; });
      S.enemyShots = S.enemyShots.filter(function (o) { return o.kind === "beam" || (o.y < world.h + 20 && o.y > -40 && o.x > -20 && o.x < world.w + 20); });
      S.asteroids = S.asteroids.filter(function (o) { return o.y < world.h + o.r + 10 && o.x > -o.r - 40 && o.x < world.w + o.r + 40; });
      S.powerUps = S.powerUps.filter(function (o) { return o.y < world.h + 20; });
      S.effects = S.effects.filter(function (o) { return o.t < o.life; });
      S.popups = S.popups.filter(function (o) { return o.t < o.life; });
    }

    /* ==================================================================== WebGL scene */
    var MAT = new Float32Array(16);
    var fxN = 0;
    function fxVert(x, y, z, u, v, r, g, b, a, mode) {
      var d = glr.fxData, o = fxN * 10;
      d[o] = x; d[o + 1] = y; d[o + 2] = z; d[o + 3] = u; d[o + 4] = v; d[o + 5] = r; d[o + 6] = g; d[o + 7] = b; d[o + 8] = a; d[o + 9] = mode;
      fxN += 1;
    }
    /* A sprite quad in the play plane at height y: (ax, az) is its half-width axis, (bx, bz)
       its half-length axis; the shader's mode shapes it (0 glow, 1 ring, 2 beam, 3 streak,
       4 blast zone, 5 shield bubble). */
    function quad(x, y, z, ax, az, bx, bz, col, a, mode) {
      if (fxN + 6 > MAX_QUADS * 6) return;
      var r = col[0], g = col[1], b = col[2];
      fxVert(x - ax - bx, y, z - az - bz, -1, -1, r, g, b, a, mode); fxVert(x + ax - bx, y, z + az - bz, 1, -1, r, g, b, a, mode); fxVert(x + ax + bx, y, z + az + bz, 1, 1, r, g, b, a, mode);
      fxVert(x - ax - bx, y, z - az - bz, -1, -1, r, g, b, a, mode); fxVert(x + ax + bx, y, z + az + bz, 1, 1, r, g, b, a, mode); fxVert(x - ax + bx, y, z - az + bz, -1, 1, r, g, b, a, mode);
    }
    function glow(x, z, rad, col, a, y) { quad(x, y == null ? 10 : y, z, rad, 0, 0, rad, col, a, 0); }
    function streak(x, z, dx, dz, len, wid, col, a, y, mode) {
      var l = Math.sqrt(dx * dx + dz * dz) || 1, ux = dx / l, uz = dz / l;
      quad(x, y == null ? 8 : y, z, -uz * wid, ux * wid, ux * len, uz * len, col, a, mode == null ? 3 : mode);
    }
    var COL = {};
    function col(hex) { return COL[hex] || (COL[hex] = hexRgb(hex)); }
    var timeShown = 0;

    function drawMesh(name, flash, glowAmt, glowCol, tint) {
      var gl = glr.gl, P = glr.mesh, m = glr.buf[name];
      if (!m) return;
      gl.bindBuffer(gl.ARRAY_BUFFER, m.b);
      gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 48, 0);
      gl.vertexAttribPointer(1, 3, gl.FLOAT, false, 48, 12);
      gl.vertexAttribPointer(2, 3, gl.FLOAT, false, 48, 24);
      gl.vertexAttribPointer(3, 3, gl.FLOAT, false, 48, 36);
      gl.uniformMatrix4fv(P.u.uModel, false, MAT);
      gl.uniform1f(P.u.uFlash, flash || 0);
      gl.uniform1f(P.u.uGlow, glowAmt || 0);
      var gc = glowCol || [0, 0, 0], t = tint || [1, 1, 1];
      gl.uniform3f(P.u.uGlowCol, gc[0], gc[1], gc[2]);
      gl.uniform3f(P.u.uTint, t[0], t[1], t[2]);
      gl.drawArrays(gl.TRIANGLES, 0, m.n);
    }
    function setCommon(P, shx, shy) {
      var gl = glr.gl;
      gl.uniform3f(P.u.uWorld, world.w, world.h, Math.tan(TILT));
      if (P.u.uCS) gl.uniform2f(P.u.uCS, Math.cos(TILT), Math.sin(TILT));
      if (P.u.uDepth) gl.uniform2f(P.u.uDepth, -400, 1 / (world.h * Math.sin(TILT) + 800));
      if (P.u.uShake) gl.uniform2f(P.u.uShake, shx, shy);
    }
    /* Engine flames: a hot core at each nozzle and a flickering plume behind it. */
    function flames(defName, colHex, power) {
      var def = MESHES[defName] || (defName.indexOf("form") === 0 ? MESHES[defName] : null);
      if (!def || !def.engines) return;
      var c = col(colHex), back = xform(MAT, [0, 0, 1]), o = xform(MAT, [0, 0, 0]);
      var bx = back[0] - o[0], bz = back[2] - o[2], bl = Math.sqrt(bx * bx + bz * bz) || 1;
      bx /= bl; bz /= bl;
      def.engines.forEach(function (e, k) {
        var w = xform(MAT, [e[0], e[1], e[2]]), s = bl * e[3];
        var flick = REDUCED ? 1 : 0.85 + 0.15 * Math.sin(S.tick * 0.9 + k * 2.1) + 0.08 * Math.sin(S.tick * 2.3 + k);
        glow(w[0], w[2], s * 2.6, c, 0.85 * power, w[1]);
        streak(w[0] + bx * s * 2.2 * flick, w[2] + bz * s * 2.2 * flick, bx, bz, s * 3.2 * flick * power, s * 0.85, c, 0.75, w[1]);
        glow(w[0], w[2], s * 1.0, [1, 1, 1], 0.6, w[1]);
      });
    }
    function drawGL() {
      var R = glr, gl = R.gl;
      if (R.lost || gl.isContextLost()) return;
      var all = meshes(), p = S.player, i, k;
      var cw = canvas.width, ch = canvas.height;
      var scale = Math.min(cw / world.w, ch / world.h);
      var vw = Math.round(world.w * scale), vh = Math.round(world.h * scale);
      var ox = Math.floor((cw - vw) / 2), oy = Math.floor((ch - vh) / 2);
      gl.viewport(0, 0, cw, ch);
      gl.clearColor(0.01, 0.02, 0.03, 1);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      gl.viewport(ox, ch - oy - vh, vw, vh);
      var shk = REDUCED ? 0 : S.shake, shx = shk ? Math.sin(S.tick * 2.1) * shk * 2 / world.w : 0, shy = shk ? Math.cos(S.tick * 2.7) * shk * 2 / world.h : 0;
      var sky = LEVEL_SKY[cfg.progression ? S.level : 1];

      /* background: nebula, three star layers drifting at their own speeds, and a planet */
      gl.disable(gl.DEPTH_TEST); gl.disable(gl.BLEND); gl.disable(gl.CULL_FACE);
      gl.useProgram(R.bg.p);
      gl.disableVertexAttribArray(1); gl.disableVertexAttribArray(2); gl.disableVertexAttribArray(3);
      gl.enableVertexAttribArray(0);
      gl.bindBuffer(gl.ARRAY_BUFFER, R.bgBuf);
      gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
      var u = R.bg.u, t = S.tick * (REDUCED ? 0.2 : 1);
      gl.uniform3f(u.uWorld, world.w, world.h, 0);
      gl.uniform3f(u.uScroll, (t * 0.12) % 26000, (t * 0.32) % 44000, (t * 0.75) % 82000);
      gl.uniform3f(u.uNebA, sky.a[0], sky.a[1], sky.a[2]);
      gl.uniform3f(u.uNebB, sky.b[0], sky.b[1], sky.b[2]);
      var pr = Math.min(world.w, world.h) * sky.planet[2] * 1.35;
      gl.uniform4f(u.uPlanet, world.w * sky.planet[0], world.h * sky.planet[1] + pr * 0.15 + (cfg.progression ? S.levelTicks * 0.004 : S.tick * 0.002), pr, 0.62);
      gl.uniform3f(u.uPlanetA, sky.pa[0], sky.pa[1], sky.pa[2]);
      gl.uniform3f(u.uPlanetB, sky.pb[0], sky.pb[1], sky.pb[2]);
      gl.uniform1f(u.uT, t);
      gl.drawArrays(gl.TRIANGLES, 0, 6);

      /* lit meshes */
      gl.enable(gl.DEPTH_TEST);
      gl.depthFunc(gl.LESS);
      gl.depthMask(true);
      gl.clear(gl.DEPTH_BUFFER_BIT);
      gl.useProgram(R.mesh.p);
      for (k = 0; k < 4; k++) gl.enableVertexAttribArray(k);
      var P = R.mesh;
      setCommon(P, shx, shy);
      var L = v3norm([-0.55, 0.8, -0.3]), F = v3norm([0.7, 0.25, 0.6]), V = [0, Math.cos(TILT), Math.sin(TILT)];
      gl.uniform3f(P.u.uLight, L[0], L[1], L[2]);
      gl.uniform3f(P.u.uFill, F[0], F[1], F[2]);
      gl.uniform3f(P.u.uView, V[0], V[1], V[2]);
      gl.uniform3f(P.u.uEnv, sky.env[0], sky.env[1], sky.env[2]);
      fxN = 0;

      for (i = 0; i < S.asteroids.length; i++) {
        var a = S.asteroids[i];
        modelMat(MAT, a.x, 0, a.y, a.spin, a.rx, a.spin * 0.6, a.r);
        drawMesh("rock" + (a.look % 6), a.flash > 0 ? 0.5 : 0);
      }
      if (S.boss) drawBossGL(S.boss);
      for (i = 0; i < S.enemies.length; i++) drawEnemyGL(S.enemies[i]);
      for (i = 0; i < S.enemyShots.length; i++) {
        var o = S.enemyShots[i];
        if (o.kind !== "bomb") continue;
        modelMat(MAT, o.x, 6, o.y, o.t * 0.08, o.t * 0.05, 0, 1);
        var blink = o.arm > 0 ? (Math.floor(o.arm / 3) % 2 ? 1 : 0.2) : (Math.floor(o.t / 10) % 2 ? 0.8 : 0.1);
        drawMesh("bomb", 0, REDUCED ? 0.6 : blink, [1, 0.3, 0.15]);
      }
      for (i = 0; i < S.shots.length; i++) {
        var sh = S.shots[i];
        if (sh.kind !== "missile") continue;
        modelMat(MAT, sh.x, 6, sh.y, Math.atan2(-sh.vx, sh.vy * -1), 0, 0, 1.1);
        drawMesh("missile");
        flames("missile", "#fb923c", 0.8);
      }
      for (i = 0; i < S.powerUps.length; i++) {
        var pu = S.powerUps[i], pc = col((POWER_LOOK[pu.kind] || POWER_LOOK.repair)[0]);
        modelMat(MAT, pu.x, 10, pu.y, pu.t * 0.05, 0.35, 0, 1.15);
        drawMesh("gem", 0, 0.5, pc, [pc[0] * 0.7 + 0.3, pc[1] * 0.7 + 0.3, pc[2] * 0.7 + 0.3]);
        glow(pu.x, pu.y, 30, pc, 0.55, 10);
      }
      for (i = 0; i < S.effects.length; i++) {
        var f = S.effects[i];
        if (f.kind !== "debris") continue;
        modelMat(MAT, f.x, 4, f.y, f.spin + f.t * 0.2, f.t * 0.15, f.spin, f.size);
        drawMesh(f.rock ? "rock" + (Math.floor(f.spin) % 6) : "shard", 0, 0, null, f.rock ? [0.75, 0.7, 0.65] : null);
      }
      var visible = !(S.state === "over" && S.overReason !== "victory");
      var pulse = p.invuln > 0 && !REDUCED ? (Math.floor(p.invuln / 5) % 2 === 0 ? 0.35 : 0) : 0;
      if (visible) {
        var form = cfg.progression ? S.level : 1;
        if (p.wingman > 0) [-42, 42].forEach(function (dx) {
          modelMat(MAT, p.x + dx, 2, p.y + 4, 0, 0, -p.bank * 0.8, 1.15 * VIS);
          drawMesh("wingman");
          flames("wingman", "#c084fc", 0.8);
        });
        modelMat(MAT, p.x, 4, p.y, 0, 0.06, -p.bank * 0.7, VIS);
        drawMesh("form" + form, Math.max(pulse, p.hurt > 0 ? p.hurt / 14 : 0));
        flames("form" + form, "#38bdf8", 1);
      }

      /* additive sprites */
      gl.disable(gl.DEPTH_TEST);
      gl.depthMask(false);
      gl.enable(gl.BLEND);
      gl.blendFunc(gl.ONE, gl.ONE);
      sprites();
      gl.useProgram(R.fx.p);
      setCommon(R.fx, shx, shy);
      gl.bindBuffer(gl.ARRAY_BUFFER, R.fxBuf);
      gl.bufferSubData(gl.ARRAY_BUFFER, 0, R.fxData.subarray(0, fxN * 10));
      gl.vertexAttribPointer(0, 3, gl.FLOAT, false, 40, 0);
      gl.vertexAttribPointer(1, 2, gl.FLOAT, false, 40, 12);
      gl.vertexAttribPointer(2, 4, gl.FLOAT, false, 40, 20);
      gl.vertexAttribPointer(3, 1, gl.FLOAT, false, 40, 36);
      if (fxN) gl.drawArrays(gl.TRIANGLES, 0, fxN);
      gl.disable(gl.BLEND);
      gl.depthMask(true);
    }
    function drawEnemyGL(e) {
      var yaw = Math.PI, pitch = 0;
      if (e.type === "interceptor" && e.mode === "dive") yaw = Math.atan2(-e.vx, -e.vy);
      modelMat(MAT, e.x, 3, e.y, yaw, pitch, e.bank, VIS * 1.12);
      var glowAmt = 0, gc = null;
      if (e.type === "lancer" && e.charge > 0) { glowAmt = 1 - e.charge / 50; gc = [1, 0.55, 0.15]; }
      drawMesh(e.type, e.flash > 0 ? 0.7 : 0, glowAmt, gc);
      flames(e.type, { gunship: "#fb7185", interceptor: "#f0abfc", lancer: "#fdba74", bomber: "#fde047" }[e.type], 0.85);
    }
    function drawBossGL(b) {
      var cx = LOGO.centre[0], cy = LOGO.centre[1], s = b.s;
      modelMat(MAT, b.x, 0, b.y, 0, 0, 0, s);
      drawMesh("bossHull", 0, 0.2 + 0.1 * Math.sin(b.t * 0.08), [0.1, 0.9, 1]);
      b.nodes.forEach(function (n, i) {
        var c = LOGO.nodes[i];
        modelMat(MAT, b.x + (c[0] - cx) * s, 6 * s, b.y + (c[1] - cy) * s, b.t * 0.01, 0, 0, s);
        drawMesh("bossNode", n.flash > 0 ? 0.8 : 0, n.alive ? 0.4 : 0, [0.2, 1, 1], n.alive ? [1, 1, 1] : [0.25, 0.3, 0.32]);
      });
      var exposed = nodesAlive(b) === 0;
      modelMat(MAT, b.x, 6 * s, b.y, 0, 0, 0, s * (REDUCED ? 1 : 0.92 + 0.08 * Math.sin(b.t * 0.12)));
      drawMesh("bossCore", b.coreFlash > 0 ? 0.6 : 0, exposed ? 0.6 : 0, [1, 1, 1], exposed ? [1, 1, 1] : [0.55, 0.6, 0.65]);
    }
    /* Build the sprite list: glows for every lit thing, shots and beams, blast zones, the
       shield, and the explosion particles. */
    function sprites() {
      var p = S.player, i;
      for (i = 0; i < S.shots.length; i++) {
        var sh = S.shots[i];
        if (sh.kind === "missile") continue;
        streak(sh.x, sh.y, sh.vx || 0, -13, 13, 3.2, col("#5eead4"), 1, 8);
        glow(sh.x, sh.y - 6, 9, col("#22d3ee"), 0.35, 8);
      }
      for (i = 0; i < S.enemies.length; i++) {
        var e = S.enemies[i];
        if (e.type === "lancer" && e.charge > 0) {
          /* the tell: a gathering glow at the emitter and a faint aiming line down the column */
          var k = 1 - e.charge / 50, em = e.y + 27;
          glow(e.x, em, 10 + k * 26, col("#fb923c"), 0.5 + k * 0.6, 12);
          quad(e.x, 4, (em + world.h) / 2, 1.5 + k * 3, 0, 0, (world.h - em) / 2, col("#fb923c"), 0.12 + k * 0.25, 2);
        }
      }
      for (i = 0; i < S.enemyShots.length; i++) {
        var o = S.enemyShots[i];
        if (o.kind === "beam") {
          var kk = o.life / o.span, w = 8 + 14 * Math.min(1, (o.span - o.life) / 6);
          quad(o.x, 6, (o.y + world.h) / 2 + 10, w, 0, 0, (world.h - o.y) / 2 + 10, col("#fb923c"), 0.7 * kk + 0.45, 2);
          glow(o.x, o.y, 34, col("#fdba74"), 0.9, 12);
        } else if (o.kind === "bomb") {
          glow(o.x, o.y, 16, col("#f87171"), 0.5, 8);
          if (o.arm > 0) {
            var fill = 1 - o.arm / BOMB_ARM;
            quad(o.x, 0, o.y, BLAST_RADIUS, 0, 0, BLAST_RADIUS, col("#f97316"), 0.35 + fill * 0.5, 4);
            quad(o.x, 0, o.y, BLAST_RADIUS * fill, 0, 0, BLAST_RADIUS * fill, col("#fdba74"), 0.5, 1);
          }
        } else if (o.kind === "needle") {
          streak(o.x, o.y, o.vx, o.vy, 9, 2, col("#f0abfc"), 1, 8);
        } else {
          var bc = o.src === "bossShot" ? col("#67e8f9") : col("#fb7185");
          streak(o.x, o.y, o.vx, o.vy, 11, 4, bc, 1, 8);
          glow(o.x, o.y, 11, bc, 0.4, 8);
        }
      }
      if (S.boss) {
        var b = S.boss;
        b.nodes.forEach(function (n, i2) { if (!n.alive) return; var at = bossPoint(b, LOGO.nodes[i2][0], LOGO.nodes[i2][1]); glow(at[0], at[1], LOGO.nodeR * b.s * 2.2, col("#22d3ee"), 0.45, 20); });
        glow(b.x, b.y, LOGO.coreR * b.s * (nodesAlive(b) ? 2 : 3.4), col("#f2feff"), nodesAlive(b) ? 0.35 : 0.8, 20);
      }
      if (p.shieldHp > 0 && !(S.state === "over" && S.overReason !== "victory")) {
        var sr = PLAYER[cfg.progression ? S.level : 1].w * VIS + 14 + (REDUCED ? 0 : Math.sin(S.tick * 0.15) * 2);
        quad(p.x, 10, p.y, sr, 0, 0, sr, col("#60a5fa"), 0.35 + 0.4 * p.shieldHp / SHIELD_MAX, 5);
      }
      for (i = 0; i < S.effects.length; i++) {
        var f = S.effects[i], q = f.t / f.life, c = col(f.color);
        if (f.kind === "flash") glow(f.x, f.y, (30 + q * 40) * f.size, c, (1 - q) * 1.4, 14);
        else if (f.kind === "ring") quad(f.x, 12, f.y, (14 + q * 46) * f.size, 0, 0, (14 + q * 46) * f.size, c, (1 - q) * 0.8, 1);
        else if (f.kind === "blast") { var br = f.size * (0.3 + 0.7 * Math.sqrt(q)); quad(f.x, 2, f.y, br, 0, 0, br, col("#fdba74"), (1 - q) * 0.9, 1); glow(f.x, f.y, f.size * 0.9, col("#f97316"), (1 - q) * 0.6, 4); }
        else if (f.kind === "fire") {
          /* fireballs cool from white-yellow through orange to deep red as they fade */
          var hot = 1 - q, fc = [Math.min(1, 0.6 + c[0] * 0.5), 0.25 + 0.6 * hot * hot, 0.08 + 0.4 * hot * hot * hot];
          glow(f.x, f.y, f.size * (0.8 + q * 1.6), fc, Math.pow(1 - q, 1.4) * 0.9, 12);
        } else if (f.kind === "spark") streak(f.x, f.y, f.vx, f.vy, 5 + Math.hypot(f.vx, f.vy), 1.6, c, 1 - q, 12);
        else if (f.kind === "dust") glow(f.x, f.y, f.size * (0.7 + q), col("#7c6f62"), (1 - q) * 0.35, 6);
      }
    }

    /* ==================================================================== 2D fallback renderer
       The same scene with canvas paths: shaded hulls with a lit edge, glass, panel lines, and
       engine glow. Used when WebGL is missing or forced off. */
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
      var sheen = ctx.createLinearGradient(0, -w, 0, w);
      sheen.addColorStop(0, "rgba(255,255,255,0.32)"); sheen.addColorStop(0.5, "rgba(255,255,255,0.04)"); sheen.addColorStop(1, "rgba(0,0,0,0.25)");
      path(pts); ctx.fillStyle = sheen; ctx.fill();
    }
    function glass(x, y, rx, ry, tint) {
      var g = ctx.createRadialGradient(x - rx * 0.3, y - ry * 0.4, 1, x, y, Math.max(rx, ry) * 1.2);
      g.addColorStop(0, "#e0fbff"); g.addColorStop(0.35, tint); g.addColorStop(1, "#06202b");
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.ellipse(x, y, rx, ry, 0, 0, 6.283); ctx.fill();
    }
    function engine(x, y, w, len, hot) {
      ctx.fillStyle = "#0b1d24"; ctx.fillRect(x - w / 2, y - 3, w, 6);
      var flick = REDUCED ? 1 : 0.82 + 0.18 * Math.sin(S.tick * 0.9 + x);
      var g = ctx.createLinearGradient(0, y, 0, y + len * flick);
      g.addColorStop(0, "rgba(255,255,255,0.95)"); g.addColorStop(0.25, hot); g.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = g;
      ctx.beginPath(); ctx.moveTo(x - w / 2, y + 2); ctx.quadraticCurveTo(x, y + len * 1.25 * flick, x + w / 2, y + 2); ctx.closePath(); ctx.fill();
    }
    var PLAYER = {
      1: { half: [[0, -26], [6, -12], [8, 0], [24, 10], [24, 15], [9, 13], [6, 19], [0, 16]], w: 24, engines: [[0, 16, 8]], glass: [0, -8, 4, 8] },
      2: { half: [[0, -32], [5, -22], [9, -8], [14, -2], [30, 8], [32, 16], [16, 15], [12, 22], [5, 20], [0, 22]], w: 32, engines: [[-7, 21, 7], [7, 21, 7]], glass: [0, -12, 4.5, 10] },
      3: { half: [[0, -40], [6, -30], [10, -14], [18, -6], [38, 2], [42, 12], [40, 18], [22, 16], [20, 24], [12, 26], [6, 22], [0, 26]], w: 42, engines: [[-15, 25, 8], [0, 26, 8], [15, 25, 8]], glass: [0, -18, 5.5, 12] }
    };
    var ENEMY_2D = {
      gunship: { half: [[0, -22], [8, -14], [22, -6], [23, 2], [8, 12], [5, 20], [0, 18]], w: 23, c: ["#fecdd3", "#9f1239", "#3f0a17", "#ffe4e6"], hot: "#fb7185" },
      interceptor: { half: [[0, -15], [3, -6], [14, -4], [14, 0], [4, 8], [0, 10]], w: 14, c: ["#f5d0fe", "#86198f", "#2e0636", "#fae8ff"], hot: "#f0abfc" },
      lancer: { half: [[0, -28], [3, -12], [6, 0], [17, 14], [17, 18], [6, 18], [3, 26], [0, 24]], w: 17, c: ["#ffedd5", "#c2410c", "#431407", "#fff7ed"], hot: "#fb923c" },
      bomber: { half: [[0, -17], [30, 4], [32, 8], [22, 6], [15, 11], [8, 8], [0, 12]], w: 32, c: ["#ecfccb", "#4d7c0f", "#1a2e05", "#f7fee7"], hot: "#facc15" }
    };
    function drawShip(p) {
      var form = cfg.progression ? S.level : 1, spec = PLAYER[form];
      ctx.save();
      ctx.translate(p.x, p.y);
      spec.engines.forEach(function (e) { engine(e[0], e[1], e[2], 26 + form * 4, "#22d3ee"); });
      hull(mirror(spec.half), spec.w, "#e8fbff", "#67c9db", "#0c4655", "#bff4fb");
      glass(spec.glass[0], spec.glass[1], spec.glass[2], spec.glass[3], "#38bdf8");
      if (p.shieldHp > 0) {
        var r = spec.w + 10;
        ctx.strokeStyle = "rgba(147,197,253,0.9)"; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(0, 0, r, 0, 6.283); ctx.stroke();
      }
      ctx.restore();
      if (p.wingman > 0) [-42, 42].forEach(function (dx) {
        ctx.save(); ctx.translate(p.x + dx, p.y + 4);
        engine(0, 9, 5, 16, "#c084fc");
        hull([[0, -12], [5, -2], [12, 6], [4, 8], [0, 10], [-4, 8], [-12, 6], [-5, -2]], 12, "#f5e8ff", "#b48be6", "#4a2a72", "#e9d5ff");
        ctx.restore();
      });
    }
    function drawEnemy2D(e) {
      var spec = ENEMY_2D[e.type];
      ctx.save();
      ctx.translate(e.x, e.y);
      ctx.scale(1, -1);
      engine(0, -spec.half[spec.half.length - 1][1] + 2, 6, 12, spec.hot);
      hull(mirror(spec.half), spec.w, spec.c[0], spec.c[1], spec.c[2], e.flash > 0 ? "#ffffff" : spec.c[3]);
      ctx.restore();
      if (e.type === "lancer" && e.charge > 0) {
        var heat = 1 - e.charge / 50;
        ctx.fillStyle = "rgba(251,146,60," + (0.15 + heat * 0.35).toFixed(2) + ")";
        ctx.fillRect(e.x - 2, e.y + e.r, 4, world.h - e.y);
        ctx.fillStyle = "rgba(255,237,213,0.9)"; ctx.beginPath(); ctx.arc(e.x, e.y + 26, 4 + heat * 8, 0, 6.283); ctx.fill();
      }
    }
    function drawRock(a) {
      var r = mulberry32(a.look * 977 + 3), n = 9;
      ctx.save();
      ctx.translate(a.x, a.y);
      ctx.rotate(a.spin);
      var g = ctx.createRadialGradient(-a.r * 0.35, -a.r * 0.35, a.r * 0.2, 0, 0, a.r * 1.1);
      g.addColorStop(0, a.flash > 0 ? "#ffffff" : "#cbd5e1"); g.addColorStop(1, "#334155");
      ctx.fillStyle = g;
      ctx.beginPath();
      for (var k = 0; k < n; k++) {
        var ang = k / n * 6.283, rad = a.r * (0.78 + r() * 0.3);
        if (k === 0) ctx.moveTo(Math.cos(ang) * rad, Math.sin(ang) * rad); else ctx.lineTo(Math.cos(ang) * rad, Math.sin(ang) * rad);
      }
      ctx.closePath(); ctx.fill();
      ctx.restore();
    }
    /* The power-up's glass capsule and icon; the WebGL HUD reuses the icon over its gem. */
    function powerIcon(kind, color, capsule, r) {
      if (capsule) {
        var g = ctx.createRadialGradient(-4, -5, 1, 0, 0, r + 2);
        g.addColorStop(0, "rgba(255,255,255,0.55)"); g.addColorStop(0.4, "rgba(2,6,23,0.75)"); g.addColorStop(1, "rgba(2,6,23,0.9)");
        ctx.fillStyle = g;
        ctx.strokeStyle = color; ctx.lineWidth = 2;
        ctx.beginPath(); ctx.arc(0, 0, r, 0, 6.283); ctx.fill(); ctx.stroke();
      }
      ctx.strokeStyle = color; ctx.fillStyle = color; ctx.lineWidth = 2;
      if (kind === "shield") { ctx.beginPath(); ctx.moveTo(0, -7); ctx.lineTo(6, -4); ctx.lineTo(5, 3); ctx.lineTo(0, 7); ctx.lineTo(-5, 3); ctx.lineTo(-6, -4); ctx.closePath(); ctx.stroke(); }
      else if (kind === "weapon") { ctx.fillRect(-5, -6, 3, 12); ctx.fillRect(2, -6, 3, 12); }
      else if (kind === "spread") { [-0.5, 0, 0.5].forEach(function (a) { ctx.save(); ctx.rotate(a); ctx.fillRect(-1.2, -8, 2.4, 9); ctx.restore(); }); }
      else if (kind === "rapid") { ctx.beginPath(); ctx.moveTo(2, -8); ctx.lineTo(-4, 1); ctx.lineTo(0, 1); ctx.lineTo(-2, 8); ctx.lineTo(4, -1); ctx.lineTo(0, -1); ctx.closePath(); ctx.fill(); }
      else if (kind === "missiles") { ctx.beginPath(); ctx.moveTo(0, -8); ctx.lineTo(3, -3); ctx.lineTo(3, 5); ctx.lineTo(5, 8); ctx.lineTo(-5, 8); ctx.lineTo(-3, 5); ctx.lineTo(-3, -3); ctx.closePath(); ctx.fill(); }
      else if (kind === "wingman") { ctx.beginPath(); ctx.moveTo(0, -6); ctx.lineTo(4, 4); ctx.lineTo(0, 2); ctx.lineTo(-4, 4); ctx.closePath(); ctx.fill(); ctx.fillRect(-9, 0, 3, 5); ctx.fillRect(6, 0, 3, 5); }
      else { ctx.fillRect(-2, -7, 4, 14); ctx.fillRect(-7, -2, 14, 4); }
    }
    function drawBoss2D(b) {
      ctx.save();
      ctx.translate(b.x, b.y);
      ctx.scale(b.s, b.s);
      ctx.translate(-LOGO.centre[0], -LOGO.centre[1]);
      function tri(t, fill) { ctx.fillStyle = fill; ctx.beginPath(); ctx.moveTo(t[0][0], t[0][1]); ctx.lineTo(t[1][0], t[1][1]); ctx.lineTo(t[2][0], t[2][1]); ctx.closePath(); ctx.fill(); }
      tri(LOGO.plates[0], "#00879f"); tri(LOGO.plates[1], "#00879f");
      tri(LOGO.blades[0], "#5fe6ee"); tri(LOGO.blades[1], "#5fe6ee");
      ctx.lineCap = "round";
      ctx.strokeStyle = "#25f4ff";
      ctx.lineWidth = LOGO.barW;
      ctx.beginPath(); ctx.moveTo(106, 97); ctx.lineTo(410, 395); ctx.moveTo(410, 97); ctx.lineTo(106, 395); ctx.stroke();
      b.nodes.forEach(function (n, i) {
        var c = LOGO.nodes[i];
        ctx.fillStyle = !n.alive ? "#164e63" : n.flash > 0 ? "#ffffff" : "#3ff7ff";
        ctx.beginPath(); ctx.arc(c[0], c[1], LOGO.nodeR, 0, 6.283); ctx.fill();
      });
      var exposed = nodesAlive(b) === 0;
      ctx.fillStyle = b.coreFlash > 0 ? "#fde68a" : exposed ? "#f2feff" : "rgba(242,254,255,0.55)";
      ctx.beginPath(); ctx.arc(LOGO.centre[0], LOGO.centre[1], LOGO.coreR, 0, 6.283); ctx.fill();
      ctx.restore();
    }
    function drawEnemyShot2D(o) {
      if (o.kind === "beam") {
        var w = 6 + 8 * Math.min(1, (o.span - o.life) / 6);
        ctx.fillStyle = "rgba(251,146,60,0.75)"; ctx.fillRect(o.x - w, o.y, w * 2, world.h - o.y);
        ctx.fillStyle = "rgba(255,247,237,0.95)"; ctx.fillRect(o.x - w * 0.3, o.y, w * 0.6, world.h - o.y);
        return;
      }
      if (o.kind === "bomb") {
        if (o.arm > 0) {
          ctx.fillStyle = "rgba(249,115,22,0.18)"; ctx.strokeStyle = "rgba(253,186,116,0.9)"; ctx.lineWidth = 2;
          ctx.beginPath(); ctx.arc(o.x, o.y, BLAST_RADIUS, 0, 6.283); ctx.fill(); ctx.stroke();
        }
        ctx.fillStyle = "#1f2937"; ctx.strokeStyle = "#f87171"; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.arc(o.x, o.y, 7, 0, 6.283); ctx.fill(); ctx.stroke();
        return;
      }
      ctx.fillStyle = o.kind === "needle" ? "#f0abfc" : o.src === "bossShot" ? "#67e8f9" : "#fecaca";
      ctx.beginPath(); ctx.ellipse(o.x, o.y, o.kind === "needle" ? 2 : 3, 8, Math.atan2(o.vx, o.vy) * -1, 0, 6.283); ctx.fill();
    }
    function draw2D() {
      var cw = canvas.width, ch = canvas.height;
      var scale = Math.min(cw / world.w, ch / world.h);
      var ox = (cw - world.w * scale) / 2, oy = (ch - world.h * scale) / 2;
      ctx.setTransform(1, 0, 0, 1, 0, 0);
      ctx.fillStyle = "#030a10";
      ctx.fillRect(0, 0, cw, ch);
      ctx.setTransform(scale, 0, 0, scale, ox, oy);
      drawBackground();
      var i;
      for (i = 0; i < S.asteroids.length; i++) drawRock(S.asteroids[i]);
      if (S.boss) drawBoss2D(S.boss);
      for (i = 0; i < S.enemies.length; i++) drawEnemy2D(S.enemies[i]);
      for (i = 0; i < S.powerUps.length; i++) { var pu = S.powerUps[i]; ctx.save(); ctx.translate(pu.x, pu.y); powerIcon(pu.kind, (POWER_LOOK[pu.kind] || POWER_LOOK.repair)[0], true, pu.r); ctx.restore(); }
      for (i = 0; i < S.enemyShots.length; i++) drawEnemyShot2D(S.enemyShots[i]);
      for (i = 0; i < S.shots.length; i++) { var sh = S.shots[i]; ctx.fillStyle = sh.kind === "missile" ? "#fb923c" : "#a5f3fc"; ctx.fillRect(sh.x - 1.5, sh.y - 8, 3, 14); }
      var p = S.player;
      if (!(S.state === "over" && S.overReason !== "victory")) {
        if (p.invuln > 0 && !REDUCED && Math.floor(p.invuln / 5) % 2 === 0) ctx.globalAlpha = 0.55;
        drawShip(p);
        ctx.globalAlpha = 1;
      }
      for (i = 0; i < S.effects.length; i++) {
        var f = S.effects[i], k = f.t / f.life;
        ctx.globalAlpha = Math.max(0, 1 - k);
        if (f.kind === "ring" || f.kind === "blast") {
          ctx.strokeStyle = f.color; ctx.lineWidth = 3;
          ctx.beginPath(); ctx.arc(f.x, f.y, f.kind === "blast" ? f.size * (0.3 + 0.7 * k) : (10 + k * 34) * f.size, 0, 6.283); ctx.stroke();
        } else if (f.kind === "fire" || f.kind === "flash" || f.kind === "dust") {
          ctx.fillStyle = f.kind === "dust" ? "rgba(138,125,112,0.5)" : f.kind === "flash" ? "#fff7e0" : f.color;
          ctx.beginPath(); ctx.arc(f.x, f.y, f.kind === "flash" ? 20 * f.size : (f.size || 8) * 0.5, 0, 6.283); ctx.fill();
        } else {
          ctx.fillStyle = f.color;
          ctx.fillRect(f.x - 1.5, f.y - 1.5, 3, 3);
        }
      }
      ctx.globalAlpha = 1;
      drawHud();
    }

    function draw() {
      if (!S) return;
      if (glr) {
        drawGL();
        if (ctx) { ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.clearRect(0, 0, hudCanvas.width, hudCanvas.height); drawWorldLabels(); drawHud(); }
      } else if (ctx) draw2D();
    }
    /* step() renders on the next animation frame, at most once, so a test or bot that runs
       thousands of ticks in one call pays for one frame, not thousands. */
    var drawQueued = false;
    function queueDraw() {
      if (drawQueued) return;
      drawQueued = true;
      window.requestAnimationFrame(function () { drawQueued = false; draw(); });
    }

    /* ---------- the HUD, drawn in the arena at screen size: hull and shield bars, score, level,
       difficulty and goal, upgrades, damage numbers */
    var hudFont = null, hpShown = HEALTH_MAX, shShown = 0;
    function goal() {
      if (!S) return null;
      if (S.boss) return { text: S.boss.entered ? (nodesAlive(S.boss) ? "Break the " + nodesAlive(S.boss) + " glowing nodes, then the core" : "The core is open: destroy it") : "The Nexus megaship is arriving", k: S.boss.entered ? 1 - nodesAlive(S.boss) / 4 : 0 };
      if (!cfg.progression) return { text: "Survive: " + clock(S.tick), k: null };
      if (S.level < 3) { var need = LEVEL_TICKS[S.level]; return { text: "Survive " + clock(need - S.levelTicks) + " to reach level " + (S.level + 1), k: S.levelTicks / need }; }
      if (cfg.boss && S.bossDue !== null) return { text: "Something big arrives in " + clock(S.bossDue), k: 1 - S.bossDue / BOSS_AFTER };
      return { text: "Final level: survive", k: null };
    }
    function clock(t) { var sec = Math.max(0, Math.ceil(t / HZ)); return Math.floor(sec / 60) + ":" + (sec % 60 < 10 ? "0" : "") + (sec % 60); }
    function screenMap() {
      var cw = canvas.width, ch = canvas.height, scale = Math.min(cw / world.w, ch / world.h);
      return { s: scale, ox: (cw - world.w * scale) / 2, oy: (ch - world.h * scale) / 2 };
    }
    /* In the WebGL view the power-up icons and damage numbers ride on the HUD canvas. */
    function drawWorldLabels() {
      var m = screenMap(), lift = Math.tan(TILT);
      ctx.setTransform(m.s, 0, 0, m.s, m.ox, m.oy);
      S.powerUps.forEach(function (pu) {
        ctx.save(); ctx.translate(pu.x, pu.y - 10 * lift); ctx.scale(0.8, 0.8);
        powerIcon(pu.kind, "#ffffff", false, pu.r);
        ctx.restore();
      });
    }
    function roundRect(x, y, w, h, r) {
      ctx.beginPath(); ctx.moveTo(x + r, y); ctx.lineTo(x + w - r, y); ctx.quadraticCurveTo(x + w, y, x + w, y + r); ctx.lineTo(x + w, y + h - r);
      ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h); ctx.lineTo(x + r, y + h); ctx.quadraticCurveTo(x, y + h, x, y + h - r); ctx.lineTo(x, y + r); ctx.quadraticCurveTo(x, y, x + r, y); ctx.closePath();
    }
    /* One labelled bar: a dark track, a lagging ghost of recent damage, the live fill, and ticks. */
    function hudBar(x, y, w, h, frac, ghost, c0, c1, label, value) {
      ctx.fillStyle = "rgba(2,8,12,0.72)"; roundRect(x - 4, y - 15, w + 8, h + 19, 6); ctx.fill();
      ctx.font = "800 10.5px " + hudFont; ctx.textAlign = "left"; ctx.textBaseline = "alphabetic";
      ctx.fillStyle = "#cfe6ea"; ctx.fillText(label, x, y - 4);
      ctx.textAlign = "right"; ctx.fillStyle = "#e6f6f8"; ctx.fillText(value, x + w, y - 4);
      ctx.fillStyle = "rgba(148,163,184,0.22)"; ctx.fillRect(x, y, w, h);
      if (ghost > frac) { ctx.fillStyle = "rgba(255,240,230,0.7)"; ctx.fillRect(x + w * frac, y, w * (ghost - frac), h); }
      var g = ctx.createLinearGradient(x, 0, x + w, 0);
      g.addColorStop(0, c0); g.addColorStop(1, c1);
      ctx.fillStyle = g; ctx.fillRect(x, y, w * Math.max(0, frac), h);
      ctx.fillStyle = "rgba(255,255,255,0.28)"; ctx.fillRect(x, y, w * Math.max(0, frac), Math.max(1, h * 0.35));
      ctx.fillStyle = "rgba(2,8,12,0.55)";
      for (var k = 1; k < 10; k++) ctx.fillRect(x + w * k / 10, y, 1, h);
    }
    function drawHud() {
      if (!S || !ctx) return;
      var dpr = canvas.width / Math.max(1, canvas.clientWidth || canvas.width);
      var W = canvas.width / dpr, H = canvas.height / dpr, small = W < 520;
      if (!hudFont) hudFont = (window.getComputedStyle && getComputedStyle(host).fontFamily) || "system-ui, sans-serif";
      var p = S.player, m = screenMap();
      /* damage numbers float over the ship */
      ctx.setTransform(m.s, 0, 0, m.s, m.ox, m.oy);
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.font = "900 " + (small ? 22 : 17) + "px " + hudFont;
      S.popups.forEach(function (u) { ctx.globalAlpha = Math.max(0, 1 - u.t / u.life); ctx.fillStyle = u.color; ctx.fillText(u.text, u.x, u.y); });
      ctx.globalAlpha = 1;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      var bar = ctx.createLinearGradient(0, 0, 0, small ? 70 : 56);
      bar.addColorStop(0, "rgba(2,8,12,0.75)"); bar.addColorStop(1, "rgba(2,8,12,0)");
      ctx.fillStyle = bar; ctx.fillRect(0, 0, W, small ? 76 : 62);
      /* hull and, while it lasts, the shield: two bars, top left */
      var hf = p.health / HEALTH_MAX;
      hpShown = Math.max(p.health, Math.min(hpShown, HEALTH_MAX) - 0.6);
      if (hpShown < p.health) hpShown = p.health;
      var bw = small ? Math.min(150, W * 0.36) : 190, bx = 14, by = 24;
      var hc = hf > 0.6 ? ["#10b981", "#5eead4"] : hf > 0.3 ? ["#f59e0b", "#fde047"] : ["#dc2626", "#fb7185"];
      hudBar(bx, by, bw, small ? 8 : 9, hf, hpShown / HEALTH_MAX, hc[0], hc[1], "HULL", Math.ceil(p.health) + " / " + HEALTH_MAX);
      if (p.shieldHp > 0) {
        shShown = Math.max(p.shieldHp, shShown - 0.5);
        hudBar(bx, by + 30, bw, small ? 6 : 7, p.shieldHp / SHIELD_MAX, shShown / SHIELD_MAX, "#2563eb", "#93c5fd", "SHIELD", p.shieldHp + " / " + SHIELD_MAX);
      } else shShown = 0;
      ctx.textBaseline = "middle";
      ctx.font = "800 " + (small ? 13 : 15) + "px " + hudFont;
      ctx.fillStyle = "#e6f6f8"; ctx.textAlign = "right";
      ctx.fillText("Score " + S.score.toLocaleString("en-US"), W - 14, 18);
      /* level, its difficulty, its goal, and progress toward it */
      var d = diff(), g = goal();
      var dc = { Easy: "#4ade80", Medium: "#fbbf24", Hard: "#f87171" }[d.name];
      if (small) {
        ctx.textAlign = "right"; ctx.font = "800 11.5px " + hudFont;
        ctx.fillStyle = dc; ctx.fillText(S.boss ? "FINAL BOSS" : ("LEVEL " + S.level + " - " + d.name).toUpperCase(), W - 14, 36);
      } else {
        ctx.textAlign = "center"; ctx.font = "800 13px " + hudFont;
        var title = S.boss ? "FINAL BOSS" : "LEVEL " + S.level + (cfg.progression ? ": " + FORMS[S.level].toUpperCase() : "");
        var tw = ctx.measureText(title).width, dn = "  " + d.name.toUpperCase(), dw = ctx.measureText(dn).width;
        ctx.fillStyle = "#5eead4"; ctx.textAlign = "left";
        ctx.fillText(title, W / 2 - (tw + dw) / 2, 14);
        ctx.fillStyle = dc; ctx.fillText(dn, W / 2 - (tw + dw) / 2 + tw, 14);
      }
      if (g) {
        ctx.textAlign = "center";
        ctx.font = "600 " + (small ? 11.5 : 12.5) + "px " + hudFont;
        ctx.fillStyle = "#c7dde2";
        var gy = small ? (p.shieldHp > 0 ? 92 : 64) : 31;
        ctx.fillText(g.text, W / 2, gy);
        if (g.k !== null) {
          var pw = Math.min(260, W * 0.36), px = W / 2 - pw / 2, py = gy + 9;
          ctx.fillStyle = "rgba(148,163,184,0.25)"; ctx.fillRect(px, py, pw, 4);
          ctx.fillStyle = S.boss ? "#f2feff" : "#2dd4bf"; ctx.fillRect(px, py, pw * Math.max(0, Math.min(1, g.k)), 4);
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
        ctx.textAlign = "center";
        ctx.font = "900 " + (small ? 20 : 26) + "px " + hudFont;
        ctx.fillStyle = "#f2feff";
        ctx.fillText(S.banner.text.toUpperCase(), W / 2, H * 0.4);
        if (S.banner.sub) { ctx.font = "700 " + (small ? 12 : 14) + "px " + hudFont; ctx.fillStyle = dc; ctx.fillText(S.banner.sub, W / 2, H * 0.4 + (small ? 22 : 28)); }
        ctx.globalAlpha = 1;
      }
      /* the edge of the arena flashes red when the hull takes damage */
      if (p.hurt > 0 && !REDUCED) {
        var v = ctx.createRadialGradient(W / 2, H / 2, Math.min(W, H) * 0.35, W / 2, H / 2, Math.max(W, H) * 0.7);
        v.addColorStop(0, "rgba(220,38,38,0)"); v.addColorStop(1, "rgba(220,38,38," + (0.35 * p.hurt / 14).toFixed(2) + ")");
        ctx.fillStyle = v; ctx.fillRect(0, 0, W, H);
      }
    }

    function sync() {
      if (!S) return;
      var p = S.player;
      hudScore.textContent = "Score " + S.score;
      hudLives.textContent = "Hull " + Math.max(0, p.health) + " of " + HEALTH_MAX + (p.shieldHp > 0 ? ", shield " + p.shieldHp : "");
      hudLevel.textContent = "Level " + S.level + " (" + diff().name + ")" + (cfg.progression ? ": " + FORMS[S.level] : "");
      var extras = [];
      if (p.shieldHp > 0) extras.push("shield");
      if (p.weapon > 0) extras.push("twin shot " + Math.ceil(p.weapon / HZ) + "s");
      if (S.boss) extras.push("boss");
      var base = S.state === "idle" ? "Ready" : S.state === "running" ? "Playing" : S.state === "paused" ? "Paused" : S.victory ? "Victory" : "Game over";
      hudState.textContent = extras.length && S.state === "running" ? base + ": " + extras.join(", ") : base;
      overlay.hidden = S.state === "running";
      overTitle.textContent = S.victory ? "The Nexus megaship is down" : S.state === "over" ? (S.overText || "Game over") : "";
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
      render: function () { draw(); return renderer; },
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
        queueDraw();
        return api.state();
      },
      input: function (keys) { for (var k in keys) if (Object.prototype.hasOwnProperty.call(held, k)) held[k] = !!keys[k]; },
      /* forceHit(source, detail): source is shot, needle, beam, blast (detail: distance from the
         blast), collision (detail: enemy class or "boss"), asteroid (detail: large, medium,
         small), bossShot, or test. */
      forceHit: function (source, detail) {
        if (!S || S.state === "idle") return false;
        return withRunning(function () { return hitPlayer(source || "test", detail, source === "blast" ? detail : undefined); });
      },
      damageFor: function (source, detail) { return S ? damageFor(source, detail, source === "blast" ? detail : undefined) : 0; },
      dropPowerUp: function (kind) {
        if (kind === "ship") kind = "repair";   /* the old extra-ship name still works */
        if (!S || !Object.prototype.hasOwnProperty.call(POWER_LOOK, kind)) return false;
        spawnPowerUp(kind, S.player.x, S.player.y);
        return true;
      },
      spawn: function (type, x, y) {
        if (!S || !ENEMY[type]) return false;
        var e = makeEnemy(type, x, y);
        e.pinned = true;
        S.enemies.push(e);
        return true;
      },
      spawnAsteroid: function (size, x, y, vx, vy) {
        if (!S || !ROCK[size]) return false;
        S.asteroids.push(makeRock(size, x, y, vx || 0, vy || 0, S.rng.rocks));
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
           as a column of falling points, the way a player reads the glow and the tell. An armed
           bomb threatens its whole blast circle. */
        var columns = [], blasts = [], beams = [];
        function column(x, y0) { for (var y = y0; y < world.h; y += 36) columns.push({ x: x, y: y, r: 14, vx: 0, vy: 8 }); }
        S.enemyShots.forEach(function (o) {
          if (o.kind === "beam") { column(o.x, o.y); beams.push({ x: o.x, y: o.y, life: o.life }); }
          else if (o.kind === "bomb" && o.arm > 0) blasts.push({ x: o.x, y: o.y, r: BLAST_RADIUS, vx: 0, vy: 8, armed: o.arm });
        });
        S.enemies.forEach(function (e) { if (e.charge > 0) { column(e.x, e.y + e.r); beams.push({ x: e.x, y: e.y + e.r, charging: e.charge }); } });
        return {
          player: { x: S.player.x, y: S.player.y, r: S.player.r },
          threats: S.enemyShots.filter(function (o) { return o.kind !== "beam" && !(o.kind === "bomb" && o.arm > 0); }).map(pick).concat(columns, blasts, S.enemies.map(pick), S.asteroids.map(pick)),
          beams: beams, blasts: blasts,
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
        var p = S.player, b = S.boss, d = diff();
        return {
          id: id, tick: S.tick, state: S.state, pausedBy: S.pausedBy, score: S.score, level: S.level,
          form: cfg.progression ? FORMS[S.level] : FORMS[1], levelUps: S.levelUps.slice(),
          health: p.health, healthMax: HEALTH_MAX, shieldHp: p.shieldHp, shieldMax: SHIELD_MAX,
          difficulty: { level: cfg.progression ? S.level : 1, name: d.name, pace: d.pace, rocks: d.rocks, fire: d.fire, damage: d.damage, cap: d.cap, classes: d.mix.map(function (x) { return x[0]; }) },
          lastDamage: S.lastDamage ? { source: S.lastDamage.source, detail: S.lastDamage.detail, amount: S.lastDamage.amount, absorbed: S.lastDamage.absorbed, tick: S.lastDamage.tick } : null,
          damageLog: S.damageLog.map(function (x) { return { source: x.source, detail: x.detail, amount: x.amount, absorbed: x.absorbed, tick: x.tick }; }),
          damageTaken: S.damageTaken, renderer: renderer,
          defects: { firstHitFatal: cfg.defects.firstHitFatal, randomExplosion: cfg.defects.randomExplosion },
          progression: cfg.progression, bossEnabled: cfg.boss,
          seed: cfg.seed, world: { w: world.w, h: world.h },
          player: { x: p.x, y: p.y, invuln: p.invuln, exploding: 0, shield: p.shieldHp, weapon: p.weapon,
            spread: p.spread || 0, rapid: p.rapid || 0, missiles: p.missiles || 0, wingman: p.wingman || 0 },
          shotKinds: S.enemyShots.map(function (o) { return o.kind; }), goal: goal(),
          enemies: S.enemies.length, enemyShots: S.enemyShots.length, asteroids: S.asteroids.length, shots: S.shots.length,
          enemyTypes: S.enemies.map(function (e) { return e.type; }), spawned: S.spawned,
          asteroidSizes: S.asteroids.map(function (a) { return a.size; }), breaks: S.breaks.slice(),
          powerUps: S.powerUps.length, collected: S.collected.slice(),
          firstShotTick: S.firstShotTick, firstShotGap: S.firstShotGap,
          explodeTicks: S.explodeTicks.slice(), hitTicks: S.hitTicks.slice(),
          nextExplosion: S.nextExplosion, overReason: S.overReason, overText: S.overText, victory: S.victory,
          boss: b ? { entered: b.entered, nodesAlive: nodesAlive(b), coreHp: b.coreHp } : null, bossDue: S.bossDue,
          canvas: { cssWidth: canvas.clientWidth, cssHeight: canvas.clientHeight, width: canvas.width, height: canvas.height }
        };
      },
      animating: function () { return !!S && S.state === "over" && S.afterglow > 0; },
      frame: function (now) {
        if (S && S.state === "over" && S.afterglow > 0) {
          S.afterglow -= 1;
          for (var k = 0; k < S.effects.length; k++) {
            var f = S.effects[k];
            f.t += 1;
            if (f.vx != null) { f.x += f.vx; f.y += f.vy; f.vx *= 0.94; f.vy *= 0.94; }
          }
          S.effects = S.effects.filter(function (o) { return o.t < o.life; });
          draw();
          last = 0;
          return;
        }
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
    for (var k in instances) if (instances[k].running() || instances[k].animating()) return true;
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
      EXPLOSION_GAP: EXPLOSION_GAP, INVULNERABLE_TICKS: HIT_INVULN, HIT_INVULN: HIT_INVULN, HEALTH_MAX: HEALTH_MAX, SHIELD_MAX: SHIELD_MAX,
      REPAIR: REPAIR, EXPLOSION_DAMAGE: EXPLOSION_DAMAGE, BLAST_RADIUS: BLAST_RADIUS, BOMB_ARM: BOMB_ARM,
      DAMAGE: DAMAGE, DIFFICULTY: { 1: DIFFICULTY[1].name, 2: DIFFICULTY[2].name, 3: DIFFICULTY[3].name },
      LEVEL_TICKS: LEVEL_TICKS, BOSS_AFTER: BOSS_AFTER, WEAPON_TICKS: WEAPON_TICKS
    }
  };
})();
