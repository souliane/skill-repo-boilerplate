#!/usr/bin/env bash
# Pre-commit hook: block commits containing banned terms.
#
# Usage: check-banned-terms.sh [--config PATH] FILE...
#
# Reads BANNED_TERMS (comma-separated, case-insensitive) from the config file
# named by --config (default: ~/.banned-terms). The config is a sourced env
# file, so an optional `export ` prefix is tolerated. Keeping the term list in
# a machine-local file (never in the repo) is what lets this generic hook ship
# in a public boilerplate without leaking the terms it enforces.
#
# Exits 0 (pass) if the config is missing or defines no terms, or if no term is
# found. Exits 1 (fail) if any banned term appears in a scanned file.
set -euo pipefail

CONFIG="${HOME}/.banned-terms"

# Parse flags; every remaining positional arg is a file to scan. Consuming the
# flags here is what stops `--config`/its value from leaking into the file loop.
files=()
while [ "$#" -gt 0 ]; do
  case "$1" in
    --config)
      CONFIG="${2:-}"
      shift 2
      ;;
    --config=*)
      CONFIG="${1#--config=}"
      shift
      ;;
    *)
      files+=("$1")
      shift
      ;;
  esac
done

# pre-commit passes the entry verbatim, so a leading ~ arrives unexpanded.
case "$CONFIG" in
  "~") CONFIG="$HOME" ;;
  "~/"*) CONFIG="$HOME/${CONFIG#\~/}" ;;
esac

# No config → nothing to check.
[ -n "$CONFIG" ] && [ -f "$CONFIG" ] || exit 0

# Extract the BANNED_TERMS value (comma-separated).
# `|| true` so a no-match grep does not abort under `set -o pipefail`/`set -e`
# when the config exists but defines no banned terms.
TERMS=$(grep -E '^(export[[:space:]]+)?BANNED_TERMS=' "$CONFIG" 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d "'" || true)
[ -n "$TERMS" ] || exit 0

# Build grep pattern: word-boundary match for each term.
PATTERN=""
IFS=',' read -ra TERM_ARRAY <<< "$TERMS"
for term in "${TERM_ARRAY[@]}"; do
  term=$(echo "$term" | xargs)  # trim whitespace
  [ -n "$term" ] || continue
  [ -n "$PATTERN" ] && PATTERN="$PATTERN|"
  PATTERN="$PATTERN\\b${term}\\b"
done
[ -n "$PATTERN" ] || exit 0

# Nothing staged to scan.
[ "${#files[@]}" -gt 0 ] || exit 0

# Check staged files.
FOUND=0
for file in "${files[@]}"; do
  [ -f "$file" ] || continue
  if grep -iEn "$PATTERN" "$file" 2>/dev/null; then
    echo "^^^ Banned term found in: $file"
    echo "These terms must not appear in this repo."
    echo "Configured in: $CONFIG (BANNED_TERMS)"
    echo ""
    FOUND=1
  fi
done

exit "$FOUND"
