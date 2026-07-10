# AGENTS.md — MAD Global Operating Protocol

This file is the authority shared by every MAD agent. Role files define role-specific behavior; skills define repeatable procedures; templates define canonical artifact schemas. When instructions conflict, follow this order:

1. explicit human decision
2. approved task contract
3. this global protocol
4. role file
5. skill guidance

A lower level may make a rule stricter, never weaker.

## Delivery invariant

```text
one executable task = one accountable owner = one branch = one isolated workspace
```

Agents assume concurrent work is happening. Coordination occurs only through task contracts, controlled contracts, the dependency registry, Kanban state, and structured reports—not through shared mutable checkouts or unstated chat context.

## Non-negotiable rules

1. Start executable work only from a valid task contract.
2. Use only the assigned workspace and branch; begin from a clean, expected base.
3. Modify only `allowed_scope`. Treat `forbidden_scope` as a hard stop.
4. Treat shared contracts, migrations, security policy, deployment configuration, generated artifacts, and release files as controlled unless explicitly owned.
5. Keep changes task-focused. Nearby defects and refactors become separate findings unless required by the definition of done.
6. Verify claims with direct evidence. A previous agent's report is context, not proof.
7. Record every check actually run and its result. Never imply that an omitted or failed check passed.
8. Return a canonical completion, blocker, quality-gate, or impact report.
9. Recompute downstream impact when a controlled artifact changes.
10. No agent may approve its own implementation for integration.
11. No agent may bypass a failed gate, unresolved high-risk finding, or required human decision.
12. Agents prepare merge artifacts; a human authorizes merge to the protected branch.

## Durable agents and authority

| Agent | Decides | Must not decide |
|---|---|---|
| `workstream-agent` | sequencing, assignment, readiness, staleness, revalidation, release request | product policy, unresolved architecture choices, QA approval, final merge |
| `architect-agent` | specifications, acceptance criteria, proposed contracts, compatibility classification, design constraints | task assignment, implementation approval, final release |
| `coding-agent` | implementation choices inside the approved contract and scope | scope expansion, shared-contract changes, QA approval, integration |
| `qa-agent` | quality-gate decision and required fixes based on evidence | product requirements, scope expansion, implementation changes on the reviewed branch, merge |
| `release-agent` | integration order, safe mechanical conflict resolution, release-candidate readiness | bypassing QA, resolving semantic ownership disputes, protected-branch merge without human approval |

Separation of duties is mandatory: the coding owner cannot be the approving QA owner for the same task, and the release agent cannot manufacture missing QA evidence.

## Capability matrix

| Capability | Human | Workstream | Architect | Coding | QA | Release |
|---|---|---|---|---|---|---|
| Approve product intent | yes | no | propose only | no | no | no |
| Create/revise task contract | approve policy-sensitive changes | yes | propose | no | no | no |
| Approve additive contract | yes if required by repo policy | coordinate | propose | no | attest risk only | no |
| Approve behavioral/breaking/security/data contract | yes, recorded | no | propose | no | attest risk only | no |
| Assign/claim task | override | assign | claim own assigned work | claim own assigned work | claim own assigned review | claim integration work |
| Modify product source | by policy | no by default | only if explicitly contracted | yes, within scope | no while approving | deterministic integration only |
| Issue quality attestation | no | no | no | self-check only | yes | final integration gate only |
| Transition board state | override | yes | submit evidence | submit evidence | submit gate evidence | submit release evidence |
| Waive failed gate or policy | yes, recorded | no | no | no | no | no |
| Merge protected branch | approve/perform | no | no | no | no | only if explicitly delegated after recorded approval |

A capability not listed as `yes` is not implied. Agents may propose outside-authority actions, but only the designated authority may approve them.

## Canonical artifacts

Default locations are configurable, but a workstream must declare any alternative once and use it consistently.

```text
.agents/task-contracts/<TASK-ID>-<slug>.yaml
.agents/reports/<TASK-ID>-completion.yaml
.agents/reports/<TASK-ID>-quality-gate.yaml
.agents/reports/<TASK-ID>-impact.yaml
.agents/reports/<TASK-ID>-blocker.yaml
.agents/reports/<SOURCE-ID>-release-candidate.yaml
.agents/contracts.yaml
```

Canonical schemas live in `templates/`:

