from pathlib import Path
import json
import re

import pytest
from xml.dom.minidom import parseString

from black_line import BLACK_PRACTICES, AssessmentStatus, WorkAttempt
from black_line.figures import COVER_SPEC, FIGURE_SPECS, build_figures
from black_line.figures.analytics_figures import (
    evidence_decay_svg,
    incremental_path_svg,
)
from black_line.figures.batch_figures import (
    batch_gap_counts,
    batch_never_gapped,
    batch_summary,
    batch_summary_svg,
)
from black_line.figures.scenarios import batch_assessments
from black_line.figures.scenarios import (
    DECAY_CELL_W,
    DECAY_GRID_X,
    DECAY_MAX_AGE,
    PATH_LABELS,
)
from black_line.figures.protocol_schematics import status_path_svg
from black_line.figures.registry_schematics import practice_wires_svg
from black_line.figures.svg import FAMILY_FILL, STATUS_GLYPH
from black_line.figures.validate import validate_generated_figures

#: Bump this constant intentionally whenever a figure is added or removed;
#: the membership assertions below keep the embed-or-inert gate honest
#: without index-pinned brittleness.
EXPECTED_FIGURE_COUNT = 15

EXPECTED_FIGURE_LABELS = {
    "fig:black-surfaces-panel",
    "fig:black-operating-loop",
    "fig:black-practice-wires",
    "fig:black-status-path",
    "fig:black-claim-layers",
    "fig:black-family-taxonomy",
    "fig:black-evidence-matrix",
    "fig:black-coverage-heatmap",
    "fig:black-incremental-path",
    "fig:black-evidence-decay",
    "fig:black-refresh-queue",
    "fig:black-monotonicity-lattice",
    "fig:black-batch-summary",
    "fig:black-intake-notes",
    "fig:black-invariant-detection",
}


ROOT = Path(__file__).resolve().parent.parent


def _bundle(tmp_path: Path) -> Path:
    """Build a figure bundle plus the manuscript config the gate reads.

    ``validate_generated_figures`` binds the registry's cover entry to
    ``paper.cover.image``, so a bundle under test carries its own config copy
    rather than silently borrowing the checkout's.
    """

    build_figures(tmp_path)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(parents=True, exist_ok=True)
    (manuscript / "config.yaml").write_text(
        (ROOT / "docs" / "manuscript" / "config.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return tmp_path


def test_figure_specs_match_the_expected_roster() -> None:
    assert len(FIGURE_SPECS) == EXPECTED_FIGURE_COUNT
    assert {spec.label for spec in FIGURE_SPECS} == EXPECTED_FIGURE_LABELS
    names = [spec.name for spec in FIGURE_SPECS]
    assert len(set(names)) == EXPECTED_FIGURE_COUNT


def test_every_registered_figure_is_embedded_in_the_manuscript() -> None:
    manuscript = Path(__file__).resolve().parent.parent / "docs" / "manuscript"
    prose = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(manuscript.glob("*.md"))
    )
    for spec in FIGURE_SPECS:
        assert f"figures/{spec.name}.png" in prose, f"{spec.name} is not embedded"
        assert f"{{#{spec.label}" in prose, f"{spec.label} anchor is not embedded"


def _normalized_caption(caption: str) -> str:
    """Collapse markdown-only differences (backticks vs quotes, whitespace)."""

    return " ".join(caption.replace("`", "").replace("'", "").split())


def test_manuscript_embed_captions_match_the_registry_captions() -> None:
    """The two caption sources for each figure must not drift independently.

    The registry caption (FIGURE_SPECS -> figure_registry.json) and the
    manuscript embed caption are compared after normalizing markdown backticks
    and straight quotes, so a wording change in one place without the other is
    a test failure instead of a silent publication defect.
    """

    manuscript = Path(__file__).resolve().parent.parent / "docs" / "manuscript"
    prose = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(manuscript.glob("*.md"))
    )
    for spec in FIGURE_SPECS:
        matches = re.findall(
            r"!\[([^\]]*)\]\(\.\./output/figures/" + re.escape(spec.name) + r"\.png\)",
            prose,
        )
        assert len(matches) == 1, f"{spec.name} must be embedded exactly once"
        assert _normalized_caption(matches[0]) == _normalized_caption(spec.caption), (
            f"embed caption for {spec.name} drifted from the registry caption"
        )


