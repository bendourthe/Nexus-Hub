// Landing-page fly-over renderer (scene contract flyover-scene/1).
// Exposes window.DURATION and async window.seek(t); every pixel is a pure function of t and the
// capture in ../capture/. No timers, no CSS transitions, no network: the render driver serves
// this folder's parent on loopback and aborts any other request.
import { makeTimeline, W, H, FOCAL, DURATION, blurRadius } from './timeline.js';

const NEAR = 2, FAR = 1e6;
const canvas = document.getElementById('c');
const gl = canvas.getContext('webgl2', {
  antialias: false, alpha: false, premultipliedAlpha: true, preserveDrawingBuffer: true,
});
if (!gl) throw new Error('WebGL2 unavailable');
if (!gl.getExtension('EXT_color_buffer_float')) throw new Error('EXT_color_buffer_float unavailable');
const ANISO = gl.getExtension('EXT_texture_filter_anisotropic');

// ---------- shaders ----------
const COMMON = `#version 300 es
precision highp float;
precision highp sampler2D;
uniform vec2 uRes;
uniform float uFocus;
uniform float uFocal;
uniform float uJitter;
vec3 floorColor(vec2 fc) {
  vec2 p = (fc - 0.5 * uRes) / (0.5 * uRes);
  float r = clamp(length(p) / 1.41421356, 0.0, 1.0);
  return mix(vec3(0.97647, 0.98431, 0.98431), vec3(0.94902, 0.95294, 0.96471), smoothstep(0.0, 1.0, r));
}
float blurR(float depth) {
  float r = depth < uFocus ? 75.0 * (uFocus - depth) / depth : 6.0 * (depth - uFocus) / depth;
  return min(r, 120.0);
}
// Taps outside the texture count as transparent for cut-out pieces (coarse mips bleed into the
// clamped edge texels otherwise); the page clamps instead and gets its edge from an analytic mask.
vec4 tap(sampler2D tex, vec2 p, vec2 gx, vec2 gy, bool cut) {
  vec4 c = textureGrad(tex, p, gx, gy);
  if (cut && (p.x < 0.0 || p.y < 0.0 || p.x > 1.0 || p.y > 1.0)) c = vec4(0.0);
  return c;
}
// Golden-angle disc gather in screen space; each tap reads a mip level matched to the blur.
vec4 gatherScreen(sampler2D tex, vec2 uv, vec2 dx, vec2 dy, float R, bool cut) {
  if (R < 0.5) return tap(tex, uv, dx, dy, cut);
  float k = max(1.0, R * 0.3);
  vec2 gx = dx * k, gy = dy * k;
  vec4 acc = vec4(0.0);
  for (int i = 0; i < 40; i++) {
    float fi = float(i);
    float r = R * sqrt((fi + 0.5) / 40.0);
    float a = fi * 2.39996323 + uJitter;
    vec2 o = r * vec2(cos(a), sin(a));
    acc += tap(tex, uv + dx * o.x + dy * o.y, gx, gy, cut);
  }
  return acc * (1.0 / 40.0);
}
float sdRoundBox(vec2 p, vec2 b, float r) {
  vec2 q = abs(p) - b + r;
  return length(max(q, 0.0)) + min(max(q.x, q.y), 0.0) - r;
}
`;

const VS_WORLD = `#version 300 es
precision highp float;
uniform vec3 uO, uAX, uAZ;
uniform vec4 uMargin; // left, right, top, bottom (fractions of the axes)
uniform vec2 uUVo, uUVs; // sub-rectangle of the texture this quad covers
uniform vec3 uC, uR, uU, uF;
uniform float uFocal;
uniform vec2 uRes;
out vec2 vUV;
out float vDepth;
void main() {
  float s = (gl_VertexID & 1) == 1 ? 0.5 + uMargin.y : -0.5 - uMargin.x;
  float t = (gl_VertexID >> 1) == 1 ? 0.5 + uMargin.w : -0.5 - uMargin.z;
  vec3 w = uO + s * uAX + t * uAZ;
  vec3 v = w - uC;
  float xc = dot(v, uR), yc = dot(v, uU), zc = dot(v, uF);
  vUV = uUVo + vec2(s + 0.5, t + 0.5) * uUVs;
  vDepth = zc;
  gl_Position = vec4(uFocal * xc / (0.5 * uRes.x), uFocal * yc / (0.5 * uRes.y),
                     (zc * ${(FAR + NEAR) / (FAR - NEAR)}) - ${(2 * FAR * NEAR) / (FAR - NEAR)}, zc);
}`;

