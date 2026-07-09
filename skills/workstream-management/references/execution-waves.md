# Execution Waves

Use waves to keep parallel work safe.

## Wave 1: Shape

Architect-agent clarifies requirements, creates the Specification or delivery brief, defines contracts, and identifies design or platform constraints.

## Wave 2: Build

Coding-agent implements bounded task contracts in isolated workspaces. Start only when consumed contracts are stable enough or explicitly mocked.

## Wave 3: Prove

QA-agent validates the branch against acceptance criteria, tests, contracts, security, accessibility, performance, and design-system expectations.

## Wave 4: Release

Release-agent integrates QA-approved branches in dependency order, runs final gates, and prepares the merge artifact.

## Revalidation

When a shared artifact changes, the workstream-agent identifies consumers and creates revalidation tasks before release integration.
