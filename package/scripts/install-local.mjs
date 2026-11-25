// Installs this package globally from the local source, as a real copy (not a link),
// so `mad` keeps working even if this folder moves. Use it before the package is published.
// Usage: npm run install-local
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const pkgDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const npm = process.platform === "win32" ? "npm.cmd" : "npm";
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "mad-pack-"));
const opts = { cwd: pkgDir, encoding: "utf8", shell: process.platform === "win32" };

const tarball = execFileSync(npm, ["pack", "--pack-destination", tmp, "--silent"], opts).trim().split(/\r?\n/).pop();
execFileSync(npm, ["install", "-g", path.join(tmp, tarball)], { ...opts, stdio: "inherit" });
fs.rmSync(tmp, { recursive: true, force: true });
console.log("\nInstalled. Try: mad help");
