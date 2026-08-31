"""Bind the manuscript's executed-example numbers to real evaluator runs.

Every numeric claim in the worked-example and adversarial-declaration prose
must be reproducible through the public API. These tests re-derive each
number and assert the manuscript quotes the derived value, so prose drift
from the evaluator becomes a test failure instead of a silent publication
defect. No mocks: every status below comes from a real ``evaluate_work``
call (directly or via the analytics helpers).
"""

import re
from pathlib import Path

import pytest

from black_line import (
    BLACK_PRACTICES,
    DECLARATION_STATUS_ORDER,
    AssessmentStatus,
    PracticeStatus,
    WorkAttempt,
    coverage_matrix,
    declaration_status_path,
    evaluate_work,
    no_status_regression,
    registry_digest,
    staleness_profile,
    status_rank,
)
from black_line.figures.scenarios import DECAY_AS_OF, PATH_LABELS

MANUSCRIPT = Path(__file__).resolve().parent.parent / "docs" / "manuscript"


def _read(name: str) -> str:
    return (MANUSCRIPT / name).read_text(encoding="utf-8")


def _collapsed(name: str) -> str:
    """One manuscript file with line wrapping removed.

    Where a sentence wraps is an editorial choice and changes with every
    re-flow; what it says is the binding. Comparisons against derived values
    use this so a rewrap cannot fail a claim that is still true.
    """

    return " ".join(_read(name).split())


def _dated_attempt(age_days: int, labels: tuple[str, ...]) -> WorkAttempt:
    from black_line.figures.scenarios import decay_attempt

    return decay_attempt(age_days, labels)


def test_incremental_path_matches_the_examples_table() -> None:
    path = declaration_status_path(
        "literature synthesis on staleness semantics", ("research",), PATH_LABELS
    )
    assert len(path) == 17
    assert path[0] is AssessmentStatus.NEEDS_EVIDENCE
    assert all(status is AssessmentStatus.NEEDS_REWORK for status in path[1:16])
    assert path[16] is AssessmentStatus.ALIGNED
    assert no_status_regression(path[1:]) is True
    assert no_status_regression(path) is False
    text = _read("04_examples.md")
    assert "| 0 | — | 0 | — | 0 of 8 | `NEEDS_EVIDENCE` |" in text
    assert "| 1 | `question` | 1 | — | 0 of 8 | `NEEDS_REWORK` |" in text
    assert (
        "| 16 | `reviewer`, `review_note` | 16 | `review-before-reliance` "
        "| 8 of 8 | `ALIGNED` |" in text
    )


def test_incremental_path_aligned_counts_match_findings() -> None:
    expected_aligned = {0: 0, 1: 0, 2: 1, 4: 2, 6: 3, 8: 4, 10: 5, 12: 6, 14: 7, 16: 8}
    for step, count in expected_aligned.items():
        assessment = evaluate_work(
            WorkAttempt(
                "literature synthesis on staleness semantics",
                frozenset({"research"}),
                frozenset(PATH_LABELS[:step]),
            ),
            BLACK_PRACTICES,
        )
        assert len(assessment.findings) == 8
        aligned = [
            finding
            for finding in assessment.findings
            if finding.status is PracticeStatus.ALIGNED
        ]
        assert len(aligned) == count