def test_builders_draw_what_their_captions_state_in_memory() -> None:
    """Validate changed builders without touching the output mirror."""

    from xml.dom.minidom import parseString

    wires = practice_wires_svg()
    parseString(wires)
    for accent in FAMILY_FILL.values():
        assert accent in wires, f"family accent {accent} missing from practice wires"
    # The caption claims a card per practice in registry declaration order, so
    # bind both the count and the order, not only the family palette.
    drawn_ids = re.findall(r"<text[^>]*>([a-z][a-z_]* · [a-z_]+)</text>", wires)
    assert len(drawn_ids) == len(BLACK_PRACTICES)
    kinds = re.findall(r"<text[^>]*>\d\d · ([A-Z]+)</text>", wires)
    assert kinds == [practice.kind.value for practice in BLACK_PRACTICES]
    for index, practice in enumerate(BLACK_PRACTICES):
        assert drawn_ids[index] == " · ".join(practice.required_evidence), practice.id

    path_fig = status_path_svg()
    parseString(path_fig)
    # The rule text wraps across <text> elements, so bind the fragments.
    assert "required labels missing beyond" in path_fig
    assert "stale refreshes" in path_fig
    assert "malformed registry" in path_fig

    decay = evidence_decay_svg()
    parseString(decay)
    decay_width = int(re.search(r'width="(\d+)"', decay).group(1))
    assert decay_width >= DECAY_GRID_X + (DECAY_MAX_AGE + 1) * DECAY_CELL_W, (
        "decay canvas clips the declared age sweep"
    )
    assert f">{DECAY_MAX_AGE}</text>" in decay, "final axis tick is missing"

    # The batch panel's caption states a status distribution, a family
    # concentration, and a gap ranking. Bind all three to the executed values,
    # including the drawn order, so a reordered or truncated panel fails.
    batch = batch_summary_svg()
    parseString(batch)
    summary = batch_summary()
    for value, count in summary.status_counts:
        assert f">{value}</text>" in batch, value
        assert f">{count} of {summary.total}</text>" in batch, value
        assert f">{STATUS_GLYPH[value]}</text>" in batch, value
    for family, count in summary.open_finding_kind_counts:
        assert f">{family}</text>" in batch, family
    gaps = batch_gap_counts()
    drawn = [
        practice_id
        for practice_id in re.findall(r"<text[^>]*>([a-z][a-z-]+)</text>", batch)
        if practice_id in {row[0] for row in gaps}
    ]
    assert drawn == [practice_id for practice_id, _count in gaps], (
        "the gap ranking is drawn out of its computed order"
    )
    never = batch_never_gapped()
    assert f">{', '.join(never)}</text>" in batch
    assert set(never).isdisjoint({practice_id for practice_id, _c in gaps})

    grid = incremental_path_svg()
    parseString(grid)
    assert "OVERALL" in grid
    assert f"+{PATH_LABELS[-1]}" in grid
    # 8 practice rows + 1 overall row, one cell per evaluator call.
    assert grid.count("<rect") >= (len(PATH_LABELS) + 1) * 9


def test_the_batch_panel_follows_its_data_rather_than_a_baked_ranking() -> None:
    """Proof of derivation: change the batch, and the drawn panel must change.

    A panel that agreed with the executed battery by coincidence — a hardcoded
    ranking, a stored total — would survive every assertion above. Passing a
    one-attempt batch through the builder's own override argument (real
    assessments, no patching) forces the counts, the ranking, and the
    never-open band to move with the data.
    """

    full_gaps = batch_gap_counts()
    full_total = batch_summary().total
    assert full_total > 1

    single = batch_assessments()[1:2]
    narrowed_gaps = batch_gap_counts(single)
    assert narrowed_gaps != full_gaps
    narrowed = batch_summary_svg(single)
    assert ">1 of 1</text>" in narrowed
    assert f">{full_total} of {full_total}</text>" not in narrowed
    for practice_id, _count in narrowed_gaps:
        assert f">{practice_id}</text>" in narrowed
    dropped = {row[0] for row in full_gaps} - {row[0] for row in narrowed_gaps}
    assert dropped, "the narrowed batch must leave some practice out"
    for practice_id in dropped:
        assert f">{practice_id}</text>" not in narrowed, practice_id


