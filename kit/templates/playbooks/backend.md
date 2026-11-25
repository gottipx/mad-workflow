# Playbook: backend
<!-- Example for a Supabase + Cloudflare Workers stack. Adapt to STACK.md. -->

## Scope
API routes, database schema and migrations, server-side logic.

## Tools
- Supabase MCP: DEV project only. Use it to inspect tables and apply migrations.
- wrangler: run the API locally with `wrangler dev`.
- Run tests: `pnpm test -- api/` (from app/, through the pinned toolchain)

## Boundaries
- Edit:  app/api/, app/db/migrations/
- Read:  app/contracts/, mad/MAP.md, mad/SPEC.md, mad/STACK.md
- Never: app/web/, app/ios/, app/contracts/ (ask instead), any .env file

## How we build
- Every schema change is a new numbered migration file. Never edit old ones.
- Validate all request input with the zod schemas from app/contracts/.
- Errors use the format in app/contracts/errors.ts.

## Traps
- Enable Row Level Security on every new table, or all its data is public.
- Supabase returns null, not an error, for missing rows. Check for it.

## Testing
- One integration test per endpoint: the success case plus at least one failure case.

## Proof of done
- Paste the full test output.
- List every new migration file.

## When to ask
- The contract doesn't fit what you need to build.
- A migration would delete or rename existing data.
- The spec or card is unclear or seems wrong.
