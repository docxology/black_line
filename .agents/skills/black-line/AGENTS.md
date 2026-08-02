# black-line skill — AGENTS.md

Project-scoped skill bundle shipped inside the `black_line` repository. Paths in
these files are relative to that repository's root, wherever it is checked out.

| File | Purpose |
| --- | --- |
| [`SKILL.md`](SKILL.md) | Runtime descriptor (boundary, recipes, gates, gotchas). |
| [`AGENTS.md`](AGENTS.md) | This file — folder contract. |
| [`README.md`](README.md) | Pointer for humans browsing the tree. |

Keep the skill free of volatile test-count literals. Registry-size claims are
bound by `tests/test_version_sync.py`. Figure ownership is
`src/black_line/figures/`; scripts are CLIs only.
