#!/usr/bin/env -S uv run --script
# /// script
# dependencies = []
# requires-python = ">=3.12"
# ///
"""Auto-update the skills catalogue in README.md from SKILL.md frontmatter.

This repo owns the generator: other skill repos run it as the
``update-readme-skills`` hook published by ``.pre-commit-hooks.yaml`` instead of
keeping a copy that drifts. pre-commit and prek both run hooks from the
consuming repo's root, so the catalogue is built from the current working
directory rather than from wherever this file happens to live.
"""

import re
import subprocess
import sys
from pathlib import Path

README_NAME = "README.md"

BEGIN = "<!-- BEGIN SKILLS -->"
END = "<!-- END SKILLS -->"
FRONTMATTER_RE = re.compile(r"^---\s*\n(.+?)\n---", re.DOTALL)
TRIGGER_SEPARATORS = (". Triggers:", ". Use when", ". Use this")


def _parse_frontmatter(path: Path) -> dict[str, str]:
    """Extract YAML-ish key: value pairs from SKILL.md frontmatter.

    Handles YAML folded (``>``) / literal (``|``) scalars and one level of
    nested mapping (e.g., ``metadata: {version: ...}``). Nested keys are stored
    with dotted names (``metadata.version``).
    """
    m = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not m:
        return {}
    meta: dict[str, str] = {}
    current_key: str | None = None
    nested_parent: str | None = None
    for line in m.group(1).splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if ":" in line and not line[0].isspace():
            k, v = line.split(":", 1)
            current_key = k.strip()
            nested_parent = None
            v_clean = v.strip().strip('"').strip("'")
            if v_clean in {">", "|", ">-", "|-"}:
                meta[current_key] = ""
            elif not v_clean:
                meta[current_key] = ""
                nested_parent = current_key
            else:
                meta[current_key] = v_clean
        elif nested_parent is not None and line[:2].isspace() and ":" in stripped:
            k, v = stripped.split(":", 1)
            meta[f"{nested_parent}.{k.strip()}"] = v.strip().strip('"').strip("'")
        elif current_key is not None and line[:1].isspace() and stripped:
            existing = meta.get(current_key, "")
            meta[current_key] = f"{existing} {stripped}".strip() if existing else stripped
    return meta


def _is_repo_owned(path: Path, root: Path) -> bool:
    """Reject ``SKILL.md`` files under dot-directories (``.venv``, caches, …)."""
    return not any(part.startswith(".") for part in path.relative_to(root).parts)


def _skill_md_files(root: Path) -> list[Path]:
    """Return tracked, repo-owned ``SKILL.md`` files under ``root``, sorted by path.

    Uses ``git ls-files`` so untracked or gitignored files never leak into the
    catalogue (an ``rglob`` scan once shipped a phantom ``typer`` entry from an
    untracked scratch dir). Falls back to a filesystem walk outside a git repo
    (e.g. a test ``tmp_path``) so the generator still works there.
    """
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    found = (
        sorted(root.rglob("SKILL.md"))
        if result.returncode != 0
        else sorted(root / line for line in result.stdout.split("\0") if line.endswith("SKILL.md"))
    )
    return [path for path in found if _is_repo_owned(path, root)]


def _short_description(description: str) -> str:
    """Drop the trigger clause, unless the description opens with one."""
    short = description
    for separator in TRIGGER_SEPARATORS:
        if separator in short and not short.startswith(separator.lstrip(". ")):
            short = short.split(separator)[0]
    return short


def _build_table(root: Path) -> str:
    """Render the catalogue as a markdownlint ``compact``-style table (MD060)."""
    rows = ["| Skill | Version | Description |", "| --- | --- | --- |"]
    for skill_md in _skill_md_files(root):
        meta = _parse_frontmatter(skill_md)
        name = meta.get("name", skill_md.parent.name)
        version = meta.get("metadata.version") or meta.get("version", "—")
        rows.append(f"| `{name}` | {version} | {_short_description(meta.get('description', ''))} |")
    return "\n".join(rows)


def update_readme(root: Path) -> int:
    """Rewrite the catalogue between the markers; return 1 when anything changed."""
    readme_path = root / README_NAME
    if not readme_path.exists():
        print(f"Error: {readme_path} not found", file=sys.stderr)
        return 1

    text = readme_path.read_text(encoding="utf-8")

    if BEGIN not in text or END not in text:
        print(f"Error: {README_NAME} missing {BEGIN} / {END} markers", file=sys.stderr)
        return 1

    before = text[: text.index(BEGIN) + len(BEGIN)]
    after = text[text.index(END) :]
    new_text = before + "\n" + _build_table(root) + "\n" + after

    if text == new_text:
        return 0

    readme_path.write_text(new_text, encoding="utf-8")
    print(f"Updated {README_NAME} skills catalogue")
    return 1  # signal pre-commit that the file was modified


def main() -> int:
    return update_readme(Path.cwd())


if __name__ == "__main__":
    sys.exit(main())
