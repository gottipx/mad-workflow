---
name: completion-and-handoff
description: "Produce and validate canonical MAD completion, blocker, QA, impact, release, and responsibility-transfer reports with immutable revision evidence and explicit next ownership. Use whenever an agent finishes, pauses, fails, requests a gate, or transfers work."
---

# Completion and Handoff

A handoff is a transfer of accountability backed by artifacts. It must be usable without hidden chat context.

## Select status and artifact

- `completed`: definition of done met and required evidence passed → `templates/completion-report.yaml`
- `partial`: useful scoped output exists but definition of done is unmet → completion report with missing outcomes
- `blocked`: external decision/dependency/permission/scope/environment is required → `templates/blocker-report.yaml`
- `failed`: attempted work/evidence failed → completion report plus failure evidence
- QA decision → `templates/quality-gate-report.yaml`
- controlled/downstream impact → `templates/impact-report.yaml`
- integrated release candidate → `templates/release-candidate.yaml`

Never report `completed` to improve board flow. Status expresses evidence.

## Report procedure

1. Pin task/source item, owner role, branch/workspace, exact revision, approved base, and artifact versions.
2. State status/decision and gate or action requested.
3. List actual changed files and controlled artifacts; use empty lists only for verified none.
4. Map definition-of-done/acceptance criteria to evidence.
5. Record each check with exact command/method, revision/environment, result, and concise reference.
6. Separate assumptions, blockers, required fixes, residual risks, follow-ups, and downstream impact.
7. Name the next accountable role/person and precise requested action.
8. Validate schema mechanically when available and self-check truthfulness against repository evidence.
9. Preserve/push the exact revision so the receiver can reproduce it.

Completion criterion: the receiver can validate the candidate, decide the next gate, and reproduce key claims without asking for unstated context.

## Blocker quality

A blocker report names:

- observed condition and direct evidence
- affected goal/criterion and impact
- why continuing is unsafe or unauthorized
- minimum decision/input/permission needed and its owner
- safe options/trade-offs when known
- work safely completed/preserved
- exact restart condition

“Need clarification,” “environment issue,” or “tests unavailable” alone is not actionable.

## Evidence rules

- Reports index evidence; they are not proof by themselves.
- Never claim a command ran if it did not.
- Record `failed` or `not_run` and consequence explicitly.
- Separate pre-existing failures with baseline evidence.
- Do not hide warnings or residual risk in prose; place them in the proper fields.
- Approval applies only to the exact reported revision.

## Receiver validation

Before accepting ownership:

1. verify schema and required fields
2. verify candidate/revision exists and matches the report
3. inspect actual diff/scope and critical evidence
4. confirm dependencies/contracts remain fresh
5. confirm requested action is within receiver authority

Return an incomplete or contradictory handoff to the sender with missing evidence named. Do not reconstruct it by guesswork.

## Hermes validation

When installed:

```bash
hermes mad validate-report completion <report.yaml> --contract <contract.yaml>
hermes mad validate-report qa <report.yaml> --contract <contract.yaml>
hermes mad validate-report impact <report.yaml> --contract <contract.yaml>
```

Mechanical validation is necessary, not sufficient; compare claims to the pinned revision.
