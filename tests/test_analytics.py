"""Real-data tests for the pure analytics surface.

The property-style sweeps use a fixed seed and the real evaluator throughout;
nothing here mocks or reimplements evaluator semantics.
"""

import random
from dataclasses import replace
from datetime import date, timedelta

import pytest

from black_line import (
    BLACK_PRACTICES,
    DECLARATION_STATUS_ORDER,
    OMISSION_STALE,
    OMISSION_UNDATED,
    OMISSION_UNREQUIRED,
    AssessmentStatus,
    BlackAssessment,
    BlackPractice,
    EvidenceItem,
    PracticeFinding,
    PracticeStatus,
    WorkAttempt,
    coverage_matrix,
    declaration_status_path,
    evaluate_work,
    no_status_regression,
    refresh_horizon,
    refresh_horizon_omissions,
    staleness_profile,
    status_rank,
    summarize_assessments,
)

SEED = 20260722
AS_OF = "2026-07-01"

#: The research tag's full required-label sequence in registry order,
#: deduplicated — 16 labels reaching 8 practices (verified by derivation).
RESEARCH_LABELS: tuple[str, ...] = tuple(
    dict.fromkeys(
        label
        for practice in BLACK_PRACTICES
        if "research" in practice.tags
        for label in practice.required_evidence
    )
)

DATA_PRACTICE = next(p for p in BLACK_PRACTICES if "data" in p.tags)


# --- coverage_matrix --------------------------------------------------------


def test_coverage_matrix_pins_the_registry_reach_and_burden() -> None:
    rows = {row.tag: row for row in coverage_matrix(BLACK_PRACTICES)}
    expected = {
        "analysis": (7, 14),
        "data": (1, 2),
        "engineering": (6, 12),
        "research": (8, 16),
        "writing": (5, 10),
    }
    assert set(rows) == set(expected)
    for tag, (reach, burden) in expected.items():
        assert rows[tag].practice_count == reach, tag
        assert rows[tag].required_label_count == burden, tag


def test_coverage_matrix_rows_are_sorted_and_preserve_registry_order() -> None:
    rows = coverage_matrix(BLACK_PRACTICES)
    assert [row.tag for row in rows] == sorted(row.tag for row in rows)
    registry_order = [practice.id for practice in BLACK_PRACTICES]
    for row in rows:
        positions = [registry_order.index(pid) for pid in row.practice_ids]
        assert positions == sorted(positions), row.tag


def test_coverage_matrix_total_cells_match_tag_declarations() -> None:
    rows = coverage_matrix(BLACK_PRACTICES)
    filled = sum(row.practice_count for row in rows)
    assert filled == sum(len(practice.tags) for practice in BLACK_PRACTICES) == 27


def test_coverage_matrix_on_a_custom_registry_uses_the_tag_union() -> None:
    custom = (
        BlackPractice("a", "A", "wire", frozenset({"zeta", "alpha"}), ("x", "y")),
        BlackPractice("b", "B", "wire", frozenset({"alpha"}), ("z",)),
    )
    rows = coverage_matrix(custom)
    assert [row.tag for row in rows] == ["alpha", "zeta"]
    assert rows[0].practice_ids == ("a", "b")
    assert rows[0].required_label_count == 3
    assert rows[1].practice_ids == ("a",)
    assert rows[1].required_label_count == 2


# --- staleness_profile ------------------------------------------------------


def _dated_attempt(age_days: int, labels: tuple[str, ...]) -> WorkAttempt:
    noted = (date.fromisoformat(AS_OF) - timedelta(days=age_days)).isoformat()
    return WorkAttempt(
        "provenance-noted data pull",
        frozenset({"data"}),
        dated_evidence=tuple(EvidenceItem(label, noted) for label in labels),
    )


def test_staleness_profile_pins_the_strict_inequality_boundary() -> None:
    attempt = _dated_attempt(51, DATA_PRACTICE.required_evidence)
    points = staleness_profile(attempt, (50, 51, None), as_of=AS_OF)
    assert [point.max_evidence_age_days for point in points] == [50, 51, None]
    assert points[0].status is AssessmentStatus.NEEDS_EVIDENCE
    assert points[1].status is AssessmentStatus.ALIGNED
    assert points[2].status is AssessmentStatus.ALIGNED


def test_staleness_profile_matches_direct_evaluator_calls() -> None:
    attempt = _dated_attempt(31, DATA_PRACTICE.required_evidence)
    for point in staleness_profile(attempt, (7, 30, 31, None), as_of=AS_OF):
        direct = evaluate_work(
            attempt, as_of=AS_OF, max_evidence_age_days=point.max_evidence_age_days
        )
        assert point.status is direct.status


