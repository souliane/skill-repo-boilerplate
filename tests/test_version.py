from version import get_version


def test_get_version_returns_string() -> None:
    result = get_version()
    assert isinstance(result, str)
    assert len(result) > 0


def test_get_version_unknown_package() -> None:
    assert get_version("nonexistent-package-xyz") == "unknown"
