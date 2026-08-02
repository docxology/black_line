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


@dataclass(frozen=True)
class RegistryCheck:
    """One structural check outcome."""

    name: str
    passed: bool
    detail: str


def _text(value: object) -> bool:
    """True when ``value`` is a non-blank string."""

    return isinstance(value, str) and bool(value.strip())


def check_practice_ids_distinct(practices: tuple[BlackPractice, ...]) -> RegistryCheck:
    """Every practice id is a distinct, non-blank string.

    A duplicate id makes findings ambiguous; a blank or non-string id makes
    the reasons trail unreadable.
    """

    ids = [practice.id for practice in practices]
    blank = [repr(identifier) for identifier in ids if not _text(identifier)]
    countable = [identifier for identifier in ids if _text(identifier)]
    dupes = sorted(
        {identifier for identifier in countable if countable.count(identifier) > 1}
    )
    ok = not dupes and not blank
    detail = "ok" if ok else f"duplicate ids: {dupes}; unusable ids: {blank}"
    return RegistryCheck("practice_ids_distinct", ok, detail)


def check_practice_fields_populated(
    practices: tuple[BlackPractice, ...],
) -> RegistryCheck:
    """Practice text and evidence records must have the declared data shape.

    An empty wire or evidence list turns a practice into an unreviewable
    slogan — it could never fail, which is drift the evaluator cannot see. The
    tuple requirement matters because a string would otherwise be iterated as
    one-character evidence labels while still looking populated.
    """

    bad: list[str] = []
    for practice in practices:
        identifier = repr(getattr(practice, "id", "<missing id>"))
        if not _text(getattr(practice, "title", None)) or not _text(
            getattr(practice, "wire", None)
        ):
            bad.append(f"{identifier}:blank title or wire")
        evidence = getattr(practice, "required_evidence", None)
        if (
            not isinstance(evidence, tuple)
            or not evidence
            or any(not _text(label) for label in evidence)
        ):
            bad.append(f"{identifier}:missing, malformed, or blank required evidence")
    ok = not bad
    return RegistryCheck(
        "practice_fields_populated", ok, "ok" if ok else f"unpopulated: {bad}"
    )


def check_practice_tags_reachable(
    practices: tuple[BlackPractice, ...],
) -> RegistryCheck:
    """Every practice has at least one tag from the reviewed vocabulary.

    A zero-tag practice can never intersect a work attempt, so it silently
    drops out of every evaluation; an out-of-vocabulary tag is unreviewed
    drift.
    """

    unreachable = [
        practice.id
        for practice in practices
        if not isinstance(practice.tags, frozenset) or not practice.tags
    ]
    unknown = [
        f"{practice.id}:{tag}"
        for practice in practices
        if isinstance(practice.tags, frozenset)
        for tag in sorted(practice.tags)
        if tag not in PRACTICE_TAG_VOCABULARY
    ]
    ok = not unreachable and not unknown
    detail = (
        "ok" if ok else f"unreachable practices: {unreachable}; unknown tags: {unknown}"
    )
    return RegistryCheck("practice_tags_reachable", ok, detail)


def check_practice_kind_valid(practices: tuple[BlackPractice, ...]) -> RegistryCheck:
    """Every kind must be a real PracticeKind member.

    ``dataclasses.replace(practice, kind="craft")`` succeeds silently; a
    string kind would then break canonical serialization and family review.
    """

    bad = [
        practice.id
        for practice in practices
        if not isinstance(practice.kind, PracticeKind)
    ]
    ok = not bad
    return RegistryCheck(
        "practice_kind_valid", ok, "ok" if ok else f"invalid kind on: {bad}"
    )


def check_kind_coverage(practices: tuple[BlackPractice, ...]) -> RegistryCheck:
    """Every craft family retains at least one practice.

    Losing a whole family (for example, all VERIFICATION entries) would
    quietly narrow what the Black Line can ever ask of strong work.
    """

    covered = {
        practice.kind
        for practice in practices
        if isinstance(practice.kind, PracticeKind)
    }
    missing = sorted(kind.value for kind in PracticeKind if kind not in covered)
    ok = not missing
    return RegistryCheck(
        "kind_coverage", ok, "ok" if ok else f"families without a practice: {missing}"
    )


def check_evidence_labels_matchable(
    practices: tuple[BlackPractice, ...],
) -> RegistryCheck:
    """Required evidence labels are distinct per practice and match-normalized.

    The evaluator lowercases declared evidence, so an uppercase registry
    label could never be satisfied; a duplicate label double-counts one
    observation.
    """

    bad: list[str] = []
    for practice in practices:
        labels = list(getattr(practice, "required_evidence", ()))
        if not isinstance(getattr(practice, "required_evidence", None), tuple):
            bad.append(
                f"{getattr(practice, 'id', '<missing id>')}:evidence must be a tuple"
            )
            continue
        dupes = sorted({label for label in labels if labels.count(label) > 1})
        if dupes:
            bad.append(f"{practice.id}:duplicate {dupes}")
        unmatchable = [
            label
            for label in labels
            if isinstance(label, str) and label != label.strip().lower()
        ]
        if unmatchable:
            bad.append(f"{practice.id}:unmatchable {unmatchable}")
    ok = not bad
    return RegistryCheck(
        "evidence_labels_matchable", ok, "ok" if ok else f"labels: {bad}"
    )


def check_registry_digest_computable(
    practices: tuple[BlackPractice, ...],
) -> RegistryCheck:
    """Canonical serialization and digesting must succeed on the registry.

    A registry that cannot be digested cannot be reviewed for drift at all,
    so a serialization break is itself a structural failure.
    """

    try:
        registry_digest(tuple(practices))
    except (AttributeError, TypeError, ValueError) as exc:
        return RegistryCheck(
            "registry_digest_computable", False, f"digest failed: {exc}"
        )
    return RegistryCheck("registry_digest_computable", True, "ok")


def all_invariants(
    practices: tuple[BlackPractice, ...] = BLACK_PRACTICES,
) -> tuple[RegistryCheck, ...]:
    """Run every structural check and return the results in battery order."""

    return (
        check_practice_ids_distinct(practices),
        check_practice_fields_populated(practices),
        check_practice_tags_reachable(practices),
        check_practice_kind_valid(practices),
        check_kind_coverage(practices),
        check_evidence_labels_matchable(practices),
        check_registry_digest_computable(practices),
    )


def invariants_hold(practices: tuple[BlackPractice, ...] = BLACK_PRACTICES) -> bool:
    """True iff every structural check passes on ``practices``."""

    return all(check.passed for check in all_invariants(practices))
