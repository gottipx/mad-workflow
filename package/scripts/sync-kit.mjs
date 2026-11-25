// Copies the repo's kit/ into the package, so the published package is self-contained.
// Runs automatically before `npm pack` and `npm publish`.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const pkgDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const src = path.resolve(pkgDir, "..", "kit");
const dest = path.join(pkgDir, "kit");

if (!fs.existsSync(path.join(src, "skill", "SKILL.md"))) {
  console.error(`sync-kit: no kit found at ${src}`);
  process.exit(1);
}
fs.rmSync(dest, { recursive: true, force: true });
fs.cpSync(src, dest, { recursive: true, filter: (p) => path.basename(p) !== ".DS_Store" });
console.log(`sync-kit: copied ${src} -> ${dest}`);

// The license lives at the repo root; npm needs a copy inside the package.
fs.copyFileSync(path.resolve(pkgDir, "..", "LICENSE"), path.join(pkgDir, "LICENSE"));
