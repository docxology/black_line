import hashlib
import json
from dataclasses import replace

import pytest

import black_line as bl


def work():
    return bl.WorkAttempt(
        "original description",
        frozenset({"data"}),
        dated_evidence=(bl.EvidenceItem(" DATA_ORIGIN ", "2026-07-01"),),
    )


def record():
    return bl.evaluation_record(
        work(),
        as_of="2026-07-18",
        max_evidence_age_days=30,
        subject_id="subject",
        source_snapshot_refs=("snapshot-1",),
    )


def test_finding_4_result_is_not_input_identity_and_bundle_replays():
    first = work()
    second = replace(first, description="different description")
    assert bl.canonical_assessment(
        bl.evaluate_work(first, as_of="2026-07-18")
    ) == bl.canonical_assessment(bl.evaluate_work(second, as_of="2026-07-18"))
    original = record()
    restored = bl.load_evaluation_record(bl.canonical_evaluation_record(original))
    assert restored == original
    assert bl.replay_evaluation_record(restored) == (
        original.assessment,
        original.surfaces,
    )
    assert original.normalized_tags == frozenset({"data"})
    assert original.fresh_labels == frozenset({"data_origin"})
    assert original.attempt == first


@pytest.mark.parametrize(
    "field, value",
    [
        ("description", "changed"),
        ("tags", frozenset({"data", "music"})),
        ("dated_evidence", (bl.EvidenceItem("data_origin", "2026-07-02"),)),
    ],
)
def test_finding_4_declaration_mutations_change_identity(field, value):
    original = record()
    changed = bl.evaluation_record(
        replace(work(), **{field: value}), as_of="2026-07-18", max_evidence_age_days=30
    )
    assert bl.evaluation_record_digest(original) != bl.evaluation_record_digest(changed)


def test_finding_4_configuration_and_version_are_retained():
    original = record()
    for changed in (
        replace(original, max_evidence_age_days=31),
        replace(original, evaluator_version="0.0.0"),
    ):
        assert bl.evaluation_record_digest(original) != bl.evaluation_record_digest(
            changed
        )
    with pytest.raises(ValueError, match="version"):
        bl.replay_evaluation_record(replace(original, evaluator_version="0.0.0"))
    payload = json.loads(bl.canonical_evaluation_record(original))
    payload["registry"][0]["wire"] = "edited"
    with pytest.raises(ValueError, match="registry"):
        bl.load_evaluation_record(json.dumps(payload))


@pytest.mark.parametrize(
    "attempt",
    [
        replace(work(), description=object()),
        replace(work(), evidence=frozenset({1})),
        replace(work(), dated_evidence=(object(),)),
    ],
)
def test_finding_4_arbitrary_python_objects_are_not_serialized(attempt):
    with pytest.raises((TypeError, ValueError), match="supported|text|EvidenceItem"):
        bl.evaluation_record(attempt, as_of="2026-07-18")


def test_finding_5_correspondence_is_separate_from_contract():
    assessment = bl.evaluate_work(work(), as_of="2026-07-18")
    envelope = bl.assessment_envelope(assessment)
    changed = replace(envelope, line_id="red_line", scope_and_nonclaims=())
    assert bl.envelope_matches_assessment(changed, assessment)
    check = bl.validate_envelope_contract(changed)
    assert not check.passed
    assert {"line_id", "scope_and_nonclaims"} <= {
        item.field for item in check.diagnostics
    }


@pytest.mark.parametrize("refs", ["snapshot-1", b"snapshot-1"])
def test_finding_5_bare_refs_container_is_rejected(refs):
    with pytest.raises(TypeError, match="container|collection"):
        bl.assessment_envelope(bl.evaluate_work(work()), source_snapshot_refs=refs)


@pytest.mark.parametrize("refs", [("one", "two"), ["one", "two"], iter(("one", "two"))])
def test_finding_5_reference_collections_are_retained(refs):
    assert bl.assessment_envelope(
        bl.evaluate_work(work()), source_snapshot_refs=refs
    ).source_snapshot_refs == ("one", "two")


@pytest.mark.parametrize(
    "field, value, valid, matches",
    [
        ("schema_version", "other/1.0", False, True),
        ("line_id", "red_line", False, True),
        ("subject_id", "allowed-context-change", True, True),
        ("review_date", "2026-07-19", True, False),
        ("registry_version", "0.0.0", True, True),
        ("registry_digest", "0" * 64, True, False),
        ("native_status", "ALIGNED", True, False),
        ("report_ref", "0" * 64, True, False),
        ("source_snapshot_refs", ("other",), True, True),
        ("scope_and_nonclaims", (), False, True),
    ],
)
def test_finding_5_all_envelope_fields_have_explicit_checks(
    field, value, valid, matches
):
    original = record()
    envelope = bl.assessment_envelope(
        original.assessment,
        subject_id=original.subject_id,
        source_snapshot_refs=original.source_snapshot_refs,
    )
    changed = replace(envelope, **{field: value})
    check = bl.validate_envelope_contract(changed)
    assert check.passed is valid
    assert bl.envelope_matches_assessment(changed, original.assessment) is matches
    assert not bl.envelope_matches_record(changed, original)
    if valid:
        assert set(check.unverified_context) == {
            "subject_id",
            "source_snapshot_refs",
            "registry_version",
        }


def test_finding_5_old_results_are_incomplete_and_method_version_is_pinned():
    assessment = bl.evaluate_work(work(), as_of="2026-07-18")
    assert assessment.evaluator_version == bl.__version__
    assert (
        bl.assessment_envelope(
            replace(assessment, evaluator_version="0.3.0")
        ).registry_version
        == "0.3.0"
    )
    old = bl.BlackAssessment(bl.AssessmentStatus.OUTSIDE_SCOPE, ())
    envelope = bl.assessment_envelope(old)
    assert not bl.validate_envelope_contract(envelope).passed
    with pytest.raises(ValueError, match="incomplete|contract"):
        bl.assessment_envelope(old, strict=True)


def test_canonical_1_0_bytes_do_not_include_new_context():
    assessment = bl.evaluate_work(work(), as_of="2026-07-18")
    payload = bl.canonical_assessment(assessment)
    assert json.loads(payload)["schema_version"] == "1.0"
    assert "evaluator_version" not in payload
    assert (
        bl.assessment_digest(assessment) == hashlib.sha256(payload.encode()).hexdigest()
    )
    assert (
        bl.canonical_assessment(replace(assessment, evaluator_version="0.0.0"))
        == payload
    )
