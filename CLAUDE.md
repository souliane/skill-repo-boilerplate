# Skill Repo Instructions

## Quality Gate (Stop Hook)

This repo uses a **Stop hook** that prevents the agent from completing until all quality gates pass. When you try to finish, `scripts/hooks/verify-completion.sh` runs automatically and checks:

1. **Pre-commit hooks** pass (`prek run --all-files` or `pre-commit run --all-files`)
2. **Tests** pass (`uv run pytest`)
3. **No uncommitted changes** remain

If any gate fails, you'll receive feedback describing what to fix. Address the issues and try again — the hook allows exit on the second attempt to prevent infinite loops.

This pattern is based on the [Ralph Loop](https://github.com/snarktank/ralph) — an autonomous iteration pattern where external verification gates replace self-assessed completion. See also Anthropic's [Effective harnesses for long-running agents](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents) for the broader harness design principles.

## Conventions

- Run `prek run --all-files` before committing (the Stop hook enforces this, but running early catches issues sooner).
- Python scripts use `#!/usr/bin/env -S uv run --script` with inline metadata.
- Skill files follow the [Agent Skills open standard](https://agentskills.io).