def test_decay_sweep_matches_the_examples_table() -> None:
    practice = next(p for p in BLACK_PRACTICES if "data" in p.tags)
    full = practice.required_evidence
    windows = (30, 51, None)
    expected = {
        0: ("ALIGNED", "ALIGNED", "ALIGNED"),
        30: ("ALIGNED", "ALIGNED", "ALIGNED"),
        31: ("NEEDS_EVIDENCE", "ALIGNED", "ALIGNED"),
        51: ("NEEDS_EVIDENCE", "ALIGNED", "ALIGNED"),
        52: ("NEEDS_EVIDENCE", "NEEDS_EVIDENCE", "ALIGNED"),
        70: ("NEEDS_EVIDENCE", "NEEDS_EVIDENCE", "ALIGNED"),
    }
    for age, statuses in expected.items():
        points = staleness_profile(
            _dated_attempt(age, full), windows, as_of=DECAY_AS_OF
        )
        assert tuple(point.status.value for point in points) == statuses
    for age in (0, 31, 70):
        (point,) = staleness_profile(
            _dated_attempt(age, full[:1]), (30,), as_of=DECAY_AS_OF
        )
        assert point.status is AssessmentStatus.NEEDS_REWORK
    text = _read("04_examples.md")
    assert "| 31 | `NEEDS_EVIDENCE` | `ALIGNED` | `ALIGNED` | `NEEDS_REWORK` |" in text
    assert (
        "| 52 | `NEEDS_EVIDENCE` | `NEEDS_EVIDENCE` | `ALIGNED` | `NEEDS_REWORK` |"
        in text
    )


def test_label_stuffing_yields_aligned_as_the_limits_section_states() -> None:
    all_labels = frozenset(
        label for practice in BLACK_PRACTICES for label in practice.required_evidence
    )
    assert len(all_labels) == 22
    stuffed = evaluate_work(
        WorkAttempt("ceremonial declaration", frozenset({"research"}), all_labels),
        BLACK_PRACTICES,
    )
    assert stuffed.status is AssessmentStatus.ALIGNED
    text = _read("05_limits.md")
    assert "22 distinct" in text


def test_tag_minimization_contrast_matches_the_limits_section() -> None:
    """The executed contrast and the fold it is described as must agree.

    The prose used to call this contrast "eightfold", borrowing the registry's
    widest spread (`research` 8 against `data` 1) for a contrast that actually
    starts from `analysis` and reaches 7. Both the ratio and the label counts
    are re-derived here, and the borrowed wording is rejected outright.
    """

    labels = frozenset({"data_origin", "transform_log"})
    wide = evaluate_work(
        WorkAttempt("cross-dataset analysis", frozenset({"analysis", "data"}), labels),
        BLACK_PRACTICES,
    )
    narrow = evaluate_work(
        WorkAttempt("cross-dataset analysis", frozenset({"data"}), labels),
        BLACK_PRACTICES,
    )
    assert wide.status is AssessmentStatus.NEEDS_REWORK
    assert len(wide.findings) == 7
    assert narrow.status is AssessmentStatus.ALIGNED
    assert len(narrow.findings) == 1
    text = _read("05_limits.md")
    assert "7 applicable practices" in text

    by_id = {practice.id: practice for practice in BLACK_PRACTICES}
    wide_labels = sum(
        len(by_id[finding.practice_id].required_evidence) for finding in wide.findings
    )
    narrow_labels = sum(
        len(by_id[finding.practice_id].required_evidence) for finding in narrow.findings
    )
    fold = len(wide.findings) // len(narrow.findings)
    assert fold == 7, "the derived fold must drive the prose, not a nearby literal"
    collapsed = " ".join(text.split())
    assert "a sevenfold smaller" in collapsed
    assert (
        f"{len(wide.findings)} practices and {wide_labels} required labels "
        f"narrowed to {len(narrow.findings)} and {narrow_labels}" in collapsed
    )
    # The wider registry spread is a different, correctly-stated number; it may
    # be named as a contrast but must never label this executed comparison.
    rows = {row.tag: row for row in coverage_matrix(BLACK_PRACTICES)}
    widest = rows["research"].practice_count // rows["data"].practice_count
    assert widest == 8 and widest != fold
    assert "eightfold smaller" not in collapsed, (
        "the executed contrast is sevenfold; eightfold is the research-vs-data spread"
    )


