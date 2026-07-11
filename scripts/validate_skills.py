#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# requires-python = ">=3.13"
# ///
"""Validate that every SKILL.md has the required frontmatter fields.

The README catalogue generator (``update_readme_skills.py``) silently falls
back to defaults when ``name``/``description`` are missing, so a broken
SKILL.md never surfaces there. This hook is the gate: it fails the commit
when a skill's frontmatter is missing or incomplete.

Required fields mirror the contract enforced by the codebase-review tooling:
``name`` and ``description`` must be present and non-empty, and a
``metadata:`` block must exist.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
REQUIRED_FIELDS = ("name", "description")


def _frontmatter_lines(text: str) -> list[str] | None:
    """Return the lines between the opening and closing ``---`` fences."""
    if not text.startswith("---"):
        return None
    lines = text.splitlines()
    for end, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:end]
    return None


def _validate(skill_md: Path) -> list[str]:
    block = _frontmatter_lines(skill_md.read_text(encoding="utf-8"))
    if block is None:
        return ["missing or unterminated YAML frontmatter"]
    keys: dict[str, str] = {}
    has_metadata = False
    for line in block:
        if line and not line[0].isspace() and ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            keys[key] = value.strip().strip('"').strip("'")
            if key == "metadata":
                has_metadata = True
    errors = [f"missing or empty required field: {field}" for field in REQUIRED_FIELDS if not keys.get(field)]
    if not has_metadata:
        errors.append("missing required field: metadata")
    return errors


def main() -> int:
    # Skip dot-dirs (.venv, vendored copies, etc.) so only real skills are checked.
    skill_files = sorted(
        p for p in ROOT_DIR.rglob("SKILL.md") if not any(part.startswith(".") for part in p.relative_to(ROOT_DIR).parts)
    )
    if not skill_files:
        return 0
    failed = False
    for skill_md in skill_files:
        for error in _validate(skill_md):
            print(f"{skill_md.relative_to(ROOT_DIR)}: {error}")
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
