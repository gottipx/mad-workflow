---
name: change-impact-analysis
description: "Determine the direct and transitive consequences of a MAD diff or controlled-contract change, classify compatibility and risk, mark stale work, and define proportionate revalidation. Use before QA/integration whenever shared artifacts or task premises may have changed."
---

# Change Impact Analysis

Impact is based on repository evidence and registered dependency edges, not filename intuition alone.

## Pin inputs

Record source task, approved base, changed revision, actual changed files, task contract, and `.agents/contracts.yaml`. If the diff/base is unknown, impact is `unclear` and release is blocked.

## Analysis procedure

1. Compute the actual diff and classify changed files as implementation, test, documentation, generated, dependency/build, configuration, migration/data, security policy, deployment, or controlled contract.
2. Identify changed authoritative artifacts and distinguish generated derivatives.
3. For each controlled artifact, find owner, producers, direct consumers, transitive consumers, tests, docs, deployment/config, and active tasks that consume it.
4. Classify change as `internal`, `additive`, `behavioral`, `breaking`, or `unclear`; cite evidence.
5. Evaluate compatibility dimensions: shape, meaning/defaults, errors, ordering/timing, permissions, side effects, data lifecycle, performance, and operational behavior.
6. Assess risk from blast radius, reversibility, data/security criticality, migration coupling, evidence strength, and active-work staleness.
7. Mark affected contracts/tasks and identify which completed/active reports are stale.
8. Define the minimum sufficient revalidation by consumer/seam and owner; include migration/rollback or integration-order work.
9. Update `.agents/contracts.yaml` when approved artifact ownership/dependency edges changed.
10. Write `templates/impact-report.yaml` and route required actions.

Completion criterion: every materially affected producer, consumer, active task, report, and release gate has an explicit disposition and owner.

## Classification rules

- `internal`: no external/cross-task behavior changes and evidence supports this
- `additive`: every previously valid consumer remains valid in shape and semantics
- `behavioral`: observable meaning changes despite possible schema stability
- `breaking`: an existing valid consumer can fail or become incorrect
- `unclear`: evidence/ownership/consumer graph is incomplete; treat as blocked

Do not label a change internal merely because a symbol is private or a schema is unchanged.

## Risk level

- `low`: local, reversible, strong focused evidence, no controlled consumer effect
- `medium`: bounded multi-module/consumer effect, migration/config interaction, or incomplete regression confidence
- `high`: breaking/unclear contract, auth/privacy/data loss, irreversible migration, broad blast radius, or weak rollback/evidence

Risk level never reduces the required handling for a breaking or unclear change.

## Revalidation selection

Choose evidence at affected seams:

- producer contract and behavior checks
- direct consumer integration/contract tests
- transitive critical journeys
- migration forward/rollback and partial failure
- security/accessibility/performance checks triggered by semantics
- integrated release checks for cross-task interactions

State what need not be rerun and why when narrowing revalidation.

## Staleness protocol

A task/report is stale when a consumed contract, approved base, dependency revision, acceptance criterion, or required environment changes materially. Pause dependent work, record the invalidated premise, assign revalidation, and restore readiness only after fresh evidence.

When installed:

```bash
hermes mad graph validate .agents/contracts.yaml
hermes mad graph consumers <contract-id> --graph .agents/contracts.yaml
hermes mad impact <task-id> --graph .agents/contracts.yaml --repo . --base <base>
```
