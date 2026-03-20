"""Expose the skill repo version from pyproject.toml metadata."""

from importlib.metadata import PackageNotFoundError, version


def get_version(package: str = "skill-repo-boilerplate") -> str:
    """Return the installed package version, or 'unknown' if not installed."""
    try:
        return version(package)
    except PackageNotFoundError:
        return "unknown"