const VS_SCREEN = `#version 300 es
precision highp float;
uniform vec2 uCenter, uSize, uRes;
out vec2 vUV;
out float vDepth;
void main() {
  float s = (gl_VertexID & 1) == 1 ? 0.5 : -0.5;
  float t = (gl_VertexID >> 1) == 1 ? 0.5 : -0.5;
  vec2 p = uCenter + vec2(s, t) * uSize;
  vUV = vec2(s + 0.5, t + 0.5);
  vDepth = 1.0;
  gl_Position = vec4(p.x / uRes.x * 2.0 - 1.0, 1.0 - p.y / uRes.y * 2.0, 0.0, 1.0);
}`;

const VS_FULL = `#version 300 es
void main() {
  vec2 p = vec2(gl_VertexID == 1 ? 3.0 : -1.0, gl_VertexID == 2 ? 3.0 : -1.0);
  gl_Position = vec4(p, 0.0, 1.0);
}`;

const FS_FLOOR = COMMON + `
out vec4 o;
void main() { o = vec4(floorColor(gl_FragCoord.xy), 1.0); }`;

// Lifted pieces and logo tiles: per-pixel depth of field, optional fade into the haze color.
const FS_PIECE = COMMON + `
uniform sampler2D uTex;
uniform float uOpacity, uHaze;
in vec2 vUV;
in float vDepth;
out vec4 o;
void main() {
  vec2 dx = dFdx(vUV), dy = dFdy(vUV);
  vec4 c = gatherScreen(uTex, vUV, dx, dy, blurR(vDepth), true);
  c.rgb = mix(c.rgb, floorColor(gl_FragCoord.xy) * c.a, uHaze);
  o = c * uOpacity;
}`;

// Screen-space overlays (title words, badge) with a uniform blur.
const FS_SCREEN = COMMON + `
uniform sampler2D uTex;
uniform float uOpacity, uBlur;
in vec2 vUV;
out vec4 o;
void main() {
  vec2 dx = dFdx(vUV), dy = dFdy(vUV);
  o = gatherScreen(uTex, vUV, dx, dy, uBlur, true) * uOpacity;
}`;

// The page: textured plane, analytic rounded mask that morphs, content below the hero fades to haze.
const FS_PAGE = COMMON + `
uniform sampler2D uTex;
uniform vec2 uPage;
uniform vec4 uMask;
uniform float uRadius, uFadeY, uFade;
in vec2 vUV;
in float vDepth;
out vec4 o;
void main() {
  vec2 dx = dFdx(vUV), dy = dFdy(vUV);
  vec2 pp = vUV * uPage;
  vec2 px = dFdx(pp), py = dFdy(pp);
  float wpp = sqrt(0.5 * (dot(px, px) + dot(py, py)));
  float R = blurR(vDepth);
  vec4 c = gatherScreen(uTex, vUV, dx, dy, R, false);
  float hz = uFade * smoothstep(uFadeY - 6.0, uFadeY + 30.0, pp.y);
  c.rgb = mix(c.rgb, floorColor(gl_FragCoord.xy), hz);
  vec2 ctr = 0.5 * (uMask.xy + uMask.zw), hb = 0.5 * (uMask.zw - uMask.xy);
  float sd = sdRoundBox(pp - ctr, hb, uRadius);
  float cov = clamp(0.5 - sd / (wpp * max(1.0, R)), 0.0, 1.0);
  o = vec4(c.rgb, 1.0) * cov;
}`;