def test_staleness_profile_partial_declaration_is_rework_at_every_window() -> None:
    attempt = _dated_attempt(10, DATA_PRACTICE.required_evidence[:1])
    for point in staleness_profile(attempt, (5, 30, None), as_of=AS_OF):
        assert point.status is AssessmentStatus.NEEDS_REWORK


def test_widening_the_window_never_regresses_coverage_rank() -> None:
    rng = random.Random(SEED)
    labels = DATA_PRACTICE.required_evidence
    for _ in range(25):
        ages = [rng.randrange(0, 90) for _ in labels]
        noted = [
            (date.fromisoformat(AS_OF) - timedelta(days=age)).isoformat()
            for age in ages
        ]
        attempt = WorkAttempt(
            "window sweep",
            frozenset({"data"}),
            dated_evidence=tuple(
                EvidenceItem(label, when) for label, when in zip(labels, noted)
            ),
        )
        points = staleness_profile(attempt, tuple(range(0, 95, 5)), as_of=AS_OF)
        ranks = [status_rank(point.status) for point in points]
        assert ranks == sorted(ranks), ages


# --- summarize_assessments --------------------------------------------------


def test_summarize_assessments_counts_statuses_and_open_finding_families() -> None:
    aligned = evaluate_work(
        WorkAttempt(
            "full data pull",
            frozenset({"data"}),
            frozenset(DATA_PRACTICE.required_evidence),
        ),
        as_of=AS_OF,
    )
    rework = evaluate_work(
        WorkAttempt(
            "bare research note", frozenset({"research"}), frozenset({"question"})
        ),
        as_of=AS_OF,
    )
    outside = evaluate_work(WorkAttempt("a song", frozenset({"music"})), as_of=AS_OF)
    summary = summarize_assessments((aligned, rework, outside))
    assert summary.total == 3
    assert summary.status_counts == (
        ("ALIGNED", 1),
        ("NEEDS_EVIDENCE", 0),
        ("NEEDS_REWORK", 1),
        ("OUTSIDE_SCOPE", 1),
    )
    # The research attempt reaches 8 practices; only question-first has a
    # partial declaration, and every finding is non-ALIGNED.
    assert sum(count for _, count in summary.open_finding_kind_counts) == 8
    kinds = dict(summary.open_finding_kind_counts)
    assert kinds["FRAMING"] == 1
    assert kinds["VERIFICATION"] == 3


def test_summarize_assessments_is_empty_safe_and_shape_stable() -> None:
    summary = summarize_assessments(())
    assert summary.total == 0
    assert summary.status_counts == (
        ("ALIGNED", 0),
        ("NEEDS_EVIDENCE", 0),
        ("NEEDS_REWORK", 0),
        ("OUTSIDE_SCOPE", 0),
    )
    assert summary.open_finding_kind_counts == ()


def test_summarize_assessments_buckets_unknown_practice_ids() -> None:
    stray = BlackAssessment(
        AssessmentStatus.NEEDS_REWORK,
        (
            PracticeFinding(
                "not-in-registry", PracticeStatus.NEEDS_REWORK, ("missing",)
            ),
        ),
    )
    summary = summarize_assessments((stray,))
    assert summary.open_finding_kind_counts == (("UNKNOWN", 1),)


def test_summarize_assessments_ignores_aligned_findings() -> None:
    aligned = evaluate_work(
        WorkAttempt(
            "full data pull",
            frozenset({"data"}),
            frozenset(DATA_PRACTICE.required_evidence),
        ),
        as_of=AS_OF,
    )
    assert summarize_assessments((aligned,)).open_finding_kind_counts == ()


# --- refresh_horizon --------------------------------------------------------


def test_refresh_horizon_sorts_by_remaining_days_and_omits_stale() -> None:
    attempt = WorkAttempt(
        "data provenance review",
        frozenset({"data"}),
        frozenset({"transform_log", "data_origin"}),
        dated_evidence=(
            EvidenceItem("transform_log", "2026-06-15"),
            EvidenceItem("data_origin", "2026-01-01"),
        ),
    )
    horizon = refresh_horizon(attempt, as_of="2026-07-18", max_evidence_age_days=90)
    assert [item.label for item in horizon] == ["transform_log"]
    assert horizon[0].days_until_stale == 57


