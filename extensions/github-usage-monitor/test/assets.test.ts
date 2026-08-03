import { readFileSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const root = resolve(__dirname, "..");
describe("brand assets", () => {
  it("ships one normalized 20x20 status path without wrapper groups or external references", () => {
    const svg = readFileSync(resolve(root, "icons/github.svg"), "utf8");
    expect(svg).toContain('viewBox="0 0 20 20"'); expect(svg.match(/<path\b/gu)).toHaveLength(1);
    expect(svg).not.toMatch(/<g\b|<script\b|<image\b|(?:href|src)="https?:/u);
    expect(svg).not.toContain("transform=");
  });
  it("ships the generated WOFF2 glyph and preserves the supplied gradient raster", () => {
    expect(statSync(resolve(root, "fonts/github-icons.woff2")).size).toBeGreaterThan(100);
    const png = readFileSync(resolve(root, "icons/github-gradient.png"));
    expect(png.readUInt32BE(16)).toBe(14); expect(png.readUInt32BE(20)).toBe(14);
  });
  it("ships a transparent 256x256 package PNG and registers all assets", () => {
    const png = readFileSync(resolve(root, "icon.png"));
    expect(png.readUInt32BE(16)).toBe(256); expect(png.readUInt32BE(20)).toBe(256); expect(png[25]).toBe(6);
    const manifest = JSON.parse(readFileSync(resolve(root, "package.json"), "utf8"));
    expect(manifest.icon).toBe("icon.png"); expect(manifest.contributes.icons["github-icon"].default.fontCharacter).toBe("\\E102");
    expect(manifest.contributes.views.githubUsageWarning[0].when).toBe("githubUsage.warningActive");
  });
});