// Soft wide shadow of the page on the studio floor.
const FS_PAGESHADOW = COMMON + `
uniform vec2 uPage;
uniform vec4 uMask;
uniform float uRadius, uFadeY, uFade;
in vec2 vUV;
out vec4 o;
void main() {
  vec2 pp = vUV * uPage;
  vec2 ctr = 0.5 * (uMask.xy + uMask.zw), hb = 0.5 * (uMask.zw - uMask.xy);
  float sdWide = sdRoundBox(pp - ctr - vec2(0.0, 26.0), hb, uRadius);
  float sdNear = sdRoundBox(pp - ctr - vec2(0.0, 5.0), hb, uRadius);
  float wide = sdWide <= 0.0 ? 1.0 : exp(-sdWide * sdWide / (2.0 * 62.0 * 62.0));
  float near = sdNear <= 0.0 ? 1.0 : exp(-sdNear * sdNear / (2.0 * 10.0 * 10.0));
  float a = 0.16 * wide + 0.10 * near;
  a *= 1.0 - uFade * smoothstep(uFadeY - 40.0, uFadeY + 220.0, pp.y);
  o = vec4(vec3(0.10196, 0.12941, 0.2) * a, a);
}`;

// Piece shadows: the same picture in a flat color, blurred in world units plus depth of field.
const FS_SHADOW = COMMON + `
uniform sampler2D uTex;
uniform vec2 uQuad, uTexSize;
uniform float uBlurW, uOpacity;
uniform vec3 uColor;
in vec2 vUV;
in float vDepth;
out vec4 o;
void main() {
  float Rd = blurR(vDepth);
  float wpp = vDepth / uFocal;
  float Rw = sqrt(uBlurW * uBlurW + (Rd * wpp) * (Rd * wpp));
  float lod = log2(max(1.0, Rw * 0.3 * uTexSize.x / uQuad.x));
  float acc = 0.0;
  for (int i = 0; i < 40; i++) {
    float fi = float(i);
    float r = Rw * sqrt((fi + 0.5) / 40.0);
    float a = fi * 2.39996323 + uJitter;
    vec2 p = vUV + r * vec2(cos(a), sin(a)) / uQuad;
    if (p.x >= 0.0 && p.y >= 0.0 && p.x <= 1.0 && p.y <= 1.0) acc += textureLod(uTex, p, lod).a;
  }
  float a = acc / 40.0 * uOpacity;
  o = vec4(uColor * a, a);
}`;

const FS_ACCUM = `#version 300 es
precision highp float;
uniform sampler2D uTex;
uniform float uWeight;
out vec4 o;
void main() { o = texelFetch(uTex, ivec2(gl_FragCoord.xy), 0) * uWeight; }`;

const FS_FINAL = `#version 300 es
precision highp float;
uniform sampler2D uTex;
out vec4 o;
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
void main() {
  vec4 c = texelFetch(uTex, ivec2(gl_FragCoord.xy), 0);
  c.rgb += (hash(gl_FragCoord.xy) - 0.5) / 255.0;
  o = vec4(c.rgb, 1.0);
}`;

function compile(vs, fs) {
  const p = gl.createProgram();
  for (const [type, src] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fs]]) {
    const s = gl.createShader(type);
    gl.shaderSource(s, src);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
    gl.attachShader(p, s);
  }
  gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
  const loc = {};
  const n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
  for (let i = 0; i < n; i++) { const u = gl.getActiveUniform(p, i); loc[u.name] = gl.getUniformLocation(p, u.name); }
  return { p, loc };
}

const P = {
  floor: compile(VS_FULL, FS_FLOOR),
  piece: compile(VS_WORLD, FS_PIECE),
  page: compile(VS_WORLD, FS_PAGE),
  pageShadow: compile(VS_WORLD, FS_PAGESHADOW),
  shadow: compile(VS_WORLD, FS_SHADOW),
  screen: compile(VS_SCREEN, FS_SCREEN),
  accum: compile(VS_FULL, FS_ACCUM),
  final: compile(VS_FULL, FS_FINAL),
};
gl.bindVertexArray(gl.createVertexArray());

