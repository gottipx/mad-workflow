# Hermes Quickstart

This guide installs MAD Workflow into [Hermes Agent](https://hermes-agent.nousresearch.com/docs) as a native workflow helper.

The integration is intentionally thin. It does not replace Hermes Kanban, profiles, skills, worktrees, or GitHub support. It maps the MAD operating model onto those existing Hermes primitives.

## What gets installed

- A Hermes plugin that adds `hermes mad ...` commands.
- The 10 MAD skills under `~/.hermes/skills/mad-workflow/`.
- Optional Hermes profiles for the five MAD roles:
  - `mad-workstream`
  - `mad-architect`
  - `mad-coding`
  - `mad-qa`
  - `mad-release`
- A Kanban board, by default `mad-workflow`.

## Install

From a checkout of this repository:

```bash
./integrations/hermes/install.sh --profiles --switch
```

Useful options:

```bash
./integrations/hermes/install.sh \
  --board mad-workflow \
  --workdir /path/to/your/project \
  --profiles \
  --switch
```

If you only want to copy the plugin and skills without enabling the plugin:

```bash
./integrations/hermes/install.sh --no-enable
```

## Verify

```bash
hermes mad --help
hermes kanban boards list
hermes profile list
hermes skills list | grep mad-workflow
```

## Validate a task contract

```bash
hermes mad validate-contract examples/hermes-task-contract.yaml
```

The validator checks that required MAD fields exist, list fields are lists, `owner_agent` is one of the five MAD roles, `mode` is known, and `allowed_scope` does not overlap `forbidden_scope`.

## Create a Kanban task from a contract

```bash
hermes mad create-task examples/hermes-task-contract.yaml --board mad-workflow
```

Role-to-profile mapping:

| MAD role | Hermes profile |
|---|---|
| `workstream-agent` | `mad-workstream` |
| `architect-agent` | `mad-architect` |
| `coding-agent` | `mad-coding` |
| `qa-agent` | `mad-qa` |
| `release-agent` | `mad-release` |

The command stores the full contract in the Kanban task body and force-loads the role's MAD skills into the worker.

## Check a diff against scope

From a repository with changes:

```bash
hermes mad check-scope examples/hermes-task-contract.yaml --repo . --base origin/main
```

The check fails if changed files are outside `allowed_scope` or inside `forbidden_scope`.

## Validate reports and gates

MAD reports are plain YAML. Validate them before moving work forward:

```bash
hermes mad validate-report completion examples/hermes-completion-report.yaml \
  --contract examples/hermes-task-contract.yaml

hermes mad validate-report qa examples/hermes-quality-gate-report.yaml \
  --contract examples/hermes-task-contract.yaml

hermes mad validate-report impact examples/hermes-impact-report.yaml \
  --contract examples/hermes-task-contract.yaml
```

Evaluate Kanban task readiness gates:

```bash
hermes mad gate <kanban-task-id> --stage review \
  --contract examples/hermes-task-contract.yaml \
  --completion examples/hermes-completion-report.yaml

hermes mad gate <kanban-task-id> --stage integration \
  --contract examples/hermes-task-contract.yaml \
  --completion examples/hermes-completion-report.yaml \
  --qa examples/hermes-quality-gate-report.yaml
```

Use `--block-on-fail` when you want a failed gate to block the Kanban task with the gate errors.

## Track contract impact

Define shared contracts in a registry:

```bash
hermes mad graph validate examples/hermes-contracts.yaml --repo .
hermes mad graph consumers examples/hermes-contracts.yaml docs/contracts/example-api.yaml
```

Generate an impact report from the current git diff:

```bash
hermes mad impact TASK-001 \
  --graph examples/hermes-contracts.yaml \
  --repo . \
  --base origin/main \
  --out .agents/reports/TASK-001-impact.yaml
```

The generated report lists changed contract artifacts, impacted consumer tasks, and required revalidation tasks.

## Render a worker prompt

```bash
hermes mad prompt examples/hermes-task-contract.yaml
```

This produces a role-specific prompt containing the task goal, allowed scope, forbidden scope, required checks, and stop conditions.

## Current scope of the integration

Implemented:

- Hermes plugin installer.
- MAD skill installation.
- Optional MAD profile creation.
- MAD board initialization.
- Contract validation.
- Kanban task creation from contracts.
- Git diff scope checking.
- Contract-to-worker prompt rendering.

Not yet implemented:

- Automatic task decomposition from a feature brief.
- Automatic QA report validation.
- Release-agent merge orchestration.
- First-class contract registry / dependency graph updates.
- GitHub issue and PR automation.
- Kanban state transition hooks that enforce MAD gates automatically.

The intended next step is to add Kanban lifecycle hooks so `Review`, `Integration`, and `Done` transitions can be blocked unless the required MAD reports and checks exist.
