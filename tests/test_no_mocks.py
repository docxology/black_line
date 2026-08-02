"""Lexical guards keep project Python files free of banned constructs."""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOTS = ("src", "tests", "scripts")
SKIP_DIRS = frozenset({"__pycache__", ".venv", ".pytest_cache", ".ruff_cache"})


def _python_files() -> tuple[Path, ...]:
    """Return every Python file the guards below apply to."""

    files: list[Path] = []
    for relative_root in SEARCH_ROOTS:
        root = PROJECT_ROOT / relative_root
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            # Judge exclusion on the path inside the project only: an ancestor
            # directory sharing a skipped name must not empty the whole scan.
            if SKIP_DIRS.isdisjoint(path.relative_to(PROJECT_ROOT).parts):
                files.append(path)
    assert files, "lexical guards scanned zero Python files"
    return tuple(files)


# Every needle below is assembled from fragments so this module never contains
# the text it forbids, and therefore scans itself like any other file. Joining
# the fragments back into literals would blind the guards to their own source.
def _text_pattern(*fragments: str) -> re.Pattern[str]:
    """Compile an exact-text rule from fragments."""

    return re.compile(re.escape("".join(fragments)))


def _name_pattern(*fragments: str) -> re.Pattern[str]:
    """Compile a rule matching fragments at the head of a word or identifier.

    The lookbehind admits a leading underscore, so an underscore-prefixed name
    is caught alongside the plain form, while mid-word matches are refused.
    """

    return re.compile(
        r"(?<![A-Za-z0-9])" + re.escape("".join(fragments)), re.IGNORECASE
    )


def _locations(*patterns: re.Pattern[str]) -> tuple[str, ...]:
    """Return ``path:line`` for every scanned line matching any pattern."""

    found: list[str] = []
    for path in _python_files():
        relative = path.relative_to(PROJECT_ROOT)
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if any(pattern.search(line) for pattern in patterns):
                found.append(f"{relative}:{lineno}")
    return tuple(found)


def _assert_absent(description: str, *patterns: re.Pattern[str]) -> None:
    """Fail naming every offending location, so the failure is actionable."""

    locations = _locations(*patterns)
    assert not locations, f"{description} found at: {', '.join(locations)}"


def test_patching_tooling_is_absent() -> None:
    """No module reaches for a patching or test-double library."""

    _assert_absent(
        "patching tooling",
        _text_pattern("unit", "test", ".", "mock"),
        _text_pattern("Magic", "Mock"),
        _text_pattern("mocker", ".", "patch"),
        _text_pattern("monkeypatch", ".", "setattr"),
        _text_pattern("monkeypatch", ".", "setitem"),
    )


def test_placeholder_prefixed_names_are_absent() -> None:
    """No module defines a stand-in named as a substitute for the real thing."""

    _assert_absent("placeholder-prefixed names", _name_pattern("fa", "ke", "_"))


def test_superseded_code_branding_is_absent() -> None:
    """No module brands its own code or tests as superseded."""

    _assert_absent("superseded-code branding", _name_pattern("leg", "acy"))


def test_machine_local_paths_are_absent() -> None:
    """No module hardcodes one machine's package-manager prefix."""

    _assert_absent(
        "machine-local path hardcodes",
        _text_pattern("/", "opt", "/", "homebrew"),
        _text_pattern("/", "usr", "/", "local", "/", "Cellar"),
    )


def test_import_path_insertion_is_absent() -> None:
    """No module rewrites the import search path to find its own package."""

    _assert_absent(
        "import-path insertion",
        _text_pattern("sys", ".", "path", ".", "insert"),
    )
