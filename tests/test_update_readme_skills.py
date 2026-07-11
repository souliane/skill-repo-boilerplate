from pathlib import Path

import pytest
import update_readme_skills as urs


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class TestParseFrontmatter:
    def test_extracts_key_values_and_strips_quotes(self, tmp_path: Path) -> None:
        skill = _write(tmp_path / "SKILL.md", "---\nname: \"foo\"\ndescription: 'bar'\n---\nBody\n")
        assert urs._parse_frontmatter(skill) == {"name": "foo", "description": "bar"}

    def test_no_frontmatter_returns_empty(self, tmp_path: Path) -> None:
        skill = _write(tmp_path / "SKILL.md", "No frontmatter here.\n")
        assert urs._parse_frontmatter(skill) == {}

    def test_lines_without_colon_are_skipped(self, tmp_path: Path) -> None:
        skill = _write(tmp_path / "SKILL.md", "---\nname: foo\nplain line no colon\n---\nBody\n")
        assert urs._parse_frontmatter(skill) == {"name": "foo"}


class TestIterSkillFiles:
    def test_skips_dot_dirs(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(urs, "ROOT_DIR", tmp_path)
        real = _write(tmp_path / "real" / "SKILL.md", "---\nname: real\n---\n")
        _write(tmp_path / ".venv" / "pkg" / "SKILL.md", "---\nname: vendored\n---\n")
        assert urs._iter_skill_files() == [real]


class TestBuildTable:
    def test_renders_rows_with_defaults_and_truncation(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(urs, "ROOT_DIR", tmp_path)
        _write(
            tmp_path / "a" / "SKILL.md",
            "---\nname: a\ndescription: Does A. Use when needed.\nmetadata:\n  version: 1.0\n---\n",
        )
        # No name key → falls back to parent dir; no version key → "—"; ". Use this" truncation.
        _write(tmp_path / "b" / "SKILL.md", "---\ndescription: Thing B. Use this daily.\n---\n")
        table = urs._build_table()
        assert "| Skill | Version | Description |" in table
        assert "| `a` | 1.0 | Does A |" in table
        assert "| `b` | — | Thing B |" in table


class TestMain:
    def _readme(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, body: str) -> Path:
        monkeypatch.setattr(urs, "ROOT_DIR", tmp_path)
        readme = _write(tmp_path / "README.md", body)
        monkeypatch.setattr(urs, "README_PATH", readme)
        return readme

    def test_writes_catalogue_and_signals_change(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        readme = self._readme(tmp_path, monkeypatch, "# T\n<!-- BEGIN SKILLS -->\nold\n<!-- END SKILLS -->\n")
        _write(tmp_path / "a" / "SKILL.md", "---\nname: a\ndescription: Does A.\n---\n")
        assert urs.main() == 1
        assert "| `a` |" in readme.read_text(encoding="utf-8")

    def test_idempotent_second_run_returns_zero(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self._readme(tmp_path, monkeypatch, "# T\n<!-- BEGIN SKILLS -->\nold\n<!-- END SKILLS -->\n")
        _write(tmp_path / "a" / "SKILL.md", "---\nname: a\ndescription: Does A.\n---\n")
        assert urs.main() == 1
        assert urs.main() == 0

    def test_missing_readme_returns_one(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(urs, "ROOT_DIR", tmp_path)
        monkeypatch.setattr(urs, "README_PATH", tmp_path / "absent.md")
        assert urs.main() == 1

    def test_missing_markers_returns_one(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        self._readme(tmp_path, monkeypatch, "# T\nno markers here\n")
        assert urs.main() == 1
