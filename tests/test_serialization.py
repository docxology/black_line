"""Determinism and drift-visibility tests for serialization."""

import dataclasses
import json
from dataclasses import replace

import pytest

from black_line import (
    BLACK_PRACTICES,
    BlackPractice,
    PracticeKind,
    WorkAttempt,
    canonical_assessment,
    canonical_registry,
    evaluate_work,
    registry_digest,
)


def test_canonical_registry_is_sorted_valid_json() -> None:
    payload = json.loads(canonical_registry(BLACK_PRACTICES))
    assert [entry["id"] for entry in payload] == sorted(
        entry["id"] for entry in payload
    )
    assert all(entry["kind"] for entry in payload)


def test_digest_is_order_independent_and_hex_shaped() -> None:
    digest = registry_digest(BLACK_PRACTICES)
    assert digest == registry_digest(tuple(reversed(BLACK_PRACTICES)))
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")


#: One distinct replacement value per serialized field, so each field gets its
#: own proof that an edit to it is visible in the digest.
FIELD_EDITS = {
    "id": "edited-practice-id",
    "title": "An edited title",
    "wire": "something else",
    "tags": frozenset({"writing"}),
    "required_evidence": ("edited_label", "second_edited_label"),
    "kind": PracticeKind.STEWARDSHIP,
}


def test_field_edit_table_covers_every_serialized_field() -> None:
    """A per-field sweep over an incomplete table would be vacuous."""

    assert set(FIELD_EDITS) == {
        field.name for field in dataclasses.fields(BlackPractice)
    }
    assert set(FIELD_EDITS) == set(BLACK_PRACTICES[0].canonical())


@pytest.mark.parametrize("field", sorted(FIELD_EDITS))
def test_digest_changes_when_any_practice_field_changes(field: str) -> None:
    """Proposition 9's universal clause, one planted edit per field."""

    original = getattr(BLACK_PRACTICES[0], field)
    assert FIELD_EDITS[field] != original, field
    edited = (replace(BLACK_PRACTICES[0], **{field: FIELD_EDITS[field]}),)
    edited += BLACK_PRACTICES[1:]
    assert registry_digest(edited) != registry_digest(BLACK_PRACTICES), field


def test_canonical_assessment_is_deterministic_and_complete() -> None:
    attempt = WorkAttempt("work", frozenset({"research"}), frozenset({"question"}))
    first = canonical_assessment(evaluate_work(attempt, as_of="2026-07-01"))
    second = canonical_assessment(evaluate_work(attempt, as_of="2026-07-01"))
    assert first == second
    payload = json.loads(first)
    assert payload["evaluated_as_of"] == "2026-07-01"
    assert payload["schema_version"] == "1.0"
    assert payload["registry_digest"] == registry_digest(BLACK_PRACTICES)
    assert payload["status"] == "NEEDS_REWORK"
    assert payload["findings"]
    assert all(entry["reasons"] for entry in payload["findings"])
