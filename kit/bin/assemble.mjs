#!/usr/bin/env node
// Builds the message a worker receives: role + rules + playbooks + task card.
// Usage: node mad/kit/bin/assemble.mjs <TASK-ID> [role]
//   role defaults to the card's own role; pass "reviewer" for a review.
// Writes mad/dispatch/<TASK-ID>.md (or <TASK-ID>.review.md) and prints its path.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

const die = (msg) => { console.error(msg); process.exit(1); };
const [id, roleArg] = process.argv.slice(2);
if (!id) die("Usage: node mad/kit/bin/assemble.mjs <TASK-ID> [role]");

const root = execFileSync("git", ["rev-parse", "--show-toplevel"], { encoding: "utf8" }).trim();
const mad = path.join(root, "mad");
const card = path.join(mad, "tasks", `${id}.md`);
if (!fs.existsSync(card)) die(`No task card: mad/tasks/${id}.md`);
const cardText = fs.readFileSync(card, "utf8");

// Read fields from the card's YAML frontmatter.
const front = {};
const lines = cardText.split(/\r?\n/);
if (lines[0] === "---") {
  for (const line of lines.slice(1)) {
    if (line === "---") break;
    const m = line.match(/^([A-Za-z_]+):\s*(.*?)\s*(#.*)?$/);
    if (m) front[m[1]] = m[2];
  }
}

const role = roleArg || front.role;
if (!role) die(`Card ${id} has no role`);
const playbooks = (front.playbooks || "").replace(/[[\]]/g, "").split(",").map((s) => s.trim()).filter(Boolean);

const need = (rel) => {
  const p = path.join(mad, rel);
  if (!fs.existsSync(p)) die(`Missing: mad/${rel}`);
  return fs.readFileSync(p, "utf8");
};
const parts = [need(`roles/${role}.md`), need("AGENTS.md")];
for (const p of playbooks) parts.push(need(`playbooks/${p}.md`));
parts.push(`# Task card\n\n${cardText}`);

const runFile = path.join(mad, "RUN.md");
const runBranch = fs.existsSync(runFile) ? (fs.readFileSync(runFile, "utf8").match(/^Run branch:\s*(.+)$/m) || [])[1] : "";
if (runBranch) parts.push(`Run branch: ${runBranch.trim()}`);

const out = path.join(mad, "dispatch", `${id}${role === "reviewer" ? ".review" : ""}.md`);
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, parts.map((p) => p.trimEnd()).join("\n\n") + "\n");
console.log(out);
