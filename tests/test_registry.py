"""Shape tests over the practice registry itself."""

from black_line import (
    BLACK_PRACTICES,
    PRACTICE_TAG_VOCABULARY,
    PracticeKind,
    registry_ids,
)


def test_registry_has_materially_more_entries_than_the_original_five() -> None:
    assert len(BLACK_PRACTICES) == 11


def test_registry_ids_match_declaration_order() -> None:
    assert registry_ids() == tuple(practice.id for practice in BLACK_PRACTICES)


def test_every_practice_has_reviewed_tags() -> None:
    for practice in BLACK_PRACTICES:
        assert practice.tags, practice.id
        assert practice.tags <= PRACTICE_TAG_VOCABULARY, practice.id


def test_every_practice_has_required_evidence_labels() -> None:
    for practice in BLACK_PRACTICES:
        assert practice.required_evidence, practice.id
        assert all(
            label == label.strip().lower() for label in practice.required_evidence
        )


def test_every_practice_kind_is_a_real_member() -> None:
    for practice in BLACK_PRACTICES:
        assert isinstance(practice.kind, PracticeKind), practice.id


def test_every_kind_family_is_represented() -> None:
    covered = {practice.kind for practice in BLACK_PRACTICES}
    assert covered == set(PracticeKind)
