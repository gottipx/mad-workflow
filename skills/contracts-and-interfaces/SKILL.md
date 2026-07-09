---
name: contracts-and-interfaces
description: "apply contract-first delivery for shared interfaces such as apis, schemas, events, commands, ui props, client models, platform contracts, and integration boundaries. use when defining, changing, consuming, or validating shared contracts and when classifying compatibility or breaking changes."
---

# Contracts and Interfaces

Use this skill when work crosses a boundary between components, services, clients, data models, platforms, or agents.

## Contract types

- API contract
- data or schema contract
- event or message contract
- command or job contract
- UI component contract
- client DTO or model contract
- configuration or infrastructure contract

## Rules

1. Define or confirm the contract before coding starts.
2. Prefer additive changes.
3. Mark breaking changes explicitly.
4. Identify known consumers.
5. Add or update contract tests when behavior changes.
6. Do not silently change a shared contract from a coding task.

## Compatibility classification

```yaml
change_type: additive | behavioral | breaking | unclear
consumers_impacted: []
required_revalidation: []
```

## Breaking-change handling

Use expand-and-contract when possible:

1. Add new behavior while keeping old behavior.
2. Migrate consumers.
3. Validate all consumers.
4. Remove old behavior only after approval.

## Output

Return the changed contract, compatibility classification, impacted consumers, and required revalidation tasks.
