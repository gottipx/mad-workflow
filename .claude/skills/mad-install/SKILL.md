---
name: mad-install
description: Install or update the MAD workflow, either the mad command on this machine or MAD in a project folder. Use when the user types /mad-install or asks to install, add or update MAD.
---

# Install MAD

This repo is the MAD source. The installable package lives in `package/`.

- **The `mad` command on this machine** (first time, or after changing MAD): run `npm run install-local` in `package/`. It packs the current source and installs it globally as a real copy.
- **MAD in a project:** run `mad init <folder>` (new project) or `mad update <folder>` (existing MAD project). If no folder was given, ask for it.

Show the user the command's output and the next step it prints. Never edit files in a project beyond what `mad` does.
