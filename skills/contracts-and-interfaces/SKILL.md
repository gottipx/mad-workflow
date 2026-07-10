---
name: contracts-and-interfaces
description: "Define, review, evolve, and register shared MAD contracts such as APIs, schemas, events, commands, configuration, persistence shapes, UI interfaces, migrations, and infrastructure boundaries. Use whenever work consumes or changes behavior shared across tasks or systems."
---

# Contracts and Interfaces

A contract is any externally consumed shape or behavior. Schema stability alone does not guarantee behavioral compatibility.

## Contract discovery

Before proposing change:

1. Identify the authoritative artifact and owner.
2. Find producers, direct consumers, generated derivatives, tests, docs, migrations, and deployment/config dependencies.
3. Record current invariants, failure semantics, versioning/deprecation policy, and compatibility expectations.
4. Verify `.agents/contracts.yaml` matches repository evidence; report drift.

Completion criterion: ownership, current behavior, and affected consumers are known well enough to classify a change.

## Proposal procedure

1. State the requirement and why the current contract cannot satisfy it.
2. Prefer an existing contract or additive extension over a parallel interface.
3. Define shape, semantics, invariants, validation, errors, authorization, idempotency/concurrency, defaults, and lifecycle where relevant.
4. Declare lifecycle metadata:

```yaml
status: proposal | approved | deprecated
owner: ""
change_type: internal | additive | behavioral | breaking | unclear
producers: []
consumers: []
required_revalidation: []
migration_or_versioning: ""
```

5. Compare at least two viable designs for consequential/hard-to-reverse contracts.
6. Define contract tests or observable conformance evidence.
7. Define rollout, coexistence, migration, deprecation, and rollback for non-internal changes.
8. Obtain required approval before implementation consumes the proposal as authoritative.
9. Update the registry, examples, generated outputs, and documentation from the same source.

Completion criterion: the approved artifact is unambiguous, testable, owned, compatible or migration-safe, and registered.

## Compatibility classification

- `internal`: no external or cross-task consumer
- `additive`: existing valid consumers retain shape and behavior
- `behavioral`: shape may remain stable but meaning, defaults, errors, ordering, timing, permissions, or side effects change
- `breaking`: a valid existing consumer can fail or become incorrect
- `unclear`: evidence is insufficient; treat as blocked until resolved

Breaking and unclear changes require explicit authority and an impact/migration plan. Prefer expand-and-contract:

1. add compatible producer behavior
2. migrate and verify consumers
3. enforce the new contract
4. remove old behavior only after evidence

## Review gate

Reject a contract when ownership is absent, semantics are vague, consumers are unknown, compatibility is asserted without evidence, error/authorization behavior is missing, generated artifacts can drift, migration/rollback is unsafe, or acceptance evidence cannot distinguish conformance.

## Controlled change rule

Coding agents may modify a contract only when the task contract explicitly names it as produced/modified and scope permits its authoritative source. Otherwise stop before editing and return a blocker requesting ownership/contract amendment.

## Handoff

Provide authoritative path, lifecycle status, owner, compatibility classification, producers/consumers, tests/evidence, registry update, migration/rollback, unresolved decisions, and required downstream revalidation.
