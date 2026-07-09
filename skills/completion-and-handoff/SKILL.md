---
name: completion-and-handoff
description: "standardize agent completion reports, blocker reports, handoff notes, board comments, qa findings, and release summaries. use whenever an agent finishes work, cannot proceed, transfers context, or returns evidence to the workstream-agent or another agent."
---

# Completion and Handoff

Use this skill whenever an agent reports status.

## Completion report

```yaml
task_id:
owner_agent:
status: completed
branch:
workspace:
changed_files:
contracts_changed:
tests_run:
test_result:
assumptions:
downstream_impact:
recommended_next_actions:
```

## Blocker report

```yaml
task_id:
owner_agent:
status: blocked
blocker_type: missing_input | forbidden_scope | dependency_changed | failing_checks | unclear_requirement | other
summary:
evidence:
needed_decision:
recommended_next_actions:
```

## Handoff rules

- Be specific enough that the next agent can act without rereading everything.
- Mention files, commands, branches, contracts, and decisions.
- Do not claim tests passed unless they were run.
- If checks were skipped, state why and what should run next.

## Final release summary

Include source item, included tasks, branches, checks run, risks, known follow-ups, and human approval requirement.
