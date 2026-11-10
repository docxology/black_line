import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest

import black_line as bl


@pytest.fixture
def record():
    return bl.evaluation_record(
        bl.WorkAttempt(
            "original description",
            frozenset({"data"}),
            dated_evidence=(bl.EvidenceItem(" DATA_ORIGIN ", "2026-07-01"),),
        ),
        as_of="2026-07-18",
        max_evidence_age_days=30,
        subject_id="subject",
        source_snapshot_refs=("snapshot-1",),
    )


def test_canonical_result_matches_pinned_revision_fixture(record):
    expected = (
        (Path(__file__).parent / "fixtures" / "assessment-a40aa78.json")
        .read_text()
        .rstrip("\n")
    )
    assert bl.canonical_assessment(record.assessment) == expected


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", "unknown/2"),
        ("evaluator_version", 12),
        ("scope_and_nonclaims", []),
        ("source_snapshot_refs", "snapshot-1"),
        ("subject_id", 7),
        ("as_of", None),
        ("unexpected", True),
    ],
)
def test_loader_rejects_unsupported_and_incomplete_fields(record, field, value):
    payload = json.loads(bl.canonical_evaluation_record(record))
    payload[field] = value
    with pytest.raises((ValueError, TypeError)):
        bl.load_evaluation_record(json.dumps(payload))


@pytest.mark.parametrize("noted", [None, "bad", "2027-01-01", "2020-01-01"])
def test_replay_retains_supported_unusable_dates_and_intake(record, noted):
    original = bl.evaluation_record(
        replace(
            record.attempt, dated_evidence=(bl.EvidenceItem(" DATA_ORIGIN ", noted),)
        ),
        as_of="2026-07-18",
        max_evidence_age_days=30,
    )
    assert bl.replay_evaluation_record(
        bl.load_evaluation_record(bl.canonical_evaluation_record(original))
    ) == (original.assessment, original.surfaces)


@pytest.mark.parametrize(
    "field",
    [
        "assessment",
        "surfaces",
        "normalized_tags",
        "fresh_labels",
        "registry_digest",
        "evidence_declared",
    ],
)
def test_replay_detects_retained_output_and_intake_mutations(record, field):
    values = {
        "assessment": replace(record.assessment, intake_notes=("edited",)),
        "surfaces": (),
        "normalized_tags": frozenset({"other"}),
        "fresh_labels": frozenset(),
        "registry_digest": "0" * 64,
        "evidence_declared": False,
    }
    with pytest.raises(ValueError, match="replay differs"):
        bl.replay_evaluation_record(replace(record, **{field: values[field]}))


@pytest.mark.parametrize(
    "field",
    [
        "schema_version",
        "line_id",
        "subject_id",
        "review_date",
        "registry_version",
        "registry_digest",
        "native_status",
        "report_ref",
        "source_snapshot_refs",
        "scope_and_nonclaims",
    ],
)
def test_envelope_contract_rejects_malformed_field_types(record, field):
    envelope = bl.assessment_envelope(record.assessment)
    check = bl.validate_envelope_contract(replace(envelope, **{field: None}))
    assert not check.passed
    assert field in {item.field for item in check.diagnostics}


def test_full_structural_checks_accept_retained_archival_pair(record):
    envelope = bl.assessment_envelope(
        record.assessment,
        subject_id=record.subject_id,
        source_snapshot_refs=record.source_snapshot_refs,
        strict=True,
    )
    assert bl.validate_envelope_contract(envelope).passed
    assert bl.envelope_matches_record(envelope, record)


@pytest.mark.parametrize(
    "field",
    ["schema_version", "subject_id", "description", "evidence_declared", "practice_id"],
)
def test_archive_rejects_duplicate_fields_at_every_object_depth(record, field):
    serialized = bl.canonical_evaluation_record(record)
    marker = json.dumps(field) + ":"
    ambiguous = serialized.replace(marker, marker + "null," + marker, 1)
    with pytest.raises(ValueError, match="duplicate replay JSON field"):
        bl.load_evaluation_record(ambiguous)


