"""Bind ``data/formalism_claim_ledger.json`` to the manuscript and the package.

The external publication engine's evidence registry knows ``fig:``/``sec:``/
``tbl:``/``eq:``/``lst:`` label prefixes and treats every other ``[@x]`` as a
bibliography key, so a formalism reference is reported as an unsupported
citation unless the project declares it. ``data/formalism_claim_ledger.json``
is that declaration; this module re-derives the whole set from the manuscript
and the running package so a block added, renamed, or removed without the
ledger following fails here rather than surfacing as a red output-validation
report after a render.

Nothing is asserted that was not first executed: the declared labels are
parsed from the real manuscript, and the numeric rows are re-derived from the
live package modules. Negative controls prove each gate can fail.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from black_line.figures.horizon_figures import horizon_rows
from black_line.figures.scenarios import LATTICE_SEED

ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = ROOT / "docs" / "manuscript"
FORMALISM = MANUSCRIPT / "03b_formalism.md"
LEDGER = ROOT / "data" / "formalism_claim_ledger.json"

#: A formalism block opener: ``::: {.definition #def:x title="X"}``.
_BLOCK = re.compile(r"^::: \{\.(?P<kind>[a-z]+)(?P<attrs>[^}]*)\}\s*$", re.M)
_LABEL = re.compile(r"#([a-z]+:[a-z0-9-]+)")
#: The reference syntax the engine's citation check sees.
_REFERENCE = re.compile(r"\[@((?:def|prop|thm|lem|cor|rem|ax|clm|ex):[a-z0-9-]+)\]")


def _body_files() -> list[Path]:
    """Every manuscript body file except the preamble."""

    return [
        path for path in sorted(MANUSCRIPT.glob("*.md")) if path.name != "preamble.md"
    ]


def _declared_labels() -> set[str]:
    """Every formalism-block label declared anywhere in the manuscript."""

    labels: set[str] = set()
    for path in _body_files():
        for match in _BLOCK.finditer(path.read_text(encoding="utf-8")):
            label = _LABEL.search(match.group("attrs"))
            if label:
                labels.add(label.group(1))
    return labels


def _referenced_labels() -> set[str]:
    """Every ``[@prefix:label]`` formalism reference in the manuscript."""

    refs: set[str] = set()
    for path in _body_files():
        refs.update(_REFERENCE.findall(path.read_text(encoding="utf-8")))
    return refs


def _ledger() -> dict:
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_every_declared_label_is_in_the_ledger() -> None:
    """A block declared in the manuscript must be declared to the engine too."""

    ledger = _ledger()
    citations = {row["value"] for row in ledger["claims"] if row["kind"] == "citation"}
    declared = _declared_labels()

    assert declared, "no labels declared; this gate would be vacuous"
    assert citations == declared, sorted(citations ^ declared)


def test_every_ledger_citation_is_a_declared_block() -> None:
    """The ledger cannot declare a label the manuscript does not carry."""

    ledger = _ledger()
    citations = {row["value"] for row in ledger["claims"] if row["kind"] == "citation"}

    assert citations <= _declared_labels(), sorted(citations - _declared_labels())


def test_every_referenced_label_is_both_declared_and_ledgered() -> None:
    """A reference the prose makes resolves on both sides of the contract."""

    declared = _declared_labels()
    ledger = _ledger()
    citations = {row["value"] for row in ledger["claims"] if row["kind"] == "citation"}
    referenced = _referenced_labels()

    assert referenced, "no formalism references found; this gate would be vacuous"
    assert referenced <= declared, sorted(referenced - declared)
    assert referenced <= citations, sorted(referenced - citations)


def test_every_ledger_source_path_exists() -> None:
    """A row pointing at a file that is not there is dead evidence."""

    for row in _ledger()["claims"]:
        assert (ROOT / row["source_path"]).is_file(), row["claim_id"]
        assert row["freshness"] == "active", row["claim_id"]


def test_ledger_claim_ids_are_unique() -> None:
    rows = _ledger()["claims"]

    assert len({row["claim_id"] for row in rows}) == len(rows)


def test_number_rows_match_the_running_package() -> None:
    """The numeric rows are re-derived from the package, not restated."""

    from black_line.figures.horizon_figures import lattice_paths

    numbers = {
        row["claim_id"]: row["value"]
        for row in _ledger()["claims"]
        if row["kind"] == "number"
    }

    assert numbers["formal_lattice_seed"] == LATTICE_SEED, (
        "seed moved; update the ledger"
    )
    assert numbers["formal_lattice_evaluate_calls"] == len(lattice_paths()) * 17
    assert (
        numbers["formal_refresh_queue_max_days"] == horizon_rows()[-1].days_until_stale
    )


def test_the_ledger_guard_rejects_an_unlisted_label() -> None:
    """Proof of detection: a label missing from the ledger is reported."""

    citations = {
        row["value"] for row in _ledger()["claims"] if row["kind"] == "citation"
    }
    planted = citations - {"prop:ladder"}

    assert planted != _declared_labels()
    assert _declared_labels() - planted == {"prop:ladder"}


def test_the_ledger_guard_rejects_a_planted_foreign_label() -> None:
    """Proof of detection: a citation no block declares cannot be added."""

    citations = {
        row["value"] for row in _ledger()["claims"] if row["kind"] == "citation"
    }
    planted = citations | {"prop:tier-monotone"}

    assert planted - _declared_labels() == {"prop:tier-monotone"}