def test_refresh_date_laundering_contrast_matches_the_limits_section() -> None:
    practice = next(p for p in BLACK_PRACTICES if "data" in p.tags)
    full = practice.required_evidence
    stale = evaluate_work(
        _dated_attempt(70, full),
        BLACK_PRACTICES,
        as_of=DECAY_AS_OF,
        max_evidence_age_days=30,
    )
    redated = evaluate_work(
        _dated_attempt(0, full),
        BLACK_PRACTICES,
        as_of=DECAY_AS_OF,
        max_evidence_age_days=30,
    )
    assert stale.status is AssessmentStatus.NEEDS_EVIDENCE
    assert redated.status is AssessmentStatus.ALIGNED
    text = _read("05_limits.md")
    assert "70 days old" in text


def test_the_practice_list_restates_every_registry_wire_verbatim() -> None:
    """The numbered list in 03_practices.md is the registry, not a paraphrase.

    Nine of the eleven entries already quoted their wire exactly; two had
    drifted a word each ("scope" for the registry's "boundary", and a dropped
    article), so the paper and the shipped registry described the same practice
    differently while the digest, the figures, and every other gate stayed
    green. Every title, family, and wire is now re-read from `BLACK_PRACTICES`.
    """

    collapsed = " ".join(_read("03_practices.md").split())
    assert BLACK_PRACTICES, "an empty registry would make this sweep vacuous"
    for index, practice in enumerate(BLACK_PRACTICES, start=1):
        assert f"{index}. **{practice.title}**" in collapsed, practice.id
        assert f"({practice.kind.value.lower()})." in collapsed, practice.id
        assert practice.wire in collapsed, (
            f"{practice.id}: the manuscript paraphrases its wire instead of "
            f"quoting it — registry says {practice.wire!r}"
        )


def test_refresh_queue_omission_wording_matches_the_executed_omissions() -> None:
    """The omitted set is not all dated, so nothing may call it dated.

    One of the three omitted classes is *undated* by construction — that is
    why it is omitted. The caption, the figure's own ``<desc>``, and the
    embedded copy in the manuscript all described the band as "dated
    declarations", which is false of exactly the row that motivates the class.
    Re-derive the classes and reject the wording wherever it can reach a
    reader.
    """

    from black_line.figures.horizon_figures import horizon_omissions, refresh_queue_svg
    from black_line.figures.specs import FIGURE_SPECS

    omitted = horizon_omissions()
    assert len(omitted) == 3, "an empty or shrunken omission set makes this vacuous"
    undated = [row for row in omitted if "undated" in row.reason]
    assert len(undated) == 1, "the undated class is what the claim gets wrong"

    spec = next(spec for spec in FIGURE_SPECS if spec.name == "black_refresh_queue")
    surfaces = {
        "caption": spec.caption,
        "alt": spec.alt,
        "svg": refresh_queue_svg(),
        "manuscript": " ".join(_read("04_examples.md").split()),
    }
    for name, surface in surfaces.items():
        assert f"{len(omitted)} dated declarations" not in surface, name
    assert f"{len(omitted)} declarations the queue omits" in surfaces["caption"]
    assert f"{len(omitted)} declarations the queue omits" in surfaces["manuscript"]
    assert f"Omitted from the queue ({len(omitted)} declarations)" in surfaces["svg"]
    # The kept rows really are all dated, so that half of the wording stands.
    from black_line.figures.horizon_figures import horizon_rows

    assert horizon_rows() and all(row.noted_on for row in horizon_rows())


def test_coverage_table_rows_match_the_registry() -> None:
    rows = {row.tag: row for row in coverage_matrix(BLACK_PRACTICES)}
    text = _read("03_practices.md")
    registry_size = len(BLACK_PRACTICES)
    for tag, row in rows.items():
        assert (
            f"| `{tag}` | {row.practice_count} of {registry_size} "
            f"| {row.required_label_count} |" in text
        )
    assert all(len(practice.required_evidence) == 2 for practice in BLACK_PRACTICES), (
        "the 'exactly two required labels' prose depends on this"
    )
    assert sum(row.practice_count for row in rows.values()) == 27