def test_loading_does_not_claim_replay_or_repair_retained_output(record):
    changed = replace(
        record, assessment=replace(record.assessment, intake_notes=("edited",))
    )
    restored = bl.load_evaluation_record(bl.canonical_evaluation_record(changed))
    assert restored == changed
    with pytest.raises(ValueError, match="replay differs"):
        bl.replay_evaluation_record(restored)


@pytest.mark.parametrize(
    "path",
    [
        ("attempt", "description"),
        ("attempt", "tags", 0),
        ("attempt", "dated_evidence", 0, "label"),
        ("attempt", "dated_evidence", 0, "noted_on"),
        ("as_of",),
        ("evaluator_version",),
        ("registry_digest",),
        ("registry", 0, "id"),
        ("registry", 0, "title"),
        ("registry", 0, "wire"),
        ("registry", 0, "tags", 0),
        ("registry", 0, "required_evidence", 0),
        ("registry", 0, "kind"),
        ("assessment", "status"),
        ("assessment", "findings", 0, "practice_id"),
        ("assessment", "findings", 0, "status"),
        ("assessment", "findings", 0, "reasons", 0),
        ("assessment", "evaluated_as_of"),
        ("assessment", "registry_digest"),
        ("assessment_context", "evaluator_version"),
        ("surfaces", 0, "practice_id"),
        ("surfaces", 0, "present", 0),
        ("normalized_intake", "tags", 0),
        ("normalized_intake", "fresh", 0),
        ("subject_id",),
        ("source_snapshot_refs", 0),
        ("scope_and_nonclaims", 0),
    ],
)
@pytest.mark.parametrize("value", [[], {}, "\ud800", "\udfff"])
def test_loader_refuses_non_text_and_non_scalar_native_fields(record, path, value):
    payload = json.loads(bl.canonical_evaluation_record(record))
    container = payload
    for part in path[:-1]:
        container = container[part]
    container[path[-1]] = value
    with pytest.raises(ValueError):
        bl.load_evaluation_record(json.dumps(payload))


@pytest.mark.parametrize(
    "field",
    ["description", "tags", "evidence", "dated_label", "noted_on"],
)
@pytest.mark.parametrize("text", ["\ud800", "\udfff", "\ud800\udfff"])
def test_raw_archive_admission_refuses_surrogates(record, field, text):
    changes = {
        "description": {"description": text},
        "tags": {"tags": frozenset({text})},
        "evidence": {"evidence": frozenset({text})},
        "dated_label": {"dated_evidence": (bl.EvidenceItem(text),)},
        "noted_on": {"dated_evidence": (bl.EvidenceItem("data_origin", text),)},
    }
    with pytest.raises(TypeError, match="Unicode scalar"):
        bl.evaluation_record(
            replace(record.attempt, **changes[field]), as_of=record.as_of
        )


@pytest.mark.parametrize("field", ["tags", "evidence", "dated_evidence"])
@pytest.mark.parametrize("text", ["\ud800", "\udfff", "\ud800\udfff"])
def test_live_malformed_labels_are_set_aside_with_hashable_notes(record, field, text):
    changes = {
        "tags": {"tags": record.attempt.tags | {text}},
        "evidence": {"evidence": frozenset({text})},
        "dated_evidence": {
            "dated_evidence": record.attempt.dated_evidence + (bl.EvidenceItem(text),)
        },
    }
    baseline, expected_surfaces = bl.evaluate_with_surfaces(
        record.attempt, as_of=record.as_of
    )
    assessment, surfaces = bl.evaluate_with_surfaces(
        replace(record.attempt, **changes[field]), as_of=record.as_of
    )
    assert assessment.status == baseline.status
    assert assessment.findings == baseline.findings
    assert surfaces == expected_surfaces
    assert assessment.intake_notes != baseline.intake_notes
    expected_digest = hashlib.sha256(
        bl.canonical_assessment(assessment).encode("utf-8")
    ).hexdigest()
    assert bl.assessment_digest(assessment) == expected_digest
    assert bl.assessment_envelope(assessment).report_ref == expected_digest


