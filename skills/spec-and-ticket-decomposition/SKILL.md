---
name: spec-and-ticket-decomposition
description: "turn rough requirements, notes, documents, conversations, or board items into a concise technical specification and implementation-ready tickets. use when the architect-agent or workstream-agent must clarify intent, reuse external skills such as to-spec or to-tickets, define acceptance criteria, or produce a dependency-aware task list."
---

# Spec and Ticket Decomposition

Use this skill to convert intent into a compact specification and board-ready tickets.

## External skill preference

If available, use `to-spec` for the specification step. If available, use `to-tickets` for task decomposition. If unavailable, use the fallback formats below.

## Specification fallback format

```markdown
# Specification

## Problem
## Goal
## Non-goals
## Users / actors
## Required behavior
## Acceptance criteria
## Constraints
## Risks
## Open decisions
```

## Decomposition rules

Create task bundles, not tiny chores. Split work by contract boundary, ownership boundary, user-facing slice, integration risk, and testability.

Do not split when subtasks would constantly edit the same files or cannot be validated independently.

## Ticket format

```markdown
## Goal
## Scope
## Out of scope
## Dependencies
## Acceptance criteria
## Required checks
## Notes for implementation
```

## Output

Return the specification, ticket list, dependency notes, and open decisions. Keep it short enough to be operational.
