#!/usr/bin/env python3
"""Generate data/formalism_claim_ledger.json from the manuscript and the package.

Every row is derived, never hand-authored: citation rows from the
``::: {.definition #def:...}`` and ``::: {.proposition #prop:...}`` blocks
declared in the manuscript, number rows from the running figure code. Tests
re-derive the whole set and fail on drift.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from _cli import require_no_arguments

from black_line.figures.horizon_figures import horizon_rows, lattice_paths
from black_line.figures.scenarios import LATTICE_SEED

ROOT = Path(__file__).resolve().parent.parent
MANUSCRIPT = ROOT / "docs" / "manuscript"
LEDGER = ROOT / "data" / "formalism_claim_ledger.json"

#: A formalism block opener: ``::: {.definition #def:x title="X"}``.
_LAB = re.compile(
    r"^::: \{[^}]*#((?:def|prop|thm|lem|cor|rem|ax|clm|ex):[a-zA-Z0-9_-]+)",
    re.MULTILINE,
)


def declared_labels() -> list[tuple[str, Path]]:
    """Every formalism-block label declared in the manuscript, in text order."""

    labels: list[tuple[str, Path]] = []
    for path in sorted(MANUSCRIPT.glob("*.md")):
        for match in _LAB.finditer(path.read_text(encoding="utf-8")):
            labels.append((match.group(1), path))
    return labels


def citation_row(label: str, path: Path) -> dict[str, str]:
    """The declaration the engine's evidence registry reads for one label."""

    kind_word = "definition" if label.startswith("def:") else "proposition"
    return {
        "claim_id": label.replace(":", "_").replace("-", "_"),
        "kind": "citation",
        "value": label,
        "source": (
            f"docs/manuscript/{path.name}: {kind_word} block declared with this label"
        ),
        "source_path": f"docs/manuscript/{path.name}",
        "source_tier": "manuscript_formalism_block",
        "freshness": "active",
    }


def number_rows() -> list[dict[str, object]]:
    """The figure numbers, re-derived from the live package at generation time."""

    paths = lattice_paths()
    return [
        {
            "claim_id": "formal_lattice_seed",
            "kind": "number",
            "value": LATTICE_SEED,
            "source": "black_line.figures.scenarios.LATTICE_SEED",
            "source_path": "src/black_line/figures/scenarios.py",
            "source_tier": "package_constant",
            "freshness": "active",
        },
        {
            "claim_id": "formal_lattice_evaluate_calls",
            "kind": "number",
            "value": len(paths) * 17,
            "source": (
                "black_line.figures.horizon_figures.lattice_paths(): "
                f"{len(paths)} seeded orders x 17 evaluation steps through "
                "the real evaluator"
            ),
            "source_path": "src/black_line/figures/horizon_figures.py",
            "source_tier": "package_constant",
            "freshness": "active",
        },
        {
            "claim_id": "formal_refresh_queue_max_days",
            "kind": "number",
            "value": horizon_rows()[-1].days_until_stale,
            "source": (
                "black_line.figures.horizon_figures.horizon_rows(): "
                "days_until_stale of the last scheduled item ('scope')"
            ),
            "source_path": "src/black_line/figures/horizon_figures.py",
            "source_tier": "package_constant",
            "freshness": "active",
        },
    ]


def main() -> int:
    require_no_arguments("gen_formalism_ledger.py")

    labels = declared_labels()
    ordered = [row for row in labels if row[0].startswith("def:")] + [
        row for row in labels if not row[0].startswith("def:")
    ]
    claims: list[dict[str, object]] = [citation_row(*row) for row in ordered]
    claims += number_rows()
    doc = {
        "schema_version": "1.0",
        "purpose": (
            "Declares the manuscript's formalism-block labels and the package "
            "constants the formalism section states in figures, so the render "
            "engine's evidence registry can resolve a [@def:...]/[@prop:...] "
            "cross-reference instead of reporting it as an unsupported "
            "bibliography citation, and can resolve the figure-sweep numbers "
            "as declared package constants. Every row is derived from the "
            "manuscript or the package; tests/test_formalism_claim_ledger.py "
            "re-derives the whole set and fails if a block is added, renamed, "
            "or removed without this file following."
        ),
        "boundary": (
            "A row here records that a label is declared and that a constant "
            "exists. It is not evidence that the proposition it names is "
            "true, and it grants no claim any weight."
        ),
        "claims": claims,
    }
    LEDGER.write_text(
        json.dumps(doc, indent=1, sort_keys=False) + "\n", encoding="utf-8"
    )
    print(f"wrote {LEDGER.relative_to(ROOT)} with {len(claims)} claims")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
