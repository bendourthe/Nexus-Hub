/**
 * Renders the full-color Antigravity logo (icons/google-antigravity.svg) into the
 * transparent 512x512 icon.png that the extension manifest references.
 *
 * sharp is used only on demand and is deliberately kept out of package.json:
 *   npm install --no-save --package-lock=false sharp && node scripts/generate-package-icon.js
 */
const fs = require("node:fs");
const path = require("node:path");
const sharp = require("sharp");

const root = path.join(__dirname, "..");
const SOURCE = path.join(root, "icons", "google-antigravity.svg");
const SIZE = 512;
// The logo is 16x15 user units; a high density keeps the blurred color fields
// smooth before the downscale to the final size.
const DENSITY = 2400;

async function main() {
  const svg = fs.readFileSync(SOURCE);
  await sharp(svg, { density: DENSITY })
    .resize(SIZE, SIZE, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } })
    .ensureAlpha()
    .png({ compressionLevel: 9 })
    .toFile(path.join(root, "icon.png"));
  console.log(`Generated transparent ${SIZE}x${SIZE} icon.png from icons/google-antigravity.svg`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