// ---------- textures ----------
// Mipmaps plus 16x anisotropic filtering keep far text from shimmering.
function makeTex(src) {
  const t = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, t);
  gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, gl.RGBA, gl.UNSIGNED_BYTE, src);
  gl.generateMipmap(gl.TEXTURE_2D);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  if (ANISO) gl.texParameterf(gl.TEXTURE_2D, ANISO.TEXTURE_MAX_ANISOTROPY_EXT, 16);
  return { t, w: src.width, h: src.height };
}
async function loadBitmap(url) {
  const blob = await (await fetch(url)).blob();
  return createImageBitmap(blob, { premultiplyAlpha: 'premultiply', colorSpaceConversion: 'none' });
}
function makeTarget() {
  const t = gl.createTexture();
  gl.bindTexture(gl.TEXTURE_2D, t);
  gl.texStorage2D(gl.TEXTURE_2D, 1, gl.RGBA16F, W, H);
  const fb = gl.createFramebuffer();
  gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, t, 0);
  return { t, fb };
}

const CAP = '../capture/';
const meta = await (await fetch(CAP + 'layers.json')).json();
const tl = makeTimeline(meta);
const TITLE = tl.title;
await Promise.all([document.fonts.load('500 74px Geist'), document.fonts.load('italic 82px "Instrument Serif"')]);
await document.fonts.ready;

const pageBmp = await loadBitmap(CAP + meta.page.file);
if (pageBmp.height > gl.getParameter(gl.MAX_TEXTURE_SIZE)) throw new Error('page texture exceeds MAX_TEXTURE_SIZE');
const pageTex = makeTex(pageBmp);
const pieceTex = {};
await Promise.all(meta.layers.map(async (L) => { pieceTex[L.id] = makeTex(await loadBitmap(CAP + L.file)); }));
const logoBmp = meta.logo ? await loadBitmap(CAP + meta.logo) : null;

// On a dark page a #1a2133 shadow reads lighter than the page itself, so it goes near-black there.
const pageLum = (() => {
  const m = String(meta.page.bg ?? '').match(/\d+(\.\d+)?/g);
  if (!m || m.length < 3) return 1;
  const [r, g, b] = m.slice(0, 3).map(Number);
  return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255;
})();
const SHADOW_ON_PAGE = pageLum < 0.35 ? { color: [0, 0.012, 0.02], opacity: 0.5 } : { color: [0.10196, 0.12941, 0.2], opacity: 0.26 };
const SHADOW_ON_FLOOR = { color: [0.10196, 0.12941, 0.2], opacity: 0.26 };

