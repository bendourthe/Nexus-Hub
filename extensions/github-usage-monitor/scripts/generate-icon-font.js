const fs = require("fs");
const path = require("path");
const svgpath = require("svgpath");
const svg2ttf = require("svg2ttf");

const root = path.join(__dirname, "..");
const svg = fs.readFileSync(path.join(root, "icons", "github.svg"), "utf8");
const match = svg.match(/<path[^>]*d="([^"]+)"/u);
if (!match) throw new Error("Expected one normalized path in icons/github.svg");
const glyph = svgpath(match[1]).scale(51.2, -51.2).translate(0, 1024).round(1).toString();
const font = `<?xml version="1.0"?><svg xmlns="http://www.w3.org/2000/svg"><defs><font id="github-icons" horiz-adv-x="1024"><font-face font-family="github-icons" units-per-em="1024" ascent="1024" descent="0"/><missing-glyph horiz-adv-x="1024"/><glyph unicode="&#xE102;" glyph-name="github" horiz-adv-x="1024" d="${glyph}"/></font></defs></svg>`;
const ttf = Buffer.from(svg2ttf(font, {}).buffer);
let convert = require("ttf2woff2");
if (typeof convert !== "function") convert = convert.default;
const fonts = path.join(root, "fonts");
fs.mkdirSync(fonts, { recursive: true });
fs.writeFileSync(path.join(fonts, "github-icons.woff2"), convert(ttf));
console.log("Generated fonts/github-icons.woff2 at U+E102");