def test_every_incremental_table_row_re_derives() -> None:
    """Every column of every incremental-table row is recomputed.

    All six columns are captured. The two that used to be discarded — the
    labels added since the previous row, and the practice completed at that
    step — are the ones a reader most needs to trust, and only three of the ten
    rows had the practice name pinned anywhere.
    """
    text = _read("04_examples.md")
    rows = re.findall(
        r"^\| (\d+) \| (.+?) \| (\d+) \| (.+?) \| (\d+) of 8 \| `(\w+)` \|$",
        text,
        flags=re.MULTILINE,
    )
    assert [int(row[0]) for row in rows] == [0, 1, 2, 4, 6, 8, 10, 12, 14, 16]
    previous_step = 0
    previous_aligned: set[str] = set()
    for step_s, added_s, declared_s, completed_s, aligned_s, status_s in rows:
        step = int(step_s)
        assert int(declared_s) == step
        assessment = evaluate_work(
            WorkAttempt(
                "literature synthesis on staleness semantics",
                frozenset({"research"}),
                frozenset(PATH_LABELS[:step]),
            ),
            BLACK_PRACTICES,
        )
        assert assessment.status.value == status_s
        aligned = {
            finding.practice_id
            for finding in assessment.findings
            if finding.status is PracticeStatus.ALIGNED
        }
        assert len(aligned) == int(aligned_s)

        # Column 2: the labels added since the previous listed row.
        expected_added = list(PATH_LABELS[previous_step:step])
        declared_added = (
            []
            if added_s.strip() == "—"
            else [item.strip().strip("`") for item in added_s.split(",")]
        )
        assert declared_added == expected_added, step

        # Column 4: the practice whose finding flips to ALIGNED at this step.
        flipped = sorted(aligned - previous_aligned)
        declared_completed = (
            [] if completed_s.strip() == "—" else [completed_s.strip().strip("`")]
        )
        assert declared_completed == flipped, step

        previous_step = step
        previous_aligned = aligned


def test_coverage_table_practice_column_re_derives() -> None:
    """The coverage table's fourth column is the row's own practice ids."""

    text = _read("03_practices.md")
    for row in coverage_matrix(BLACK_PRACTICES):
        expected = ", ".join(f"`{practice_id}`" for practice_id in row.practice_ids)
        assert (
            f"| `{row.tag}` | {row.practice_count} of {len(BLACK_PRACTICES)} "
            f"| {row.required_label_count} | {expected} |" in text
        ), row.tag


def test_every_decay_table_row_re_derives() -> None:
    """Each decay-table row is recomputed across all four status columns."""
    text = _read("04_examples.md")
    rows = re.findall(
        r"^\| (\d+) \| `(\w+)` \| `(\w+)` \| `(\w+)` \| `(\w+)` \|$",
        text,
        flags=re.MULTILINE,
    )
    assert [int(row[0]) for row in rows] == [0, 30, 31, 51, 52, 70]
    practice = next(p for p in BLACK_PRACTICES if "data" in p.tags)
    full = practice.required_evidence
    for age_s, w30, w51, wnone, missing in rows:
        age = int(age_s)
        points = staleness_profile(
            _dated_attempt(age, full), (30, 51, None), as_of=DECAY_AS_OF
        )
        assert tuple(point.status.value for point in points) == (w30, w51, wnone)
        (point,) = staleness_profile(
            _dated_attempt(age, full[:1]), (30,), as_of=DECAY_AS_OF
        )
        assert point.status.value == missing


def test_coverage_summary_literal_matches_the_matrix() -> None:
    """The '27 of the 55 tag-practice cells' prose literal is derived."""
    text = _read("03_practices.md")
    rows = coverage_matrix(BLACK_PRACTICES)
    applicable = sum(row.practice_count for row in rows)
    total = len(rows) * len(BLACK_PRACTICES)
    assert f"{applicable} of the {total} tag-practice cells" in text


# --- formalism section bindings (03b_formalism.md) ---------------------------


