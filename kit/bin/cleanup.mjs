#!/usr/bin/env node
// Removes finished task worktrees and their branches.
// Usage: node mad/kit/bin/cleanup.mjs [TASK-ID ...] [--dry-run]
//   Without IDs: every task worktree whose branch is merged into the run branch.
//
// Safe by design. A worktree is removed only if all of these hold:
//   - its branch ends in the ID of a task card in mad/tasks/ (never other worktrees)
//   - its branch is fully merged into the run branch
//   - it has no uncommitted changes
// Everything else is kept and reported.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const isWin = process.platform === "win32";
const run = (cmd, args, opts = {}) =>
  spawnSync(cmd, args, { encoding: "utf8", shell: isWin && cmd !== "git", ...opts });
const git = (...args) => run("git", args);
const die = (msg) => { console.error(msg); process.exit(1); };

const args = process.argv.slice(2);
const dry = args.includes("--dry-run");
const ids = args.filter((a) => a !== "--dry-run");

const root = git("rev-parse", "--show-toplevel").stdout.trim() || die("Not inside a git repository");
const mad = path.join(root, "mad");
const runFile = path.join(mad, "RUN.md");
const runBranch = fs.existsSync(runFile)
  ? ((fs.readFileSync(runFile, "utf8").match(/^Run branch:\s*(.+)$/m) || [])[1] || "").trim()
  : "";
if (!runBranch) die("No run branch in mad/RUN.md");
if (git("rev-parse", "--verify", "-q", runBranch).status !== 0) die(`Run branch not found: ${runBranch}`);

// Task cards live in mad/tasks/; projects from older MAD versions used tasks/.
const tasksDir = fs.existsSync(path.join(mad, "tasks")) ? path.join(mad, "tasks") : path.join(root, "tasks");
const wanted = (id) => fs.existsSync(path.join(tasksDir, `${id}.md`)) && (ids.length === 0 || ids.includes(id));

const worktrees = [];
let current = null;
for (const line of git("worktree", "list", "--porcelain").stdout.split(/\r?\n/)) {
  if (line.startsWith("worktree ")) current = { path: line.slice(9) };
  else if (line.startsWith("branch ") && current) {
    current.branch = line.slice(7).replace(/^refs\/heads\//, "");
    worktrees.push(current);
  }
}

const hasOrca = run("orca", ["--help"]).status === 0;
let removed = 0, kept = 0;
for (const wt of worktrees) {
  if (wt.branch === runBranch) continue;
  const id = wt.branch.split("/").pop();
  if (!wanted(id)) continue;

  if (git("merge-base", "--is-ancestor", wt.branch, runBranch).status !== 0) {
    console.log(`kept     ${id}: not merged into ${runBranch} yet`); kept++; continue;
  }
  if (run("git", ["-C", wt.path, "status", "--porcelain"]).stdout.trim()) {
    console.log(`kept     ${id}: has uncommitted changes in ${wt.path}`); kept++; continue;
  }
  if (dry) { console.log(`would remove ${id} (${wt.branch})`); removed++; continue; }

  const viaOrca = hasOrca &&
    run("orca", ["worktree", "rm", "--worktree", `path:${wt.path}`, "--delete-branch", "--json"]).status === 0;
  if (!viaOrca) git("worktree", "remove", wt.path);
  git("branch", "-d", wt.branch); // safe delete: only merged branches; fine if already gone
  console.log(`removed  ${id} (${wt.branch})`); removed++;
}

git("worktree", "prune");
console.log(dry ? `Dry run: ${removed} would be removed, ${kept} kept.` : `Done: ${removed} removed, ${kept} kept.`);