def test_refresh_horizon_skips_undated_evidence_items() -> None:
    attempt = WorkAttempt(
        "method note",
        frozenset({"research"}),
        frozenset({"method", "scope"}),
        dated_evidence=(
            EvidenceItem("method", "2026-07-10"),
            EvidenceItem("scope"),
        ),
    )
    horizon = refresh_horizon(attempt, as_of="2026-07-18", max_evidence_age_days=30)
    assert [item.label for item in horizon] == ["method"]


def test_refresh_horizon_accepts_date_as_of() -> None:
    attempt = WorkAttempt(
        "method note",
        frozenset({"research"}),
        frozenset({"method"}),
        dated_evidence=(EvidenceItem("method", "2026-07-10"),),
    )
    horizon = refresh_horizon(
        attempt, as_of=date(2026, 7, 18), max_evidence_age_days=30
    )
    assert horizon == (
        refresh_horizon(attempt, as_of="2026-07-18", max_evidence_age_days=30)[0],
    )


# --- status ordering --------------------------------------------------------


def test_declaration_status_order_ranks_rework_lowest_and_aligned_highest() -> None:
    assert DECLARATION_STATUS_ORDER == (
        AssessmentStatus.NEEDS_REWORK,
        AssessmentStatus.NEEDS_EVIDENCE,
        AssessmentStatus.ALIGNED,
    )
    ranks = [status_rank(status) for status in DECLARATION_STATUS_ORDER]
    assert ranks == [0, 1, 2]


def test_status_rank_rejects_outside_scope() -> None:
    with pytest.raises(ValueError, match="OUTSIDE_SCOPE"):
        status_rank(AssessmentStatus.OUTSIDE_SCOPE)


# --- declaration_status_path and monotonicity sweeps ------------------------


def test_research_declaration_path_pins_the_17_step_fixture() -> None:
    assert len(RESEARCH_LABELS) == 16
    path = declaration_status_path(
        "literature synthesis", ("research",), RESEARCH_LABELS, as_of=AS_OF
    )
    assert len(path) == 17
    assert path[0] is AssessmentStatus.NEEDS_EVIDENCE
    assert path[-1] is AssessmentStatus.ALIGNED
    assert all(status is AssessmentStatus.NEEDS_REWORK for status in path[1:-1])


def test_boundary_regression_is_real_and_the_checker_can_reject() -> None:
    """Positive control: the empty-declaration boundary is a rank regression."""

    path = declaration_status_path(
        "literature synthesis", ("research",), RESEARCH_LABELS, as_of=AS_OF
    )
    assert not no_status_regression(path)
    assert no_status_regression(path[1:])


def test_sampled_permutations_never_regress_after_first_declaration() -> None:
    rng = random.Random(SEED)
    for _ in range(20):
        labels = list(RESEARCH_LABELS)
        rng.shuffle(labels)
        path = declaration_status_path(
            "literature synthesis", ("research",), tuple(labels), as_of=AS_OF
        )
        assert len(path) == 17
        assert path[0] is AssessmentStatus.NEEDS_EVIDENCE
        assert path[-1] is AssessmentStatus.ALIGNED
        assert no_status_regression(path[1:]), labels


def test_permutations_with_irrelevant_labels_still_never_regress() -> None:
    rng = random.Random(SEED + 1)
    for _ in range(10):
        labels = list(RESEARCH_LABELS) + ["unrelated-a", "unrelated-b"]
        rng.shuffle(labels)
        path = declaration_status_path(
            "literature synthesis", ("research",), tuple(labels), as_of=AS_OF
        )
        assert no_status_regression(path[1:]), labels


def test_declaration_path_under_staleness_never_regresses_after_first_step() -> None:
    """Fresh-label accumulation is monotone even with a stale dated backdrop."""

    rng = random.Random(SEED + 2)
    stale_backdrop = tuple(
        EvidenceItem(label, "2025-01-01") for label in RESEARCH_LABELS[:4]
    )
    for _ in range(10):
        labels = list(RESEARCH_LABELS)
        rng.shuffle(labels)
        statuses = []
        for step in range(len(labels) + 1):
            attempt = WorkAttempt(
                "aged research trail",
                frozenset({"research"}),
                frozenset(labels[:step]),
                dated_evidence=stale_backdrop,
            )
            statuses.append(
                evaluate_work(attempt, as_of=AS_OF, max_evidence_age_days=30).status
            )
        assert no_status_regression(statuses), labels


