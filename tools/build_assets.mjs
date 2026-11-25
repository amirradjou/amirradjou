// Builds the images for README.md, in the same cyanotype style as amirradjou.com.
//
// It reuses the site's work, so the profile and the site never drift apart:
//   - the project prints and their brushed edges from ../amirradjou-site/public/prints
//     (made there by `pnpm prints`), with the edge baked in, since GitHub can't apply CSS masks;
//   - sharp and the Archivo font from ../amirradjou-site/node_modules.
// The banner (tools/banner.html) is rendered with headless Chromium.
//
//   node tools/build_assets.mjs
import { execFileSync } from "node:child_process";
import { mkdir, readFile, rm } from "node:fs/promises";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const site = join(root, "..", "amirradjou-site");
const sharp = createRequire(join(site, "package.json"))("sharp");
const prints = join(site, "public", "prints");
const out = join(root, "assets");

// Same order as README.md; the edge cycles so neighbours differ.
const PROJECTS = [
  "go-orbitdb",
  "cnsim",
  "leash",
  "pennywatch",
  "llm-honeypot",
  "exitcheck",
  "poker-table",
  "overhead",
  "chess-coach",
];

// The print's pixels with the brushed edge as its alpha channel.
async function withEdge(input, edge, width, height) {
  const mask = await sharp(await readFile(join(prints, `edge-${edge}.svg`)))
    .resize(width, height, { fit: "fill" })
    .extractChannel("alpha")
    .raw()
    .toBuffer();
  const rgb = await sharp(input).resize(width, height).removeAlpha().raw().toBuffer();
  const rgba = Buffer.alloc(width * height * 4);
  for (let i = 0; i < width * height; i++) {
    rgba[i * 4] = rgb[i * 3];
    rgba[i * 4 + 1] = rgb[i * 3 + 1];
    rgba[i * 4 + 2] = rgb[i * 3 + 2];
    rgba[i * 4 + 3] = mask[i];
  }
  return sharp(rgba, { raw: { width, height, channels: 4 } });
}

await rm(join(out, "cards"), { recursive: true, force: true });
await mkdir(join(out, "prints"), { recursive: true });

for (const [i, id] of PROJECTS.entries()) {
  const img = await withEdge(join(prints, `${id}-1200.webp`), (i % 3) + 1, 900, 600);
  await img.webp({ quality: 80, alphaQuality: 90, effort: 6 }).toFile(join(out, "prints", `${id}.webp`));
  console.log(`print ${id}`);
}

const shot = join(out, "banner-raw.png");
execFileSync("chromium-browser", [
  "--headless=new",
  `--user-data-dir=${join(root, ".cache", "chromium")}`,
  "--disable-gpu",
  "--hide-scrollbars",
  "--allow-file-access-from-files",
  "--window-size=1600,520",
  `--screenshot=${shot}`,
  `file://${join(root, "tools", "banner.html")}`,
]);
const banner = await withEdge(shot, 2, 1600, 520);
await banner.png({ compressionLevel: 9, palette: false }).toFile(join(out, "banner.png"));
await rm(shot);
console.log("banner");
