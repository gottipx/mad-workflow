# Rules for every worker

These rules are included in every worker's message, whatever agent it runs in.

## Where things are
- The software lives in the app folder (see mad/config/mad.yaml, default `app/`).
- What we build: mad/SPEC.md. How we build it: mad/STACK.md.
- Map of the code: mad/MAP.md. Read it instead of exploring.
- Commands (install, test, build, smoke test): mad/STACK.md → Commands.

## Save tokens
- Read only what your task needs: your card's Context files, the files you own, mad/MAP.md and the contracts you use.
- Don't scan or read the whole repository. If you can't find something, ask.
- Don't read anything in mad/ except the files named above.

## Rules
- Stay inside the files your task card owns.
- Never change files in contracts/ unless your card owns them. Ask instead.
- Run tools through the pinned toolchain (mise or pixi, see mad/STACK.md). Never install global tools.
- Add libraries only with the project's package manager, and only if your card needs them.
- Never read, print or commit secrets. Never touch .env files.
- Never use production credentials. Only dev and preview environments.
- Run the tests once when your work is done, not after every edit. Report with proof, not claims.
- If the same command fails 3 times, stop and ask with the error output.
- If something is unclear or seems wrong, ask instead of guessing.

## Lessons
<!-- The retro adds project-wide lessons here, one line each. -->
