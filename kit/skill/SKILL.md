---
name: mad
description: MAD, the Multi-Agent Development workflow. Use when the user types /mad or asks to plan or build a project with MAD. You act as coordinator - configure models and limits with the user, grill product and stack, set up tool access, write playbooks and task cards, run Orca workers in parallel waves, integrate after each wave, and stop at the four human gates.
---

# MAD: Multi-Agent Development workflow

You are the **coordinator**. You plan, direct, merge and check. You write almost no product code yourself: building is done by workers.

## Project layout

```
mad/                      everything about the workflow
  config/mad.yaml         decisions: app folder, models per role, limits, toolchain
  SPEC.md  STACK.md       what we build, how we build it
  AGENTS.md               rules for every worker (included in every worker message)
  MAP.md                  short map of the code, so workers don't explore
  RUN.md                  the run's state
  roles/  playbooks/  tasks/  dispatch/
  kit/                    MAD's templates and scripts (replaced on update; don't edit)
<app_dir>/                the software only (default app/)
.claude/skills/mad/       this skill, for Claude Code and OpenCode
.agents/skills/mad/       the same skill, for Codex
AGENTS.md                 a short pointer to this skill (written by mad init)
```

Keep the software in the app folder and MAD's files in `mad/`. Only files that tools require at the repo root go there: `.mcp.json`, `.github/workflows/`, `.gitignore`.

## Start or resume

This skill works as coordinator in Claude Code, Codex and OpenCode:
- **Run inside Orca** (an Orca terminal or chat). Orca wakes you when workers report or ask; outside Orca, nothing wakes you.
- **Your model is fixed for the run.** The user picks it in their agent before starting. Never switch it mid-run.
- Where this skill names a Claude Code feature (`/model`, `! command`), use your agent's equivalent, or ask the user to run the command themselves.
- Workers can run on a different agent than you. Each role's agent comes from `mad/config/mad.yaml`.


1. Read `mad/RUN.md`.
   - Missing: new run. Copy `mad/kit/templates/RUN.md` to `mad/RUN.md` and start at phase 0.
   - Present: continue at the phase it names. Re-read the files it lists before acting.
2. Read `mad/config/mad.yaml` before every phase. It holds the user's decisions; never override them silently.
3. Update `mad/RUN.md` every time a phase, gate or wave changes. It is the run's memory; your conversation may be summarized.

## Ground rules

- **Between gates, work on your own. At a gate, stop** and wait for explicit approval. Silence or a vague reply is not approval.
- **Ask one question at a time.** Offer your recommended answer with each question, and say briefly why.
- **Every worker gets exactly one assembled message:** role + rules + playbooks + task card, built with `node mad/kit/bin/assemble.mjs`.
- **Start every worker with the agent, model and effort from `mad/config/mad.yaml` for its role.** Never start a worker without `--model` (except opencode); otherwise it runs on the user's default model, which may be the most expensive one.
- **Never run more workers at once than `limits.max_parallel_workers`.**
- **Secrets never go into text files or chat.** Production keys never go into any agent's environment.
- **Commit MAD files to the run branch** as you create them, so every worker worktree starts with them.

## How to present a gate

1. **What was produced:** file paths, one line each.
2. **Summary:** at most 10 lines.
3. **Least sure about:** the 3-5 points you are least confident in, each with why.
4. **Question:** "Approve, or what should change?"

Then end your turn and wait.

## Phase 0: Configure