function canvas2d(w, h) {
  const c = document.createElement('canvas');
  c.width = w; c.height = h;
  return [c, c.getContext('2d')];
}
// Logo tile: the mark on a rounded square in the page's own card color, transparent margin for blur.
const tileTex = (() => {
  const [c, g] = canvas2d(512, 512);
  g.beginPath(); g.roundRect(20, 20, 472, 472, 108);
  g.fillStyle = meta.tileColor ?? (pageLum < 0.35 ? '#0c1f26' : '#ffffff'); g.fill();
  g.lineWidth = 4; g.strokeStyle = pageLum < 0.35 ? 'rgba(255, 255, 255, 0.16)' : 'rgba(18, 20, 24, 0.10)'; g.stroke();
  if (logoBmp) g.drawImage(logoBmp, 74, 74, 364, 364);
  return makeTex(c);
})();
const TILE_INNER = 472 / 512;
// White card edge for the testimonial.
const edgeTex = (() => {
  const [c, g] = canvas2d(256, 64);
  g.beginPath(); g.roundRect(6, 6, 244, 52, 4);
  g.fillStyle = '#ffffff'; g.fill();
  return makeTex(c);
})();
// Title words, each in its own texture so it can blur independently.
const SS = 2; // supersample text textures
function wordTex(text, font, color, size, letterSpacing) {
  const [, mg] = canvas2d(4, 4);
  mg.font = font; mg.letterSpacing = letterSpacing;
  const wpx = Math.ceil(mg.measureText(text).width);
  const pad = 30, hgt = Math.ceil(size * 1.5);
  const [c, g] = canvas2d((wpx + 2 * pad) * SS, (hgt + 2 * pad) * SS);
  g.scale(SS, SS);
  g.font = font; g.letterSpacing = letterSpacing; g.fillStyle = color; g.textBaseline = 'alphabetic';
  g.fillText(text, pad, pad + size * 1.1);
  return { ...makeTex(c), cw: wpx + 2 * pad, ch: hgt + 2 * pad, pad, base: pad + size * 1.1 };
}
function layoutLine(text, font, color, size, letterSpacing, baseline) {
  if (!text) return [];
  const [, mg] = canvas2d(4, 4);
  mg.font = font; mg.letterSpacing = letterSpacing;
  const x0 = W / 2 - mg.measureText(text).width / 2;
  let idx = 0;
  return text.split(' ').map((wd) => {
    const x = x0 + mg.measureText(text.slice(0, idx)).width;
    idx += wd.length + 1;
    const tx = wordTex(wd, font, color, size, letterSpacing);
    return { tx, x: x - tx.pad, y: baseline - tx.base };
  });
}
const LINE1 = layoutLine(TITLE.line1, '500 74px Geist', '#121418', 74, '-1.6px', 168);
const TAIL = layoutLine(TITLE.tail, 'italic 82px "Instrument Serif"', '#8b8b92', 82, '0px', 250);
const badge = (() => {
  const font = '500 21px Geist';
  const [, mg] = canvas2d(4, 4);
  mg.font = font;
  const tw = Math.ceil(mg.measureText(TITLE.badge || ' ').width);
  const ph = 44, pw = 8 + 30 + 10 + tw + 18, pad = 30;
  const [c, g] = canvas2d((pw + 2 * pad) * SS, (ph + 2 * pad) * SS);
  g.scale(SS, SS);
  g.save();
  g.shadowColor = 'rgba(26, 33, 51, 0.10)'; g.shadowBlur = 18; g.shadowOffsetY = 5;
  g.beginPath(); g.roundRect(pad, pad, pw, ph, ph / 2); g.fillStyle = '#ffffff'; g.fill();
  g.restore();
  g.beginPath(); g.roundRect(pad + 0.5, pad + 0.5, pw - 1, ph - 1, ph / 2);
  g.strokeStyle = 'rgba(18, 20, 24, 0.07)'; g.lineWidth = 1; g.stroke();
  g.beginPath(); g.roundRect(pad + 7, pad + 7, 30, 30, 8); g.fillStyle = pageLum < 0.35 ? '#0c1f26' : '#f2f3f6'; g.fill();
  if (logoBmp) g.drawImage(logoBmp, pad + 10, pad + 10, 24, 24);
  g.font = font; g.fillStyle = '#15171c'; g.textBaseline = 'middle';
  g.fillText(TITLE.badge || '', pad + 8 + 30 + 10, pad + ph / 2 + 1);
  return { tx: makeTex(c), cw: pw + 2 * pad, ch: ph + 2 * pad, x: W / 2 - pw / 2 - pad, y: 44 - pad };
})();

const scene = makeTarget();
const accum = makeTarget();

