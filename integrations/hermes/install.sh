#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Install the MAD Workflow Hermes integration.

Usage:
  ./integrations/hermes/install.sh [options]

Options:
  --board <slug>       Kanban board slug to create/use (default: mad-workflow)
  --workdir <path>     Default workdir for the MAD board
  --profiles           Create the five MAD Hermes profiles
  --switch             Switch the active Kanban board to the MAD board
  --no-enable          Copy the plugin but do not enable it
  -h, --help           Show help

What this installs:
  - Hermes plugin: ~/.hermes/plugins/mad-workflow
  - MAD skills:    ~/.hermes/skills/mad-workflow/*

After install, use:
  hermes mad --help
EOF
}

BOARD="mad-workflow"
WORKDIR=""
CREATE_PROFILES=0
SWITCH=0
ENABLE=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    --board)
      BOARD="${2:?--board requires a value}"; shift 2 ;;
    --workdir)
      WORKDIR="${2:?--workdir requires a value}"; shift 2 ;;
    --profiles)
      CREATE_PROFILES=1; shift ;;
    --switch)
      SWITCH=1; shift ;;
    --no-enable)
      ENABLE=0; shift ;;
    -h|--help)
      usage; exit 0 ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2 ;;
  esac
done

if ! command -v hermes >/dev/null 2>&1; then
  echo "Error: hermes command not found. Install Hermes Agent first." >&2
  echo "Docs: https://hermes-agent.nousresearch.com/docs" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
PLUGIN_DEST="$HERMES_HOME/plugins/mad-workflow"
SKILLS_DEST="$HERMES_HOME/skills/mad-workflow"

mkdir -p "$HERMES_HOME/plugins" "$HERMES_HOME/skills"
rm -rf "$PLUGIN_DEST"
cp -R "$ROOT/integrations/hermes/plugin/mad-workflow" "$PLUGIN_DEST"
find "$PLUGIN_DEST" -type d -name __pycache__ -prune -exec rm -rf {} +

echo "Installed plugin to $PLUGIN_DEST"

rm -rf "$SKILLS_DEST"
mkdir -p "$SKILLS_DEST"
for skill_dir in "$ROOT"/skills/*; do
  [[ -d "$skill_dir" && -f "$skill_dir/SKILL.md" ]] || continue
  cp -R "$skill_dir" "$SKILLS_DEST/$(basename "$skill_dir")"
done

echo "Installed MAD skills to $SKILLS_DEST"

if [[ "$ENABLE" -eq 1 ]]; then
  hermes plugins enable mad-workflow >/dev/null || true
  echo "Enabled Hermes plugin: mad-workflow"
else
  echo "Skipped plugin enablement (--no-enable)"
fi

INIT_ARGS=(mad init --board "$BOARD" --install-skills-from "$ROOT")
if [[ -n "$WORKDIR" ]]; then
  INIT_ARGS+=(--workdir "$WORKDIR")
fi
if [[ "$CREATE_PROFILES" -eq 1 ]]; then
  INIT_ARGS+=(--create-profiles)
fi
if [[ "$SWITCH" -eq 1 ]]; then
  INIT_ARGS+=(--switch)
fi

hermes "${INIT_ARGS[@]}"

echo
cat <<EOF
MAD Workflow Hermes integration is ready.

Try:
  hermes mad --help
  hermes mad validate-contract examples/hermes-task-contract.yaml
  hermes mad create-task examples/hermes-task-contract.yaml --board $BOARD
EOF
