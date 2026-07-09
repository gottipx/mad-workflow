---
name: testing-and-quality-gates
description: "define and run testing, review, security, accessibility, performance, build, and merge-readiness checks. use when the qa-agent validates a task, reviews code, prepares findings, or when the release-agent decides whether work can proceed toward merge."
---

# Testing and Quality Gates

Use this skill to decide whether work can proceed.

## Test layers

Use the smallest effective set for the change:

- unit tests
- component tests
- contract tests
- integration tests
- end-to-end tests
- accessibility checks
- security or static checks
- build, type, and lint checks
- performance checks where relevant

## Review checklist

- task contract satisfied
- scope respected
- tests cover changed behavior
- contracts remain compatible or impact is handled
- security-sensitive behavior reviewed
- UI follows design-system and accessibility rules when relevant
- no unrelated refactoring
- completion report is usable

## Gate decision

```yaml
decision: pass | pass_with_notes | fail | blocked
evidence:
failed_checks:
required_fixes:
follow_up:
```

## Do not approve when

- required tests are missing without justification
- shared contract impact is unresolved
- security or data risk is unresolved
- build, type, or lint checks fail
- UI accessibility or critical interaction behavior is broken