// ---------- drawing ----------
let curJitter = 0;
function setCamera(prog, cam) {
  const l = prog.loc;
  gl.uniform2f(l.uRes, W, H);
  if (l.uFocus) gl.uniform1f(l.uFocus, cam.focus);
  if (l.uFocal) gl.uniform1f(l.uFocal, FOCAL);
  if (l.uJitter) gl.uniform1f(l.uJitter, curJitter);
  if (l.uC) {
    gl.uniform3fv(l.uC, cam.C); gl.uniform3fv(l.uR, cam.R);
    gl.uniform3fv(l.uU, cam.U); gl.uniform3fv(l.uF, cam.F);
  }
}
const depthOf = (cam, p) => (p[0] - cam.C[0]) * cam.F[0] + (p[1] - cam.C[1]) * cam.F[1] + (p[2] - cam.C[2]) * cam.F[2];
// Quad margin (world units) wide enough for the blur to spill past the quad's edge.
function spill(cam, O, AX, AZ) {
  let dmin = Infinity;
  for (const s of [-0.5, 0.5]) for (const t of [-0.5, 0.5]) {
    dmin = Math.min(dmin, depthOf(cam, [O[0] + s * AX[0] + t * AZ[0], O[1] + s * AX[1] + t * AZ[1], O[2] + s * AX[2] + t * AZ[2]]));
  }
  dmin = Math.max(dmin, 10);
  return (blurRadius(dmin, cam.focus) * dmin) / FOCAL + 2;
}
const len = (v) => Math.hypot(v[0], v[1], v[2]);
function drawWorldQuad(prog, O, AX, AZ, margin, uvo = [0, 0], uvs = [1, 1], mz = [margin, margin]) {
  gl.uniform3fv(prog.loc.uO, O); gl.uniform3fv(prog.loc.uAX, AX); gl.uniform3fv(prog.loc.uAZ, AZ);
  const ax = len(AX), az = len(AZ);
  gl.uniform4f(prog.loc.uMargin, margin / ax, margin / ax, mz[0] / az, mz[1] / az);
  gl.uniform2fv(prog.loc.uUVo, uvo);
  gl.uniform2fv(prog.loc.uUVs, uvs);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}
// A page-sized plane drawn as bands down its length; bands wholly behind the lens are skipped so
// no huge triangle straddles the camera plane.
const BANDS = 48;
function drawPlaneBanded(prog, cam, y, PW, PH, mx, mzTop, mzBottom) {
  const bh = PH / BANDS;
  for (let i = 0; i < BANDS; i++) {
    const z0 = i * bh - (i === 0 ? mzTop : 0), z1 = (i + 1) * bh + (i === BANDS - 1 ? mzBottom : 0);
    if (Math.max(depthOf(cam, [PW / 2, y, z0]), depthOf(cam, [PW / 2, y, z1])) < NEAR) continue;
    drawWorldQuad(prog, [PW / 2, y, (i + 0.5) * bh], [PW, 0, 0], [0, 0, bh], mx,
      [0, i / BANDS], [1, 1 / BANDS], [i === 0 ? mzTop : 0, i === BANDS - 1 ? mzBottom : 0]);
  }
}
function bindTex(prog, tex) {
  gl.activeTexture(gl.TEXTURE0);
  gl.bindTexture(gl.TEXTURE_2D, tex.t);
  gl.uniform1i(prog.loc.uTex, 0);
}
// A flat-faced object that stands up by turning about its own middle, top edge toward the lens.
function standingQuad(x, h, z, w, hgt, a) {
  return { O: [x, h, z], AX: [w, 0, 0], AZ: [0, -hgt * Math.sin(a), hgt * Math.cos(a)] };
}
// Shadow: the same picture in a flat color, offset (0.10z, 4 + 0.36z), blurred 7 + 0.5z.
function drawShadow(cam, tex, x, h, z, w, hgt, opacity, style) {
  if (opacity <= 0.001 || h < 1) return;
  const heightFade = 1 - Math.min(1, Math.max(0, (h - 300) / 400));
  if (heightFade <= 0) return;
  const prog = P.shadow;
  gl.useProgram(prog.p);
  setCamera(prog, cam);
  bindTex(prog, tex);
  const blurW = 7 + 0.5 * h;
  const O = [x + 0.1 * h, 0.3, z + 4 + 0.36 * h];
  const AX = [w, 0, 0], AZ = [0, 0, hgt];
  gl.uniform2f(prog.loc.uQuad, w, hgt);
  gl.uniform2f(prog.loc.uTexSize, tex.w, tex.h);
  gl.uniform1f(prog.loc.uBlurW, blurW);
  gl.uniform3fv(prog.loc.uColor, style.color);
  gl.uniform1f(prog.loc.uOpacity, style.opacity * opacity * heightFade);
  drawWorldQuad(prog, O, AX, AZ, blurW + spill(cam, O, AX, AZ));
}
function drawPiece(cam, tex, q, opacity, haze) {
  if (opacity <= 0.001) return;
  const prog = P.piece;
  gl.useProgram(prog.p);
  setCamera(prog, cam);
  bindTex(prog, tex);
  gl.uniform1f(prog.loc.uOpacity, opacity);
  gl.uniform1f(prog.loc.uHaze, haze);
  drawWorldQuad(prog, q.O, q.AX, q.AZ, spill(cam, q.O, q.AX, q.AZ));
}
const insidePage = (ps, x, z) => x > ps.mask[0] && x < ps.mask[2] && z > ps.mask[1] && z < ps.mask[3];

