"""Bind every stored copy of the version to the package's version marker.

Version authority for the manuscript is ``manuscript/config.yaml``
(``paper.version``); the package marker is ``black_line.__version__``. These
tests make a drift between the copies — including the derived cover-art
marker — a test failure instead of a silent publication defect.
"""

import re
from pathlib import Path

import pytest

try:  # ``tomllib`` entered the standard library in 3.11.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - depends on the interpreter
    tomllib = None  # type: ignore[assignment]

from black_line import __version__

from black_line.figures.cover import cover_art_svg
from black_line.figures.svg import SHORT_VERSION

ROOT = Path(__file__).resolve().parent.parent


def _config_paper_version() -> str:
    """Read paper.version from manuscript/config.yaml with a scoped line parse."""

    text = (ROOT / "docs" / "manuscript" / "config.yaml").read_text(encoding="utf-8")
    in_paper = False
    for line in text.splitlines():
        if line.strip() and not line.startswith(" "):
            in_paper = line.strip() == "paper:"
            continue
        if in_paper:
            match = re.match(r'\s+version:\s*"([^"]+)"\s*$', line)
            if match:
                return match.group(1)
    raise AssertionError("paper.version not found in manuscript/config.yaml")


def test_version_marker_is_a_semantic_version() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__)


def test_manuscript_config_paper_version_matches_package() -> None:
    assert _config_paper_version() == __version__


@pytest.mark.skipif(
    tomllib is None,
    reason="reading pyproject.toml needs tomllib, added to the standard library in Python 3.11",
)
def test_pyproject_version_matches_package() -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert pyproject["project"]["version"] == __version__


def test_cover_art_version_marker_derives_from_package() -> None:
    expected_short = ".".join(__version__.split(".")[:2])
    assert SHORT_VERSION == expected_short
    assert f"{expected_short} · LIVING METHOD" in cover_art_svg()
    # No stray full-version or foreign short-version literal on the cover.
    marker_hits = re.findall(r"\d+\.\d+ · LIVING METHOD", cover_art_svg())
    assert marker_hits == [f"{expected_short} · LIVING METHOD"]
