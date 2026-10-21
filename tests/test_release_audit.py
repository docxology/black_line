import json
from dataclasses import replace
from pathlib import Path

import pytest

import black_line as bl


@pytest.mark.parametrize("number", [0, 1])
def test_nested_projection_context_rejects_numeric_booleans(number):
    record = bl.evaluation_record(
        bl.WorkAttempt(
            "work",
            frozenset({"data"}),
            frozenset({"data_origin"}) if number else frozenset(),
        ),
        as_of="2026-07-18",
    )
    payload = json.loads(bl.canonical_evaluation_record(record))
    payload["assessment_context"]["evidence_declared"] = number
    with pytest.raises(ValueError, match="context"):
        bl.load_evaluation_record(json.dumps(payload))
    changed = replace(
        record, assessment=replace(record.assessment, evidence_declared=number)
    )
    assert bl.evaluation_record_digest(changed) != bl.evaluation_record_digest(record)
    with pytest.raises(ValueError, match="replay differs"):
        bl.replay_evaluation_record(changed)


@pytest.mark.parametrize("review,window", [("9999-12-31", 0), ("2026-07-18", 10**12)])
def test_unrepresentable_expiry_has_structured_omission(review, window):
    attempt = bl.WorkAttempt(
        "work",
        frozenset({"data"}),
        dated_evidence=(bl.EvidenceItem("data_origin", review),),
    )
    kw = dict(as_of=review, max_evidence_age_days=window)
    assert bl.evaluate_work(attempt, **kw).findings
    assert bl.refresh_horizon(attempt, **kw) == ()
    (omission,) = bl.refresh_horizon_omissions(attempt, **kw)
    assert omission.reason == "expiry_out_of_calendar_range"
    assert omission.occurrence_index == 0
    queue = bl.effective_refresh_queue(attempt, **kw)
    assert queue.items == ()
    assert queue.omissions == (omission,)


def test_previous_edition_doi_is_not_assigned_to_current_edition():
    root = Path(__file__).resolve().parents[1]
    config = (root / "docs" / "manuscript" / "config.yaml").read_text()
    citation = (root / "CITATION.cff").read_text()
    previous = "10.5281/zenodo.22833503"
    publication = config.split("publication:\n")[1].split("\n\n")[0]
    assert '\n  doi: "' + previous + '"' not in "\n" + publication
    assert previous not in citation.split("references:")[0]
    assert previous in citation.split("references:")[1]
    assert previous in (root / "docs" / "publication.md").read_text()
