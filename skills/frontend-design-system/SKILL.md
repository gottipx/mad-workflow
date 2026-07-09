---
name: frontend-design-system
description: "ensure frontend and mobile ui work follows product design rules, design tokens, approved components, accessibility, responsive behavior, ui states, and interaction patterns. use when implementing or reviewing screens, components, forms, navigation, user flows, or design-to-code tasks."
---

# Frontend Design System

Use this skill for UI implementation and UI review.

## Source priority

1. Project design-system documentation.
2. Existing components and patterns in the codebase.
3. Task-specific design brief.
4. Sensible platform conventions.

Do not invent colors, spacing, typography, icon styles, or component behavior when project rules exist.

## Required UI states

For interactive UI, handle relevant states:

- default
- loading
- empty
- error
- success
- disabled
- validation
- permission denied

## Accessibility baseline

- keyboard reachable controls
- visible focus states
- semantic structure
- labels for inputs and controls
- usable error messages
- sufficient contrast according to project policy

## Responsive baseline

Respect declared breakpoints or platform form factors. Avoid layout that only works at one viewport size unless the task explicitly targets one environment.

## Design review checklist

```yaml
uses_design_tokens:
uses_approved_components:
handles_required_states:
responsive_behavior_checked:
accessibility_checked:
visual_or_interaction_risks:
```

## Output

For UI tasks, return implemented files, states handled, accessibility notes, responsive notes, and any design gaps.