def test_formalism_strict_boundary_witness_re_derives() -> None:
    """Proposition 6's aged-51 witness is recomputed through the public API."""
    practice = next(p for p in BLACK_PRACTICES if "data" in p.tags)
    points = staleness_profile(
        _dated_attempt(51, practice.required_evidence),
        (50, 51, None),
        as_of=DECAY_AS_OF,
    )
    assert [point.status.value for point in points] == [
        "NEEDS_EVIDENCE",
        "ALIGNED",
        "ALIGNED",
    ]
    text = _collapsed("03b_formalism.md")
    assert "aged exactly $51$ days is fresh under $\\omega = 51$" in text
    assert "stale under $\\omega = 50$" in text
    assert "staleness begins at age $\\omega + 1$" in text


def test_formalism_window_sweep_witness_re_derives() -> None:
    """Proposition 7's fully-enumerated integer window sweep is recomputed."""
    practice = next(p for p in BLACK_PRACTICES if "data" in p.tags)
    attempt = _dated_attempt(51, practice.required_evidence)
    windows: tuple[int | None, ...] = tuple(range(0, 91)) + (None,)
    points = staleness_profile(attempt, windows, as_of=DECAY_AS_OF)
    for point in points:
        expected = (
            AssessmentStatus.NEEDS_EVIDENCE
            if point.max_evidence_age_days is not None
            and point.max_evidence_age_days < 51
            else AssessmentStatus.ALIGNED
        )
        assert point.status is expected, point
    ranks = [status_rank(point.status) for point in points]
    assert ranks == sorted(ranks)
    text = _collapsed("03b_formalism.md")
    assert "`NEEDS_EVIDENCE` for every $\\omega < 51$" in text
    assert "`ALIGNED` for every $\\omega \\ge 51$" in text


def test_formalism_coverage_algebra_re_derives() -> None:
    """Proposition 8's row tuples and both identities are recomputed."""
    rows = coverage_matrix(BLACK_PRACTICES)
    text = _collapsed("03b_formalism.md")
    for row in rows:
        assert row.required_label_count == 2 * row.practice_count, row.tag
        assert (
            f"(`{row.tag}`, {row.practice_count}, {row.required_label_count})" in text
        ), row.tag
    filled = sum(row.practice_count for row in rows)
    total = len(rows) * len(BLACK_PRACTICES)
    assert f"${filled}$ of the ${total}$ tag-practice cells" in text


def test_formalism_digest_claims_re_derive() -> None:
    """Proposition 9's shape and permutation-invariance claims are recomputed."""
    digest = registry_digest(BLACK_PRACTICES)
    assert digest == registry_digest(tuple(reversed(BLACK_PRACTICES)))
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")
    text = _collapsed("03b_formalism.md")
    assert "64 lowercase hexadecimal characters" in text


def test_formalism_ladder_matches_exported_order() -> None:
    """Proposition 10's ranks and the OUTSIDE_SCOPE refusal are recomputed."""
    assert [status.value for status in DECLARATION_STATUS_ORDER] == [
        "NEEDS_REWORK",
        "NEEDS_EVIDENCE",
        "ALIGNED",
    ]
    assert [status_rank(status) for status in DECLARATION_STATUS_ORDER] == [0, 1, 2]
    with pytest.raises(ValueError, match="OUTSIDE_SCOPE"):
        status_rank(AssessmentStatus.OUTSIDE_SCOPE)
    text = _collapsed("03b_formalism.md")
    assert "ranks $0$, $1$, and $2$" in text


def test_formalism_test_references_all_exist() -> None:
    """Every `tests/file::function` reference in the formalism section is real."""
    text = _read("03b_formalism.md")
    refs = re.findall(r"`tests/(test_\w+\.py)::(test_\w+)`", text)
    assert len(refs) >= 15, "the binding table should reference the suite densely"
    tests_dir = Path(__file__).resolve().parent
    for filename, function in sorted(set(refs)):
        source = (tests_dir / filename).read_text(encoding="utf-8")
        assert f"def {function}(" in source, f"unknown reference {filename}::{function}"


# --- method-section and sibling-tense bindings -------------------------------


