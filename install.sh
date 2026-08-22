#!/usr/bin/env bash
# Model-agnostic install of the texra-lean-skills bundle.
#
# Claude Code needs no script: a repository's .claude/settings.json declares
# the marketplace and plugin, and the session auto-installs on first trust.
# This script serves every other agent that reads SKILL.md directories:
#
#   ./install.sh                 # Codex: symlink into ~/.codex/skills
#   ./install.sh --dir DIR       # any agent: symlink into DIR
#   ./install.sh --copy --dir D  # copy instead of symlink (no live updates)
#
# Idempotent: re-running refreshes the link; `git pull` in this checkout
# updates every linked agent at once.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
MODE="link"
TARGET=""

while [ $# -gt 0 ]; do
  case "$1" in
    --dir)  TARGET="$2"; shift 2 ;;
    --copy) MODE="copy"; shift ;;
    -h|--help) sed -n '2,14p' "$0"; exit 0 ;;
    *) echo "install.sh: unknown argument $1" >&2; exit 2 ;;
  esac
done

if [ -z "$TARGET" ]; then
  TARGET="${CODEX_HOME:-$HOME/.codex}/skills"
fi
mkdir -p "$TARGET"

if [ "$MODE" = "copy" ]; then
  rm -rf "$TARGET/texra-lean-skills"
  cp -R "$HERE/skills" "$TARGET/texra-lean-skills"
  echo "Copied skills to $TARGET/texra-lean-skills (re-run to update)."
else
  ln -sfn "$HERE/skills" "$TARGET/texra-lean-skills"
  echo "Linked $TARGET/texra-lean-skills -> $HERE/skills"
  echo "Update any time with: git -C $HERE pull"
fi
