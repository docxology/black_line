from datetime import date, datetime, timedelta

import pytest

import black_line as bl


def attempt(*items, evidence=frozenset(), tags=frozenset({"data"})):
    return bl.WorkAttempt("review declaration", tags, evidence, items)


@pytest.mark.parametrize("label", ["data_origin", "DATA_ORIGIN", " DATA_ORIGIN "])
@pytest.mark.parametrize(
    "noted", ["2026-07-01", "2020-01-01", "bad", "2027-01-01", None]
)
def test_finding_1_inventory_matches_evaluator_intake(label, noted):
    work = attempt(bl.EvidenceItem(label, noted))
    kw = dict(as_of="2026-07-18", max_evidence_age_days=30)
    assessment, surfaces = bl.evaluate_with_surfaces(work, **kw)
    rows = bl.refresh_horizon(work, **kw)
    omissions = bl.refresh_horizon_omissions(work, **kw)
    assert len(rows) + len(omissions) == 1
    if noted == "2026-07-01":
        assert rows[0].label == "data_origin"
        assert rows[0].label in surfaces[0].present
    else:
        assert not rows
        expected_reason = {
            "2020-01-01": bl.OMISSION_STALE,
            "bad": bl.OMISSION_UNREADABLE,
            "2027-01-01": bl.OMISSION_FUTURE,
            None: bl.OMISSION_UNDATED,
        }[noted]
        assert omissions[0].reason == expected_reason
        assert omissions[0].label == "data_origin"
    assert assessment == bl.evaluate_work(work, **kw)


@pytest.mark.parametrize(
    "window, error", [(-1, ValueError), (True, TypeError), ("30", TypeError)]
)
def test_finding_1_configuration_is_shared(window, error):
    work = attempt(bl.EvidenceItem("data_origin", "2026-07-01"))
    for function in (
        bl.evaluate_work,
        bl.refresh_horizon,
        bl.refresh_horizon_omissions,
    ):
        with pytest.raises(error):
            function(work, as_of="2026-07-18", max_evidence_age_days=window)


def test_finding_1_datetime_rejected_and_none_disables_expiry():
    work = attempt(bl.EvidenceItem("data_origin", "2026-07-01"))
    for function in (
        bl.evaluate_work,
        bl.refresh_horizon,
        bl.refresh_horizon_omissions,
    ):
        with pytest.raises(TypeError, match="as_of"):
            function(work, as_of=datetime(2026, 7, 18), max_evidence_age_days=30)
    assert (
        bl.refresh_horizon(work, as_of="2026-07-18", max_evidence_age_days=None) == ()
    )
    assert (
        "disabled"
        in bl.refresh_horizon_omissions(
            work, as_of="2026-07-18", max_evidence_age_days=None
        )[0].reason
    )


def test_finding_1_malformed_occurrences_are_explained():
    work = attempt(
        bl.EvidenceItem([], "bad"), object(), bl.EvidenceItem("data_origin", 3)
    )
    omissions = bl.refresh_horizon_omissions(
        work, as_of="2026-07-18", max_evidence_age_days=30
    )
    assert len(omissions) == 3
    assert all(
        "malformed" in row.reason or "unreadable" in row.reason for row in omissions
    )
    assert {row.occurrence_index for row in omissions} == {0, 1, 2}


@pytest.mark.parametrize(
    "case", ["non_applicable", "shadowed_by_undated", "superseded_by_newer_declaration"]
)
def test_finding_2_effective_queue_preserves_excluded_observations(case):
    items = [bl.EvidenceItem("data_origin", "2026-07-01")]
    evidence = frozenset()
    if case == "non_applicable":
        items = [bl.EvidenceItem("method", "2026-07-01")]
    elif case == "shadowed_by_undated":
        evidence = frozenset({" DATA_ORIGIN "})
    else:
        items.append(bl.EvidenceItem("data_origin", "2026-07-10"))
    work = attempt(*items, evidence=evidence)
    kw = dict(as_of="2026-07-18", max_evidence_age_days=30)
    inventory = bl.refresh_horizon(work, **kw)
    queue = bl.effective_refresh_queue(work, **kw)
    assert len(inventory) == len(items)
    assert queue.omissions[0].reason == case
    assert len(queue.items) == (1 if len(items) == 2 else 0)
    before = bl.evaluate_with_surfaces(
        work, as_of="2026-07-31", max_evidence_age_days=30
    )[1]
    after = bl.evaluate_with_surfaces(
        work, as_of="2026-08-01", max_evidence_age_days=30
    )[1]
    assert before == after
    for row in queue.items:
        assert row.practice_ids == ("data-provenance",)
        before = bl.evaluate_with_surfaces(
            work, as_of=row.last_fresh_on, max_evidence_age_days=30
        )[1]
        after = bl.evaluate_with_surfaces(
            work, as_of=row.stale_on, max_evidence_age_days=30
        )[1]
        assert before != after
        assert row.transitions == tuple((a, b) for a, b in zip(before, after) if a != b)


@pytest.mark.parametrize(
    "review, window, age",
    [
        ("2026-07-18", 0, 0),
        ("2026-07-18", 30, 29),
        ("2026-07-18", 30, 30),
        ("2026-07-18", 30, 31),
        ("2027-01-01", 3, 2),
        ("2024-02-29", 1, 1),
    ],
)
def test_finding_3_first_stale_day_is_after_last_fresh_day(review, window, age):
    today = date.fromisoformat(review)
    noted = today - timedelta(days=age)
    work = attempt(bl.EvidenceItem("data_origin", noted.isoformat()))
    rows = bl.refresh_horizon(work, as_of=review, max_evidence_age_days=window)
    if age > window:
        assert not rows
        return
    row = rows[0]
    assert row.last_fresh_on == (noted + timedelta(days=window)).isoformat()
    assert row.stale_on == (noted + timedelta(days=window + 1)).isoformat()
    assert row.days_until_stale == window - age + 1
    assert row.days_until_last_fresh_day == window - age
    for day, expected in ((row.last_fresh_on, True), (row.stale_on, False)):
        surface = bl.evaluate_with_surfaces(
            work, as_of=day, max_evidence_age_days=window
        )[1][0]
        assert ("data_origin" in surface.present) is expected