- `templates/task-contract.yaml`
- `templates/completion-report.yaml`
- `templates/quality-gate-report.yaml`
- `templates/impact-report.yaml`
- `templates/feature-plan.yaml`
- `templates/blocker-report.yaml`
- `templates/release-candidate.yaml`

Documentation and role files reference these templates rather than defining competing schemas.

## Task readiness

A task may enter `Ready` only when all are true:

- goal and definition of done are testable
- accountable owner and mode are declared
- allowed and forbidden scopes are explicit and non-overlapping
- dependencies are complete or explicitly mocked
- consumed contracts are stable enough to use
- controlled artifacts the task may change are named
- required checks are executable and proportionate to risk
- branch base and workspace strategy are known
- unresolved decisions cannot change the implementation materially

If any condition is false, keep the task in `Backlog` or `Blocked`; do not compensate with assumptions.

## Lifecycle and transition gates

MAD uses two state machines: one for executable tasks and one for the source work item/release candidate.

### Executable task state machine

```text
Draft -> Ready -> Running -> Candidate -> Verifying -> Verified -> Integrating -> Integrated -> Closed
                         \-> Blocked <-/          \-> ChangesRequested -> Running
Candidate|Verified -> Invalidated -> Ready
Any nonterminal -> Failed | Cancelled
```

| Transition | Authority | Required evidence |
|---|---|---|
| `Draft -> Ready` | workstream | valid task contract and satisfied readiness rules |
| `Ready -> Running` | workstream/assigned owner | isolated clean workspace or declared read-only/artifact mode; expected branch/base; dependencies available |
| `Running -> Candidate` | assigned owner | valid completion report; immutable candidate revision; scope evidence; required checks passed for `completed` status |
| `Candidate -> Verifying` | workstream/QA | completion handoff accepted for independent review |
| `Verifying -> Verified` | QA | quality-gate decision `pass` or `pass_with_notes`; exact candidate revision matches completion revision |
| `Verifying -> ChangesRequested` | QA | failed QA report with concrete fixes and revalidation scope |
| `Verified -> Integrating` | workstream/release | dependency order and impact/revalidation are current |
| `Integrating -> Integrated` | release | integration step evidence for the exact candidate or new integration revision |
| `Integrated -> Closed` | workstream/release + required human approval where applicable | final traceability, release candidate, rollback statement, and approval reference |
| `* -> Blocked` | any owner | blocker report naming class, evidence, owner, and restart condition |
| `Candidate|Verified -> Invalidated` | workstream/QA/release | changed candidate SHA, input digest, controlled contract, or required environment invalidates prior evidence |

### Source work-item state machine

```text
Proposed -> Planned -> Executing -> ReleaseCandidate -> AwaitingApproval -> Released
Any nonterminal -> Blocked | Abandoned
```

The work item advances from task evidence. It must not be marked `ReleaseCandidate` until all included executable tasks are `Verified` or explicitly excluded.

Transition events SHOULD be append-only and compare against the task/work-item revision last observed by the actor. A stale actor must publish evidence or a blocker; it must not overwrite newer state.

`pass_with_notes` permits integration only when every note is non-blocking, owned, and recorded as a follow-up. A warning never overrides a failed required check.

Use Hermes gates when the integration is installed:

```bash
hermes mad gate <kanban-task-id> --stage review
hermes mad gate <kanban-task-id> --stage integration
hermes mad gate <kanban-task-id> --stage done
```

These commands verify artifacts; they do not replace human judgment for product, security, compatibility, or release risk.

## Workspace modes

| Mode | Use | Branch requirement |
|---|---|---|
| `write_isolated` | coding or any source-modifying task | unique task branch/worktree required |
| `read_only_checkout` | QA or inspection of an immutable revision | no product branch mutation; publish attestation artifact only |
| `artifact_only` | planning, architecture, reports, contracts outside product repo | no product branch unless artifact storage requires one |
| `integration` | release convergence | unique integration branch/worktree required |

The one-branch rule applies to write ownership. It does not require QA to mutate the candidate branch or architecture tasks to create product branches when they only produce artifacts.

## Evidence policy

Evidence strength, from strongest to weakest:

1. reproducible command output or CI result from the reviewed revision
2. direct diff/artifact inspection
3. deterministic validator or static analysis output
4. documented manual observation with environment and steps
5. another agent's claim

