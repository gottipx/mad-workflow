# SKILLS.md - Lean Skill Catalog

Use no more than these ten skills for the multi-agent delivery process.

| Skill | Used by | Responsibility |
|---|---|---|
| `workstream-management` | workstream-agent | Delivery flow, task waves, board state, dependency management. |
| `spec-and-ticket-decomposition` | workstream-agent, architect-agent | Specification and ticket decomposition. |
| `task-contracts` | all agents | Precise task packets and definitions of done. |
| `repository-workspaces` | workstream-agent, coding-agent, release-agent | Branch/worktree/workspace discipline. |
| `contracts-and-interfaces` | architect-agent, coding-agent, qa-agent | Contract-first delivery and compatibility rules. |
| `coding-standards` | coding-agent | Safe code changes across backend, frontend, mobile, infra, and data. |
| `frontend-design-system` | architect-agent, coding-agent, qa-agent | UI consistency, accessibility, responsive behavior, interaction states. |
| `testing-and-quality-gates` | qa-agent, release-agent | Tests, review checklist, gate decisions. |
| `change-impact-analysis` | workstream-agent, qa-agent, release-agent | Diff classification and downstream revalidation. |
| `completion-and-handoff` | all agents | Structured completion, blocker, and handoff reporting. |

## External skill reuse

When available, reuse specialized planning skills such as `to-spec` and `to-tickets` before using local fallback instructions in `spec-and-ticket-decomposition`.
