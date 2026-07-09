---
name: coding-standards
description: "guide safe coding work for coding agents across backend, frontend, mobile, infrastructure, data, and tooling tasks. use when the coding-agent writes code, edits configuration, adds tests, follows existing patterns, or decides whether to stop because the task scope is insufficient."
---

# Coding Standards

Use this skill while implementing assigned work.

## Working method

1. Read the task contract.
2. Confirm workspace, branch, allowed scope, forbidden scope, and required checks.
3. Inspect nearby existing patterns before adding new patterns.
4. Keep the change focused.
5. Avoid unrelated refactoring.
6. Update tests for changed behavior.
7. Run required checks or state why they could not run.
8. Report assumptions and downstream impact.

## Backend mode

Follow existing service, handler, adapter, repository, job, and domain patterns. Do not alter shared contracts or persistence shape unless explicitly allowed.

## Frontend mode

Use project components, design tokens, client patterns, routing conventions, state management, validation rules, and UI tests. Also use `frontend-design-system`.

## Mobile mode

Follow the stack declared in the task contract. Do not mix Flutter, React Native, iOS native, or Android native patterns unless the project already does so.

## Infrastructure and data mode

Treat config, deployment, migrations, pipelines, permissions, and data movement as high-impact changes. Include validation and rollback notes.

## Stop conditions

Stop and return a blocker report when required behavior is unclear, forbidden scope is needed, a shared contract must change, tests cannot be executed or approximated, or security/data-loss/compliance risk appears.
