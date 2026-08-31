# `src/black_line/model/` — data model

Typed data-model primitives for the Black Line package: `enums.py`
(vocabulary/enumerations) and `records.py` (record dataclasses). The rest of
`src/black_line/` imports from here; this module must not import siblings
upward (no cycles, model stays dependency-free).

Verify: `uv run pytest tests/model/` from the project root.
