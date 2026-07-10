---
name: testing-and-quality-gates
description: "Design and execute independent, risk-based validation for a pinned MAD task or integration candidate and issue a pass, pass-with-notes, fail, or blocked decision. Use for QA review, integration gates, regression analysis, and release readiness."
---

# Testing and Quality Gates

A quality gate proves an exact revision; it does not endorse an agent's narrative.

## Pin and validate inputs

1. Record repository, approved base, candidate branch, immutable revision, task contract, completion report, and impact report versions.
2. Verify completion status, actual diff, scope, required checks, controlled contracts, and claimed evidence.
3. Stop as `blocked` if candidate identity, required behavior, environment, authority, or critical contract input is missing.

Completion criterion: the evidence target is immutable and QA can trace requirements and risk to observable checks.

## Risk model

Classify:

- changed behavior and blast radius
- trust boundaries, auth, secrets, and sensitive data
- API/schema/event/configuration and consumer compatibility
- persistence, migration, partial failure, and rollback
- UI states, accessibility, responsiveness, and async behavior
- dependency/build/deployment and environment compatibility
- performance, reliability, and observability expectations

Select the smallest check set that adequately covers the actual risk. Required contract checks are the floor, not the ceiling.

## Evidence procedure

1. Inspect the actual diff and verify allowed/forbidden scope.
2. Map every definition-of-done item and acceptance criterion to evidence.
3. Re-run critical claimed checks against the pinned revision.
4. Exercise negative, boundary, permission, recovery, and concurrency paths when relevant.
5. Validate controlled-contract compatibility, registry, consumers, and revalidation.
6. Apply relevant security, privacy, accessibility, performance, migration, deployment, and rollback gates.
7. Distinguish candidate regressions from pre-existing failures with baseline evidence.
8. Challenge whether tests would detect the important defect they claim to guard against.
9. Record exact command/method, revision/environment, result, and concise output/reference.
10. Issue one decision using `templates/quality-gate-report.yaml`.

Completion criterion: every applicable criterion/material risk is proven, failed, or explicitly blocks a trustworthy decision.

## Decision policy

- `pass`: all required/applicable evidence passed; scope and impact are clean; no material residual risk
- `pass_with_notes`: blocking evidence passed; each note is truly non-blocking, risk-stated, and owned
- `fail`: behavior, scope, compatibility, or required evidence is wrong; fixes and revalidation are concrete
- `blocked`: a trustworthy decision is impossible because a prerequisite/authority/environment is missing

Never use `pass_with_notes` for a failed required check, missing critical evidence, unresolved security/privacy/data-loss risk, unapproved behavioral/breaking contract, or unknown candidate revision.

## Evidence quality

Prefer reproducible command/CI output, direct diff/artifact inspection, deterministic validators, then documented manual observation. Another agent's report tells QA what to verify; it is not proof.

Manual evidence names environment, steps, expected result, and observation. Screenshots prove appearance only. Flaky success is not a pass until characterized.

## Finding format

Each blocker contains severity/category, violated requirement/invariant, revision/location, reproduction/evidence, expected vs actual behavior, impact, minimum required outcome, and revalidation scope. Specify outcomes rather than implementation unless only one correction is safe.

## Revalidation

Any candidate change invalidates prior approval. Re-run checks based on changed risk and affected seams; do not blindly rerun too little or the entire suite. Integration candidates require combined-behavior evidence even when each task passed independently.

When installed:

```bash
hermes mad validate-report qa <report.yaml> --contract <contract.yaml>
hermes mad gate <kanban-task-id> --stage integration --qa-report <report.yaml>
```
