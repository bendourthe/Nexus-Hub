const fs = require("node:fs");
const path = require("node:path");
const svgpath = require("svgpath");
const svg2ttf = require("svg2ttf");

const root = path.join(__dirname, "..");
const svg = fs.readFileSync(path.join(root, "icons", "cursor.svg"), "utf8");
const match = svg.match(/<path[^>]*d="([^"]+)"/u);
if (!match) throw new Error("Expected one normalized path in icons/cursor.svg");

// Derive the scale from the source viewBox instead of hardcoding it. The scale
// was previously fixed at 51.2 (1024/20), which silently mis-scales any artwork
// authored on a different grid -- swapping in a 24-unit icon would have rendered
// it at 120% and clipped, with no error to explain why.
const viewBox = svg.match(/viewBox="0 0 (\d+(?:\.\d+)?) (\d+(?:\.\d+)?)"/u);
if (!viewBox) throw new Error("Expected a `viewBox=\"0 0 W H\"` on icons/cursor.svg");
const [width, height] = [Number(viewBox[1]), Number(viewBox[2])];
if (width !== height) throw new Error(`Expected a square viewBox, got ${width}x${height}`);
const unitsPerEm = 1024;
const scale = unitsPerEm / width;

const glyph = svgpath(match[1]).scale(scale, -scale).translate(0, unitsPerEm).round(1).toString();
const font = `<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><defs><font id="cursor-icons" horiz-adv-x="1024"><font-face font-family="cursor-icons" units-per-em="1024" ascent="1024" descent="0"/><missing-glyph horiz-adv-x="1024"/><glyph unicode="&#xE103;" glyph-name="cursor" horiz-adv-x="1024" d="${glyph}"/></font></defs></svg>`;
const ttf = Buffer.from(svg2ttf(font, {}).buffer);
let convert = require("ttf2woff2");
if (typeof convert !== "function") convert = convert.default;

const fonts = path.join(root, "fonts");
fs.mkdirSync(fonts, { recursive: true });
fs.writeFileSync(path.join(fonts, "cursor-icons.woff2"), convert(ttf));
console.log("Generated fonts/cursor-icons.woff2 at U+E103");
