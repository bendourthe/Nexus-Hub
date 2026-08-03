const path = require("path");
const sharp = require("sharp");

const fs = require("fs");
const root = path.join(__dirname, "..");
const source = fs.readFileSync(path.join(root, "icons", "github.svg"), "utf8");
const gradient = source
  .replace("<path", "<defs><linearGradient id=\"brand\" x1=\"2\" y1=\"18\" x2=\"18\" y2=\"2\" gradientUnits=\"userSpaceOnUse\"><stop stop-color=\"#2456F5\"/><stop offset=\"0.52\" stop-color=\"#651DA8\"/><stop offset=\"1\" stop-color=\"#A21CAF\"/></linearGradient></defs><path")
  .replace('fill="currentColor"', 'fill="url(#brand)"');
sharp(Buffer.from(gradient), { density: 384 })
  .resize(256, 256, { fit: "contain" })
  .png({ compressionLevel: 9, adaptiveFiltering: false, palette: false })
  .toFile(path.join(root, "icon.png"))
  .then(() => console.log("Generated transparent 256x256 icon.png from vector geometry"));
