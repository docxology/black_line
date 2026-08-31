# Method: positive wires and observable evidence {#sec:method}

The registry contains eleven practices grouped into six practice families. Each
practice has a short wire, a tag set drawn from a reviewed five-tag vocabulary, a
family, and required evidence labels. The labels are deliberately coarse: the
evaluator checks whether labels were *declared and matched*, not whether the
underlying artifacts or claims are adequate. This is the load-bearing design
choice of the whole instrument — it can expose a review surface, never certify
its truth — and everything downstream inherits that limit.

## Six practice families: decision, procedure, record, world, authority

The instrument is easiest to use when six practice families are kept separate. The first
is the **decision**: what choice could the work change? The second is the
**procedure**: what is the smallest method that could inform that choice? The
third is the **record**: what source, observation, transformation, failure, or
review note can another reader inspect? The fourth is the **world**: whether the
source is authentic, the observation is adequate, the inference is sound, and
the claimed effect would survive an independent study. The fifth is **authority**:
whether the work is safe, lawful, permitted, or governed by a refusal boundary.
Black Line structures the first three and deliberately refuses to certify
the fourth or decide the fifth.

This distinction keeps the instrument aligned with the reproducibility
literature. A clean rerun with the same data, code, and conditions is a useful
computational property, but it is not the same as reproducing a result under a
new study or agreeing on the inference drawn from it
[@goodman2016reproducibility; @nationalacademies2019rr]. The registry therefore
names a review surface, not a truth or authority surface.

![The six-practice-family boundary map separates the decision, procedure, and record that Black Line can structure from world adequacy and authority that require domain, independent, or governance review. `ALIGNED` means fresh declaration coverage for applicable practices, not truth or permission.](../output/figures/black_claim_layers.png){#fig:black-claim-layers width=100%}

## Three claim classes, three evidentiary burdens

The boundary becomes operational when claims are classified before they are
written. Black Line distinguishes three burdens:

| Claim class | Example | What supports it | What it cannot become |
| --- | --- | --- | --- |
| Implementation | "The evaluator returns `NEEDS_REWORK` for a blank description." | Source inspection and a test that exercises the branch. | A claim that the work itself needs substantive rework beyond the declared contract. |
| Methodological | "A concise handoff is worth requiring." | Design rationale, scholarly lineage, and a stated limitation. | A causal finding that the practice improves outcomes. |
| World or authority | "The source is authentic" or "the work is permitted." | Domain verification, independent evidence, or governance review. | A conclusion licensed by `ALIGNED`. |

This classification prevents a polished figure, a citation, or a deterministic
test from silently changing the type of claim being made. The companion
[claim ledger](../docs/claims.md) keeps the same distinction available during
maintenance.

`evaluate_work` runs four stages behind two pre-stages, and the
[formal method section](#sec:formalism) states each of them exactly. In outline:
configuration validation rejects an invalid review date or freshness window, and
a registry that cannot be scored fails closed; intake normalization records
malformed tags, labels, and dates as notes rather than crashing, while a blank or
non-text description blocks scoring entirely; dated evidence is partitioned into
fresh and stale under the optional window; practices are selected by tag
intersection; and each selected practice is scored, with the overall status
taking the most demanding per-practice finding, or `OUTSIDE_SCOPE` when no
practice applies.

One branch of that scoring is worth stating in prose because it is the one
readers misread. The first branch is about the attempt, not the practice: if the
attempt declared no usable evidence at all, every selected practice returns
`NEEDS_EVIDENCE`. Where none of a practice's own labels are present but other
evidence exists, control reaches the last branch instead — `NEEDS_REWORK`, which
is missing work rather than an empty declaration. Stale gaps are the third case:
a practice whose only remaining gaps are aged observations asks for a refresh,
not a rework, and future or unreadable dates are never counted and surface as
notes for the declarer to fix.

Inside the scoring stage, the status word is the last step, not the whole
state. Each selected practice is first split into typed *evidence surfaces* —
its present, missing, and merely-stale required labels, co-present in declared
order — and the finding's status and reasons trail are projected from those
surfaces ([@def:evidence-surfaces] and [@prop:surfaces-projection]). The
projection selects the most demanding reading for action; the surfaces
preserve what it compresses, so strong support and strong resistance on one
practice stay readable together instead of collapsing into the projected word.
`evaluate_with_surfaces` returns the surfaces beside the identical assessment —
one shared staged implementation, never a second evaluator.

This is a deliberately positive counterpart to Red Line's refusal evaluator. It
does not inspect prohibited uses, infer hidden semantics, or turn alignment into
permission. The evidence vocabulary is a handoff surface for review, not a claim
that a source, test, or limitation note suffices by itself. The registry digest
travels with each assessment and beside each generated figure, so a changed
method is visible in a diff — a drift instrument for method content, never an
authentication of evidence.

The same distinction travels across domains. In research, the question may be
whether a result should be rerun; in engineering, whether a change is ready for
another reviewer; in writing, whether a synthesis can be handed off without
private context. The labels change, but the decision–procedure–record boundary
does not. Black Line becomes more relevant by staying at that shared layer and
leaving domain-specific truth and authorization to the people and systems that
actually possess them.
