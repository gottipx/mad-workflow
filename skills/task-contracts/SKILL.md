---
name: task-contracts
description: "Create or validate executable MAD task contracts with explicit authority, scope, dependencies, controlled artifacts, observable completion, checks, and handoff requirements. Use before any agent starts architecture, coding, QA, release, planning, or revalidation work."
---

# Task Contracts

A task contract is an executable work packet, not a ticket summary. Its canonical schema is `templates/task-contract.yaml`.

## Creation procedure

1. Assign a unique task ID, source item, one owner agent, and one valid mode.
2. Write one outcome-focused goal and context sufficient to work without hidden chat history.
3. Define `allowed_scope` as concrete paths/globs. Define `forbidden_scope` for nearby controlled/high-risk files the task does not own.
4. Name dependencies by task/artifact and distinguish blocking inputs from informational context.
5. Name controlled contracts consumed and produced/modified. Empty lists mean “none,” not “unknown.”
6. Write observable definition-of-done items covering behavior, negative/recovery cases, evidence, report, and downstream impact.
7. Select exact required checks proportionate to risk; use commands where known and explicit manual evidence otherwise.
8. Define required report fields by referencing the canonical report template for the owner/mode.
9. Declare base revision, branch/workspace strategy, acceptance-criteria references, and controlled-artifact authority in context or extended fields when the runtime supports them.
10. Validate the contract mechanically and perform the readiness review below.

Completion criterion: the assigned agent can start safely, knows exactly what may change, and QA can decide completion without requesting hidden intent.

## Scope quality

Good `allowed_scope` is narrow enough to detect accidental edits but broad enough for the coherent outcome. Avoid repository-wide wildcards. Shared contracts, migrations, deployment/configuration, generated outputs, security policy, and release files are forbidden unless explicitly owned.

Allowed and forbidden patterns must not overlap. If legitimate work requires forbidden scope, amend/reapprove the contract; the executor does not reinterpret it.

## Definition-of-done quality

Each item is observable and binary enough for a gate. Cover:

- delivered behavior and critical failure/recovery path
- owned tests or alternative evidence
- controlled-contract/compatibility outcome
- required checks and report artifact
- downstream impact/revalidation statement

Do not use “implemented,” “works,” “proper,” or “complete” without an observation.

## Check selection

Checks name exact commands or review methods and expected evidence. Include focused checks plus risk-triggered contract, integration, accessibility, security, migration, deployment, or performance evidence. A check that cannot be run in the expected environment makes the task not ready unless an approved equivalent is named.

## Task sizing

A valid task is coherent, bounded, independently verifiable, reversible, and owned by one agent. Split tasks when behavior, controlled contracts, ownership, or risk require different decisions. Combine tasks when splitting would force shared files, hidden sequencing, or outputs with no independent value.

## Validation gate

Reject the contract if:

- goal or definition of done is subjective
- scope is empty, broad, overlapping, or omits controlled files
- dependency/contract state is unknown
- required check is vague or unavailable
- owner lacks authority for a required decision/change
- an open decision can materially alter implementation
- placeholders/TODOs remain

When Hermes is installed:

```bash
hermes mad validate-contract <contract.yaml>
```

Mechanical validity is necessary, not sufficient; apply the semantic gate above.

## Handoff

Deliver the contract path, approved base revision, assigned branch/workspace, dependency versions, required skills, report destination, and responsible workstream owner. Changes to these premises invalidate readiness until reviewed.
