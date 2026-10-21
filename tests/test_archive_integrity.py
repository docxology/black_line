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
