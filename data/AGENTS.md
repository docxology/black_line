# Data folder contract

Static inputs referenced by manuscript prose or tests. Black Line's executable
method is registry-driven (`src/black_line/registry.py`); this folder holds
supplementary reference material only.

- Do not treat files here as runtime configuration for the evaluator.
- Prefer typed records in `src/black_line/` when new structured inputs are needed.

## Formalism claim ledger

`formalism_claim_ledger.json` declares every formalism-block label the
manuscript (`03b_formalism.md` and siblings) uses in `[@def:...]`/`[@prop:...]`
cross-references, plus the package constants the formalism figures state, so
the render engine's evidence registry resolves them instead of reporting them
as unsupported bibliography citations.

- Every row is re-derived by `tests/test_formalism_claim_ledger.py`; a block
  added, renamed, or removed without the ledger following fails there.
- Negative controls in that module prove the guards can fail (unlisted label,
  foreign label).
- Pattern source: `witness_register`/`red_line` `formalism_claim_ledger.json`.