@pytest.mark.parametrize("field", ["id", "title", "wire", "tags", "required_evidence"])
def test_non_scalar_registry_text_is_refused_without_poisoning_assessment(field):
    text = "\ud800"
    value = (
        frozenset({text})
        if field == "tags"
        else (text,)
        if field == "required_evidence"
        else text
    )
    practice = replace(bl.BLACK_PRACTICES[0], **{field: value})
    assessment = bl.evaluate_work(
        bl.WorkAttempt("Review", frozenset({"data"})),
        (practice, practice),
        as_of="2026-07-18",
    )
    assert assessment.status is bl.AssessmentStatus.NEEDS_REWORK
    assert assessment.findings == ()
    assert assessment.registry_digest == ""
    assert assessment.intake_notes
    expected_digest = hashlib.sha256(
        bl.canonical_assessment(assessment).encode("utf-8")
    ).hexdigest()
    assert bl.assessment_digest(assessment) == expected_digest
    assert bl.assessment_envelope(assessment).report_ref == expected_digest


@pytest.mark.parametrize("field", ["subject_id", "source_snapshot_refs"])
@pytest.mark.parametrize("text", ["\ud800", "\udfff", "\ud800\udfff"])
def test_provenance_factories_and_contract_reject_non_scalar_text(record, field, text):
    value = (text,) if field == "source_snapshot_refs" else text
    with pytest.raises((TypeError, ValueError), match="Unicode scalar"):
        bl.assessment_envelope(record.assessment, **{field: value}, strict=True)
    with pytest.raises((TypeError, ValueError), match="Unicode scalar"):
        bl.evaluation_record(record.attempt, as_of=record.as_of, **{field: value})
    envelope = bl.assessment_envelope(record.assessment, strict=True)
    check = bl.validate_envelope_contract(replace(envelope, **{field: value}))
    assert not check.passed
    assert field in {diagnostic.field for diagnostic in check.diagnostics}


def test_scalar_unicode_archive_round_trip_preserves_raw_text_and_bytes():
    practice = bl.BlackPractice(
        "méthode😀",
        "Café and Cafe\u0301",
        "Inspect résumé 😀",
        frozenset({"étude😀"}),
        ("source😀",),
    )
    expected_registry = (
        '[{"id":"méthode😀","kind":"METHOD","required_evidence":["source😀"],'
        '"tags":["étude😀"],"title":"Café and Cafe\u0301","wire":"Inspect résumé 😀"}]'
    ).encode("utf-8")
    assert bl.canonical_registry((practice,)).encode("utf-8") == expected_registry
    expected_digest = hashlib.sha256(expected_registry).hexdigest()
    assert bl.registry_digest((practice,)) == expected_digest
    attempt = bl.WorkAttempt(
        "Café and Cafe\u0301 😀",
        frozenset({" ÉTUDE😀 "}),
        frozenset({" SOURCE😀 "}),
        (bl.EvidenceItem(" SOURCE😀 ", "unreadable été😀"),),
    )
    refs = ["snapshot-é😀", "snapshot-e\u0301"]
    original = bl.evaluation_record(
        attempt,
        (practice,),
        as_of="2026-07-18",
        subject_id="",
        source_snapshot_refs=refs,
    )
    refs.append("later")
    serialized = bl.canonical_evaluation_record(original)
    restored = bl.load_evaluation_record(serialized)
    assert restored == original
    assert restored.attempt == attempt
    assert restored.source_snapshot_refs == ("snapshot-é😀", "snapshot-e\u0301")
    assert bl.canonical_evaluation_record(restored).encode("utf-8") == serialized.encode(
        "utf-8"
    )
    assert "Café and Cafe\u0301 😀" in serialized
    assert bl.replay_evaluation_record(restored) == (
        original.assessment,
        original.surfaces,
    )
    envelope = bl.assessment_envelope(
        restored.assessment,
        subject_id=restored.subject_id,
        source_snapshot_refs=restored.source_snapshot_refs,
        strict=True,
    )
    assert bl.envelope_matches_record(envelope, restored)
    assert bl.validate_envelope_contract(envelope).passed
    assert "snapshot-é😀" in bl.canonical_envelope(envelope)
