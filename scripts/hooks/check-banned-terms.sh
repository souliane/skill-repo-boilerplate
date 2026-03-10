#!/usr/bin/env bash
# Pre-commit hook: block commits containing banned terms.
#
# Reads T3_BANNED_TERMS from ~/.teatree (comma-separated, case-insensitive).
# Exits 0 (pass) if no banned terms found or if config is missing.
# Exits 1 (fail) if any banned term appears in staged files.
set -euo pipefail

CONFIG="$HOME/.teatree"

# No config → nothing to check.
[ -f "$CONFIG" ] || exit 0

# Extract T3_BANNED_TERMS value (comma-separated).
TERMS=$(grep -E '^T3_BANNED_TERMS=' "$CONFIG" 2>/dev/null | head -1 | cut -d'=' -f2- | tr -d '"' | tr -d "'")
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

# Check staged files.
FOUND=0
for file in "$@"; do
  [ -f "$file" ] || continue
  if grep -iEn "$PATTERN" "$file" 2>/dev/null; then
    echo "^^^ Banned term found in: $file"
    echo "These terms must not appear in this repo."
    echo "Configured in: $CONFIG (T3_BANNED_TERMS)"
    echo ""
    FOUND=1
  fi
done

exit "$FOUND"
