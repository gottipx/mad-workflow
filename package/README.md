# mad-workflow

MAD, the Multi-Agent Development workflow. A coordinator turns your idea into a spec and small task cards; workers build them in parallel, each in its own git worktree, on Claude Code, Codex or OpenCode, coordinated by [Orca](https://orca.dev). You decide at four gates.

**Docs:** https://gottipx.github.io/mad-workflow/ · **Source:** https://github.com/gottipx/mad-workflow

## Install

Needs Node.js 18.17+, git, and Orca. Works on macOS, Linux and Windows.

```bash
npm install -g mad-workflow
```

## Use

```bash
cd my-project
mad init
```

Then start your agent in that folder, inside Orca, on a high-end model:

| Agent | Start MAD with |
|---|---|
| Claude Code | `/mad` |
| Codex | `$mad`, or ask "start MAD" |
| OpenCode | ask "start MAD" |

## Commands

```
mad init [folder]     set up MAD in a folder (default: current folder)
mad update [folder]   update MAD's own files in a project, keep everything else
mad clean [--dry-run] remove finished task worktrees and branches
mad models            list installed agents and the models each offers
mad version           show the installed version
```

## License

MIT