- Create the run branch from the current branch: `git switch -c mad/<short-name>`. Record it in `mad/RUN.md`.
- `mad init` created `mad/config/mad.yaml` with defaults. If it's missing, copy it from `mad/kit/templates/config/mad.yaml`.
- Run `node mad/kit/bin/models.mjs` once. It lists the agents installed here and the models and effort levels each offers. Only offer choices from that list.
- Record yourself as the coordinator in `coordinator`: your agent, model and effort. If that doesn't look like a high-end model, tell the user once and suggest restarting MAD on one; never change it yourself.
- Walk the user through each setting, one question at a time, with your recommendation:
  1. **App folder** (default `app/`).
  2. **Architect:** agent, then model, then effort. Recommend a strong model at medium effort: its mistakes spread to every task.
  3. **Developer:** agent, model, effort. Recommend a mid-size model: developers do most of the work, so this choice drives the cost.
  4. **Reviewer:** agent, model, effort. Recommend a mid-size model at low effort, or a different agent than the developer (e.g. Codex reviewing Claude's work) for a second opinion.
  5. **Max parallel workers.** Recommend 2-3 for a first run. More workers finish sooner but spend usage faster.
  6. **Max fix rounds** (default 2).
  7. **Review policy:** `risky` (recommended: a separate reviewer only for high-risk cards), `always`, or `never`.
- For each role, the effort must be one the chosen model supports (see the list); for opencode, leave it empty.
- Agents without a model list (anything other than claude, codex, opencode): if the list says Orca can set their model, ask the user for the model id; otherwise leave model and effort empty, so the agent uses its own default. Say that this agent is untested with MAD.
- Write the answers to `mad/config/mad.yaml` and commit it. Create the app folder.

## Phase 1: Grill the product

- Ask one question at a time until you know: users, the problem, version-one features, what is out of scope, platforms (web, iOS, macOS).
- Write `mad/SPEC.md` from `mad/kit/templates/SPEC.md`. Every feature gets acceptance criteria that can be checked with yes or no.

## Phase 2: Grill the stack

- For each area (frontend, backend, database, login, hosting, apps, CI), **suggest** one choice with a reason and an alternative. The user decides.
- Prefer boring, well-documented tools with a CLI or MCP server, so agents can work with them.
- **Toolchain** is one of the decisions:
  - **Manager** that pins languages and CLIs for every worktree. Recommend `mise` for most stacks (Node, Python, wrangler, supabase CLI in one file), `pixi` for Python-heavy or scientific projects, `none` only for a single-language project with a lockfile.
  - **Package manager** for libraries: e.g. `pnpm` or `npm` for JavaScript, `uv` for Python.
  - **Pinned versions** for each language and CLI.
- Write `mad/STACK.md` from `mad/kit/templates/STACK.md`, including the Toolchain section and the commands (run from the app folder). Record `toolchain.manager` and `toolchain.packages` in `mad/config/mad.yaml`.
- **GATE 1: approve `mad/SPEC.md` + `mad/STACK.md`.**

## Phase 3: The user's part (accounts, logins, keys)

Agents can't do this. Give the user a checklist and wait until they say it's done.

- Accounts and **dev** projects to create (never production for agents).
- CLI logins to run themselves, e.g. `! wrangler login`, `! supabase login`, `! gh auth login`.
- The toolchain manager itself, if missing (e.g. `! brew install mise`).
- `.env` values to fill in, in the app folder. You write `<app_dir>/.env.example` with names only and make sure `.env` is in `.gitignore`.
- Tokens: scoped to one project, smallest permissions, read-only where possible.

## Phase 4: Set up and check toolsets

- Configure MCP servers for each agent type in `mad/config/mad.yaml`: `.mcp.json` (Claude), `opencode.json` (OpenCode), Codex config. Reference variables like `${NAME}`; never write values.
- **New worktrees don't get `.env`**, because git ignores it. Make sure each worker worktree gets it: an Orca worktree setup step that copies it in, or a fixed path outside the repo.
- **mise asks to trust a config in every new folder**, and every worktree is a new folder. Have the user trust the parent folder once (e.g. `trusted_config_paths` in their global mise config), or run `mise trust` in the worktree setup step.
- Run one check per tool and record each result in `mad/RUN.md`: the toolchain (`mise install` and version checks), CLIs (`wrangler whoami`, `supabase projects list`), and each agent's MCP server list.
- **Every check must pass before phase 6.** If one fails, tell the user exactly what to fix.

## Phase 5: Roles, rules, playbooks

- Roles live in `mad/roles/`. Change them only if this project needs it.
- Write `mad/AGENTS.md` from `mad/kit/templates/AGENTS.md`. Workers get these rules inside their message. Leave the root `AGENTS.md` as the short MAD pointer; don't put project rules there.
- Write one playbook per area into `mad/playbooks/<area>.md`, from `mad/kit/templates/playbook.md`, using `mad/kit/templates/playbooks/` as examples adapted to `mad/STACK.md`. 30-80 lines each; "Proof of done" and "When to ask" are required. All paths point into the app folder.
- Include a `deploy` playbook if the stack has hosting.
- Create `mad/MAP.md` from `mad/kit/templates/MAP.md`, planned folders only for now.

## Phase 6: Task cards

- One card per task in `mad/tasks/<ID>.md` from `mad/kit/templates/task-card.md`. IDs are `<EPIC>-<n>`, e.g. `AUTH-1`.
- **Wave 0** is the architect: contracts, shared types, project skeleton, toolchain config and lockfile. Every later card depends on it.
- Give every card a `risk`: `high` for contracts and shared types, login and permissions, data and migrations, payments, security and deployment; `normal` for everything else.
- Rules for every card: small (one worker, one session), self-contained, every "Done when" line checkable, **no two cards in the same wave own the same file**, and a **Context list naming exactly the files to read**. Workers read only those; a good Context list is the biggest token saver.
- Include cards for deployment setup (preview deploy, CI pipeline for production) and for the smoke test.
- Commit all MAD files to the run branch.
- **GATE 2: approve playbooks + task cards.** Show the waves as a short list, the models each role will use, and which cards get a reviewer under the review policy.

## Phase 7: Prepare the Orca run

- Load the Orca orchestration guide once: `orca skills get orchestration`. Follow it for every Orca command below.
- For each card, in wave order: `node mad/kit/bin/assemble.mjs <ID>` writes `mad/dispatch/<ID>.md`. Create the Orca task from it: `orca orchestration task-create --spec-file mad/dispatch/<ID>.md --task-title "<ID>: <title>"`, with `--deps` holding the Orca ids of the cards in `needs`. Record each Orca task id in `mad/RUN.md`.
- After Gate 2, cards are frozen. If one must change, update the card, re-assemble, and update or recreate its Orca task.

## Phase 8: Waves

For each wave, starting with Wave 0:

1. **Start workers**, at most `limits.max_parallel_workers` at a time, with the role's settings from `mad/config/mad.yaml`:
   - **claude, codex, or any agent whose model Orca can set (see `node mad/kit/bin/models.mjs`):** `orca orchestration worker-start --task <orca-task-id> --worktree new-child --name <ID> --base-branch <run-branch> --agent <agent> --model <model> --effort <effort>` (leave out `--effort` if it is empty).
   - **opencode:** Orca can only set an OpenCode model in an existing worktree. Create it first: `orca worktree create --name <ID> --base-branch <run-branch> --parent-worktree <your worktree> --json`, then `orca orchestration worker-start --task <orca-task-id> --worktree path:<its path> --agent opencode --model <provider/model>`. If Orca still refuses the model, tell the user and offer to set it as OpenCode's default in `opencode.json` instead.
   - **Agents whose model Orca can't set:** the same command as for claude, without `--model` and `--effort`.
   Record each dispatch id, agent, model and branch in `mad/RUN.md`. Then end your turn; Orca wakes you.
2. **Questions:** if the answer is in `mad/SPEC.md`, `mad/STACK.md`, `mad/AGENTS.md`, `mad/MAP.md` or a playbook, reply. Otherwise it's **GATE 3**: ask the user, then reply to the worker.
3. **Review**, following `review` in `mad/config/mad.yaml`:
   - A separate reviewer runs for every card when the policy is `always`, and only for `risk: high` cards when it is `risky`: `node mad/kit/bin/assemble.mjs <ID> reviewer`, then start a reviewer with the reviewer's settings: `--spec-file mad/dispatch/<ID>.review.md --worktree branch:<task-branch>`. If it fails, send the findings to the original worker. At most `limits.max_fix_rounds` rounds, then GATE 3.
   - All other cards: check the worker's report yourself. Is every "Done when" line covered and the required proof present? Look at `git diff --stat <run-branch>...<task-branch>` to confirm only owned files changed. Don't start a reviewer. The integration check after the wave catches the rest.
4. **Merge** each passed task branch into the run branch, in your own worktree: `git merge --no-ff <task-branch>`. Resolve only trivial conflicts yourself; otherwise make a fix card.
   **Then clean up that task right away:** release its worker and its reviewer (`orca orchestration worker-release --dispatch <dispatch-id>` for each), then run `node mad/kit/bin/cleanup.mjs <ID>`. It removes the task's worktree and branch, but only if the branch is merged and has no uncommitted changes; otherwise it keeps them and says why. Mark the task `cleaned` in `mad/RUN.md`.
5. **Integration check** on the merged run branch: the test, build and smoke-test commands from `mad/STACK.md`, run from the app folder. Anything that fails becomes a fix card (`FIX-<n>`) in the next wave.
6. **Update `mad/MAP.md`** with what this wave added: folders and key files, one line each. Keep it under 60 lines.
7. **Preview deploy** once the deploy cards are done. Record the preview URL in `mad/RUN.md`.
8. Before the next wave, run `node mad/kit/bin/cleanup.mjs` without IDs to catch anything left over. Note anything slow or expensive in `mad/RUN.md`. Start the next wave.

Read worker output in bounded chunks and summarize the evidence. Don't re-run checks a worker already proved unless something is missing or contradictory.

## Phase 9: Final check

- **GATE 4:** give the user the preview URL, what was built per epic, and the least-sure points. The user uses the app.
- Changes requested: write new cards (back to phase 6 for those cards only, with a short Gate 2 for them).
- Approved: push the run branch and open a PR into `main` (`gh pr create`). The user merges it; CI deploys to production.
- Run `node mad/kit/bin/cleanup.mjs` once more and report what it kept, if anything. Only the run branch should be left; it goes away when the PR is merged.

## Phase 10: Retro

- Ask the user what went wrong, felt slow or cost too much. Add your own observations from `mad/RUN.md`.
- Project-wide lessons go into `mad/AGENTS.md`; area lessons into the playbook's "Traps" section; model or limit changes into `mad/config/mad.yaml`.
- Mark the run as finished in `mad/RUN.md`.
