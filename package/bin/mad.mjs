#!/usr/bin/env node
// mad: set up the MAD workflow (Multi-Agent Development) in a project.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HELP = `mad: set up the MAD workflow (Multi-Agent Development) in a project.

  mad init [folder]     set up MAD in a folder (default: current folder)
  mad update [folder]   update MAD's own files in a project, keep everything else
  mad clean [--dry-run] remove finished task worktrees and branches in this project
  mad models            list installed agents and the models each offers
  mad version           show the installed MAD version`;

const here = path.dirname(fileURLToPath(import.meta.url));
const pkgDir = path.resolve(here, "..");
// Installed package: kit/ sits inside the package. Source repo: kit/ sits next to package/.
const kit = [path.join(pkgDir, "kit"), path.resolve(pkgDir, "..", "kit")].find((d) =>
  fs.existsSync(path.join(d, "skill", "SKILL.md")));
const version = JSON.parse(fs.readFileSync(path.join(pkgDir, "package.json"), "utf8")).version;

const die = (msg) => { console.error(`mad: ${msg}`); process.exit(1); };
const git = (cwd, ...args) => spawnSync("git", ["-C", cwd, ...args], { encoding: "utf8" });
const exists = (...p) => fs.existsSync(path.join(...p));
const skipJunk = (src) => path.basename(src) !== ".DS_Store";

if (!kit) die("MAD's kit folder is missing from this installation; reinstall mad-workflow");

function isSourceRepo(dir) {
  return exists(dir, "kit", "skill", "SKILL.md") && exists(dir, "package", "bin", "mad.mjs");
}

// Copy MAD's own files into a project. Never touches project files.
function installInto(target) {
  // The skill, for every agent: .claude/skills (Claude Code, OpenCode), .agents/skills (Codex).
  for (const dir of [".claude/skills/mad", ".agents/skills/mad"]) {
    const dest = path.join(target, dir);
    fs.rmSync(dest, { recursive: true, force: true });
    fs.cpSync(path.join(kit, "skill"), dest, { recursive: true, filter: skipJunk });
  }
  const kitDest = path.join(target, "mad", "kit");
  fs.rmSync(kitDest, { recursive: true, force: true });
  fs.cpSync(path.join(kit, "templates"), path.join(kitDest, "templates"), { recursive: true, filter: skipJunk });
  fs.cpSync(path.join(kit, "bin"), path.join(kitDest, "bin"), { recursive: true, filter: skipJunk });
  fs.writeFileSync(path.join(kitDest, "VERSION"), version + "\n");

  // Roles: only if missing, so project changes survive updates.
  const roles = path.join(target, "mad", "roles");
  fs.mkdirSync(roles, { recursive: true });
  for (const f of fs.readdirSync(path.join(kit, "roles"))) {
    if (!exists(roles, f)) fs.copyFileSync(path.join(kit, "roles", f), path.join(roles, f));
  }
}

function init(folder = ".") {
  const target = path.resolve(folder);
  fs.mkdirSync(target, { recursive: true });
  if (isSourceRepo(target)) die("this is the MAD source repo; run 'mad init' in a project folder");

  if (git(target, "rev-parse", "--git-dir").status !== 0) {
    if (git(target, "init", "-q").status !== 0) die("git is required; install it from https://git-scm.com");
    console.log("created  git repository");
  }

  installInto(target);
  console.log("added    .claude/skills/mad, .agents/skills/mad, mad/kit, mad/roles");

  const config = path.join(target, "mad", "config", "mad.yaml");
  if (!fs.existsSync(config)) {
    fs.mkdirSync(path.dirname(config), { recursive: true });
    fs.copyFileSync(path.join(kit, "templates", "config", "mad.yaml"), config);
    console.log("added    mad/config/mad.yaml");
  }

  // Keep secrets out of git, in the project's own .gitignore so it holds for anyone who clones it.
  const gi = path.join(target, ".gitignore");
  const giText = fs.existsSync(gi) ? fs.readFileSync(gi, "utf8") : "";
  if (!giText.split(/\r?\n/).includes(".env")) {
    const sep = giText && !giText.endsWith("\n") ? "\n\n" : giText ? "\n" : "";
    fs.appendFileSync(gi, `${sep}# Secrets (added by mad init)\n.env\n.env.*\n!.env.example\n`);
    console.log("updated  .gitignore (secrets)");
  }

  // A short pointer for agents that read AGENTS.md but have no skills.
  const agents = path.join(target, "AGENTS.md");
  const agentsText = fs.existsSync(agents) ? fs.readFileSync(agents, "utf8") : "";
  if (!agentsText.includes("<!-- mad:start -->")) {
    fs.appendFileSync(agents, `${agentsText.trim() ? "\n" : ""}<!-- mad:start -->
## MAD workflow
This project uses MAD, the Multi-Agent Development workflow.
When asked to run MAD (\`/mad\`, \`$mad\`, "start MAD"), follow \`.agents/skills/mad/SKILL.md\`.
MAD's files live in \`mad/\`. The software lives in the app folder set in \`mad/config/mad.yaml\`.
<!-- mad:end -->
`);
    console.log("updated  AGENTS.md (MAD pointer)");
  }

  console.log(`
MAD ${version} is set up in ${target}

Start it inside Orca with:
  Claude Code:  /mad
  Codex:        $mad   (or ask: "start MAD")
  OpenCode:     ask: "start MAD"`);
}

function update(folder = ".") {
  const target = path.resolve(folder);
  if (!exists(target, "mad")) die(`no MAD project in ${target} (run 'mad init' first)`);
  const versionFile = path.join(target, "mad", "kit", "VERSION");
  const old = fs.existsSync(versionFile) ? fs.readFileSync(versionFile, "utf8").trim() : "none";
  installInto(target);
  console.log(`MAD updated in ${target}: ${old} -> ${version}`);
  console.log("Kept: your config, spec, stack, rules, playbooks, tasks, roles and run state.");
}

function runKitScript(name, args, { inProject }) {
  let script = path.join(kit, "bin", name);
  let cwd = process.cwd();
  if (inProject) {
    const root = spawnSync("git", ["rev-parse", "--show-toplevel"], { encoding: "utf8" }).stdout.trim();
    if (!root) die("not inside a git repository");
    script = path.join(root, "mad", "kit", "bin", name);
    if (!fs.existsSync(script)) die("this project has no MAD kit (run 'mad init' or 'mad update' first)");
    cwd = root;
  }
  const r = spawnSync(process.execPath, [script, ...args], { stdio: "inherit", cwd });
  process.exit(r.status ?? 1);
}

const [cmd = "help", ...rest] = process.argv.slice(2);
switch (cmd) {
  case "init": init(rest[0]); break;
  case "update": update(rest[0]); break;
  case "clean": runKitScript("cleanup.mjs", rest, { inProject: true }); break;
  case "models": runKitScript("models.mjs", [], { inProject: false }); break;
  case "version": case "-v": case "--version": console.log(version); break;
  case "help": case "-h": case "--help": console.log(HELP); break;
  default: die(`unknown command '${cmd}' (try: mad help)`);
}
