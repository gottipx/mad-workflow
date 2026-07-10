# SKILLS.md — MAD Skill System

MAD uses ten composable skills. Agent files define authority; skills define repeatable procedures; templates define canonical schemas. Skills may make the global protocol stricter, never weaker.

## Routing catalog

| Skill | Primary users | Trigger | Required output |
|---|---|---|---|
| `workstream-management` | workstream | board control, execution waves, assignment, staleness, release request | truthful state, dependency plan, assignments, revalidation/release action |
| `spec-and-ticket-decomposition` | architect, workstream | rough intent, specification, acceptance criteria, candidate tasks | traceable spec, non-goals, criteria, task/dependency candidates |
| `task-contracts` | all task creators/executors | create, review, or consume executable work | validated bounded task contract |
| `repository-workspaces` | workstream, coding, QA, release | concurrent repository work, integration, cleanup | isolated workspace with branch/base/revision provenance |
| `contracts-and-interfaces` | architect, coding, QA, release | shared behavior/interface consumed or changed | owned, classified, testable contract and registry/impact data |
| `coding-standards` | coding | backend/data/infra/tooling/mixed implementation | focused implementation with risk-driven evidence |
| `frontend-design-system` | architect, coding, QA | any user-visible UI or interaction | design-system-consistent, state-complete, accessible behavior/evidence |
| `testing-and-quality-gates` | QA, release | task/integration quality decision | revision-pinned gate report and revalidation scope |
| `change-impact-analysis` | workstream, architect, QA, release | controlled artifact or task premise changed | compatibility/risk classification and owned revalidation |
| `completion-and-handoff` | all agents | finish, pause, fail, block, or transfer accountability | canonical report with exact revision and next owner/action |

## Loading policy

Load the smallest sufficient set, but never omit a safety-critical skill:

- every executable task: `task-contracts` and `completion-and-handoff`
- every writable repository task: `repository-workspaces`
- implementation: `coding-standards`
- shared contract consumption/change: `contracts-and-interfaces`
- UI/mobile: `frontend-design-system`
- QA or release gate: `testing-and-quality-gates`
- changed shared artifact/premise: `change-impact-analysis`
- board/sequencing decisions: `workstream-management`
- ambiguous intent/decomposition: `spec-and-ticket-decomposition`

Do not load all skills by default. Repeated context makes agents slower and can create conflicting local procedures. Route by the current branch of work and unload conceptual branches that are no longer active.

## Composition order

For a typical delivery:

```text
spec-and-ticket-decomposition
-> workstream-management
-> task-contracts
-> repository-workspaces
-> contracts-and-interfaces (when triggered)
-> coding-standards + frontend-design-system (when triggered)
-> completion-and-handoff
-> testing-and-quality-gates
-> change-impact-analysis (when triggered)
-> completion-and-handoff
```

A skill's completion criterion must pass before responsibility moves to the next stage. Reports do not repair missing upstream authority.

## Source of truth

Canonical artifact schemas live in `templates/`. Skills reference templates instead of embedding competing full schemas. Hermes validators provide mechanical checks; the semantic completion/readiness/gate rules in the global protocol and skills still apply.

## External skill reuse

Specialized skills such as `to-spec`, `to-tickets`, repository-specific test guidance, accessibility tooling, or deployment runbooks may accelerate a branch. Their output remains draft/evidence until it passes the relevant MAD skill's completion and authority gates.

## Skill quality standard

Every MAD skill must retain:

- a precise trigger-oriented description
- required inputs or discovery procedure
- ordered deterministic process
- explicit completion criterion
- evidence/output requirements
- hard stops or rejection conditions where risk exists
- references only to canonical schemas/commands that exist

Prefer concise decision rules and observable outcomes over motivational prose, duplicated agent responsibilities, or exhaustive advice unrelated to the active task.
