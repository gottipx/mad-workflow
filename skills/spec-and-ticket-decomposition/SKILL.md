---
name: spec-and-ticket-decomposition
description: "Transform rough intent into an authoritative, testable specification and coherent dependency-aware task candidates. Use when clarifying requirements, defining non-goals and acceptance criteria, or preparing feature plans before task contracts."
---

# Spec and Ticket Decomposition

Turn intent into execution without hiding decisions in prose.

## Source discipline

Classify every input as:

- approved fact/decision
- repository or contract evidence
- inference to validate
- unresolved question with an owner

Conflicts and missing authority remain explicit. Never resolve business, legal, security-policy, or data-ownership ambiguity by convenience.

## Specification procedure

1. State the problem, affected actors, user/system value, measurable goal, and non-goals.
2. Describe required behavior, failure/recovery behavior, permissions, boundary conditions, and state/data lifecycle where relevant.
3. Identify controlled contracts, owners, producers/consumers, compatibility, migration, and rollback constraints.
4. Capture applicable quality attributes: security/privacy, accessibility, reliability, performance, observability, operability, and compliance.
5. Convert every requirement and material risk into observable acceptance criteria.
6. Separate approved decisions from proposals; list open decisions with consequence and required owner.
7. Check traceability: every approved requirement maps to behavior and evidence; everything else is a non-goal, risk, or open decision.

Completion criterion: implementation behavior is unambiguous, QA can decide pass/fail, and no material decision is disguised as an assumption.

## Acceptance-criterion test

A criterion is valid when it names preconditions, observable action/event, expected result, and critical negative/recovery behavior. Use Given/When/Then when stateful interactions benefit. Replace subjective words with a project policy, threshold, or explicit observation.

## Decomposition procedure

1. Find seams by user-facing outcome, controlled contract, ownership, risk, and independent testability.
2. Build the artifact dependency graph before choosing execution order.
3. Form coherent task bundles: one outcome, one accountable owner type, bounded scope, stable inputs, and independently verifiable completion.
4. Separate architecture/contract decisions, implementation, QA, release, and revalidation when authority differs.
5. Avoid splits that create shared mutable checkout work or repeated edits to high-conflict files.
6. For each candidate, provide goal, scope/out-of-scope, dependencies, consumed/produced contracts, definition of done, and required evidence.
7. Group candidates into execution waves and flag which tasks may safely run in parallel.
8. Validate coverage: every acceptance criterion and controlled change has an owner; no task exists without a requirement/risk trace.

Completion criterion: the candidate graph covers the specification exactly—no missing requirement and no speculative task.

## External accelerators

Use `to-spec` or `to-tickets` when available, then apply this skill's source, acceptance, decomposition, and completeness tests. Their output is draft until it passes these gates.

## Output

Produce a compact specification, candidate tasks, dependency graph, wave plan, controlled-contract notes, risk register, and open decisions. The workstream agent owns final task contracts and assignment.
