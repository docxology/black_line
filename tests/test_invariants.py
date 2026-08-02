"""Proof-of-detection tests: every check passes on the real registry AND
fails on a planted-bad registry. A green check that never saw a bad input
does not count."""

from dataclasses import replace

from black_line import (
    BLACK_PRACTICES,
    PracticeKind,
    RegistryCheck,
    all_invariants,
    check_evidence_labels_matchable,
    check_kind_coverage,
    check_practice_fields_populated,
    check_practice_ids_distinct,
    check_practice_kind_valid,
    check_practice_tags_reachable,
    check_registry_digest_computable,
    invariants_hold,
)


def _planted(**changes):
    """The real registry with its first practice mutated in place."""

    return (replace(BLACK_PRACTICES[0], **changes),) + BLACK_PRACTICES[1:]


# --- practice_ids_distinct -------------------------------------------------


def test_ids_distinct_passes_on_real_registry() -> None:
    assert check_practice_ids_distinct(BLACK_PRACTICES).passed


def test_ids_distinct_detects_a_duplicate_id() -> None:
    planted = BLACK_PRACTICES + (replace(BLACK_PRACTICES[0]),)
    result = check_practice_ids_distinct(planted)
    assert not result.passed
    assert "question-first" in result.detail


def test_ids_distinct_detects_a_blank_id() -> None:
    result = check_practice_ids_distinct(_planted(id="   "))
    assert not result.passed


def test_ids_distinct_detects_a_non_string_id() -> None:
    result = check_practice_ids_distinct(_planted(id=7))
    assert not result.passed


# --- practice_fields_populated ---------------------------------------------


def test_fields_populated_passes_on_real_registry() -> None:
    assert check_practice_fields_populated(BLACK_PRACTICES).passed


def test_fields_populated_detects_a_blank_title() -> None:
    result = check_practice_fields_populated(_planted(title=""))
    assert not result.passed
    assert "blank title or wire" in result.detail


def test_fields_populated_detects_empty_required_evidence() -> None:
    result = check_practice_fields_populated(_planted(required_evidence=()))
    assert not result.passed


def test_fields_populated_detects_a_blank_evidence_label() -> None:
    result = check_practice_fields_populated(
        _planted(required_evidence=("question", " "))
    )
    assert not result.passed


def test_fields_populated_detects_string_evidence_shape() -> None:
    result = check_practice_fields_populated(_planted(required_evidence="question"))  # type: ignore[arg-type]
    assert not result.passed


def test_fields_populated_detects_non_text_evidence_label() -> None:
    result = check_practice_fields_populated(
        _planted(required_evidence=("question", 3))
    )  # type: ignore[arg-type]
    assert not result.passed


# --- practice_tags_reachable -----------------------------------------------


def test_tags_reachable_passes_on_real_registry() -> None:
    assert check_practice_tags_reachable(BLACK_PRACTICES).passed


def test_tags_reachable_detects_a_zero_tag_practice() -> None:
    result = check_practice_tags_reachable(_planted(tags=frozenset()))
    assert not result.passed
    assert "unreachable" in result.detail


def test_tags_reachable_detects_a_non_frozenset_tag_declaration() -> None:
    result = check_practice_tags_reachable(_planted(tags="research"))
    assert not result.passed


def test_tags_reachable_detects_an_out_of_vocabulary_tag() -> None:
    result = check_practice_tags_reachable(_planted(tags=frozenset({"astrology"})))
    assert not result.passed
    assert "astrology" in result.detail


# --- practice_kind_valid ---------------------------------------------------


def test_kind_valid_passes_on_real_registry() -> None:
    assert check_practice_kind_valid(BLACK_PRACTICES).passed


def test_kind_valid_detects_a_string_kind() -> None:
    result = check_practice_kind_valid(_planted(kind="craft"))
    assert not result.passed


# --- kind_coverage ---------------------------------------------------------


def test_kind_coverage_passes_on_real_registry() -> None:
    assert check_kind_coverage(BLACK_PRACTICES).passed


def test_kind_coverage_detects_a_lost_family() -> None:
    planted = tuple(
        practice
        for practice in BLACK_PRACTICES
        if practice.kind is not PracticeKind.STEWARDSHIP
    )
    result = check_kind_coverage(planted)
    assert not result.passed
    assert "STEWARDSHIP" in result.detail


# --- evidence_labels_matchable ---------------------------------------------


def test_evidence_labels_matchable_passes_on_real_registry() -> None:
    assert check_evidence_labels_matchable(BLACK_PRACTICES).passed


def test_evidence_labels_matchable_detects_a_duplicate_label() -> None:
    result = check_evidence_labels_matchable(
        _planted(required_evidence=("question", "question"))
    )
    assert not result.passed
    assert "duplicate" in result.detail


def test_evidence_labels_matchable_detects_an_uppercase_label() -> None:
    result = check_evidence_labels_matchable(
        _planted(required_evidence=("Question", "scope"))
    )
    assert not result.passed
    assert "unmatchable" in result.detail


def test_evidence_labels_matchable_detects_non_tuple_evidence() -> None:
    result = check_evidence_labels_matchable(_planted(required_evidence=["question"]))  # type: ignore[arg-type]
    assert not result.passed
    assert "tuple" in result.detail


# --- registry_digest_computable --------------------------------------------


def test_digest_computable_passes_on_real_registry() -> None:
    assert check_registry_digest_computable(BLACK_PRACTICES).passed


def test_digest_computable_detects_an_unserializable_registry() -> None:
    result = check_registry_digest_computable(_planted(tags=None))
    assert not result.passed
    assert "digest failed" in result.detail


# --- battery ---------------------------------------------------------------


def test_battery_runs_every_check_once_and_passes_on_real_registry() -> None:
    results = all_invariants()
    assert len(results) == 7
    assert len({result.name for result in results}) == 7
    assert all(isinstance(result, RegistryCheck) for result in results)
    assert all(result.passed for result in results)
    assert all(result.detail == "ok" for result in results)


def test_invariants_hold_is_true_on_real_and_false_on_planted() -> None:
    assert invariants_hold()
    assert not invariants_hold(_planted(id=""))
