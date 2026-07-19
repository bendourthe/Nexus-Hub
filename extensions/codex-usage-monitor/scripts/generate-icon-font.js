/**
 * Generates a WOFF2 icon font from the Codex SVG icon.
 *
 * SVG fonts use an inverted Y-axis compared to regular SVGs:
 *   - Regular SVG: origin at top-left, Y increases downward
 *   - Font glyphs: origin at baseline (bottom-left), Y increases upward
 *
 * This script transforms the 16x16 SVG path to 1024 unitsPerEm font space
 * by scaling 64x and flipping the Y-axis.
 */
const fs = require("fs");
const path = require("path");
const svgpath = require("svgpath");
const svg2ttf = require("svg2ttf");

const ICONS_DIR = path.join(__dirname, "..", "icons");
const FONTS_DIR = path.join(__dirname, "..", "fonts");
const SVG_FILE = path.join(ICONS_DIR, "codex.svg");
const UNITS_PER_EM = 1024;
const SVG_SIZE = 16;
const SCALE = UNITS_PER_EM / SVG_SIZE; // 64
const CODEPOINT = 0xe101; // 57601

// Read SVG and extract path data
const svgContent = fs.readFileSync(SVG_FILE, "utf-8");
const pathMatch = svgContent.match(/d="([^"]+)"/);
if (!pathMatch) {
  console.error("Could not extract path data from SVG");
  process.exit(1);
}

// Transform path: scale to font units and flip Y-axis
const fontPath = svgpath(pathMatch[1])
  .scale(SCALE, -SCALE)
  .translate(0, UNITS_PER_EM)
  .round(1)
  .toString();

// Build SVG font XML
const svgFont = [
  '<?xml version="1.0" standalone="no"?>',
  '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">',
  '<svg xmlns="http://www.w3.org/2000/svg">',
  "<defs>",
  `<font id="codex-icons" horiz-adv-x="${UNITS_PER_EM}">`,
  `<font-face font-family="codex-icons" units-per-em="${UNITS_PER_EM}" ascent="${UNITS_PER_EM}" descent="0" />`,
  `<missing-glyph horiz-adv-x="${UNITS_PER_EM}" />`,
  `<glyph unicode="&#x${CODEPOINT.toString(16).toUpperCase()};" glyph-name="codex" horiz-adv-x="${UNITS_PER_EM}" d="${fontPath}" />`,
  "</font>",
  "</defs>",
  "</svg>",
].join("\n");

// Convert SVG font -> TTF
const ttfResult = svg2ttf(svgFont, {});
const ttfBuffer = Buffer.from(ttfResult.buffer);

// Convert TTF -> WOFF2
let ttf2woff2 = require("ttf2woff2");
if (typeof ttf2woff2 !== "function") {
  ttf2woff2 = ttf2woff2.default;
}
const woff2Buffer = ttf2woff2(ttfBuffer);

// Write outputs
if (!fs.existsSync(FONTS_DIR)) {
  fs.mkdirSync(FONTS_DIR, { recursive: true });
}
fs.writeFileSync(path.join(FONTS_DIR, "codex-icons.woff2"), woff2Buffer);
fs.writeFileSync(path.join(FONTS_DIR, "codex-icons.ttf"), ttfBuffer);

console.log("Generated fonts/codex-icons.woff2 and fonts/codex-icons.ttf");
console.log(`Glyph codepoint: U+${CODEPOINT.toString(16).toUpperCase()} (${CODEPOINT})`);
