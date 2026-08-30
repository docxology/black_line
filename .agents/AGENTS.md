# `.agents/` — agent notes

Project-local agent-skill hub. The only child on disk is `skills/` (vendored project skill directories). Runtime sync of these skills is governed by the project's own skill tooling; do not invent additional entries.

Regenerate via the canonical pipeline; see the project root `README.md` and `AGENTS.md` (referenced by name — relative links from this depth would escape the repository root, which `tests/test_standalone_contract.py` forbids).
