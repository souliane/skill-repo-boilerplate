# Contributor Guidelines

## Repo Structure

```text
my-skill/SKILL.md       Skill definition
my-skill/references/    Skill-specific reference docs (one level deep)
my-skill/scripts/       Skill-specific scripts
scripts/                Shared repo-level scripts and hooks
tests/                  Tests for scripts
```

## Skill Files

- `SKILL.md` is the entry point. Keep it focused on workflow and rules.
- Move detailed content to `references/` -- one level deep only.
- Never change `version:` in YAML frontmatter -- auto-managed.

## Python Scripts

All scripts must follow these conventions:

1. **uv shebang:** `#!/usr/bin/env -S uv run --script`
2. **Inline metadata:** `# /// script` block with `dependencies` list (even if empty)
3. **Typer for CLI:** `typer>=0.12` in inline deps -- no raw `sys.argv` or `argparse`
4. **Single entry point:** each skill's CLI lives in `my-skill/scripts/cli.py`
5. **Type annotations:** `ty-check` runs on all files -- use `str | None` not `Optional[str]`
6. **4-space indentation** everywhere (matches `.editorconfig`)
7. **Make executable:** `chmod +x` the script file

## Testing

- **100% coverage required** -- enforced by `pytest-cov` (`fail_under = 100` in pyproject.toml).
- Run tests: `uv run pytest`
- Pre-commit: `prek run --all-files`

## Quality Gate (Stop Hook)

This repo uses a Stop hook that prevents the agent from completing until all
quality gates pass. When you try to finish, `scripts/hooks/verify-completion.sh`
runs automatically and checks:

1. Pre-commit hooks pass (`prek run --all-files`)
2. Tests pass (`uv run pytest`)
3. No uncommitted changes remain

If any gate fails, address the issues and try again.
