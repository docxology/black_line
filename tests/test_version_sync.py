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


def test_skill_descriptor_registry_size_matches_the_registry() -> None:
    from black_line import BLACK_PRACTICES

    skill = (ROOT / ".agents" / "skills" / "black-line" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert f"registry of {len(BLACK_PRACTICES)} practices" in skill


def test_cover_art_version_marker_derives_from_package() -> None:
    expected_short = ".".join(__version__.split(".")[:2])
    assert SHORT_VERSION == expected_short
    assert f"{expected_short} · LIVING METHOD" in cover_art_svg()
    # No stray full-version or foreign short-version literal on the cover.
    marker_hits = re.findall(r"\d+\.\d+ · LIVING METHOD", cover_art_svg())
    assert marker_hits == [f"{expected_short} · LIVING METHOD"]


# --- descriptor and README literals ------------------------------------------


def _coverage_rows():
    from black_line import BLACK_PRACTICES, coverage_matrix

    return {row.tag: row for row in coverage_matrix(BLACK_PRACTICES)}


def test_skill_descriptor_numeric_literals_are_derived() -> None:
    """Every number the skill descriptor states is re-derived from the package.

    The 2026-07-22 CHANGELOG entry recorded an open follow-up for exactly these
    unbound literals; this test closes it rather than letting the row disappear.
    """

    from black_line import BLACK_PRACTICES, PRACTICE_TAG_VOCABULARY, PracticeKind
    from black_line.figures.specs import FIGURE_SPECS

    skill = (ROOT / ".agents" / "skills" / "black-line" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    rows = _coverage_rows()
    research, data = rows["research"], rows["data"]
    applicable = sum(row.practice_count for row in rows.values())
    total_cells = len(rows) * len(BLACK_PRACTICES)
    burden_ratio = research.practice_count // data.practice_count

    expected = (
        f"registry of {len(BLACK_PRACTICES)} practices",
        f"{len(FIGURE_SPECS)} figures + cover",
        f"registry of {len(BLACK_PRACTICES)} practices "
        f"({len(PracticeKind)} craft families, "
        f"{len(PRACTICE_TAG_VOCABULARY)}-tag reviewed vocabulary",
        f"`research` reaches {research.practice_count} practices / "
        f"{research.required_label_count} labels",
        f"`data` reaches {data.practice_count} / {data.required_label_count}",
        f"{applicable} of {total_cells} tag-practice cells",
        f"burden {burden_ratio}-fold",
    )
    for literal in expected:
        assert literal in skill, literal


def test_readme_numeric_literals_are_derived() -> None:
    from black_line import BLACK_PRACTICES
    from black_line.figures.specs import FIGURE_SPECS

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    rows = _coverage_rows()
    research, data = rows["research"], rows["data"]
    applicable = sum(row.practice_count for row in rows.values())
    total_cells = len(rows) * len(BLACK_PRACTICES)
    for literal in (
        f"`research` reaches {research.practice_count} practices / "
        f"{research.required_label_count} required labels",
        f"`data` reaches {data.practice_count} / {data.required_label_count}",
        f"across {applicable} applicable tag-practice cells of {total_cells}",
        f"{len(FIGURE_SPECS)} deterministic manuscript figures",
    ):
        assert literal in readme, literal


def test_the_descriptor_literal_check_can_fail() -> None:
    """Positive control: a wrong count must not be accepted."""

    from black_line.figures.specs import FIGURE_SPECS

    skill = (ROOT / ".agents" / "skills" / "black-line" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert f"{len(FIGURE_SPECS) + 1} figures + cover" not in skill
