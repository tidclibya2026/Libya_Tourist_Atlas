import sharp from "sharp";
import { mkdir } from "node:fs/promises";
import { join, resolve } from "node:path";

const root = resolve(process.cwd(), "../..");
const entries = [
  ["assets/media/LIBYA/Sabratha/published/main-site/sabratha-main-aerial-001.JPG", "sabratha.webp"],
  ["assets/media/LIBYA/heritage/cyrene/published/main-site/cyrene-main-aerial-001.JPG", "cyrene.webp"],
  ["assets/images/old-tripoli/old-tripoli-LY-OLD-TRIPOLI-00123-02.png", "old-tripoli.webp"],
];
const target = join(root, "apps/portal/public/media/hero");
await mkdir(target, { recursive: true });
for (const [source, name] of entries) {
  const output = join(target, name);
  const result = await sharp(join(root, source))
    .rotate()
    .resize({ width: 1920, height: 1080, fit: "cover", withoutEnlargement: true })
    .webp({ quality: 80, effort: 5 })
    .toFile(output);
  console.log(`${name}: ${(result.size / 1024).toFixed(0)} KiB`);
}