def test_declaration_path_accepts_custom_registries() -> None:
    demo = BlackPractice(
        "demo", "Demo", "wire", frozenset({"research"}), ("alpha", "beta")
    )
    path = declaration_status_path(
        "demo work", ("research",), ("alpha", "beta"), practices=(demo,), as_of=AS_OF
    )
    assert path == (
        AssessmentStatus.NEEDS_EVIDENCE,
        AssessmentStatus.NEEDS_REWORK,
        AssessmentStatus.ALIGNED,
    )


# --- refresh_horizon consumes its registry -----------------------------------


def test_refresh_horizon_filters_to_labels_the_registry_requires() -> None:
    """The `practices` argument is read, not decorative.

    A caller supplying a narrower registry expects a narrower queue. Before
    this binding the parameter was accepted and ignored, so an empty registry
    still returned every dated label.
    """

    attempt = WorkAttempt(
        "provenance and framing review",
        frozenset({"data", "research"}),
        dated_evidence=(
            EvidenceItem("data_origin", "2026-06-01"),
            EvidenceItem("question", "2026-06-10"),
            EvidenceItem("dashboard_link", "2026-06-20"),
        ),
    )
    full = refresh_horizon(attempt, as_of="2026-07-18", max_evidence_age_days=90)
    assert [item.label for item in full] == ["data_origin", "question"]

    only_provenance = tuple(p for p in BLACK_PRACTICES if p.id == "data-provenance")
    narrowed = refresh_horizon(
        attempt,
        practices=only_provenance,
        as_of="2026-07-18",
        max_evidence_age_days=90,
    )
    assert [item.label for item in narrowed] == ["data_origin"]
    assert narrowed[0].practice_ids == ("data-provenance",)

    assert (
        refresh_horizon(
            attempt, practices=(), as_of="2026-07-18", max_evidence_age_days=90
        )
        == ()
    )


def test_refresh_horizon_names_every_practice_requiring_a_label() -> None:
    """A label two practices require names both, in registry declaration order."""

    shared = tuple(
        replace(practice, required_evidence=("question", "scope"))
        for practice in BLACK_PRACTICES[:2]
    )
    attempt = WorkAttempt(
        "shared label",
        frozenset({"research"}),
        dated_evidence=(EvidenceItem("question", "2026-07-01"),),
    )
    (item,) = refresh_horizon(
        attempt, practices=shared, as_of="2026-07-18", max_evidence_age_days=90
    )
    assert item.practice_ids == tuple(practice.id for practice in shared)


def test_refresh_horizon_omissions_name_each_excluded_class() -> None:
    """Every omission the queue makes is reported with its reason."""

    attempt = WorkAttempt(
        "mixed declaration",
        frozenset({"data"}),
        dated_evidence=(
            EvidenceItem("data_origin", "2026-06-25"),
            EvidenceItem("transform_log", "2020-01-01"),
            EvidenceItem("handoff", None),
            EvidenceItem("dashboard_link", "2026-06-25"),
        ),
    )
    omissions = refresh_horizon_omissions(
        attempt, as_of="2026-07-18", max_evidence_age_days=30
    )
    assert {row.label: row.reason for row in omissions} == {
        "transform_log": OMISSION_STALE,
        "handoff": OMISSION_UNDATED,
        "dashboard_link": OMISSION_UNREQUIRED,
    }
    kept = refresh_horizon(attempt, as_of="2026-07-18", max_evidence_age_days=30)
    assert {item.label for item in kept} == {"data_origin"}
    # Every dated declaration is either scheduled or explained; nothing vanishes.
    assert {item.label for item in kept} | {row.label for row in omissions} == {
        item.label for item in attempt.dated_evidence
    }


def test_refresh_horizon_omissions_are_empty_when_nothing_is_excluded() -> None:
    attempt = WorkAttempt(
        "clean declaration",
        frozenset({"data"}),
        dated_evidence=(EvidenceItem("data_origin", "2026-07-01"),),
    )
    assert (
        refresh_horizon_omissions(attempt, as_of="2026-07-18", max_evidence_age_days=90)
        == ()
    )


def test_no_status_regression_refuses_an_outside_scope_sequence() -> None:
    """The documented `Raises` clause, exercised.

    `summarize_assessments` counts OUTSIDE_SCOPE, so a caller summarizing a
    mixed batch can reach this path; an undocumented exception there is a trap.
    """

    with pytest.raises(ValueError, match="OUTSIDE_SCOPE"):
        no_status_regression([AssessmentStatus.ALIGNED, AssessmentStatus.OUTSIDE_SCOPE])
    assert "Raises" in no_status_regression.__doc__
    assert "OUTSIDE_SCOPE" in no_status_regression.__doc__