function renderScene(t, jitter) {
  curJitter = jitter;
  const cam = tl.camera(t);
  const ps = tl.pageState(t);
  const PW = meta.page.width, PH = meta.page.height;
  gl.bindFramebuffer(gl.FRAMEBUFFER, scene.fb);
  gl.viewport(0, 0, W, H);
  gl.disable(gl.BLEND);
  gl.useProgram(P.floor.p);
  gl.uniform2f(P.floor.loc.uRes, W, H);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
  gl.enable(gl.BLEND);
  gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA);

  for (const [prog, y, margin] of [[P.pageShadow, -0.5, 320], [P.page, 0, 160]]) {
    gl.useProgram(prog.p);
    setCamera(prog, cam);
    if (prog === P.page) bindTex(prog, pageTex);
    gl.uniform2f(prog.loc.uPage, PW, PH);
    gl.uniform4fv(prog.loc.uMask, ps.mask);
    gl.uniform1f(prog.loc.uRadius, ps.radius);
    gl.uniform1f(prog.loc.uFadeY, ps.fadeY);
    gl.uniform1f(prog.loc.uFade, ps.fade);
    drawPlaneBanded(prog, cam, y, PW, PH, margin, margin, margin);
  }

  // Everything that floats, lowest first (no depth buffer).
  const items = [];
  for (const p of tl.pieces) {
    const s = tl.pieceState(p, t);
    if (s.opacity <= 0.001) continue;
    items.push({ h: s.h, draw: () => {
      drawShadow(cam, pieceTex[p.id], s.x, s.h, s.z, p.qw, p.qh, s.opacity * (1 - s.haze), SHADOW_ON_PAGE);
      if (s.edge > 0.01) {
        // White card edge hanging from the bottom edge of the standing card.
        const n = [0, Math.cos(s.a), Math.sin(s.a)];
        const B = [s.x, s.h - (p.h / 2) * Math.sin(s.a), s.z + (p.h / 2) * Math.cos(s.a)];
        const th = s.edge, k = 64 / 52;
        const O = [B[0] - n[0] * th / 2, B[1] - n[1] * th / 2, B[2] - n[2] * th / 2];
        drawPiece(cam, edgeTex, { O, AX: [p.w * 256 / 244, 0, 0], AZ: [-n[0] * th * k, -n[1] * th * k, -n[2] * th * k] }, s.opacity, s.haze);
      }
      drawPiece(cam, pieceTex[p.id], standingQuad(s.x, s.h, s.z, p.qw, p.qh, s.a), s.opacity, s.haze);
    } });
  }
  for (const tile of tl.tiles(t)) {
    if (tile.opacity <= 0.001) continue;
    const size = tile.s / TILE_INNER;
    items.push({ h: tile.h, draw: () => {
      drawShadow(cam, tileTex, tile.x, tile.h, tile.z, size, size, tile.opacity,
        insidePage(ps, tile.x, tile.z) ? SHADOW_ON_PAGE : SHADOW_ON_FLOOR);
      drawPiece(cam, tileTex, standingQuad(tile.x, tile.h, tile.z, size, size, tile.a), tile.opacity, 0);
    } });
  }
  items.sort((a, b) => a.h - b.h);
  for (const it of items) it.draw();

  // End-card title: no text is laid over the page before the card lands.
  const ov = tl.overlays(t);
  const prog = P.screen;
  gl.useProgram(prog.p);
  setCamera(prog, cam);
  const drawScreen = (tx, cw, ch, x, y, opacity, blur) => {
    if (opacity <= 0.001) return;
    bindTex(prog, tx);
    gl.uniform2f(prog.loc.uCenter, x + cw / 2, y + ch / 2);
    gl.uniform2f(prog.loc.uSize, cw, ch);
    gl.uniform1f(prog.loc.uOpacity, opacity);
    gl.uniform1f(prog.loc.uBlur, blur);
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  };
  if (TITLE.badge) drawScreen(badge.tx, badge.cw, badge.ch, badge.x, badge.y + ov.badge.dy, ov.badge.opacity, 0);
  LINE1.forEach((w, k) => { const a = ov.line1(k); drawScreen(w.tx, w.tx.cw, w.tx.ch, w.x, w.y + a.dy, a.opacity, a.blur); });
  TAIL.forEach((w, k) => { const a = ov.tail(k); drawScreen(w.tx, w.tx.cw, w.tx.ch, w.x, w.y + a.dy, a.opacity, a.blur); });
}