def test_figure_builder_is_deterministic(tmp_path: Path) -> None:
    first = build_figures(tmp_path)
    bytes_first = {path.name: path.read_bytes() for path in first}
    second = build_figures(tmp_path)
    assert {path.name: path.read_bytes() for path in second} == bytes_first
    registry = json.loads(
        (tmp_path / "output" / "figures" / "figure_registry.json").read_text()
    )
    # 1.5 is the schema in which the cover joined the `figures` list and every
    # reader-facing contract field became gate-enforced. Bump it deliberately.
    assert registry["schema_version"] == "1.5"
    assert registry["registry_digest"]
    figures = registry["figures"]
    assert len(figures) == EXPECTED_FIGURE_COUNT + 1, "manuscript figures plus cover"
    assert {figure["label"] for figure in figures} == EXPECTED_FIGURE_LABELS | {
        COVER_SPEC.label
    }
    filenames = [figure["filename"] for figure in figures]
    assert len(set(filenames)) == EXPECTED_FIGURE_COUNT + 1
    assert all(filename.endswith(".png") for filename in filenames)
    assert all(figure["caption"] for figure in figures)
    assert all(figure["alt"] for figure in figures)
    assert all(figure["interpretive_claim"] for figure in figures)
    assert all(figure["epistemic_boundary"] for figure in figures)
    assert registry["cover"]["filename"] == "cover_art.png"
    assert registry["cover"]["interpretive_claim"]
    assert registry["cover"]["epistemic_boundary"]
    assert (tmp_path / "output" / "figures" / "cover_art.png").is_file()
    for path in first:
        assert path.read_bytes().startswith(b"\x89PNG\r\n\x1a\n"), path.name


def test_generated_figure_gate_detects_registry_drift(tmp_path: Path) -> None:
    """The on-disk output gate must fail when its registry is stale."""

    _bundle(tmp_path)
    assert validate_generated_figures(tmp_path) == []

    registry_path = tmp_path / "output" / "figures" / "figure_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    dropped = registry["figures"].pop()["filename"].removesuffix(".png")
    registry_path.write_text(json.dumps(registry), encoding="utf-8")

    errors = validate_generated_figures(tmp_path)
    assert any("missing" in error and dropped in error for error in errors)


def test_generated_figure_gate_reports_missing_and_corrupt_registry(
    tmp_path: Path,
) -> None:
    missing = validate_generated_figures(tmp_path)
    assert len(missing) == 1
    assert "missing generated figure registry" in missing[0]

    figures = tmp_path / "output" / "figures"
    figures.mkdir(parents=True)
    bad = figures / "figure_registry.json"
    bad.write_text("{not-json", encoding="utf-8")
    corrupt = validate_generated_figures(tmp_path)
    assert len(corrupt) == 1
    assert "cannot read" in corrupt[0]

    bad.write_text(json.dumps({"figures": "nope"}), encoding="utf-8")
    shape = validate_generated_figures(tmp_path)
    assert any("list-valued" in error for error in shape)


def test_generated_figure_gate_detects_file_and_metadata_drift(
    tmp_path: Path,
) -> None:
    _bundle(tmp_path)
    figures = tmp_path / "output" / "figures"
    (figures / "black_practice_wires.png").unlink()
    errors = validate_generated_figures(tmp_path)
    assert any("black_practice_wires.png" in error for error in errors)

    _bundle(tmp_path)
    registry_path = figures / "figure_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["package_version"] = "0.0.0-drift"
    registry["cover"] = {"filename": "wrong.png"}
    registry_path.write_text(json.dumps(registry), encoding="utf-8")
    drift = validate_generated_figures(tmp_path)
    assert any("package_version" in error for error in drift)
    assert any("cover" in error for error in drift)


def test_resolve_converter_fails_when_rsvg_convert_is_absent(
    monkeypatch, tmp_path: Path
) -> None:
    """Missing rasterizer is a hard error, not a silent skip.

    Isolates the real ``PATH`` lookup with an empty directory — no patched
    callables or stand-in converters.
    """

    from black_line.figures.output import resolve_converter

    empty = tmp_path / "empty_bin"
    empty.mkdir()
    monkeypatch.setenv("PATH", str(empty))
    with pytest.raises(RuntimeError, match="rsvg-convert is required"):
        resolve_converter()


