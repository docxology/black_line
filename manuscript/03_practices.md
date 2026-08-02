# The Black Line practices

The registry holds eleven practices, each assigned to a craft family
(framing, traceability, method, verification, communication, stewardship).

1. **State the question before the method** (framing). Name the decision,
   object, and boundary before choosing tools.
2. **Make substantive claims traceable** (traceability). Point each substantive
   claim to a source, local observation, or explicit hypothesis label.
3. **Use the smallest method that can answer the question** (method). Do not
   add machinery whose output cannot change the decision.
4. **Make failure conditions explicit** (verification). Record what would
   falsify, break, or materially weaken the result.
5. **Leave a handoff another person can continue** (communication). A
   collaborator should recover the purpose, next action, and evidence without
   private context.
6. **Rerun the result from a clean environment** (verification). Treat a result
   that appears only in one warm environment as provisional until rerun.
7. **Keep changes small and reviewable** (stewardship). Record each increment
   so its history can be read, reverted, and reviewed.
8. **State uncertainty and limits with results** (traceability). A number
   without its uncertainty and boundary conditions can overstate what is known.
9. **Record null and negative results** (verification). A documented non-result
   can narrow the hypothesis space and guide the next attempt.
10. **Invite review before relying on a result** (communication). A second
    reader can expose omissions the author no longer sees.
11. **Keep data origin and transformations explicit** (traceability). State
    where each dataset came from and which transformations produced the analyzed
    form.

These practices are intentionally ordinary. Their value lies in making ordinary
discipline inspectable and repeatable across research, software, and writing.
The figure below draws the registry in its declaration order, with each card
color-keyed to its craft family.

![The 11 practices drawn as cards in registry declaration order, color-keyed to the 6 practice families. The order interleaves families and ends at `data-provenance`: it is a declaration order, not a workflow. Each card names a review surface and its required labels; the figure is not a quality or truth score and does not grant permission to cross Red Line.](../output/figures/black_practice_wires.png){#fig:black-practice-wires width=100%}

The six practice families exist so the registry can be reviewed for balance: a
registry that only rewarded framing but never verification would have drifted
from the purpose of making strong work inspectable end to end. Each practice
also carries the reviewed tags — drawn from `analysis`, `data`, `engineering`,
`research`, and `writing` — that decide which work attempts it applies to. The
taxonomy figure groups the practices by family and shows the tags that reach
each one; the [structural invariants](#sec:formalism) require every family to
retain at least one practice and every tag to stay inside the reviewed
vocabulary.

![The 11 practices grouped by 6 practice families, with the reviewed 5-tag vocabulary that makes each practice applicable to a work attempt. Family coverage and tag membership are enforced by structural invariants; the taxonomy maps reachability, not evidence quality.](../output/figures/black_family_taxonomy.png){#fig:black-family-taxonomy width=100%}

The registry's evidence contract is shown separately so that applicability and
evidence are not mistaken for proof. The labels below are declarations the
evaluator can match; they still require a human or external system to inspect
the underlying source, test, observation, or transformation.

![The registry's evidence-label contract: each practice names labels a reviewer can look for, while the instrument explicitly does not treat a declaration as independent verification of a source, test, or claim.](../output/figures/black_evidence_matrix.png){#fig:black-evidence-matrix width=100%}

## Registry coverage and burden {#sec:coverage-burden}

Applicability is deliberately asymmetric across the tag vocabulary, and the
asymmetry is itself a reviewable property of the method. Computed directly
from the registry via `coverage_matrix`, 27 of the 55 tag-practice cells are
applicable, and the per-tag reach is:

| Tag | Practices reached | Required labels | Practices |
| --- | :---: | :---: | --- |
| `research` | 8 of 11 | 16 | `question-first`, `source-traceable`, `failure-visible`, `concise-handoff`, `reproducible-from-clean`, `stated-uncertainty`, `negative-results-kept`, `review-before-reliance` |
| `analysis` | 7 of 11 | 14 | `question-first`, `source-traceable`, `smallest-sufficient-method`, `failure-visible`, `stated-uncertainty`, `negative-results-kept`, `data-provenance` |
| `engineering` | 6 of 11 | 12 | `smallest-sufficient-method`, `failure-visible`, `concise-handoff`, `reproducible-from-clean`, `versioned-increments`, `review-before-reliance` |
| `writing` | 5 of 11 | 10 | `question-first`, `source-traceable`, `concise-handoff`, `versioned-increments`, `review-before-reliance` |
| `data` | 1 of 11 | 2 | `data-provenance` |

The declaration burden therefore varies eightfold with tag choice — a
`data`-only attempt is scored against a single two-label practice, while a
`research` attempt must declare sixteen labels to reach `ALIGNED`. Every
practice carries exactly two required labels, so burden scales linearly with
reach; the asymmetry lives entirely in how many practices each tag selects.

This creates a coverage-side failure mode the instrument cannot police from
inside: *tag minimization*. Because tags are self-declared, a declarer can
narrow the tag set to buy a cheaper `ALIGNED` — the status is then true, but
over a smaller review surface (this attack is executed, with others, in the
[adversarial-declarations subsection](#sec:adversarial)). The coverage matrix
exists so a reviewer can read the status together with the burden it was
earned against; whether the declared tags honestly describe the work remains
a human judgment, exactly like the evidence behind each label.

![The tag-practice coverage matrix derived from the registry: filled cells mark applicability, cell numbers give each practice's required-label count, and the margin totals each tag's reach and declaration burden. The burden is asymmetric — `research` reaches 8 practices (16 required labels) while `data` reaches 1 (2 labels) — so a narrow tag set buys a cheaper `ALIGNED`. The matrix maps applicability, not evidence quality, safety, or permission.](../output/figures/black_coverage_heatmap.png){#fig:black-coverage-heatmap width=100%}
