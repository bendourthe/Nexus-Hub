// Landing-page fly-over: camera and animation curves (scene contract flyover-scene/1).
// Pure math, no DOM and no clock: every value is a function of time t and the capture metadata.
// World units are page CSS px: X = page x, Y = height above the page, Z = page y (down the page).

export const W = 1440, H = 1152, FOCAL = 1880, DURATION = 14.5;
export const DEG = Math.PI / 180;
export const TILT = 56 * DEG;

export const clamp01 = (x) => Math.min(1, Math.max(0, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const smooth = (a, b, x) => { const t = clamp01((x - a) / (b - a)); return t * t * (3 - 2 * t); };
// Integral of smooth(a, b, x) from -inf to x, so speed curves integrate exactly into positions.
export const smoothInt = (a, b, x) => {
  if (x <= a) return 0;
  if (x >= b) return (b - a) * 0.5 + (x - b);
  const u = (x - a) / (b - a);
  return (b - a) * (u * u * u - 0.5 * u * u * u * u);
};
export const easeOutCubic = (x) => 1 - Math.pow(1 - clamp01(x), 3);
export const quadInOut = (u) => (u < 0.5 ? 2 * u * u : 1 - 2 * (1 - u) * (1 - u));
export const blurRadius = (depth, focus) =>
  Math.min(120, depth < focus ? (75 * (focus - depth)) / depth : (6 * (depth - focus)) / depth);

// Speed down the page as a share of cruise, and its exact integral.
export const speed = (t) => 0.5 * smooth(0, 0.6, t) + 0.5 * smooth(1.25, 1.6, t) - 0.88 * smooth(7.3, 8.3, t);
export const travel = (t) =>
  0.5 * smoothInt(0, 0.6, t) + 0.5 * smoothInt(1.25, 1.6, t) - 0.88 * smoothInt(7.3, 8.3, t);

const add = (a, b) => [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const mul = (a, s) => [a[0] * s, a[1] * s, a[2] * s];
const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];

export function project(cam, P) {
  const v = sub(P, cam.C);
  const z = dot(v, cam.F);
  return [W / 2 + (FOCAL * dot(v, cam.R)) / z, H / 2 - (FOCAL * dot(v, cam.U)) / z, z];
}

// World point at height h seen at screen (sx, sy).
export function unproject(cam, sx, sy, h) {
  const dir = add(add(cam.F, mul(cam.R, (sx - W / 2) / FOCAL)), mul(cam.U, -(sy - H / 2) / FOCAL));
  return add(cam.C, mul(dir, (h - cam.C[1]) / dir[1]));
}

export function makeTimeline(meta) {
  const PW = meta.page.width, PH = meta.page.height, A = meta.anchors;
  const title = meta.title ?? { badge: '', line1: '', tail: '' };

  // Glide: anchored so the second section's title crosses frame centre at 1.6s and the footer
  // title at 8.0s. Cruise follows from the page; the brief's ~770 px/s fits a ~5400px page.
  const cruise = (A.footerTitle - A.secondTitle) / (travel(8.0) - travel(1.6));
  const y0 = A.secondTitle - cruise * travel(1.6);
  const glideZ = (t) => y0 + cruise * travel(Math.max(0, t));

  // Flight distance 1360 -> 1700: velocity ramps in with the glide, then eases out by 8.2s.
  const N = 4000, gTab = new Float64Array(N + 1);
  const gv = (t) => smooth(0, 0.6, t) * (1 - smooth(1.6, 8.2, t));
  for (let i = 1; i <= N; i++) {
    const t0 = (8.2 * (i - 1)) / N, t1 = (8.2 * i) / N;
    gTab[i] = gTab[i - 1] + 0.5 * (gv(t0) + gv(t1)) * (t1 - t0);
  }
  const glideDist = (t) => {
    const x = clamp01(t / 8.2) * N, i = Math.min(N - 1, Math.floor(x));
    return 1360 + (340 * lerp(gTab[i], gTab[i + 1], x - i)) / gTab[N];
  };

  const tilt = (t) => TILT * (1 - smooth(8.15, 8.95, t));
  const LINE = H - 42 - H / 2; // the 42px line, measured from frame centre
  const dStrip = (FOCAL * PH) / (H - 84); // whole page as one strip, 42px top and bottom
  const riseV = Math.log(dStrip / 1700) / (smoothInt(7.75, 8.35, 9.25) - smoothInt(8.95, 9.25, 9.25));
  const rise = (t) => riseV * (smoothInt(7.75, 8.35, t) - smoothInt(8.95, 9.25, t));
  const CREEP = Math.log(1.035);
  const creepV = CREEP / smoothInt(9.25, 9.32, 9.47);
  const CARD_W = 1018, CARD_TOP = 283;
  const dCard = (FOCAL * PW) / CARD_W;
  const L1 = Math.log(dStrip), Lc = L1 - CREEP, L3 = Math.log(dCard);
  const top0 = H / 2 - (FOCAL * (PH / 2)) / Math.exp(Lc);
  const tzCard = ((H / 2 - CARD_TOP) * dCard) / FOCAL;

  function camera(t) {
    const th = tilt(t);
    let d, tz;
    if (t <= 9.25) {
      d = glideDist(t) * Math.exp(rise(t));
      const zg = glideZ(t);
      const w = smooth(8.3, 8.65, t);
      tz = zg;
      if (w > 0) {
        // Hand the glide to a camera that holds the page's bottom edge on the 42px line.
        const dz = PH - zg;
        const kG = (FOCAL * dz * Math.cos(th)) / (d - dz * Math.sin(th));
        const k = lerp(kG, LINE, w);
        tz = PH - (k * d) / (FOCAL * Math.cos(th) + k * Math.sin(th));
      }
    } else if (t <= 9.47) {
      d = Math.exp(L1 - creepV * smoothInt(9.25, 9.32, t));
      tz = PH / 2;
    } else if (t <= 9.97) {
      // Dive: log distance on a quadratic ease in-out (plus the creep's slope at the start),
      // look-at point solved so the page's top edge stays pinned, then drops to y 283.
      const u = (t - 9.47) / 0.5;
      d = Math.exp(Lc + (L3 - Lc) * quadInOut(u) - creepV * 0.5 * u * (1 - u) * (1 - u));
      const topY = lerp(top0, CARD_TOP, smooth(0.35, 1, u));
      tz = ((H / 2 - topY) * d) / FOCAL;
    } else {
      d = Math.exp(L3 - Math.log(1.02) * smooth(10.6, 14.5, t));
      tz = tzCard;
    }
    const s = Math.sin(th), c = Math.cos(th);
    const T = [PW / 2, 0, tz];
    const C = [T[0], d * c, tz + d * s];
    // Focus starts on the hero's mockup row and settles on frame centre.
    const bias = ((A.mockup ?? y0) - y0) * (1 - smooth(0, 1.2, t));
    return { t, th, d, T, C, F: [0, -c, -s], U: [0, s, -c], R: [1, 0, 0], focus: d - bias * s };
  }

  // ---------- lifted pieces ----------
  const REST = { card: 24, heroChip: 8, button: 26, chip: 12, photo: 14, flyChip: 6, testimonial: 22 };
  const HERO_PEAK = [66, 76, 80, 72, 62];
  const pieces = meta.layers.map((L, i) => ({
    ...L, i,
    cx: L.x + L.w / 2, cz: L.y + L.h / 2,
    qw: L.w + 2 * L.pad, qh: L.h + 2 * L.pad,
    hash: (i * 0.6180339887) % 1,
    rest: (REST[L.role] ?? 20) + (L.role === 'card' && L.h > 600 ? 6 : 0),
    belowHero: L.y > A.heroBottom - 1,
  }));
  pieces.filter((p) => p.role === 'heroChip').sort((a, b) => a.cx - b.cx).forEach((p, k) => { p.k = k; });

  // Fly chips: lateral flight solved so their centres cross the left and right frame edges at 2.5s.
  const flyLift = (t) => smooth(1.55, 2.4, t);
  const flyLat = (t) => 2 * smoothInt(1.6, 2.4, t); // = 1 at 2.5s, keeps flying outward after
  const cam25 = camera(2.5);
  const flyTargets = [[-40, 800], [W + 40, 740]];
  pieces.filter((p) => p.role === 'flyChip').sort((a, b) => a.cx - b.cx).slice(0, 2).forEach((p, k) => {
    const w = unproject(cam25, flyTargets[k][0], flyTargets[k][1], 200);
    p.fdx = w[0] - p.cx;
    p.fdz = w[2] - p.cz;
  });

  // Testimonial edge: thickness chosen so the white edge reads 34px on screen once it stands.
  const testi = pieces.find((p) => p.role === 'testimonial');
  if (testi) {
    const cam = camera(6.3), a = 30 * DEG;
    const B = [testi.cx, 112 - (testi.h / 2) * Math.sin(a), testi.cz + (testi.h / 2) * Math.cos(a)];
    const n = [0, Math.cos(a), Math.sin(a)];
    const p0 = project(cam, B), p1 = project(cam, sub(B, n));
    testi.edgeUnit = 34 / Math.hypot(p1[0] - p0[0], p1[1] - p0[1]);
  }

  function pieceState(p, t) {
    let h = p.rest, a = 0, dx = 0, dz = 0, opacity = 1, haze = 0, edge = 0;
    const gz = glideZ(Math.min(t, 8.3));
    if (p.role === 'heroChip') {
      const k = p.k ?? 0;
      const q = smooth(0.1 + 0.05 * k, 1.1 + 0.0625 * Math.min(k, 4), t);
      h = lerp(p.rest, HERO_PEAK[k % HERO_PEAK.length], q);
      a = 30 * DEG * q;
    } else if (p.role === 'photo') {
      const q = smooth(1.35, 2.7, t);
      h = lerp(p.rest, 118, q);
      a = 46 * DEG * q;
    } else if (p.role === 'flyChip' && p.fdx !== undefined) {
      const q = flyLift(t), l = flyLat(t);
      h = lerp(p.rest, 200, q);
      a = 54 * DEG * q;
      dx = p.fdx * l;
      dz = p.fdz * l;
      opacity = 1 - smooth(3.2, 3.3, t);
    } else if (p.role === 'testimonial') {
      const q = smooth(5.45, 6.3, t);
      h = lerp(p.rest, 112, q);
      a = 30 * DEG * q;
      edge = (p.edgeUnit ?? 0) * q;
    } else if (p.role === 'chip' || p.role === 'flyChip') {
      // Generic chips lift a little as the camera passes over them.
      const q = smooth(p.cz - 1150, p.cz - 350, gz);
      h = lerp(p.rest, 22 + 16 * p.hash, q);
      a = (14 + 10 * p.hash) * DEG * q;
    }
    // Never let a standing piece sink through the page.
    a = Math.min(a, Math.asin(clamp01((h - 4) / (p.h / 2))));
    // Settle back to rest during the rise so the hero lands flat.
    const r = smooth(8.4, 9.3, t);
    h = lerp(h, p.rest, r);
    a = lerp(a, 0, r);
    edge = lerp(edge, 0, r);
    if (p.belowHero) {
      // Fade into the haze colour first, cut to transparent only once it matches the floor.
      haze = smooth(9.5, 9.66, t);
      if (t > 9.7) opacity = 0;
    }
    return { x: p.cx + dx, z: p.cz + dz, h, a, opacity, haze, edge };
  }

  // ---------- logo tiles ----------
  const btn = A.button ?? { x: PW / 2 - 32, y: A.heroBottom * 0.6, w: 64, h: 64 };
  const bx = btn.x + btn.w / 2, by = btn.y + btn.h / 2, gap = btn.w / 2 + 38;
  const tStart = [[bx - gap, by - 18], [bx - gap, by + 18], [bx + gap, by - 18], [bx + gap, by + 18]];
  // Hang points solved from where the tiles should sit on screen at 1.35s: just outside the
  // page's top corners, inside the frame.
  const cam135 = camera(1.35);
  const tHang = [
    { sx: 70, sy: 175, h: 170, s: 150 }, { sx: 200, sy: 70, h: 250, s: 190 },
    { sx: 1380, sy: 170, h: 150, s: 140 }, { sx: 1250, sy: 62, h: 230, s: 180 },
  ].map((g) => { const w = unproject(cam135, g.sx, g.sy, g.h); return { x: w[0], z: w[2], h: g.h, s: g.s }; });
  const tEnd = [
    { x: -700, z: 300, h: 220, s: 160 }, { x: 14, z: 14, h: 70, s: 124 },
    { x: PW + 265, z: A.heroBottom * 0.65, h: 6, s: 170 }, { x: PW - 14, z: 14, h: 70, s: 124 },
  ];
  const t7 = unproject(camera(5.4), 30, 640, 520);
  const cam106 = camera(10.6);
  const blurTiles = [unproject(cam106, 70, 1110, 1450), unproject(cam106, 1375, 1120, 1450)];

  function tiles(t) {
    const out = [];
    const drift = smooth(10.6, 14.5, t);
    for (let i = 0; i < 4; i++) {
      const st = 0.1 + 0.05 * i;
      const p = smooth(st, 1.35, t), ph = smooth(st, 1.0, t);
      let x = lerp(tStart[i][0], tHang[i].x, p);
      let z = lerp(tStart[i][1], tHang[i].z, p) + 300 * smooth(1.2, 2.4, t);
      let h = lerp(3, tHang[i].h, ph);
      let s = lerp(32, tHang[i].s, p);
      const e = smooth(8.5, 9.55, t);
      x = lerp(x, tEnd[i].x, e) + (i % 2 ? -1 : 1) * 5 * drift;
      z = lerp(z, tEnd[i].z, e) + 3 * drift;
      h = lerp(h, tEnd[i].h, e);
      s = lerp(s, tEnd[i].s, e);
      out.push({ id: `T${i}`, x, z, h, s, a: tilt(t) * smooth(st, 1.1, t), opacity: 1 });
    }
    out.push({
      id: 'T4', x: t7[0] - 700 * (t - 5.4), z: t7[2], h: 520, s: 230, a: tilt(t),
      opacity: smooth(4.7, 4.8, t) * (1 - smooth(6.2, 6.3, t)),
    });
    blurTiles.forEach((w, k) => {
      const e = easeOutCubic((t - 9.7) / 0.85);
      out.push({
        id: `T${5 + k}`,
        x: w[0] + (k ? 1 : -1) * (800 * (1 - e) + 6 * drift),
        z: w[2] + 700 * (1 - e) - 4 * drift,
        h: 1450, s: 215, a: 0,
        opacity: smooth(9.62, 9.75, t),
      });
    });
    return out;
  }

  function pageState(t) {
    return {
      mask: [0, 0, PW, lerp(PH, A.heroBottom, smooth(9.62, 9.92, t))],
      radius: lerp(24, (38 * PW) / CARD_W, smooth(9.47, 9.97, t)),
      fadeY: A.heroBottom,
      fade: smooth(9.5, 9.66, t),
    };
  }

  const word = (t, start) => {
    const e = easeOutCubic((t - start) / 0.34);
    return { dy: 16 * (1 - e), blur: 12 * (1 - e), opacity: smooth(0, 1, clamp01((t - start) / 0.34)) };
  };
  function overlays(t) {
    return {
      badge: { opacity: smooth(10.02, 10.32, t), dy: 8 * (1 - easeOutCubic((t - 10.02) / 0.4)) },
      line1: (k) => word(t, 10.12 + 0.06 * k),
      tail: (k) => word(t, 10.36 + 0.05 * k),
    };
  }

  // Analytic self-check run before any frame renders: the flight never slows down the page or
  // zooms in, and the hero lands as the 1018px card with its top at y 283.
  function check() {
    let minV = Infinity, minDD = Infinity, prev = camera(0);
    for (let t = 0.001; t <= 8.2; t += 0.001) {
      const c = camera(t);
      minV = Math.min(minV, (c.T[2] - prev.T[2]) / 0.001);
      minDD = Math.min(minDD, (c.d - prev.d) / 0.001);
      prev = c;
    }
    const c = camera(9.97);
    const tl = project(c, [0, 0, 0]), br = project(c, [PW, 0, A.heroBottom]);
    const card = { x0: tl[0], x1: br[0], top: tl[1], bottom: br[1] };
    const pass = minV > -1e-6 && minDD > -1e-6 && Math.abs(card.x1 - card.x0 - CARD_W) < 0.5 &&
      Math.abs(card.top - CARD_TOP) < 0.5 && y0 >= 0 && y0 <= A.heroBottom;
    return { pass, minPageSpeed: minV, minZoomOut: minDD, card, cruise, y0 };
  }

  return {
    camera, pieces, pieceState, tiles, pageState, overlays, glideZ, glideDist, tilt, check, title,
    info: { cruise, y0, dStrip, dCard, tzCard, top0, riseV, PW, PH },
  };
}