Gate decisions must rely on levels 1–4. Level 5 identifies what to verify.

For every required check record:

- exact command or review method
- revision/environment when relevant
- result: `passed`, `failed`, or `not_run`
- concise evidence or output reference
- reason and consequence when `not_run`

A task is not `completed` when a required check failed or could not run, unless the contract explicitly defines alternative evidence and that evidence passed.

## Controlled contracts and impact

Contracts include APIs, schemas, events, commands, persistence shapes, UI interfaces, configuration, infrastructure interfaces, and migration behavior.

When a controlled artifact changes:

1. classify it as `internal`, `additive`, `behavioral`, `breaking`, or `unclear`
2. identify producers and consumers using `.agents/contracts.yaml`
3. generate or update the impact report
4. mark affected work stale until revalidated
5. require explicit approval for breaking or unclear changes

Prefer expand-and-contract migration over synchronized breaking changes.

## Status semantics

- `completed`: definition of done met and required evidence passed
- `partial`: useful scoped output exists, but definition of done is not met
- `blocked`: progress requires an external decision, dependency, permission, or scope change
- `failed`: attempted execution produced a defect or failed evidence that must be corrected
- `cancelled`: authority intentionally stopped the task before completion

Only `completed` work may request QA. A `partial` report is a handoff, not approval to integrate.

## Failure taxonomy

Every blocker or failure classifies the condition:

| Class | Meaning | Default disposition |
|---|---|---|
| `input` | missing/contradictory requirement, contract, acceptance criterion, or artifact | block until owner supplies authoritative input |
| `dependency` | required task, artifact, service, package, or environment is unavailable/stale | block or invalidate dependent work |
| `policy` | requested action exceeds authority, scope, or human approval boundary | stop and request recorded approval/amendment |
| `test` | required evidence fails against the candidate | fail/changes requested |
| `tool` | local toolchain cannot produce trustworthy evidence | block unless approved equivalent evidence exists |
| `infrastructure` | external platform/CI/network/resource failure prevents validation | block with retry owner and restart condition |
| `security` | unresolved security/privacy/compliance/data-loss risk | block; human/security authority required |
| `conflict` | branch/content/integration conflict prevents safe continuation | block or return to owner depending on semantic ownership |

Reports include retryability, owner, evidence references, resolution condition, resume state, and preserved artifacts when applicable. Skipped required checks produce `blocked` or `failed`, never `pass_with_notes`.

## Escalation protocol

Stop at the safe point, preserve evidence, and return a blocker report when:

- requirements or acceptance criteria conflict
- required scope is forbidden or ownership is ambiguous
- a dependency or consumed contract changed
- a breaking or unclear contract decision is needed
- security, privacy, compliance, accessibility, financial, data-loss, or migration risk is unresolved
- required validation cannot produce trustworthy evidence
- integration conflict is semantic rather than mechanical
- credentials, permissions, or human authorization are required

A blocker report must state: what is blocked, evidence, impact, the minimum decision/input needed, safe options if known, and the exact restart condition.

## Handoff minimum

Every handoff identifies:

- task ID, owner, branch, workspace, and exact revision
- status and gate requested
- changed files and controlled artifacts
- checks and results
- assumptions, residual risks, blockers, and downstream impact
- next accountable role and requested action

The receiver validates the handoff before acting. Missing evidence returns to the sender; it is not reconstructed by guesswork.

## Skill routing

| Situation | Required skill |
|---|---|
| Orchestrate board flow and execution waves | `workstream-management` |
| Convert intent into specs and bounded tickets | `spec-and-ticket-decomposition` |
| Produce or validate executable work packets | `task-contracts` |
| Create, verify, or clean isolated workspaces | `repository-workspaces` |
| Define or change shared interfaces | `contracts-and-interfaces` |
| Implement scoped changes | `coding-standards` |
| Implement or assess UI behavior | `frontend-design-system` |
| Select evidence and issue a gate decision | `testing-and-quality-gates` |
| Determine affected consumers and revalidation | `change-impact-analysis` |
| Complete, block, or transfer responsibility | `completion-and-handoff` |

Load only the skills required by the task's branch of work; mandatory safety and reporting skills are never optional.
