from dataclasses import replace

import pytest

import black_line as bl


PRACTICE = bl.BLACK_PRACTICES[0]


@pytest.mark.parametrize(
    "changes, code",
    [
        ({"required_evidence": ("Alpha",)}, "required_labels_not_normalized"),
        ({"required_evidence": ("alpha", "alpha")}, "required_labels_duplicate"),
        ({"tags": frozenset({"Research"})}, "tags_not_normalized"),
    ],
)
def test_finding_6_runtime_and_battery_share_shape_defects(changes, code):
    registry = (replace(PRACTICE, **changes),)
    result = bl.evaluate_work(
        bl.WorkAttempt("work", frozenset({"research"}), frozenset({"alpha"})),
        registry,
        as_of="2026-07-18",
    )
    assert result.status is bl.AssessmentStatus.NEEDS_REWORK
    assert result.findings == ()
    assert code in result.intake_codes
    assert any(
        code in check.detail
        for check in bl.all_invariants(registry)
        if not check.passed
    )


def test_finding_6_custom_registry_policy_is_separate_from_shape():
    registry = (
        replace(PRACTICE, tags=frozenset({"custom"}), required_evidence=("alpha",)),
    )
    result = bl.evaluate_work(
        bl.WorkAttempt("work", frozenset({"custom"}), frozenset({"alpha"})), registry
    )
    assert result.status is bl.AssessmentStatus.ALIGNED
    assert not bl.invariants_hold(registry)


@pytest.mark.parametrize(
    "registry",
    [
        (replace(PRACTICE, tags=frozenset({"research", 1})),),
        (replace(PRACTICE, required_evidence=([], [])),),
        (object(),),
        (replace(PRACTICE, id=[]),),
        (replace(PRACTICE, required_evidence=None, tags=3, kind=[]),),
        (object(), replace(PRACTICE, tags=frozenset({1}), required_evidence=([],))),
    ],
)
def test_finding_7_seven_named_checks_are_total_on_malformed_shapes(registry):
    checks = bl.all_invariants(registry)
    assert tuple(check.name for check in checks) == tuple(
        check.name for check in bl.all_invariants()
    )
    assert len(checks) == 7
    assert not all(check.passed for check in checks)
    assert all(check.detail for check in checks)
    assert bl.evaluate_work(bl.WorkAttempt("work"), registry).intake_codes


@pytest.mark.parametrize(
    "evidence, expected",
    [
        (frozenset(), bl.PracticeStatus.NEEDS_EVIDENCE),
        (frozenset({"unrelated"}), bl.PracticeStatus.NEEDS_REWORK),
    ],
)
def test_finding_8_empty_versus_irrelevant_projection_context(evidence, expected):
    assessment, surfaces = bl.evaluate_with_surfaces(
        bl.WorkAttempt("work", PRACTICE.tags, evidence), (PRACTICE,)
    )
    assert surfaces[0].present == ()
    assert surfaces[0].missing == PRACTICE.required_evidence
    assert assessment.evidence_declared is bool(evidence)
    projected = bl.project_finding(surfaces[0], assessment.evidence_declared)
    assert projected.status is expected
    assert (projected,) == assessment.findings


@pytest.mark.parametrize(
    "digest_mode", ["different_kind", "missing_id", "mixed", "empty"]
)
def test_finding_9_family_attribution_never_reinterprets_pinned_method(digest_mode):
    first = (PRACTICE,)
    second = (replace(PRACTICE, kind=bl.PracticeKind.STEWARDSHIP),)
    if second == first:
        second = (replace(PRACTICE, kind=bl.PracticeKind.METHOD),)
    old = bl.evaluate_work(bl.WorkAttempt("work", PRACTICE.tags), first)
    if digest_mode == "missing_id":
        old = replace(old, findings=(replace(old.findings[0], practice_id="absent"),))
        second = first
    if digest_mode == "empty":
        old = replace(old, registry_digest="")
    batch = (
        (old, bl.evaluate_work(bl.WorkAttempt("new", PRACTICE.tags), second))
        if digest_mode == "mixed"
        else (old,)
    )
    summary = bl.summarize_assessments(batch, second)
    assert dict(summary.open_finding_kind_counts)["UNKNOWN"] == 1
    assert sum(count for _, count in summary.status_counts) == len(batch)
    assert len(summary.registry_partitions) == len({a.registry_digest for a in batch})
