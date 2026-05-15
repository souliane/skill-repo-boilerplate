from pathlib import Path

import pytest
import validate_skills

VALID = "---\nname: my-skill\ndescription: Does a thing.\nmetadata:\n  version: 0.0.1\n---\nBody.\n"


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_valid_frontmatter_has_no_errors(tmp_path: Path) -> None:
    assert validate_skills._validate(_write(tmp_path / "SKILL.md", VALID)) == []


def test_no_frontmatter_fence(tmp_path: Path) -> None:
    assert validate_skills._validate(_write(tmp_path / "SKILL.md", "Body only.\n")) == [
        "missing or unterminated YAML frontmatter",
    ]


def test_unterminated_frontmatter(tmp_path: Path) -> None:
    assert validate_skills._validate(_write(tmp_path / "SKILL.md", "---\nname: x\nno closing fence\n")) == [
        "missing or unterminated YAML frontmatter",
    ]


def test_missing_required_field_and_metadata(tmp_path: Path) -> None:
    errors = validate_skills._validate(_write(tmp_path / "SKILL.md", "---\nname: x\n---\nBody.\n"))
    assert "missing or empty required field: description" in errors
    assert "missing required field: metadata" in errors


def test_indented_and_colonless_lines_are_skipped(tmp_path: Path) -> None:
    text = "---\nname: x\ndescription: y\nmetadata:\n  version: 1\nplain line without colon\n---\nBody.\n"
    assert validate_skills._validate(_write(tmp_path / "SKILL.md", text)) == []


def test_main_returns_zero_when_no_skills(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(validate_skills, "ROOT_DIR", tmp_path)
    assert validate_skills.main() == 0


def test_main_returns_zero_when_all_valid(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write(tmp_path / "SKILL.md", VALID)
    monkeypatch.setattr(validate_skills, "ROOT_DIR", tmp_path)
    assert validate_skills.main() == 0


def test_main_returns_one_and_reports_when_invalid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _write(tmp_path / "SKILL.md", "---\nname: x\n---\nBody.\n")
    monkeypatch.setattr(validate_skills, "ROOT_DIR", tmp_path)
    assert validate_skills.main() == 1
    assert "SKILL.md:" in capsys.readouterr().out
