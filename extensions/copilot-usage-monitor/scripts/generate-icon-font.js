/**
 * Generates fonts/copilot-icons.woff2 (the status-bar glyph) from icons/copilot.svg.
 *
 * Ported from the Cursor monitor's generator. The Copilot artwork differs from
 * the Cursor and Codex icons in three ways this script has to handle:
 *
 *   - Its view box is not square (512 x 416), so the artwork is scaled by its
 *     longer side and centered on the 1024-unit em square rather than stretched.
 *   - It has several <path> elements, which are merged into one glyph.
 *   - It declares fill-rule="evenodd", while TrueType glyphs always fill with the
 *     nonzero rule. The script checks, contour by contour, that both rules fill
 *     the same regions and refuses to write a font when they would not (a hole
 *     that would render filled).
 *
 * SVG fonts use an inverted Y axis (origin at the baseline, Y up), so the path
 * is flipped after scaling.
 */
const fs = require("node:fs");
const path = require("node:path");
const svgpath = require("svgpath");
const svg2ttf = require("svg2ttf");

const root = path.join(__dirname, "..");
const SOURCE = path.join(root, "icons", "copilot.svg");
const UNITS_PER_EM = 1024;
const CODEPOINT = 0xe104;

const svg = fs.readFileSync(SOURCE, "utf8");
const viewBox = svg.match(/viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"/u);
if (!viewBox) throw new Error('Expected a viewBox="0 0 W H" on icons/copilot.svg');
const [width, height] = [Number(viewBox[1]), Number(viewBox[2])];
const paths = [...svg.matchAll(/<path[^>]*\sd="([^"]+)"/gu)].map((m) => m[1]);
if (paths.length === 0) throw new Error("Expected at least one <path d=...> in icons/copilot.svg");

/** Every subpath as a polygon of its endpoints and control points (enough for area sign and containment). */
function contours(d) {
  const out = [];
  let current = null;
  svgpath(d).abs().unarc().unshort().iterate((seg, _index, x, y) => {
    const command = seg[0];
    if (command === "M") {
      current = [[seg[1], seg[2]]];
      out.push(current);
      return;
    }
    if (command === "Z" || current === null) return;
    if (command === "H") { current.push([seg[1], y]); return; }
    if (command === "V") { current.push([x, seg[1]]); return; }
    for (let k = 1; k + 1 < seg.length; k += 2) current.push([seg[k], seg[k + 1]]);
  });
  return out;
}

function signedArea(poly) {
  let area = 0;
  for (let i = 0; i < poly.length; i++) {
    const [x1, y1] = poly[i];
    const [x2, y2] = poly[(i + 1) % poly.length];
    area += x1 * y2 - x2 * y1;
  }
  return area / 2;
}

function contains(poly, [px, py]) {
  let inside = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if ((yi > py) !== (yj > py) && px < ((xj - xi) * (py - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

// For the region just inside each contour, evenodd fills when the number of
// enclosing contours is odd and nonzero fills when their signed directions do
// not cancel. The glyph is only faithful when the two agree everywhere.
const all = paths.flatMap(contours);
all.forEach((poly, i) => {
  const area = signedArea(poly);
  const enclosing = all.filter(
    (other, j) => j !== i && Math.abs(signedArea(other)) > Math.abs(area) && contains(other, poly[0]),
  );
  const winding = [poly, ...enclosing].reduce((sum, p) => sum + Math.sign(signedArea(p)), 0);
  const evenOddFills = (enclosing.length + 1) % 2 === 1;
  if ((winding !== 0) !== evenOddFills) {
    throw new Error(`Contour ${i} would render differently under the nonzero fill rule; reverse its direction in the source`);
  }
});

const size = Math.max(width, height);
const scale = UNITS_PER_EM / size;
const glyph = svgpath(paths.join(" "))
  .translate((size - width) / 2, (size - height) / 2)
  .scale(scale, -scale)
  .translate(0, UNITS_PER_EM)
  .round(1)
  .toString();

const hex = CODEPOINT.toString(16).toUpperCase();
const font =
  `<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><defs>` +
  `<font id="copilot-icons" horiz-adv-x="${UNITS_PER_EM}">` +
  `<font-face font-family="copilot-icons" units-per-em="${UNITS_PER_EM}" ascent="${UNITS_PER_EM}" descent="0"/>` +
  `<missing-glyph horiz-adv-x="${UNITS_PER_EM}"/>` +
  `<glyph unicode="&#x${hex};" glyph-name="copilot" horiz-adv-x="${UNITS_PER_EM}" d="${glyph}"/>` +
  `</font></defs></svg>`;
const ttf = Buffer.from(svg2ttf(font, {}).buffer);
let convert = require("ttf2woff2");
if (typeof convert !== "function") convert = convert.default;

const fonts = path.join(root, "fonts");
fs.mkdirSync(fonts, { recursive: true });
fs.writeFileSync(path.join(fonts, "copilot-icons.woff2"), convert(ttf));
console.log(`Generated fonts/copilot-icons.woff2 at U+${hex} from ${paths.length} paths (${all.length} contours)`);
