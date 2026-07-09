---
name: change-impact-analysis
description: "inspect diffs, changed files, contracts, modules, tests, configuration, and reports to determine downstream impact and required revalidation. use when a task completes, a contract changes, tests fail after integration, or the workstream-agent must decide which tasks are stale."
---

# Change Impact Analysis

Use this skill to determine what changed and who must react.

## Inspect

- changed files
- changed contracts
- generated artifacts
- test files
- configuration
- dependencies
- migrations or data shape
- public interfaces
- UI components and shared styles

## Classify change

```yaml
change_type: internal | additive | behavioral | breaking | unclear
risk_level: low | medium | high
changed_artifacts:
impacted_consumers:
required_revalidation:
```

## Impact rules

- Contract changes require consumer revalidation.
- Shared component changes require UI regression review.
- Auth, permissions, secrets, data exposure, and migrations are high-risk by default.
- Build config and dependency changes require full release gates.
- Test-only changes still need review if they weaken coverage.

## Output

Return an impact report with changed artifacts, consumers, stale tasks, risk level, and next actions.