def test_method_prose_matches_the_global_emptiness_branch() -> None:
    """02_method.md must describe the first branch as attempt-wide, not per-practice.

    The counter-example is executed here: an attempt declaring one irrelevant
    label has, for `question-first`, none of its own required labels — yet the
    finding is NEEDS_REWORK, because the first branch tests the attempt's whole
    evidence set. Prose reading it as a per-practice test is wrong about the
    code and contradicts the formalism section's own remark.
    """

    assessment = evaluate_work(
        WorkAttempt("work", frozenset({"research"}), frozenset({"unrelated"})),
        BLACK_PRACTICES,
    )
    finding = next(f for f in assessment.findings if f.practice_id == "question-first")
    assert finding.status is PracticeStatus.NEEDS_REWORK
    assert not set(("question", "scope")) & {"unrelated"}

    text = _collapsed("02_method.md")
    assert (
        "if the attempt declared no usable evidence at all, every selected "
        "practice returns `NEEDS_EVIDENCE`" in text
    )
    assert "missing work rather than an empty declaration" in text
    assert "A selected practice with no usable evidence" not in text, (
        "the per-practice reading of the first branch is the defect"
    )


def test_batch_section_prose_re_derives_from_the_executed_battery() -> None:
    """The batch paragraph names counts, a ranking, and a reach; re-derive all three.

    The caption is bound to the figure spec elsewhere. This binds the
    *interpretation* around it: the never-open practice, the two most
    frequently open ones, and the registry tags the prose blames for that,
    each recomputed from the executed battery and the registry.
    """

    from black_line.figures.batch_figures import batch_gap_counts, batch_never_gapped
    from black_line.figures.scenarios import batch_assessments

    # Line wrapping is an editorial choice, so the comparison is against the
    # whitespace-collapsed prose; the words and the derived values are not.
    text = " ".join(_read("04_examples.md").split())
    assessments = batch_assessments()
    gaps = batch_gap_counts()
    never = batch_never_gapped()

    assert len(assessments) == 8
    assert len(never) == 1, "the prose says 'the only practice'"
    assert f"`{never[0]}` is the only practice the batch never leaves open" in text

    top = [practice_id for practice_id, count in gaps if count == gaps[0][1]]
    assert len(top) == 2, "the prose names exactly two leaders"
    assert f"`{top[0]}` and `{top[1]}` are open most often" in text

    by_id = {practice.id: practice for practice in BLACK_PRACTICES}
    first_tags, second_tags = (sorted(by_id[practice_id].tags) for practice_id in top)
    assert (
        f"`{first_tags[0]}` and `{first_tags[1]}` for the first, "
        f"`{second_tags[0]}` and `{second_tags[1]}` for the second" in text
    )
    # And the practice the batch never leaves open is exactly the one every
    # applicable attempt satisfied, which is what the prose asserts next.
    assert "all named a question and a scope" in text
    assert set(by_id[never[0]].required_evidence) == {"question", "scope"}


def test_conclusion_uses_the_same_tense_as_the_rest_of_the_manuscript() -> None:
    """The sibling enumeration must not describe shipped works as forthcoming.

    The predicate is taken from 05_limits.md rather than restated, so the two
    enumerations cannot drift apart again. The White Line predicate also has to
    match how White Line describes itself — absence, restraint, and
    unknowability — rather than shrinking to "uncertainty", so the stale list
    below rejects the narrower reading in either file.
    """

    limits = _collapsed("05_limits.md")
    conclusion = _collapsed("06_conclusion.md")
    for predicate in (
        "White Line marks absence, restraint, and unknowability",
        "Golden Line addresses direction and aspiration",
    ):
        assert predicate in limits
    assert "White Line marks absence, restraint, and unknowability" in conclusion
    assert "Golden Line holds the higher thread" in conclusion
    for stale in ("will hold the higher thread", "will mark absence"):
        assert stale not in conclusion, stale
    for narrowed in ("absence and uncertainty", "the absence and uncertainty"):
        assert narrowed not in conclusion, narrowed
        assert narrowed not in limits, narrowed