// Render time t: `sub` subframes spread across `shutter` of a frame, averaged for motion blur.
function frame(t, { sub = 16, shutter = 0.7, fps = 60, format = 'png' } = {}) {
  gl.bindFramebuffer(gl.FRAMEBUFFER, accum.fb);
  gl.viewport(0, 0, W, H);
  gl.clearColor(0, 0, 0, 0);
  gl.clear(gl.COLOR_BUFFER_BIT);
  for (let i = 0; i < sub; i++) {
    const ts = sub === 1 ? t : t + ((i + 0.5) / sub - 0.5) * (shutter / fps);
    renderScene(Math.min(DURATION, Math.max(0, ts)), i * 2.39996323);
    gl.bindFramebuffer(gl.FRAMEBUFFER, accum.fb);
    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE);
    gl.useProgram(P.accum.p);
    gl.activeTexture(gl.TEXTURE0);
    gl.bindTexture(gl.TEXTURE_2D, scene.t);
    gl.uniform1i(P.accum.loc.uTex, 0);
    gl.uniform1f(P.accum.loc.uWeight, 1 / sub);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
  }
  gl.disable(gl.BLEND);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  gl.useProgram(P.final.p);
  gl.bindTexture(gl.TEXTURE_2D, accum.t);
  gl.uniform1i(P.final.loc.uTex, 0);
  gl.drawArrays(gl.TRIANGLES, 0, 3);
  if (format === 'none') { gl.finish(); return null; }
  return canvas.toDataURL('image/png');
}

function info() {
  const dbg = gl.getExtension('WEBGL_debug_renderer_info');
  return {
    contract: 'flyover-scene/1',
    renderer: dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER),
    maxTex: gl.getParameter(gl.MAX_TEXTURE_SIZE),
    aniso: ANISO ? gl.getParameter(ANISO.MAX_TEXTURE_MAX_ANISOTROPY_EXT) : 0,
    fonts: [document.fonts.check('500 74px Geist'), document.fonts.check('italic 82px "Instrument Serif"')],
    darkPage: pageLum < 0.35,
    timeline: tl.info,
    check: tl.check(),
  };
}
// Camera distance, tilt and look-at per frame, for converting screen flow into page speed.
function cameraTrack(fps) {
  const rows = [];
  for (let i = 0; i <= Math.round(DURATION * fps); i++) {
    const c = tl.camera(i / fps);
    rows.push({ t: i / fps, d: c.d, th: c.th, tz: c.T[2] });
  }
  return rows;
}

window.DURATION = DURATION;
window.seek = async (t) => { frame(t, { sub: 1, format: 'none' }); };
window.film = { frame, info, cameraTrack, ready: true };

// Optional scrubber for previewing in a browser: ?preview
if (new URLSearchParams(location.search).has('preview')) {
  const ui = document.createElement('input');
  Object.assign(ui, { type: 'range', min: 0, max: DURATION, step: 1 / 60, value: 0 });
  ui.style.cssText = 'position:fixed;left:16px;right:16px;bottom:12px;width:calc(100% - 32px)';
  ui.oninput = () => frame(+ui.value, { sub: 1, format: 'none' });
  document.body.append(ui);
  frame(0, { sub: 1, format: 'none' });
}
