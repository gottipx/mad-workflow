# Playbook: web
<!-- Example for a React + Vite stack. Adapt to STACK.md. -->

## Scope
Web screens, components, forms, client-side state and API calls.

## Tools
- Dev server: `pnpm dev` (from app/)
- Browser: open the page and take a screenshot of every screen you change.
- Run tests: `pnpm test -- web/` (from app/)

## Boundaries
- Edit:  app/web/src/
- Read:  app/contracts/, mad/MAP.md, mad/SPEC.md, mad/STACK.md
- Never: app/api/, app/db/, app/contracts/ (ask instead), any .env file

## How we build
- Call the API only through the typed client in app/web/src/api/, built on app/contracts/.
- One component per file. Keep components small; move logic into hooks.
- Every screen handles three states: loading, error, empty.

## Traps
- Missing loading and error states: the screen looks fine in tests and broken on a slow network.
- Hard-coded API URLs: always read them from the environment config.

## Testing
- Component tests for logic and form validation.
- Check each screen at phone width (about 400px) and desktop width.

## Proof of done
- Paste the test output.
- Attach a screenshot of every changed screen, phone and desktop width.

## When to ask
- The contract doesn't give you the data a screen needs.
- The spec doesn't say how something should look or behave.
- The card is unclear or seems wrong.
