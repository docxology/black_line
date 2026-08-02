# Black Line documentation

Black Line is a positive practice instrument. The executable source is under
[`../src/black_line/`](../src/black_line/); the manuscript explains its scope and
limits. The project is intentionally separate from Red Line's refusal evaluator.

- [Architecture](architecture.md) — module layout, staged evaluation, digest
  as a review instrument
- [Usage and review protocol](usage.md) — API examples, status semantics, and
  the smallest honest operating loop
- [Registry invariants](invariants.md) — structural checks and the
  proof-of-detection testing discipline
- [Claim ledger](claims.md) — claim classes, evidence, and explicit boundaries
- [Correspondence](correspondence.md) — external design reviews received and
  the adopted/deferred/declined decision record
- [Development](development.md)
- [Standalone guide](../STANDALONE.md) — what a separated copy is, can, and cannot do
- [Method](../manuscript/02_method.md)
- [Practice registry](../manuscript/03_practices.md)
- [Limits](../manuscript/05_limits.md)
- [Relationship to the line set](../manuscript/01b_line_set_relationship.md), and
  the companion `line_set` work at <https://github.com/docxology/line_set> that
  documents the set once for all five works

The figure builder writes deterministic SVG and PNG outputs under
`../output/figures/` and records the figure contract, package version, and
registry digest in `../output/figures/figure_registry.json`. Each figure entry
also records its alt text, interpretive claim, and epistemic boundary, and
`validate_generated_figures` compares all three against the builders' declared
specs, so a caption cannot quietly outclaim the method by blanking the field
that bounds it. The visual system
uses a cream-paper editorial palette, serif headlines, and restrained purple /
teal accents so the figures remain expressive without pretending to be
independent evidence. It also writes `cover_art.svg` and `cover_art.png`, which
are configured as the paper's title-page cover, tracked in the registry's
`cover` entry, and embedded with their caption in the naming section so the
description reaches a reader rather than only the registry. The gate binds
`paper.cover.image` in `manuscript/config.yaml` to that registry entry.

In-figure text is measured, not eyeballed: `figures/legibility.py` derives the
point size each label prints at from the canvas, the declared embed width, and
the page geometry, and the suite fails below a 6pt floor.

See [AGENTS.md](AGENTS.md) for the working contract.
