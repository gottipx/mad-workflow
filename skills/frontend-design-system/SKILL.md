---
name: frontend-design-system
description: "Implement or review frontend/mobile work using the product's approved design system, complete interaction states, semantic accessibility, responsive behavior, and evidence at the right layers. Use for any task that changes user-visible UI or interaction."
---

# Frontend Design System

The repository's design system, component library, tokens, patterns, and accessibility policy are authoritative. Do not invent a parallel visual language.

## Discovery

1. Identify target users, journey, devices/form factors, localization, and permissions.
2. Inspect approved components, tokens, layout primitives, interaction patterns, and nearby screens.
3. Read acceptance criteria and list applicable states: initial, loading, empty, success, error, validation, disabled, permission-denied, offline/stale, and destructive recovery.
4. Identify data contracts, async/race behavior, analytics, security/privacy, performance budgets, and browser/platform support.
5. Stop when product behavior or design authority is missing and would materially change the experience.

Completion criterion: the intended experience and its edge states can be implemented without inventing product or visual policy.

## Implementation procedure

1. Use existing semantic component and token APIs before custom markup/styles.
2. Keep data/domain behavior separate from presentation while preserving a clear local module boundary.
3. Implement relevant states explicitly; never let loading, failure, empty, or denied cases emerge accidentally.
4. Preserve user input and focus through recoverable errors where safe.
5. Handle async cancellation, stale responses, duplicate actions, optimistic rollback, and destructive confirmation when triggered.
6. Implement responsive behavior from content constraints rather than fixed screenshots.
7. Validate incrementally with component/unit evidence, integration/e2e journeys, and targeted visual/manual review.
8. Inspect for design-system drift, duplicated components, hard-coded tokens, and accessibility regressions.

## Accessibility gate

Where relevant, verify:

- native semantics before ARIA and valid accessible names
- logical keyboard order, visible focus, and no traps
- focus movement/restoration for dialogs, navigation, errors, and dynamic content
- labels, instructions, validation linkage, and error summary/announcement
- contrast and non-color cues under project policy
- touch target and zoom/reflow behavior
- motion preferences and media alternatives
- screen-reader state/relationship communication

Automation assists but does not replace keyboard and semantic inspection.

## Visual and responsive gate

Verify approved typography, spacing, color, elevation, iconography, density, and component variants. Check narrow, nominal, and wide layouts plus content expansion/localization. Avoid brittle coordinates, unnecessary absolute positioning, ad-hoc breakpoints, and custom components that duplicate approved primitives.

## Evidence matrix

| Concern | Preferred evidence |
|---|---|
| pure logic/state reducer | unit/component test |
| component states and events | component/integration test |
| critical user journey | e2e test |
| semantics/keyboard/focus | automated a11y plus manual inspection |
| visual layout/responsiveness | rendered inspection or approved visual regression |
| performance | representative measurement against budget |

Screenshots prove appearance only; they do not prove semantics, keyboard behavior, persistence, or backend correctness.

## Review gate

Reject UI work for missing required states, invented styles/components, hard-coded design values, inaccessible interaction, unstable async behavior, unhandled destructive recovery, broken responsive/content expansion, missing critical journey evidence, or client/server contract drift.

## Handoff

Report components/screens changed, states covered, design-system APIs used, accessibility evidence, responsive/form-factor checks, critical journeys, known platform gaps, screenshots/visual references when useful, and any approved deviations with owner.
