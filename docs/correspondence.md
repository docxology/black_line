<!-- Note (2026-07-29): reviewer attribution has been anonymized pending explicit
consent for inclusion in permanently archived DOI records. Attribution will be
restored on confirmation. -->

# Correspondence: design reviews received

This page records external design reviews of Black Line and what this
repository did about them. It is a decision record, not an endorsement chain:
each item names what was adopted, what was deferred with a reason, and what
was declined with a reason.

## 2026-07-29 — "The Space Between the Lines" (an external reviewer, with an analytic reader)

A two-voiced review of the collected line set (dated source: *The Line Set:
The Collected Volume*, 2026-07-27). Its reading of Black Line: the instrument
already witnesses inside the work trail — per-practice findings survive
beneath the overall status, and ALIGNED is declaration coverage, not quality,
truth, or permission. Its central proposal for the set: each line's selected
status is a safe projection that should not become the whole state, and the
missing layer is a *shared witness register* that co-registers each line's
complete report without ranking, averaging, merging, or overriding any of
them — "precedence without information destruction."

**Adopted here:**

- *Typed co-present surfaces.* The review's polarity observation — "strong
  positive and strong negative evidence together are not the same as no
  evidence, even when both correctly block a positive next step" — was true
  of this evaluator's findings but only legible in prose. The scoring stage
  now derives each finding from typed `EvidenceSurfaces` (present, missing,
  stale), and `evaluate_with_surfaces` returns them beside the identical
  assessment. One staged core serves both public forms.
- *The common report envelope.* The review's smallest implementable version
  starts with a data contract: one envelope per line report, pointing at the
  complete native report rather than copying it. `envelope.py` exports that
  contract under `line.report-envelope/1.0`, with the digest pointer
  (`assessment_digest`), the native status word in this line's own
  vocabulary, and transportable non-claims.

**Deferred, then closed (2026-07-29 manuscript window):** manuscript
formalism definitions for the surfaces and the envelope were deferred to the
next manuscript window because formal edits require a re-render and manifest
pass. That window ran the same day: `docs/manuscript/03b_formalism.md` now defines
`EvidenceSurfaces` and the report envelope, states the surfaces-to-finding
projection as a proposition, and embeds the derived `black_surfaces_panel`
plate — one executed `evaluate_with_surfaces` call drawn as typed
present/missing/stale surfaces beside the statuses projected from them.
Nothing remains deferred from this review except what is declined below.

**Declined, by design:**

- The shared witness register itself. The review is explicit that it should
  not be smuggled into any existing line, and this repository agrees: Black
  Line ships its envelope export and stops. A register that stores cross-line
  relations, unclassified observations, and joint return contracts is a
  separate work with its own tests and its own claim boundaries.
- Any change that would let the envelope carry a merged verdict, a score, or
  a cross-line comparison. `native_status` is this instrument's word in this
  instrument's vocabulary; the envelope documentation forbids ranking,
  averaging, or merging on it, and the non-claims travel inside the envelope
  so a stored copy cannot outgrow them.


### Wave-3 update (2026-07-29, later the same day)

The manuscript window was independently re-verified (CHANGELOG "2026-07-29
verification follow-up"): all measured numbers reproduced, the three new
formalism bindings were proven to bite on the real manuscript, and the
surfaces panel's caption numbers were re-derived through a fresh
`surfaces_result()` call and checked chip-by-chip against the rendered
image, with one clarification recorded ("distinct surface shapes" means
count signatures; the label-set reading is stronger). The skill descriptor
gained the surfaces + envelope section. The companion register now exists
and accepted this line's actually-exported envelope unmodified.
