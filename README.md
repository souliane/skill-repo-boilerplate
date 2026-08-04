# my-skills

AI agent skills — composable workflow automation as structured markdown.

## Available Skills

<!-- BEGIN SKILLS -->
| Skill | Version | Description |
| --- | --- | --- |
| `my-skill` | 0.0.1 | Description of what this skill does and when to use it. |
<!-- END SKILLS -->

## Installation

### Consumer install

Use `npx skills add` when you want a managed install and do not plan to edit the repo locally:

```bash
npx skills add https://github.com/YOUR_USERNAME/my-skills --skill '*' -g -y
```

If you want multiple agent runtimes at once, pass them explicitly:

```bash
npx skills add https://github.com/YOUR_USERNAME/my-skills --skill '*' -g -y --agent claude-code codex cursor github-copilot
```

### Contributor mode

Contributor mode means your agent reads the live git clone directly, so review and retro improvements land in version-controlled files that you can commit.

If you cloned the repo locally and want that behavior, symlink the skill directories you contribute to into the agent runtimes you actually use:

```bash
git clone git@github.com:YOUR_USERNAME/my-skills.git ~/workspace/my-skills
mkdir -p ~/.claude/skills ~/.codex/skills ~/.cursor/skills ~/.copilot/skills
ln -sfn ~/workspace/my-skills/my-skill ~/.claude/skills/my-skill
```

If your repo needs more automation, add a small repo-local installer script later. `npx skills add` remains the right choice for consumer installs, but it does not point at your live git clone.

## Keeping up to date

If you forked from the [skill-repo-boilerplate](https://github.com/souliane/skill-repo-boilerplate), pull upstream improvements:

```bash
git remote add boilerplate https://github.com/souliane/skill-repo-boilerplate.git
git fetch boilerplate
git merge boilerplate/main --allow-unrelated-histories
```

Repeat `git fetch boilerplate && git merge boilerplate/main` whenever the boilerplate gets updated.

## Shared hooks published by this repo

`.pre-commit-hooks.yaml` publishes the repo-level scripts so skill repos run them instead of keeping
their own copy:

| Hook id | What it does | Stage |
| --- | --- | --- |
| `update-readme-skills` | Regenerates the README skills table from `SKILL.md` frontmatter | pre-commit |
| `bump-pyproject-deps-from-lock-file` | Raises every dependency floor in `pyproject.toml` to the version `uv.lock` resolved | manual |

Consume them by SHA:

```yaml
  - repo: https://github.com/souliane/skill-repo-boilerplate
    rev: <sha>  # <date>
    hooks:
      - id: update-readme-skills
      - id: bump-pyproject-deps-from-lock-file
        stages: [manual]
```

Run the manual one on demand:

```bash
prek run --hook-stage manual --all-files bump-pyproject-deps-from-lock-file
```

## Contributing

```bash
uv run pytest               # tests
prek run --all-files         # all pre-commit hooks
```
