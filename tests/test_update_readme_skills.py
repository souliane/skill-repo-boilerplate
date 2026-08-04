"""Tests for the README skills-catalogue generator this repo publishes as a hook.

The generator existed in three repos with three different behaviours. These
tests are the union of what each copy guaranteed: only tracked, repo-owned
``SKILL.md`` files are listed, folded/literal YAML descriptions are parsed,
nested ``metadata.version`` wins over a flat ``version``, and the rendered table
matches markdownlint's ``compact`` style (MD060).
"""

import shutil
import subprocess
from pathlib import Path

import update_readme_skills as urs

_SKILL = "---\nname: {name}\ndescription: {desc}\nmetadata:\n  version: 0.0.1\n---\n# {name}\n"


def _git_binary() -> str:
    git = shutil.which("git")
    assert git is not None, "git is required to exercise the tracked-files path"
    return git


_GIT = _git_binary()


def _run_git(cwd: Path, *args: str) -> None:
    subprocess.run([_GIT, *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    _run_git(path, "init", "-q", "-b", "main")
    _run_git(path, "config", "user.email", "test@test.com")
    _run_git(path, "config", "user.name", "Test")


def _commit_all(path: Path) -> None:
    _run_git(path, "add", ".")
    _run_git(path, "commit", "-q", "-m", "init")


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _make_skill(root: Path, name: str, desc: str = "A skill.") -> Path:
    return _write(root / name / "SKILL.md", _SKILL.format(name=name, desc=desc))


class TestParseFrontmatter:
    def test_returns_empty_without_frontmatter_fence(self, tmp_path: Path) -> None:
        assert urs._parse_frontmatter(_write(tmp_path / "SKILL.md", "Body only.\n")) == {}

    def test_parses_keys_strips_quotes_and_ignores_blank_and_colonless_lines(self, tmp_path: Path) -> None:
        text = "---\nname: \"my-skill\"\n\nplain line without colon\ndescription: 'Does a thing.'\n---\nBody.\n"
        meta = urs._parse_frontmatter(_write(tmp_path / "SKILL.md", text))
        assert meta == {"name": "my-skill", "description": "Does a thing."}

    def test_nested_mapping_becomes_dotted_key(self, tmp_path: Path) -> None:
        meta = urs._parse_frontmatter(_make_skill(tmp_path, "ac-demo", desc="Plain inline description."))
        assert meta["name"] == "ac-demo"
        assert meta["description"] == "Plain inline description."
        assert meta["metadata.version"] == "0.0.1"

    def test_folded_description_is_joined(self, tmp_path: Path) -> None:
        skill_md = _write(
            tmp_path / "ac-folded" / "SKILL.md",
            "---\nname: ac-folded\ndescription: >\n  Line one.\n  Line two.\nmetadata:\n  version: 0.0.1\n---\n",
        )
        meta = urs._parse_frontmatter(skill_md)
        assert meta["description"] == "Line one. Line two."
        assert meta["metadata.version"] == "0.0.1"

    def test_continuation_extends_an_inline_value(self, tmp_path: Path) -> None:
        skill_md = _write(
            tmp_path / "ac-wrapped" / "SKILL.md",
            "---\nname: ac-wrapped\ndescription: First half\n  second half\n---\n",
        )
        assert urs._parse_frontmatter(skill_md)["description"] == "First half second half"


class TestSkillMdFiles:
    def test_lists_only_tracked_skill_files(self, tmp_path: Path) -> None:
        _init_repo(tmp_path)
        _make_skill(tmp_path, "ac-tracked")
        _commit_all(tmp_path)
        _make_skill(tmp_path, "phantom-untracked")

        listed = [p.parent.name for p in urs._skill_md_files(tmp_path)]
        assert listed == ["ac-tracked"]

    def test_falls_back_to_rglob_outside_git(self, tmp_path: Path) -> None:
        _make_skill(tmp_path, "ac-standalone")
        assert [p.parent.name for p in urs._skill_md_files(tmp_path)] == ["ac-standalone"]

    def test_skips_vendored_skills_under_dot_dirs(self, tmp_path: Path) -> None:
        _make_skill(tmp_path, "ac-owned")
        _make_skill(tmp_path, ".venv/vendored")
        assert [p.parent.name for p in urs._skill_md_files(tmp_path)] == ["ac-owned"]


class TestShortDescription:
    def test_truncates_at_each_trigger_separator(self) -> None:
        assert urs._short_description("Core purpose. Use when the trigger fires.") == "Core purpose"
        assert urs._short_description("Core purpose. Use this before X.") == "Core purpose"
        assert urs._short_description("Core purpose. Triggers: foo, bar.") == "Core purpose"

    def test_keeps_a_description_that_opens_with_a_trigger_word(self) -> None:
        text = "Use when the user asks for X. Use when they ask for Y."
        assert urs._short_description(text) == text

    def test_leaves_a_description_without_triggers_alone(self) -> None:
        assert urs._short_description("Just a description.") == "Just a description."


class TestBuildTable:
    def test_renders_compact_style_rows_alphabetically(self, tmp_path: Path) -> None:
        _init_repo(tmp_path)
        _make_skill(tmp_path, "ac-beta", desc="Beta skill.")
        _make_skill(tmp_path, "ac-alpha", desc="Alpha skill.")
        _commit_all(tmp_path)
        _make_skill(tmp_path, "phantom")

        table = urs._build_table(tmp_path)
        assert table.splitlines()[:2] == ["| Skill | Version | Description |", "| --- | --- | --- |"]
        assert "| `ac-alpha` | 0.0.1 | Alpha skill. |" in table
        assert "| `ac-beta` | 0.0.1 | Beta skill. |" in table
        assert "phantom" not in table
        assert table.index("ac-alpha") < table.index("ac-beta")

    def test_flat_version_key_is_used_when_metadata_is_absent(self, tmp_path: Path) -> None:
        _write(tmp_path / "ac-flat" / "SKILL.md", "---\nname: ac-flat\nversion: 9.9.9\ndescription: Flat.\n---\n")
        assert "| `ac-flat` | 9.9.9 | Flat. |" in urs._build_table(tmp_path)

    def test_falls_back_to_dir_name_em_dash_version_and_empty_description(self, tmp_path: Path) -> None:
        _write(tmp_path / "fallback-skill" / "SKILL.md", "---\nother: y\n---\n")
        assert "| `fallback-skill` | — |  |" in urs._build_table(tmp_path)

    def test_header_only_table_when_the_repo_has_no_skills(self, tmp_path: Path) -> None:
        assert urs._build_table(tmp_path) == "| Skill | Version | Description |\n| --- | --- | --- |"


class TestUpdateReadme:
    def test_returns_one_when_readme_missing(self, tmp_path: Path) -> None:
        assert urs.update_readme(tmp_path) == 1

    def test_returns_one_when_markers_absent(self, tmp_path: Path) -> None:
        _write(tmp_path / "README.md", "# Title\nno markers here\n")
        assert urs.update_readme(tmp_path) == 1

    def test_returns_one_and_writes_table_when_changed(self, tmp_path: Path) -> None:
        readme = _write(tmp_path / "README.md", f"# T\n{urs.BEGIN}\nstale\n{urs.END}\n")
        _write(tmp_path / "ac-x" / "SKILL.md", "---\nname: ac-x\ndescription: Does X.\n---\n")
        assert urs.update_readme(tmp_path) == 1
        assert "| `ac-x` | — | Does X. |" in readme.read_text(encoding="utf-8")

    def test_returns_zero_when_already_current(self, tmp_path: Path) -> None:
        _write(tmp_path / "ac-x" / "SKILL.md", "---\nname: ac-x\ndescription: Does X.\n---\n")
        _write(tmp_path / "README.md", f"# T\n{urs.BEGIN}\n{urs._build_table(tmp_path)}\n{urs.END}\n")
        assert urs.update_readme(tmp_path) == 0
