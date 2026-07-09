---
name: task-contracts
description: "create precise task contracts for agents, including goal, scope, dependencies, consumed and produced contracts, allowed files, forbidden files, definition of done, checks, and report format. use before assigning coding, qa, release, architecture, or workstream tasks to an agent."
---

# Task Contracts

Use this skill to create strict work packets for agents.

## Principle

A task contract must make work executable without hidden context. It defines what the agent may change, what it must not change, and how completion is proven.

## Required schema

```yaml
task_id:
source_item:
owner_agent:
goal:
context:
mode: architecture | coding | qa | release | revalidation
allowed_scope:
forbidden_scope:
dependencies:
contracts_consumed:
contracts_produced_or_modified:
definition_of_done:
required_checks:
report_format:
```

## Scope rules

- `allowed_scope` must be specific enough to prevent broad edits.
- `forbidden_scope` must include shared contracts, migrations, config, generated files, or release files unless the task owns them.
- If an agent needs forbidden scope, it must stop and report blocked.

## Definition of Done rules

Every DoD must include delivered behavior, tests or validation evidence, checks run, completion report, and downstream impact statement.

## Task size

A task should be small enough for one focused branch and large enough to deliver a coherent, testable outcome.