def test_the_intake_plate_follows_the_executed_battery() -> None:
    """Every drawn row of the intake plate is read off a real evaluator call.

    Proof of derivation, not agreement: the same builder is run over a narrowed
    battery through its own override argument (real ``WorkAttempt`` records, no
    patching), so a hardcoded status letter, note string, or count could not
    survive. The default plate is then checked cell by cell against a fresh
    re-derivation.
    """

    from black_line.figures.intake_figures import (
        intake_blocked,
        intake_note_total,
        intake_notes_svg,
        intake_rows,
        intake_scored,
        intake_unmatched,
    )
    from black_line.figures.scenarios import INTAKE_CASES

    rows = intake_rows()
    assert len(rows) == len(INTAKE_CASES) >= 8
    plate = intake_notes_svg()
    parseString(plate)

    # Every row's own three derived values reach the plate.
    for label, status, findings, notes in rows:
        assert f">{label}</text>" in plate, label
        assert f">{status}</text>" in plate, label
        plural = "" if findings == 1 else "s"
        assert f">{findings} practice finding{plural}</text>" in plate, label
        assert notes, f"{label}: a row with no note would make this vacuous"
        for note in notes:
            assert f"· {note}" in plate.replace("&#x27;", "'"), (label, note)

    # The partition the caption states is the partition the rows produce.
    assert set(intake_blocked()) | set(intake_unmatched()) | set(intake_scored()) == {
        label for label, _s, _f, _n in rows
    }
    assert intake_note_total() == sum(len(notes) for *_head, notes in rows)
    assert {status for _l, status, _f, _n in rows} == {
        status.value for status in AssessmentStatus
    }, "the battery is supposed to reach every assessment status"

    # Narrow the battery: the plate must move with it.
    narrowed_cases = INTAKE_CASES[:2]
    narrowed = intake_notes_svg(narrowed_cases)
    parseString(narrowed)
    assert narrowed != plate
    assert f"{len(narrowed_cases)} DECLARATIONS" in narrowed
    assert f"{len(rows)} DECLARATIONS" not in narrowed
    dropped = {label for label, _s, _f, _n in rows} - {
        label for label, _attempt in narrowed_cases
    }
    assert dropped
    for label in dropped:
        assert f">{label}</text>" not in narrowed, label


def test_the_surfaces_panel_follows_the_executed_call() -> None:
    """Every chip and status on the surfaces panel is read off one real
    ``evaluate_with_surfaces`` call.

    Proof of derivation, not agreement: the same builder is run over an
    override attempt (a real ``WorkAttempt``, no patching), so a hardcoded
    chip, status word, or count could not survive. The default panel is then
    checked row by row against a fresh re-derivation through the public API.
    """

    from black_line import evaluate_with_surfaces
    from black_line.figures.scenarios import (
        SURFACES_AS_OF,
        SURFACES_ATTEMPT,
        SURFACES_WINDOW,
    )
    from black_line.figures.surface_figures import (
        surfaces_label_totals,
        surfaces_overall,
        surfaces_panel_svg,
        surfaces_rows,
        surfaces_shape_counts,
    )

    rows = surfaces_rows()
    assessment, surfaces = evaluate_with_surfaces(
        SURFACES_ATTEMPT,
        BLACK_PRACTICES,
        as_of=SURFACES_AS_OF.isoformat(),
        max_evidence_age_days=SURFACES_WINDOW,
    )
    assert rows == tuple(
        (s.practice_id, f.status.value, s.present, s.missing, s.stale)
        for f, s in zip(assessment.findings, surfaces)
    )
    assert surfaces_overall() == assessment.status.value

    plate = surfaces_panel_svg()
    parseString(plate)
    # Every row's practice, status, and every label chip reach the plate.
    for practice_id, status, present, missing, _stale in rows:
        assert f">{practice_id}</text>" in plate, practice_id
        assert f">{status}</text>" in plate, practice_id
        assert f">{STATUS_GLYPH[status]}</text>" in plate, practice_id
        for label in (*present, *missing):
            assert f">{label}</text>" in plate, (practice_id, label)
    present_total, missing_total, stale_total = surfaces_label_totals()
    assert present_total + missing_total == sum(
        len(p.required_evidence)
        for p in BLACK_PRACTICES
        if p.tags & SURFACES_ATTEMPT.tags
    )
    assert f"{present_total + missing_total} REQUIRED LABELS" in plate
    assert f"({stale_total} of the {missing_total} missing here)" in plate
    # The compression footer names the executed shape counts, in enum order.
    shapes = surfaces_shape_counts()
    assert dict(shapes)["NEEDS_REWORK"] > 1, (
        "the pinned scenario exists to show one word over several shapes"
    )
    footer = " · ".join(f"{status} {count}" for status, count in shapes)
    assert footer in plate

    # Narrow the declaration: the panel must move with it.
    narrowed_attempt = WorkAttempt(
        "narrowed to the data practice alone",
        frozenset({"data"}),
        frozenset({"data_origin"}),
    )
    narrowed = surfaces_panel_svg(narrowed_attempt)
    parseString(narrowed)
    assert narrowed != plate
    narrowed_rows = surfaces_rows(narrowed_attempt)
    assert [row[0] for row in narrowed_rows] == ["data-provenance"]
    assert "1 MATCHED PRACTICES" in narrowed
    assert f"{len(rows)} MATCHED PRACTICES" not in narrowed
    dropped = {row[0] for row in rows} - {row[0] for row in narrowed_rows}
    assert dropped
    for practice_id in dropped:
        assert f">{practice_id}</text>" not in narrowed, practice_id


