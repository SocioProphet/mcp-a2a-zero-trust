#!/usr/bin/env bash
set -euo pipefail

# Fail closed if we're not inside a git worktree
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "ERR: not in a git repo"; exit 2; }

ROOT="$(git rev-parse --show-toplevel)"
MARKER="$ROOT/.repo-root"

# Require an explicit marker file at the git root
[[ -f "$MARKER" ]] || { echo "ERR: missing $MARKER (repo root marker)"; exit 2; }

EXPECTED="$(cat "$MARKER" | tr -d '\r\n')"
BASENAME="$(basename "$ROOT")"

# Require marker content to match repo basename (simple, robust, boring)
[[ "$EXPECTED" == "$BASENAME" ]] || {
  echo "ERR: repo marker mismatch: expected '$EXPECTED' but repo root is '$BASENAME'"
  exit 2
}

echo "OK: repo root verified ($ROOT)"
