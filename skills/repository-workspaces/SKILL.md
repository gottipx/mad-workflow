---
name: repository-workspaces
description: "manage one shared codebase with isolated agent workspaces, one branch per task, safe worktree usage, branch naming, ownership, integration branches, and cleanup. use whenever agents work on the same repository or setup must prevent workspace, branch, and merge conflicts."
---

# Repository Workspaces

Use this skill to keep multiple agents from corrupting the same codebase.

## Core rule

```text
one task = one branch = one isolated workspace = one owner
```

## Recommended layout

```text
repo/
  main-checkout/
  worktrees/
    TASK-001-architecture/
    TASK-002-coding/
    TASK-003-qa/
```

## Branch naming

```text
agent/<source-item>/<task-id>-<short-name>
integration/<source-item>-<short-name>
```

## Workspace rules

- Never let two agents write to the same checkout.
- Never let coding agents work directly on main.
- Keep integration work in an integration branch.
- Require agents to state branch and workspace in completion reports.
- Clean up stale worktrees only after branches are pushed or explicitly abandoned.

## Integration pattern

1. Create task branches from the approved base.
2. Merge completed task branches into the integration branch in dependency order.
3. Run gates after each wave.
4. Prepare one final PR or merge request to main.

## Hard stop

If a task requires workspace sharing, direct main edits, or branch switching outside the contract, stop and request workstream-agent approval.