def test_the_detection_plate_follows_the_executed_battery() -> None:
    """Every cell of the detection matrix is a real ``all_invariants`` outcome.

    The plate claims each plant fails the check it targets. That claim is
    re-derived here from the battery rather than read off the figure, and the
    collateral failures the caption names are re-derived too — a plate drawing a
    clean diagonal while the battery reported otherwise would pass a
    shape-only check.
    """

    from black_line import BLACK_PRACTICES, all_invariants
    from black_line.figures.invariant_figures import (
        FAIL_GLYPH,
        PASS_GLYPH,
        detection_collateral,
        detection_targets_all_fire,
        invariant_detection_svg,
    )
    from black_line.figures.scenarios import (
        INVARIANT_PLANTS,
        detection_check_names,
        detection_rows,
    )

    checks = detection_check_names()
    rows = detection_rows()
    assert len(checks) == 7
    assert len(rows) == len(INVARIANT_PLANTS) + 1

    # Row 0 is the positive control: the shipped registry passes everything.
    assert rows[0][2] == tuple(
        (check.name, True) for check in all_invariants(BLACK_PRACTICES)
    )
    # Every plant fires on its target, which is the claim the caption makes.
    assert detection_targets_all_fire()
    for target, _planted, results in rows[1:]:
        assert dict(results)[target] is False, target
    # The collateral is real and named, not designed away.
    collateral = detection_collateral()
    assert collateral, "a clean diagonal here would contradict the caption"
    for target, others in collateral:
        assert others
        assert target not in others

    plate = invariant_detection_svg()
    parseString(plate)
    for name in checks:
        assert f">{name}</text>" in plate, name
    for label, planted, results in rows:
        assert f">{label}</text>" in plate, label
        assert f">{planted}</text>" in plate, planted
        failed = sum(1 for _n, passed in results if not passed)
        assert f">{failed} of {len(checks)}</text>" in plate, label
    assert plate.count(f">{PASS_GLYPH}</text>") >= sum(
        1 for _l, _p, results in rows for _n, passed in results if passed
    )
    assert plate.count(f">{FAIL_GLYPH}</text>") >= sum(
        1 for _l, _p, results in rows for _n, passed in results if not passed
    )

    # Narrow the matrix: the plate must move with it.
    narrowed = invariant_detection_svg(rows[:3])
    parseString(narrowed)
    assert narrowed != plate
    assert f"{len(checks)} CHECKS × {len(rows[:3])} REGISTRIES" in narrowed
    # Row labels double as column headers, so the dropped rows are identified by
    # their planted description, which appears only in the row band.
    for _label, planted, _results in rows[3:]:
        assert f">{planted}</text>" not in narrowed, planted
