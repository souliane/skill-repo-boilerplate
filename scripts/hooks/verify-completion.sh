#!/usr/bin/env bash
# Stop hook: verify quality gates before allowing the agent to stop.
#
# Returns JSON with decision: "block" + reason when gates fail,
# or exits silently (exit 0, no JSON) to allow stopping.
#
# Prevents infinite loops: if stop_hook_active is true, the agent
# already continued from a previous block — allow exit this time.

set -euo pipefail

INPUT=$(cat)

# Prevent infinite loops — if we already blocked once and the agent
# continued, let it stop now regardless of gate results.
if [ "$(echo "$INPUT" | jq -r '.stop_hook_active // false')" = "true" ]; then
  exit 0
fi

REPO_ROOT=$(echo "$INPUT" | jq -r '.cwd // empty')
[ -n "$REPO_ROOT" ] || REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

cd "$REPO_ROOT"

# Collect failures
failures=()

# Gate 1: pre-commit hooks (prek or pre-commit)
if command -v prek &>/dev/null; then
  if ! prek run --all-files &>/dev/null; then
    failures+=("prek run --all-files failed — fix lint/format/type errors")
  fi
elif command -v pre-commit &>/dev/null; then
  if ! pre-commit run --all-files &>/dev/null; then
    failures+=("pre-commit run --all-files failed — fix lint/format/type errors")
  fi
fi

# Gate 2: tests
if [ -f pyproject.toml ] && grep -q "pytest" pyproject.toml 2>/dev/null; then
  if ! uv run python -m pytest --no-header -q &>/dev/null; then
    failures+=("pytest failed — fix failing tests")
  fi
fi

# Gate 3: uncommitted changes
if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
  failures+=("uncommitted changes — commit or stash before stopping")
fi

# All gates passed — allow stop
if [ ${#failures[@]} -eq 0 ]; then
  exit 0
fi

# Gates failed — block with reason
reason=$(printf '%s\n' "${failures[@]}" | sed 's/^/- /' | tr '\n' ' ')
cat <<EOF
{"decision": "block", "reason": "Quality gates failed:\n${reason}\nFix these issues before completing."}
EOF
