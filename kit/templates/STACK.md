# STACK: <project name>

Every decision has a reason and an alternative, so anyone can see later why it was chosen.
The software lives in the app folder from mad/config/mad.yaml (default `app/`).

## <Area, e.g. Database + login>: <Choice>
Why:         <reason>
Alternative: <other option, and its trade-off>
Decision:    ✅ <Choice>

## <Area>: <Choice>
Why:         <reason>
Alternative: <other option>
Decision:    ✅ <Choice>

## Toolchain
Manager:  <mise | pixi | none>, config in `<app>/mise.toml` (or `pixi.toml`)
Packages: <npm | pnpm | uv>, lockfile committed
Pinned:   <e.g. node 22.11, python 3.12, wrangler 3.x, supabase CLI 2.x>
Why:      every worker worktree gets the same tool versions.

## Commands (run from the app folder)
- Install:    `<command, e.g. mise install && pnpm install>`
- Test:       `<command>`
- Build:      `<command>`
- Smoke test: `<command that starts the app and checks the main page loads>`

## Environments
- Dev / preview: <where, which dev project>
- Production:    deployed only by CI after merge to main
