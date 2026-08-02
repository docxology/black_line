"""Re-derive every row of data/claim_ledger.yaml from the running package.

The ledger used to be self-declared: no code in the project read it, the
sibling template collector ingested the declared tier verbatim, and one row
declared a tier its own file header contradicted. A hand-written file cannot
be its own evidence, so every row now has an executable derivation here, the
mapping is closed in both directions, and a planted-bad row is shown to fail.

The parser is deliberately small — the ledger is a flat list of inline
mappings, so a real YAML dependency would be a heavier promise than the file
makes.
"""

import re
from pathlib import Path

import pytest

from black_line import (
    BLACK_PRACTICES,
    PRACTICE_TAG_VOCABULARY,
    AssessmentStatus,
    PracticeKind,
    all_invariants,
    coverage_matrix,
    declaration_status_path,
    registry_digest,
    staleness_profile,
)
from black_line.figures.horizon_figures import horizon_omissions, horizon_rows
from black_line.figures.intake_figures import intake_note_total, intake_rows
from black_line.figures.invariant_figures import detection_collateral
from black_line.figures.legibility import MIN_RENDERED_PT
from black_line.figures.scenarios import (
    DECAY_AS_OF,
    DECAY_MAX_AGE,
    LATTICE_ROWS,
    PATH_LABELS,
    PATH_TAG,
    decay_attempt,
    detection_rows,
    path_first_aligned,
)
from black_line.figures.specs import FIGURE_SPECS

ROOT = Path(__file__).resolve().parent.parent
LEDGER = ROOT / "data" / "claim_ledger.yaml"
_ROW = re.compile(r"^\s*-\s*\{(?P<body>.*)\}\s*$")


def _rows(text: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        match = _ROW.match(line)
        if not match:
            continue
        row = {}
        for pair in match["body"].split(","):
            key, _, value = pair.partition(":")
            row[key.strip()] = value.strip()
        rows.append(row)
    return rows


def _coverage() -> dict[str, tuple[int, int]]:
    return {
        row.tag: (row.practice_count, row.required_label_count)
        for row in coverage_matrix(BLACK_PRACTICES)
    }


def _decay_flip_age(window: int) -> int:
    """The first age at which a full data declaration stops being ALIGNED."""

    practice = next(p for p in BLACK_PRACTICES if "data" in p.tags)
    for age in range(DECAY_MAX_AGE + 1):
        (point,) = staleness_profile(
            decay_attempt(age, practice.required_evidence),
            (window,),
            as_of=DECAY_AS_OF,
        )
        if point.status is not AssessmentStatus.ALIGNED:
            return age
    raise AssertionError(f"no flip found under window {window}")


def _staleness_boundary(fresh: bool) -> int:
    """The widest stale window, or the narrowest fresh one, for a 51-day age."""

    practice = next(p for p in BLACK_PRACTICES if "data" in p.tags)
    attempt = decay_attempt(51, practice.required_evidence)
    windows = tuple(range(0, 91))
    points = staleness_profile(attempt, windows, as_of=DECAY_AS_OF)
    aligned = [
        point.max_evidence_age_days
        for point in points
        if point.status is AssessmentStatus.ALIGNED
    ]
    return min(aligned) if fresh else min(aligned) - 1


def _derivations() -> dict[str, int]:
    coverage = _coverage()
    path = declaration_status_path("ledger", (PATH_TAG,), PATH_LABELS)
    derived = {
        "practice-count": len(BLACK_PRACTICES),
        "craft-family-count": len(PracticeKind),
        "tag-vocabulary-size": len(PRACTICE_TAG_VOCABULARY),
        "structural-invariant-count": len(all_invariants(BLACK_PRACTICES)),
        "distinct-evidence-label-count": len(
            {label for p in BLACK_PRACTICES for label in p.required_evidence}
        ),
        "applicable-tag-practice-cells": sum(
            reach for reach, _burden in coverage.values()
        ),
        "tag-practice-cell-total": len(coverage) * len(BLACK_PRACTICES),
        "incremental-path-steps": len(path),
        "incremental-path-first-aligned-step": path_first_aligned(),
        "decay-narrow-window-days": 30,
        "decay-narrow-window-flip-age": _decay_flip_age(30),
        "staleness-boundary-fresh-window": _staleness_boundary(fresh=True),
        "staleness-boundary-stale-window": _staleness_boundary(fresh=False),
        "decay-wide-window-flip-age": _decay_flip_age(51),
        "decay-sweep-max-age": DECAY_MAX_AGE,
        "digest-hex-length": len(registry_digest(BLACK_PRACTICES)),
        "generated-figure-count": len(FIGURE_SPECS),
        "refresh-queue-scheduled": len(horizon_rows()),
        "refresh-queue-omitted": len(horizon_omissions()),
        "lattice-order-count": LATTICE_ROWS,
        "minimum-rendered-point-size": int(MIN_RENDERED_PT),
        "intake-battery-declarations": len(intake_rows()),
        "intake-battery-notes": intake_note_total(),
        "detection-matrix-registries": len(detection_rows()),
        "detection-matrix-collateral-plants": len(detection_collateral()),
    }
    for tag, (reach, burden) in coverage.items():
        derived[f"{tag}-tag-reach"] = reach
        derived[f"{tag}-tag-burden"] = burden
    return derived


LEDGER_ROWS = _rows(LEDGER.read_text(encoding="utf-8"))


def test_the_ledger_has_rows_to_check() -> None:
    """A gate over an empty scan set proves nothing."""

    assert len(LEDGER_ROWS) >= 30


def test_every_ledger_row_has_a_derivation_and_every_derivation_a_row() -> None:
    """Closed in both directions, so neither side can drift alone."""

    assert {row["claim_id"] for row in LEDGER_ROWS} == set(_derivations())


@pytest.mark.parametrize("row", LEDGER_ROWS, ids=lambda row: row["claim_id"])
def test_ledger_row_re_derives(row: dict[str, str]) -> None:
    derived = _derivations()[row["claim_id"]]
    assert int(row["value"]) == derived, row["claim_id"]
    assert (ROOT / row["source"]).is_file(), row["source"]
    assert (ROOT / row["artifact_path"]).exists(), row["artifact_path"]
    assert row["source_tier"] == "test", (
        "every row has an executable derivation, so no row may claim a weaker tier"
    )


def test_a_planted_bad_row_is_rejected() -> None:
    """Proof of detection for the row parser and the derivation table."""

    planted = _rows(
        "  - {claim_id: practice-count, kind: number, value: 999, "
        "source: tests/test_claim_ledger.py, artifact_path: src/black_line/registry.py, "
        "source_tier: test}\n"
    )
    assert len(planted) == 1
    with pytest.raises(AssertionError):
        test_ledger_row_re_derives(planted[0])

    unknown = _rows(
        "  - {claim_id: not-a-claim, kind: number, value: 1, "
        "source: tests/test_claim_ledger.py, artifact_path: src/black_line/registry.py, "
        "source_tier: test}\n"
    )
    with pytest.raises(KeyError):
        test_ledger_row_re_derives(unknown[0])


def test_manuscript_quotes_the_headline_ledger_values() -> None:
    """The ledger supports prose, so spot-check that the prose still says it."""

    prose = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "manuscript").glob("*.md"))
    )
    derived = _derivations()
    for claim_id, spelling in (
        ("applicable-tag-practice-cells", "{value} of the 55 tag-practice cells"),
        ("research-tag-reach", "`research` | {value} of 11"),
        ("distinct-evidence-label-count", "{value} distinct"),
    ):
        assert spelling.format(value=derived[claim_id]) in prose, claim_id
