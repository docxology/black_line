from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, datetime


def resolve_review_date(as_of: str | date | None) -> date:
    if as_of is None:
        return date.today()
    if isinstance(as_of, str):
        try:
            return date.fromisoformat(as_of)
        except ValueError as exc:
            raise ValueError("as_of must be an ISO date in YYYY-MM-DD form") from exc
    if isinstance(as_of, datetime) or not isinstance(as_of, date):
        raise TypeError("as_of must be None, an ISO date string, or a datetime.date")
    return as_of


def resolve_max_age(max_age_days: int | None) -> int | None:
    if max_age_days is None:
        return None
    if isinstance(max_age_days, bool) or not isinstance(max_age_days, int):
        raise TypeError("max_evidence_age_days must be a non-negative integer or None")
    if max_age_days < 0:
        raise ValueError("max_evidence_age_days must be non-negative")
    return max_age_days


def clean_labels(raw: object, field: str) -> tuple[frozenset[str], tuple[str, ...]]:
    if isinstance(raw, str) or not isinstance(raw, Iterable):
        return frozenset(), (
            f"{field} declaration is not a collection of labels and was ignored",
        )
    kept: set[str] = set()
    notes: list[str] = []
    for token in raw:
        if not isinstance(token, str) or not token.strip():
            notes.append(f"ignored a malformed {field} label")
            continue
        kept.add(token.strip().lower())
    return frozenset(kept), tuple(notes)


@dataclass(frozen=True)
class DatedIntake:
    occurrence_index: int
    raw_label: object
    label: str
    noted: date | None
    category: str


def dated_intake(
    records: object, review_date: date, max_age_days: int | None
) -> tuple[DatedIntake, ...]:
    if isinstance(records, str) or not isinstance(records, Iterable):
        return (DatedIntake(-1, None, "", None, "malformed_collection"),)
    rows = []
    for index, item in enumerate(records):
        raw_label = getattr(item, "label", None)
        if not isinstance(raw_label, str) or not raw_label.strip():
            rows.append(DatedIntake(index, raw_label, "", None, "malformed_label"))
            continue
        label = raw_label.strip().lower()
        noted_on = getattr(item, "noted_on", None)
        if noted_on is None:
            rows.append(DatedIntake(index, raw_label, label, None, "undated"))
            continue
        try:
            noted = date.fromisoformat(noted_on)
        except (TypeError, ValueError):
            rows.append(DatedIntake(index, raw_label, label, None, "unreadable"))
            continue
        category = "fresh"
        if noted > review_date:
            category = "future"
        elif max_age_days is not None and (review_date - noted).days > max_age_days:
            category = "stale"
        rows.append(DatedIntake(index, raw_label, label, noted, category))
    return tuple(rows)


def dated_labels(
    records: object, review_date: date, max_age_days: int | None
) -> tuple[frozenset[str], frozenset[str], tuple[str, ...]]:
    fresh: set[str] = set()
    stale: set[str] = set()
    notes: list[str] = []
    for row in dated_intake(records, review_date, max_age_days):
        if row.category in {"fresh", "undated"}:
            fresh.add(row.label)
        elif row.category == "stale":
            stale.add(row.label)
        elif row.category == "malformed_collection":
            notes.append("dated evidence declaration is not a collection of records")
        elif row.category == "malformed_label":
            notes.append("ignored a dated evidence record without a usable label")
        elif row.category == "unreadable":
            notes.append(
                f"evidence '{row.label}' has an unreadable date and was not counted"
            )
        elif row.category == "future":
            notes.append(
                f"evidence '{row.label}' is dated in the future and was not counted"
            )
    return frozenset(fresh), frozenset(stale), tuple(notes)
