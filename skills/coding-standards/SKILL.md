---
name: coding-standards
description: "Implement an approved MAD task with minimal scope, established architecture, risk-driven validation, diff self-review, and truthful evidence. Use for backend, data, infrastructure, tooling, or mixed implementation work after task preflight."
---

# Coding Standards

Correctness and evidence outrank code volume. Follow repository-local rules before this generic skill when they are stricter.

## Preflight

1. Verify assigned workspace, branch, base revision, and clean/expected status.
2. Read task contract, acceptance criteria, consumed contracts, allowed/forbidden scope, dependencies, and required checks.
3. Inspect the existing implementation, tests, and nearest architectural seam.
4. Map each definition-of-done item to a code change and evidence.
5. Establish a focused baseline when practical.
6. Stop if behavior, authority, scope, dependency, or evidence premise is materially ambiguous.

Completion criterion: work can proceed without inventing behavior or modifying unowned artifacts.

## Implementation loop

1. Make the smallest coherent change that satisfies one observable criterion.
2. Preserve established architecture and invariants; prefer existing seams over new abstractions.
3. Add validation at trust boundaries and tests at the lowest effective layer.
4. Run focused evidence early.
5. Inspect the diff for scope, contract, security, generated-file, and unrelated-change drift.
6. Repeat until every criterion is covered.
7. Run all contract-required and risk-triggered checks.
8. Perform final skeptical self-review and produce the canonical report.

## Design discipline

- Keep behavior changes distinct from mechanical cleanup.
- Avoid speculative generality, pass-through wrappers, broad formatting, unrelated dependency upgrades, and opportunistic rewrites.
- Prefer deep modules that hide complexity behind small stable interfaces.
- Make invalid states difficult to represent where local design permits.
- Preserve authorization, validation, privacy, transactions, concurrency/idempotency, errors, observability, and resource lifecycle.
- Comments explain constraints or non-obvious rationale, not syntax.
- Change generated sources, not generated output, unless the contract explicitly owns regeneration.
- Never add secrets, personal data, debug artifacts, machine-specific paths, or silent failure handling.

## Risk triggers

### Backend/data

Validate authorization, inputs, error mapping, transactions, concurrency/idempotency, persistence compatibility, migrations/rollback, and observability as applicable.

### Infrastructure/deployment

Validate least privilege, secret/config handling, idempotence, plan/dry-run, health/readiness, rollout/rollback, state preservation, and environment compatibility.

### Tooling/automation

Validate deterministic output, non-zero failure exits, actionable diagnostics, path portability, clean-environment execution, and dry-run before external side effects.

For UI/mobile, load `frontend-design-system` in addition to this skill.

## Testing standard

A useful test protects behavior, fails for the defect it claims to detect, avoids internal implementation coupling, and covers critical negative/recovery behavior. Do not weaken or delete meaningful tests solely to make a change green. Separate pre-existing failures with baseline evidence.

## Final diff gate

Confirm:

- every changed file is intentional and within allowed scope
- forbidden/controlled files changed only with explicit authority
- no unrelated refactor, generated drift, secret, or debug artifact remains
- acceptance criteria and critical risks have evidence
- required checks ran against the reported revision
- assumptions, residual risks, and downstream impact are concrete

Use mechanical scope validation when available:

```bash
hermes mad check-scope <contract.yaml> --repo . --base <approved-base>
```

## Status rule

Report `completed` only when definition of done and required evidence passed. Use `partial`, `blocked`, or `failed` according to the global protocol; never convert unavailable or failing evidence into success.
