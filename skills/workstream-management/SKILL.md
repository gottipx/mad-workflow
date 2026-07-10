---
name: workstream-management
description: "Orchestrate a MAD work item through readiness, artifact-based dependency planning, execution waves, assignment, staleness, revalidation, QA, and release. Use when controlling Kanban flow or deciding what may run next or in parallel."
---

# Workstream Management

Produce truthful, controlled flow. Board state follows evidence; it never substitutes for it.

## Inputs

Read the source item, approved specification/decisions, current board, task contracts, `.agents/contracts.yaml`, reports, repository state, and available isolated workspaces. Record missing authority as a blocker.

## Control loop

1. **Observe:** reconcile board state with current artifacts, immutable revisions, dependencies, blockers, and reports.
2. **Shape:** capture goal, acceptance criteria, non-goals, controlled artifacts, risks, and unresolved decisions. Route specification/contract ambiguity to `architect-agent`.
3. **Graph:** model dependencies by consumed/produced artifact, not chronology. Identify shared-file and ownership conflicts.
4. **Wave:** group ready work into Shape, Build, Prove, Release, and Revalidate waves as needed. Read `references/execution-waves.md` for multi-wave work.
5. **Contract:** produce one reviewed `templates/task-contract.yaml` per executable task. Validate it and remove every placeholder before `Ready`.
6. **Admit:** assign one owner, branch, workspace, and base revision only when the global readiness gate passes.
7. **Monitor:** react to reports and repository evidence. Keep every active task's owner, state, premise, and next action current.
8. **Revalidate:** when a consumed artifact changes, pause affected tasks, run impact analysis, mark them stale, and create explicit revalidation.
9. **Converge:** request QA for completed candidate revisions; send only QA-approved, dependency-consistent revisions to release.
10. **Close:** verify traceability, follow-up ownership, workspace disposition, and truthful final board state.

Completion criterion: every task is either safely closed or has one accountable owner, an evidence-backed state, fresh dependencies, and an explicit next action/restart condition.

## Readiness test

A task enters `Ready` only if:

- behavior and definition of done are observable
- allowed/forbidden scope and controlled artifacts are explicit
- required inputs/contracts are stable or explicitly mocked
- checks are executable and proportionate to risk
- owner type, base, branch, and workspace strategy are known
- no open decision can materially change implementation

## Parallelization test

Parallelize only when inputs are stable, file ownership does not materially overlap, workspaces are isolated, outputs are independently testable, and one failure does not invalidate another task's premise. Otherwise sequence.

## Event responses

| Event | Response |
|---|---|
| forbidden scope needed | block and route ownership/scope decision |
| controlled artifact changed | generate impact; mark consumers stale; revalidate |
| completion not `completed` | keep out of Review; assign restart action |
| QA `fail` | return required outcomes and revalidation scope to owner |
| QA `blocked` | route missing input/environment to its owner |
| QA `pass_with_notes` | require non-blocking classification and follow-up owner |
| overlapping ownership or branch drift | stop, reconcile bases/ownership, then resume |

## Hermes acceleration

When installed, use:

```bash
hermes mad decompose <feature-plan.yaml> --out .agents/task-contracts
hermes mad validate-contract <contract.yaml>
hermes mad create-task <contract.yaml>
hermes mad impact <task-id> --graph .agents/contracts.yaml --repo . --base <base>
hermes mad gate <kanban-task-id> --stage <review|integration|done>
```

Generated decomposition is draft material. Review it before dispatch.

## Required outputs

Feature plan/spec reference, dependency registry, validated task contracts, execution/assignment plan, board decisions, revalidation tasks, and an evidence-complete release request.
