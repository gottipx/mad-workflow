---
name: workstream-management
description: "coordinate multi-agent software delivery from a kanban-style work item through planning, task contracts, dependency control, isolated workspaces, quality review, and release readiness. use when the workstream-agent must split work across agents, manage board state, decide what can run in parallel, or trigger revalidation after a change."
---

# Workstream Management

Use this skill to run the delivery flow for one work item or feature across the five-agent model.

## Outcome

Produce controlled execution: clear task contracts, known dependencies, isolated workspaces, explicit quality gates, and traceable release readiness.

## Procedure

1. Read the source work item and capture goal, constraints, acceptance criteria, and known risks.
2. Use `to-spec` for specification and `to-tickets` for decomposition when available.
3. If external planning skills are unavailable, create a compact delivery brief and task list locally.
4. Group work into waves:
   - Wave 1: requirement clarification, architecture, contracts, design constraints.
   - Wave 2: coding tasks with stable inputs.
   - Wave 3: QA review, integration, release preparation.
5. Create one task contract per executable task.
6. Assign exactly one accountable owner per task.
7. Require one branch and one isolated workspace per active task.
8. Track dependencies by artifacts: contracts consumed, contracts produced, modules touched.
9. When a consumed artifact changes, mark downstream tasks stale and create revalidation tasks.
10. Send only QA-approved branches to the release-agent.

## Parallelization rules

Parallelize only when tasks have stable inputs, low file overlap, separate workspaces, and independently checkable outputs. Sequence tasks when they modify shared contracts, depend on unresolved decisions, or touch the same high-conflict files.

## Board states

```text
Backlog -> Ready -> In Progress -> Review -> Integration -> Done
Blocked may be used from any state.
```

## Required outputs

- delivery brief or specification reference
- task list
- dependency graph
- task contracts
- branch/workspace plan
- revalidation tasks when needed
- release request for completed work

## Reference

Read `references/execution-waves.md` when planning complex work with multiple dependent tasks.
