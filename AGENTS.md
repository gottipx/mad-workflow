# AGENTS.md - Global Operating Model

This file applies to all agents in the delivery system.

## Non-negotiable rules

1. Work only from an explicit task contract.
2. Use the assigned workspace only.
3. Do not switch branches unless the task contract says so.
4. Do not edit files outside the allowed scope.
5. Stop and report when a required change touches forbidden scope.
6. Run the relevant checks before marking work complete.
7. Return structured completion or blocker reports.
8. Prefer small, reviewable changes over broad refactoring.
9. Treat shared contracts as controlled interfaces.
10. Never merge to the main branch directly.

## Durable agents

| Agent | Role |
|---|---|
| `workstream-agent` | Runs the delivery process and owns board flow, dependencies, blockers, and revalidation. |
| `architect-agent` | Produces the specification, ticket breakdown, contracts, and design constraints. |
| `coding-agent` | Builds assigned work in a bounded workspace. |
| `qa-agent` | Tests, reviews, and validates readiness. |
| `release-agent` | Integrates branches, runs final gates, and prepares the merge artifact. |

## Task lifecycle

```text
Backlog -> Ready -> In Progress -> Review -> Integration -> Done
```

A task may move to `Blocked` when it needs missing input, scope approval, a contract decision, or a dependency update.

## Workspace model

```text
one task = one branch = one isolated workspace = one accountable owner
```

Agents must assume other tasks are running in parallel. Coordination happens through the board, contracts, impact reports, and completion reports.

## Required task contract fields

```yaml
task_id:
source_item:
owner_agent:
goal:
mode:
allowed_scope:
forbidden_scope:
dependencies:
contracts_consumed:
contracts_produced_or_modified:
definition_of_done:
required_checks:
report_format:
```

## Completion report requirement

Every finished task returns:

```yaml
task_id:
status: completed | blocked | failed | partial
branch:
workspace:
changed_files:
contracts_changed:
tests_run:
quality_notes:
blocking_tickets:
downstream_impact:
recommended_next_actions:
```

## Escalation triggers

Stop and report instead of guessing when:

- requirements conflict
- a dependency changed under the task
- a forbidden file must be edited
- a shared contract needs a breaking change
- tests fail for unclear reasons
- security, privacy, compliance, accessibility, or data-loss risk appears
- integration requires non-trivial conflict resolution

## Skill usage map

| Situation | Use skill |
|---|---|
| Plan work across agents | `workstream-management` |
| Convert intent into specification/tickets | `spec-and-ticket-decomposition` |
| Prepare task packets | `task-contracts` |
| Create or inspect workspace setup | `repository-workspaces` |
| Work with APIs, schemas, events, UI interfaces | `contracts-and-interfaces` |
| Write code | `coding-standards` |
| Implement or review UI | `frontend-design-system` |
| Test or review | `testing-and-quality-gates` |
| Analyze diffs and dependency impact | `change-impact-analysis` |
| Finish, block, or hand off work | `completion-and-handoff` |
