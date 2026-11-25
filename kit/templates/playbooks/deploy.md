# Playbook: deploy
<!-- Example for Cloudflare + GitHub Actions. Adapt to STACK.md. -->

## Scope
Deployment config, the preview (staging) deploy, and the CI pipeline that deploys production.

## Tools
- wrangler: config in app/wrangler.toml; `wrangler deploy --env preview` for staging.
- GitHub Actions: pipeline files in .github/workflows/ (must stay at the repo root).

## Boundaries
- Edit:  app/wrangler.toml, .github/workflows/, app/scripts/deploy/
- Read:  mad/STACK.md, mad/MAP.md, app/.env.example
- Never: any .env file, production secrets, app code

## How we build
- Preview deploys use dev keys and a separate staging environment.
- Production deploys run only in CI, only on merge to main.
- Production secrets live only in the CI's secret storage. Reference them by name.

## Traps
- A pipeline that deploys on every push instead of only on merge to main.
- Secrets printed in CI logs. Never echo them.

## Testing
- Run the preview deploy once and open the URL.
- Check the pipeline file with the CI's own validation where possible.

## Proof of done
- The preview URL, and the output of the deploy command.
- The list of secret names the pipeline expects (names only).

## When to ask
- You would need a production key to finish the task.
- The hosting setup in STACK.md doesn't match what the provider supports.
