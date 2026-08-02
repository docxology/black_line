# Registry invariants

Structural review checks over the practice registry, run by
`black_line.all_invariants()` and by `scripts/check_registry.py` (which exits
non-zero on any failure). Each check returns a frozen
`RegistryCheck(name, passed, detail)`.

| Check | What it protects | Planted-bad proof |
| --- | --- | --- |
| `practice_ids_distinct` | Findings stay unambiguous: ids are distinct, non-blank strings | duplicate entry; blank id; non-string id |
| `practice_fields_populated` | No practice degrades into an unfalsifiable slogan: title, wire, and required evidence are populated with the declared tuple/string shape | blank title; empty evidence tuple; blank label; string evidence field |
| `practice_tags_reachable` | Every practice can actually be reached by `evaluate_work`, and tags stay inside the reviewed vocabulary | zero-tag practice; non-frozenset tags; out-of-vocabulary tag |
| `practice_kind_valid` | `kind` is a real `PracticeKind` member (frozen dataclasses do not type-check `replace`) | string kind |
| `kind_coverage` | No craft family silently disappears from the registry | registry stripped of its STEWARDSHIP entry |
| `evidence_labels_matchable` | Registry labels can be satisfied by normalized declared evidence and are not double-counted | duplicate label; uppercase label; non-tuple evidence |
| `registry_digest_computable` | The registry stays canonically serializable, so drift review remains possible | unserializable tags field |

## Proof-of-detection discipline

Every check has paired tests in `tests/test_invariants.py`:

- an assertion that the check **passes** on the real `BLACK_PRACTICES`, and
- one or more assertions that it **fails** on a planted-bad registry built
  with `dataclasses.replace`.

This is the difference between a check and a decoration. An invariant that
has never been shown to fire on a bad registry provides no evidence that it
would detect drift.

The shape checks are intentionally stricter than the dataclass annotations:
runtime callers can construct frozen records with `dataclasses.replace` or
untyped input, so the invariant battery must defend the representation the
evaluator and canonical serializer actually consume. These checks describe the
health of a method registry. They say nothing about safety, refusal, or
permission — that is a different project's job.
