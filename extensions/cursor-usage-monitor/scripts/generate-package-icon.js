const crypto = require("node:crypto");
const fs = require("node:fs");
const path = require("node:path");
const sharp = require("sharp");

const root = path.join(__dirname, "..");
const sourcePath = path.join(root, "icons", "cursor-ai-480.png");
const source = fs.readFileSync(sourcePath);
const expectedHash = "5706468f30fc4bc45c96f8909b94fa110cc5014d4ddb7e1a3f360d51f75cf459";
const actualHash = crypto.createHash("sha256").update(source).digest("hex");

if (actualHash !== expectedHash) {
  throw new Error(`Source artwork hash mismatch: expected ${expectedHash}, received ${actualHash}`);
}

async function main() {
  const metadata = await sharp(source).metadata();
  if (metadata.width !== 480 || metadata.height !== 480 || !metadata.hasAlpha) {
    throw new Error("Expected a transparent 480x480 source PNG");
  }

  await sharp(source)
    .resize(256, 256, { fit: "contain", withoutEnlargement: true })
    .ensureAlpha()
    .png({ compressionLevel: 9, adaptiveFiltering: false, palette: false })
    .toFile(path.join(root, "icon.png"));

  console.log("Generated transparent 256x256 icon.png from icons/cursor-ai-480.png");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
