---
name: repository-workspaces
description: "Create and verify isolated Git branches/worktrees for MAD tasks and integration, preserving ownership, base provenance, clean state, safe conflict handling, and cleanup. Use whenever agents share a repository or work must be dispatched, integrated, recovered, or retired."
---

# Repository Workspaces

## Invariant

```text
one executable task = one owner = one branch = one isolated workspace
```

The protected/base checkout is control-plane only. Product edits occur in task or integration workspaces.

## Create a task workspace

1. Fetch the declared remote and verify the approved base revision exists.
2. Inspect repository/worktree status. Stop before overwriting uncommitted or untracked work.
3. Create a uniquely named branch from the exact approved base.
4. Create an isolated worktree outside another agent's workspace.
5. Verify repository root, branch, `HEAD`, clean status, remotes, and repository instructions from inside the worktree.
6. Record task ID, owner, branch, workspace path, base revision, and creation time in the workstream plan/Kanban task.
7. Give the owner only that workspace.

Completion criterion: the owner can prove it is on the assigned clean branch at the recorded base and no other active task writes there.

Recommended names:

```text
agent/<source-item>/<task-id>-<slug>
integration/<source-item>-<slug>
```

## Preflight and drift

Before every execution or handoff, verify current branch, exact revision, clean/expected status, and upstream. Unexpected commits, branch switches, detached HEAD, rewritten history, or unrelated files are drift: stop and reconcile with the workstream owner.

Never hide drift with reset, clean, stash, force checkout, or force push without explicit ownership and preservation instructions.

## Integration workspace

Create integration work from an approved clean base in its own branch/worktree. Admit only immutable QA-approved revisions. Integrate in dependency order, one candidate at a time, and record resulting revision plus evidence after each step.

Resolve only behavior-preserving mechanical conflicts with proof. Route semantic conflicts to the workstream agent and original owners.

## Handoff

A workspace handoff records task, owner, path, branch, exact revision, base revision, status, uncommitted files, pushed remote ref, and next role. QA/release approval applies to the recorded revision; later changes require revalidation.

## Cleanup

1. Confirm work is merged/released, pushed for preservation, or explicitly abandoned.
2. Preserve reports and branch provenance.
3. Verify the worktree is clean.
4. Remove the worktree through Git, then prune metadata.
5. Delete local/remote branches only under repository retention policy.
6. Update the workspace registry/board.

Completion criterion: no unique work is lost, no active owner references the workspace, and Git worktree metadata is consistent.

## Hard stops

Stop on shared writable checkouts, direct protected-branch edits, branch switching outside contract, dirty unknown state, base ambiguity, destructive cleanup without preservation, semantic conflict, or a request to force-push another owner's branch.
