/**
 * Generates the WOFF2 icon font that puts the Nexus-Hub mark in the status bar.
 *
 * VS Code draws a contributed icon from a font glyph, never from an SVG file, so the
 * one-color mark in icons/nexus-hub.svg is converted once and the font is committed.
 * Rerun this script only when that SVG changes: `node scripts/generate-icon-font.js`.
 *
 * A font glyph has its origin at the baseline and Y pointing up, while SVG has its
 * origin at the top-left and Y pointing down. The path is therefore moved to the
 * viewBox origin, scaled to 1024 units per em, and flipped. The mark is one path whose
 * shapes all wind the same way, so overlaps fill instead of cutting holes.
 */
const fs = require("fs");
const path = require("path");
const svgpath = require("svgpath");
const svg2ttf = require("svg2ttf");

const ROOT = path.join(__dirname, "..");
const SVG_FILE = path.join(ROOT, "icons", "nexus-hub.svg");
const FONTS_DIR = path.join(ROOT, "fonts");
const UNITS_PER_EM = 1024;
const CODEPOINT = 0xe201;

const svg = fs.readFileSync(SVG_FILE, "utf-8");
const box = svg.match(/viewBox="([-\d.]+) ([-\d.]+) ([\d.]+) ([\d.]+)"/);
const d = svg.match(/ d="([^"]+)"/);
if (!box || !d || box[3] !== box[4]) {
  console.error("icons/nexus-hub.svg needs a square viewBox and exactly one path");
  process.exit(1);
}
const [minX, minY, size] = box.slice(1, 4).map(Number);
const scale = UNITS_PER_EM / size;

const glyph = svgpath(d[1])
  .translate(-minX, -minY)
  .scale(scale, -scale)
  .translate(0, UNITS_PER_EM)
  .round(1)
  .toString();

const svgFont = [
  '<?xml version="1.0" standalone="no"?>',
  '<svg xmlns="http://www.w3.org/2000/svg"><defs>',
  `<font id="nexus-hub-icons" horiz-adv-x="${UNITS_PER_EM}">`,
  `<font-face font-family="nexus-hub-icons" units-per-em="${UNITS_PER_EM}" ascent="${UNITS_PER_EM}" descent="0" />`,
  `<missing-glyph horiz-adv-x="${UNITS_PER_EM}" />`,
  `<glyph unicode="&#x${CODEPOINT.toString(16).toUpperCase()};" glyph-name="nexus-hub" horiz-adv-x="${UNITS_PER_EM}" d="${glyph}" />`,
  "</font></defs></svg>",
].join("\n");

let ttf2woff2 = require("ttf2woff2");
if (typeof ttf2woff2 !== "function") {
  ttf2woff2 = ttf2woff2.default;
}
const ttf = Buffer.from(svg2ttf(svgFont, {}).buffer);
fs.mkdirSync(FONTS_DIR, { recursive: true });
fs.writeFileSync(path.join(FONTS_DIR, "nexus-hub-icons.woff2"), ttf2woff2(ttf));
console.log(`Generated fonts/nexus-hub-icons.woff2 (glyph U+${CODEPOINT.toString(16).toUpperCase()})`);
