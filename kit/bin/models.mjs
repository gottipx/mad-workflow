#!/usr/bin/env node
// Lists the agents Orca can start on this machine and the models each offers,
// so /mad can offer real choices for every role.
// Usage: node mad/kit/bin/models.mjs
//
// The agent list comes from Orca, so any agent Orca supports shows up without a MAD update.
// Claude, Codex and OpenCode also get their full model lists; others get a note on how
// their model is chosen.
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const isWin = process.platform === "win32";
const run = (cmd, args) => spawnSync(cmd, args, { encoding: "utf8", shell: isWin, timeout: 30000 });
const works = (cmd) => { const r = run(cmd, ["--version"]); return !r.error && r.status === 0; };

// Agents that are a mode of another agent, not a separate worker type.
const HIDDEN = new Set(["claude-agent-teams"]);

// How Orca passes a model to agents MAD has no model list for (from `orca orchestration worker-start --help`).
const VIA_ORCA = {
  cursor: "set with --model (Orca passes it on)",
  antigravity: "set with --model (Orca passes it on)",
  grok: "set with --model (Orca passes it on)",
  muse: "set with --model (Orca passes it on)",
  pi: "set with --model as provider/id; effort maps to its thinking level",
  omp: "set with --model as a role or provider/model; effort is its thinking level",
};

function claude() {
  console.log("claude    effort: low, medium, high, xhigh, max");
  console.log("  claude-opus-5-5     strongest; for coordinator and architect");
  console.log("  claude-sonnet-5-5   balanced; for developers and reviewers");
  console.log("  claude-haiku-5-5    fastest and cheapest; for simple tasks");
  console.log("  claude-fable-5-2");
}

function codex() {
  console.log("codex     effort: per model, shown in brackets");
  try {
    const data = JSON.parse(run("codex", ["debug", "models"]).stdout);
    for (const m of Array.isArray(data) ? data : data.models || []) {
      if (!m || m.visibility === "hide") continue;
      const levels = (m.supported_reasoning_levels || []).map((l) => (typeof l === "object" ? l.effort : l));
      console.log(`  ${String(m.slug || m.id).padEnd(18)} [${levels.filter(Boolean).join(", ")}]`);
    }
  } catch {
    console.log("  (could not read the model list; see /model in Codex)");
  }
  const cfg = path.join(os.homedir(), ".codex", "config.toml");
  const current = fs.existsSync(cfg) ? (fs.readFileSync(cfg, "utf8").match(/^model\s*=\s*"([^"]+)"/m) || [])[1] : "";
  if (current) console.log(`  your default: ${current}`);
}

function opencode(id) {
  console.log(`${id.padEnd(9)} effort: not supported; model only in an existing worktree`);
  const list = run("opencode", ["models"]).stdout.trim();
  console.log(list ? list.split(/\r?\n/).map((l) => "  " + l).join("\n") : "  (could not read the model list)");
}

function other(id, name) {
  console.log(`${id.padEnd(9)} ${name && name.toLowerCase() !== id ? `(${name}) ` : ""}`.trimEnd());
  if (VIA_ORCA[id]) {
    console.log(`  model: ${VIA_ORCA[id]}`);
    console.log("  no model list in MAD: type the model id yourself, or leave it empty for the agent's default");
  } else {
    console.log("  model: from this agent's own config; Orca can't set it. Leave model and effort empty.");
  }
}

// Which agents are installed: ask Orca, or probe the three known CLIs without it.
let agents;
const orca = run("orca", ["agent", "installed", "--json"]);
try {
  agents = JSON.parse(orca.stdout).result.agents.filter((a) => !HIDDEN.has(a.id));
  console.log("Agents Orca can start: " + agents.map((a) => a.id).join(", "));
} catch {
  console.log(orca.error ? "Orca not found. MAD needs Orca to run workers; showing the agents found directly." :
    "Could not read the agent list from Orca; showing the agents found directly.");
  agents = ["claude", "codex", "opencode"].filter(works).map((id) => ({ id }));
}

for (const a of agents) {
  console.log();
  if (a.id === "claude") claude();
  else if (a.id === "codex") codex();
  else if (a.id.startsWith("opencode")) opencode(a.id);
  else other(a.id, a.name);
}
