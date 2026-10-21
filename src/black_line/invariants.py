"""Structural review checks over the Black Line practice registry.

Pure-compute checks (zero I/O) that validate the *shape* of the registry
rather than any single work attempt. They are review and drift instruments
for the practice content — nothing here carries safety or permission
semantics.

Each ``check_*`` returns one :class:`RegistryCheck`; ``all_invariants`` runs
the full battery. The test suite asserts every check passes on the real
registry AND fails on a planted-bad registry (proof-of-detection) — a green
check that never saw a bad input does not count.
"""

from __future__ import annotations

from dataclasses import dataclass

from .model import BlackPractice, PracticeKind
from .registry import BLACK_PRACTICES, PRACTICE_TAG_VOCABULARY
from .serialization import registry_digest
from .registry_validation import registry_defects


@dataclass(frozen=True)
class RegistryCheck:
    """One structural check outcome."""

    name: str
    passed: bool
    detail: str


def _structural_check(
    name: str, practices: tuple[BlackPractice, ...], codes: set[str]
) -> RegistryCheck:
    defects = registry_defects(practices)
    relevant = tuple(d for d in defects if d.code in codes or d.code == "record_type")
    return RegistryCheck(
        name,
        not relevant,
        "ok" if not relevant else "; ".join(f"{d.code}: {d.detail}" for d in relevant),
    )


def check_practice_ids_distinct(practices: tuple[BlackPractice, ...]) -> RegistryCheck:
    return _structural_check(
        "practice_ids_distinct", practices, {"id_text", "duplicate_id"}
    )


def check_practice_fields_populated(
    practices: tuple[BlackPractice, ...],
) -> RegistryCheck:
    return _structural_check(
        "practice_fields_populated",
        practices,
        {"title_wire_text", "required_labels_shape"},
    )


def check_practice_tags_reachable(
    practices: tuple[BlackPractice, ...],
) -> RegistryCheck:
    shape = _structural_check(
        "practice_tags_reachable", practices, {"tags_shape", "tags_not_normalized"}
    )
    if not shape.passed:
        return shape
    unknown = sorted(
        f"{p.id}:{tag}"
        for p in practices
        for tag in p.tags
        if tag not in PRACTICE_TAG_VOCABULARY
    )
    return RegistryCheck(
        shape.name, not unknown, "ok" if not unknown else f"unknown tags: {unknown}"
    )


def check_practice_kind_valid(practices: tuple[BlackPractice, ...]) -> RegistryCheck:
    return _structural_check("practice_kind_valid", practices, {"kind_type"})


def check_kind_coverage(practices: tuple[BlackPractice, ...]) -> RegistryCheck:
    shape = _structural_check("kind_coverage", practices, {"kind_type"})
    if not shape.passed:
        return RegistryCheck(
            shape.name, False, "blocked by structural preflight: " + shape.detail
        )
    covered = {p.kind for p in practices}
    missing = sorted(kind.value for kind in PracticeKind if kind not in covered)
    return RegistryCheck(
        shape.name,
        not missing,
        "ok" if not missing else f"families without a practice: {missing}",
    )


def check_evidence_labels_matchable(
    practices: tuple[BlackPractice, ...],
) -> RegistryCheck:
    return _structural_check(
        "evidence_labels_matchable",
        practices,
        {
            "required_labels_shape",
            "required_labels_duplicate",
            "required_labels_not_normalized",
        },
    )


def check_registry_digest_computable(
    practices: tuple[BlackPractice, ...],
) -> RegistryCheck:
    try:
        registry_digest(tuple(practices))
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        return RegistryCheck(
            "registry_digest_computable", False, f"digest failed: {exc}"
        )
    return RegistryCheck("registry_digest_computable", True, "ok")


def all_invariants(
    practices: tuple[BlackPractice, ...] = BLACK_PRACTICES,
) -> tuple[RegistryCheck, ...]:
    return tuple(
        check(practices)
        for check in (
            check_practice_ids_distinct,
            check_practice_fields_populated,
            check_practice_tags_reachable,
            check_practice_kind_valid,
            check_kind_coverage,
            check_evidence_labels_matchable,
            check_registry_digest_computable,
        )
    )


def invariants_hold(practices: tuple[BlackPractice, ...] = BLACK_PRACTICES) -> bool:
    return all(check.passed for check in all_invariants(practices))
