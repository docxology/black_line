# Formal method: the evaluator and its invariants {#sec:formalism}

The formalism below restates the evaluator that produces the coverage properties
just shown.

This section states, as definitions and propositions, exactly what the
implemented package computes. Every object, status name, and decision rule is
taken from the source; the formalism describes the code and does not extend it.
Each property is marked as guaranteed by an executable test or as following by
inspection of the decision rule. Writing down what would falsify a claim, and
then planting a counter-example to confirm the check can fail, is the
falsificationist stance of the [scholarship section](#sec:scholarship) applied
to the tool itself [@popper1959logic].

No number below is written in the source. Every definition and proposition
carries a label, the numbering is generated in document order, and every
cross-reference resolves from the label, so an inserted block cannot leave a
reference pointing at the wrong statement.

## Domain objects

::: {.definition #def:practice title="Practice"}
A *practice* is a frozen record
$p = (\mathrm{id}, \mathrm{title}, \mathrm{wire}, \mathrm{tags}, \mathrm{req}, \mathrm{kind})$
where $\mathrm{id}, \mathrm{title}, \mathrm{wire}$ are strings, $\mathrm{tags}$ is a
finite set of tag strings, $\mathrm{req}$ is a finite ordered tuple of required
evidence labels, and $\mathrm{kind}$ is a craft family. The field $\mathrm{kind}$
defaults to `METHOD` when omitted from positional construction.
:::

::: {.definition #def:tag-vocabulary title="Tag vocabulary"}
The reviewed tag vocabulary is the fixed set
$$V = \{\texttt{analysis}, \texttt{data}, \texttt{engineering}, \texttt{research}, \texttt{writing}\},$$
with $|V| = 5$. Practice tags outside $V$ are unreviewed drift, which is what
I3 in [@prop:invariants] refuses.
:::

::: {.definition #def:registry title="Registry"}
The *registry* $R = (p_1, \dots, p_n)$ is the ordered tuple of eleven practices
exported as `BLACK_PRACTICES`. Its content is summarized by the deterministic
SHA-256 `registry_digest`, so any edit to a wire is visible as a digest change
in review. An assessment records this digest so a serialized result can be
compared with the registry that produced it.
:::

::: {.definition #def:craft-families title="Craft families"}
The family of a practice is a member of
$$K = \{\texttt{FRAMING}, \texttt{TRACEABILITY}, \texttt{METHOD}, \texttt{VERIFICATION}, \texttt{COMMUNICATION}, \texttt{STEWARDSHIP}\},$$
with six families. Families exist so registry balance can be reviewed; I5 in
[@prop:invariants] requires each family to retain at least one practice.
:::

::: {.definition #def:work-attempt title="Work attempt"}
A *work attempt* is a record $W = (\mathrm{desc}, T, E, D)$ where
$\mathrm{desc}$ is a description string, $T$ is a declared tag set, $E$ is a
declared undated evidence-label set, and $D$ is a tuple of *dated evidence
items*. A dated evidence item is a pair $(\ell, \tau)$ of a label $\ell$ and an
optional ISO date $\tau$ (with $\tau = \bot$ meaning undated).
:::

::: {.definition #def:assessment-record title="Assessment record"}
An assessment is a record $A = (s, \mathcal{F}, N, d, h)$ containing an overall
status $s$, ordered practice findings $\mathcal{F}$, intake notes $N$, review
date $d$, and registry digest $h$. Each finding is itself a triple of a practice
id, a practice status, and an ordered reasons trail. The digest identifies
method content only; it is not a signature of the evidence or the work.
:::

## Status codomains

::: {.definition #def:practice-status title="Practice status"}
A per-practice outcome lies in
$$S_p = \{\texttt{ALIGNED}, \texttt{NEEDS\_EVIDENCE}, \texttt{NEEDS\_REWORK}\}.$$
:::

::: {.definition #def:assessment-status title="Assessment status"}
An overall outcome lies in
$$S_a = S_p \cup \{\texttt{OUTSIDE\_SCOPE}\} = \{\texttt{ALIGNED}, \texttt{NEEDS\_EVIDENCE}, \texttt{NEEDS\_REWORK}, \texttt{OUTSIDE\_SCOPE}\}.$$
`OUTSIDE_SCOPE` is available to the overall status only; it is never a
per-practice status.
:::

## The staged evaluator

The function under study is
$$\mathrm{evaluate\_work} : (W, R, d, \omega) \mapsto A,$$
where $d$ is the review date (`as_of`, defaulting to today), $\omega$ is an
optional staleness window in days (`max_evidence_age_days`, with $\omega = \bot$
disabling staleness), and $A$ is a `BlackAssessment`. Two pre-stages run before
any scoring: the review configuration is validated, and the supplied registry is
checked for a shape that can be scored at all. Only then do the four numbered
stages run.

::: {.definition #def:review-config title="Review configuration"}
The review date accepts $\bot$ (meaning today), an ISO date string, or a
`datetime.date`. A malformed ISO string raises `ValueError`; a `datetime`, or
any other type, raises `TypeError` rather than being coerced. The window accepts
$\bot$ or a non-negative `int`; a `bool`, a non-integer, or a negative value
raises. This is the one input class the evaluator refuses outright, because a
misread review date silently changes every age comparison downstream.
:::

::: {.definition #def:intake title="Intake normalization"}
*Stage 1* normalizes hostile or malformed input into declarations plus review
notes rather than raising. A declared label collection $X$ is normalized by
$$\mathrm{clean}(X) = \{\, \mathrm{lower}(\mathrm{strip}(t)) : t \in X,\ t \text{ a non-blank string}\,\},$$
and every dropped token, non-collection field, or string-valued field is
recorded as an intake note. The *blocking predicate* is
$$\mathrm{block}(W) \equiv \neg\,\mathrm{isstr}(\mathrm{desc}) \ \lor\ \mathrm{strip}(\mathrm{desc}) = \varepsilon.$$
:::

::: {.definition #def:freshness title="Freshness partition"}
*Stage 2* splits the dated evidence $D$, at review date $d$ under window
$\omega$, into a fresh set and a stale set:

- a record whose label is missing or is not a non-blank string is dropped with a
  note;
- an undated item $(\ell, \bot)$ contributes $\ell$ to *fresh*;
- an item dated $\tau > d$ (future) or with an unparseable $\tau$ is counted in
  neither set and is surfaced as a note;
- an item with $\omega \neq \bot$ and age $(d - \tau) > \omega$ contributes
  $\ell$ to *stale*;
- otherwise the item contributes $\ell$ to *fresh*.

The evaluated evidence sets are the *fresh* set
$F = \mathrm{clean}(E) \cup \mathrm{fresh\_dated}$ and the *stale* set $\Sigma$.

The staleness comparison is *strict*: an item aged exactly $\omega$ days
satisfies $(d - \tau) = \omega \not> \omega$ and is therefore still fresh;
staleness begins at age $\omega + 1$. [@prop:strict-staleness] pins this
boundary with an executed witness.
:::

::: {.definition #def:applicability title="Applicability"}
*Stage 3* selects the applicable practices by non-empty tag intersection:
$$A(W) = \{\, p \in R : p.\mathrm{tags} \cap \mathrm{clean}(T) \neq \emptyset \,\}.$$
:::

::: {.definition #def:finding-rule title="Practice finding rule"}
*Stage 4* scores each applicable practice $p$ against $(F, \Sigma)$. Let
$\mathrm{present}$ and $\mathrm{missing}$ be the subsequences of
$p.\mathrm{req}$, in declaration order, whose labels are respectively in and not
in $F$. The finding $\varphi(p, F, \Sigma)$ is given by the first matching rule:

- `NEEDS_EVIDENCE` if $F = \emptyset$ and $\Sigma = \emptyset$ (the attempt
  declared no usable evidence at all);
- otherwise `ALIGNED` if $\mathrm{missing} = \emptyset$ (every required label is
  fresh);
- otherwise `NEEDS_EVIDENCE` if $\mathrm{missing} \subseteq \Sigma$ (every
  remaining gap is merely a stale item awaiting refresh);
- otherwise `NEEDS_REWORK`.

Each finding also carries a reasons trail naming present, missing, and
stale-refresh labels.
:::

The first branch is a statement about the attempt, not about the practice;
[@prop:global-local] gives that reading exactly, because it is the branch most
often misread.

::: {.definition #def:aggregation title="Overall aggregation"}
*Stage 4, second half* aggregates the set of finding statuses
$\mathrm{stat}(\mathcal{F})$ into the assessment status by the first matching
rule:

- `NEEDS_REWORK` if `NEEDS_REWORK` $\in \mathrm{stat}(\mathcal{F})$;
- otherwise `NEEDS_EVIDENCE` if `NEEDS_EVIDENCE` $\in \mathrm{stat}(\mathcal{F})$;
- otherwise `ALIGNED` if $\mathcal{F} \neq \emptyset$;
- otherwise `OUTSIDE_SCOPE`.
:::

The decision path from intake through per-practice findings to this status is
drawn below.

![The staged evaluation path. Intake normalization can block on a blank description, and a malformed practice registry fails closed as `NEEDS_REWORK` before any scoring; otherwise practices are matched by tag intersection, each applicable practice is scored `ALIGNED`, `NEEDS_EVIDENCE`, or `NEEDS_REWORK`, and the overall status takes the most demanding per-practice status, or `OUTSIDE_SCOPE` when no practice applies. The diagram is derived from the evaluator rules and status enums; a status reports declaration coverage and freshness, not verified evidence or authorization.](../output/figures/black_status_path.png){#fig:black-status-path width=100%}

## Surfaces, projection, and the report envelope

The scoring rule of [@def:finding-rule] reads its subsequences off an
intermediate object worth naming, because a status word is the *last* step of
Stage 4, not the whole state. Strong support and strong resistance co-present
on one practice are not the same as no evidence, even when both correctly
yield the same demanding word for action; the typed surfaces are what keep
those situations distinguishable after the word is chosen.

::: {.definition #def:evidence-surfaces title="Evidence surfaces"}
For an applicable practice $p$ evaluated against $(F, \Sigma)$, the *evidence
surfaces* are the frozen record
$\sigma(p) = (\mathrm{practice\_id}, \mathrm{present}, \mathrm{missing}, \mathrm{stale})$
with exactly those four fields: $\mathrm{present}$ and $\mathrm{missing}$
partition $p.\mathrm{req}$ by membership in $F$, and $\mathrm{stale}$ is the
subsequence of $\mathrm{missing}$ whose labels are in $\Sigma$, so
$\mathrm{stale} \subseteq \mathrm{missing}$ always holds. All three tuples
keep the practice's declared evidence order. The surfaces are co-present
state — support and resistance on one practice are both kept, and neither
erases the other — and, like every object in this section, they describe
declaration coverage only.
:::

The finding is then a *projection* of that state: precedence selects the most
demanding reading for action, and the surfaces preserve what the selection
compresses.

::: {.proposition #prop:surfaces-projection title="The finding is a projection of its surfaces"}
For every applicable practice, the finding's status and its ordered reasons
trail are functions of $(\sigma(p), e)$ alone, where
$e \equiv (F \cup \Sigma \neq \emptyset)$ is the attempt-wide
evidence-declared bit whose reading [@prop:global-local] gives; every reasons
trail is re-derivable from its surfaces. The two public forms report one
staged computation: `evaluate_with_surfaces` returns the surfaces beside an
assessment that is byte-identical, under canonical serialization, to what
`evaluate_work` returns for the same arguments — one staged core, never a
second evaluator. On a blocking intake defect or an unscorable registry there
are no findings and therefore no surfaces. *Evidence:*
`tests/test_witness_surfaces.py::test_both_public_forms_report_one_staged_computation`
across a battery reaching every assessment status,
`tests/test_witness_surfaces.py::test_surfaces_align_one_to_one_with_findings_and_generate_their_reasons`,
and the definition re-derivation in
`tests/test_formalism_definitions.py::test_surfaces_projection_matches_the_proposition`.
:::

The panel below draws the projection once, from a single executed call, so
the compression is visible rather than asserted: several distinguishable
surface shapes share one projected word, and the overall status is one word
for all of them.

![One declaration's typed evidence surfaces beside the statuses projected from them: a single `evaluate_with_surfaces` call at review date 2026-07-01 under a 30-day window matches 7 practices, whose 14 required labels split into 5 present (filled), 9 missing (hollow), and 3 of the missing merely stale (amber refresh marks). One status word covers distinguishable surface shapes: `NEEDS_EVIDENCE` is projected from 2 distinct present/missing/stale shapes and `NEEDS_REWORK` is projected from 2 distinct present/missing/stale shapes, while the single overall word for the whole attempt is `NEEDS_REWORK`. The surfaces keep what the projection compresses — strong support and strong resistance co-present on one practice are not the same as no evidence — and, like the statuses, they describe declaration coverage only: a present label is a declaration, never verified evidence, and no surface shape grants permission.](../output/figures/black_surfaces_panel.png){#fig:black-surfaces-panel width=100%}

A reader holding reports from several independent instruments needs one
uniform way to say "this instrument, about this subject, at this review
moment, said this — and here is the pointer to its complete native report."
The envelope is that data contract and nothing more.

::: {.definition #def:report-envelope title="The report envelope"}
The *report envelope* is the frozen record `AssessmentEnvelope` with exactly
the ten fields, in order, `schema_version`, `line_id`, `subject_id`,
`review_date`, `registry_version`, `registry_digest`, `native_status`,
`report_ref`, `source_snapshot_refs`, and `scope_and_nonclaims`, declared
under the cross-instrument schema string `line.report-envelope/1.0`.
$\mathrm{report\_ref}$ is the SHA-256 digest of the complete
`canonical_assessment` serialization of [@prop:determinism], so the envelope
points at the full native derivation — every finding and every intake note —
without restating or reinterpreting any of it, and
$\mathrm{scope\_and\_nonclaims}$ carries the instrument's non-claims inside
the record itself, so a stored envelope cannot quietly outgrow what the
instrument was allowed to say. $\mathrm{native\_status}$ is this line's own
status word in this line's own vocabulary; envelopes from different lines
must not be compared, ranked, averaged, or merged on it. Sibling instruments
that export the same shape do so by publishing the same schema string, never
by importing one another. $\mathrm{source\_snapshot\_refs}$ is
caller-supplied provenance that the envelope stores and does not verify.
:::

An envelope is a witness record, not a score: it makes one instrument's
complete report co-registrable beside the others' without granting any
reader a licence to aggregate the status words.

## Propositions

::: {.proposition #prop:registry-fail-closed title="A malformed registry fails closed"}
Before any attempt is read, the supplied registry is checked for entries that
are not practice records, for blank or non-text ids, titles, and wires, for
duplicate ids, for malformed tag or evidence fields, and for invalid families;
the canonical digest is then computed. If either step fails, the assessment is
`NEEDS_REWORK` with no findings, an empty digest, and an intake note naming the
defect. The direction is deliberate: a registry that cannot be scored must not
produce a permissive status. *Evidence:*
`tests/test_evaluator.py::test_custom_registry_failures_are_blocking` and
`tests/test_evaluator.py::test_malformed_custom_registry_is_blocked_before_tag_matching`.
:::

::: {.proposition #prop:intake title="Intake records supported malformed declarations"}
For a work attempt whose $T$, $E$, and $D$ fields are non-iterable, strings, or
ordinary iterables yielding malformed tokens, Stage 1 returns normalized sets
and notes rather than raising: non-collection or string-valued fields become a
single note, malformed tokens are dropped with a note, and unreadable or future
dates are excluded with a note. This is defensive normalization, not a sandbox
for arbitrary user-defined iterators or properties. *Evidence:* the
hostile-input cases in `tests/test_evaluator.py`, and the executed battery in
`tests/test_figures.py::test_the_intake_plate_follows_the_executed_battery`.
:::

The battery is drawn below, one row per malformed declaration, so the claim
"notes rather than exceptions" can be read off outputs instead of taken on
trust.

![Stage 1 executed over 9 deliberately malformed declarations at review date 2026-07-01: each is one real evaluate_work call, together they return 10 intake notes, and none raises. 2 block scoring outright (description is blank and description is not text) and 1 reaches no practice once its dropped tag declaration leaves nothing to match, while the other 6 are scored normally; across the battery the outcomes are ALIGNED, NEEDS_EVIDENCE, NEEDS_REWORK, OUTSIDE_SCOPE. Surviving malformed input is a robustness property of the intake stage, not tolerance of a bad declaration, and a note asks the declarer to fix something rather than verifying anything declared correctly.](../output/figures/black_intake_notes.png){#fig:black-intake-notes width=100%}

Two rows of that plate read directly against [@def:intake]. An evidence
collection carrying a blank and a non-text token still reaches `ALIGNED`,
because the two usable labels survive normalization while the two dropped tokens
become notes. A tag set declared as the bare string `data` is dropped whole,
leaving nothing to match, so the attempt is `OUTSIDE_SCOPE` — a coverage
statement produced by a typo, which is why intake notes belong in the returned
record rather than in a log line.

::: {.proposition #prop:blocking title="Blocking description short-circuits"}
If $\mathrm{block}(W)$ holds, then $A.\mathrm{status} = \texttt{NEEDS\_REWORK}$,
$A.\mathrm{findings} = \emptyset$, and $A.\mathrm{notes}$ contains the
restatement instruction. No practice is scored, because no honest scoring is
possible without a described work item. *Evidence:* by inspection of Stage 1's
early return, exercised in
`tests/test_evaluator.py::test_blank_description_is_a_blocking_intake_defect`.
:::

::: {.proposition #prop:scope title="Scope characterization"}
For a non-blocking attempt, $A.\mathrm{status} = \texttt{OUTSIDE\_SCOPE}$ if and
only if $A(W) = \emptyset$: no practice's tags intersect the declared tags. An
`OUTSIDE_SCOPE` status is therefore a statement about *coverage*, never about
safety or permission. *Evidence:* follows from [@def:applicability] and
[@def:aggregation], exercised in
`tests/test_evaluator.py::test_no_matching_tags_is_outside_scope_with_review_date`.
:::

::: {.proposition #prop:global-local title="Global versus local emptiness"}
The first branch of [@def:finding-rule] tests the *global* evidence sets $F$ and
$\Sigma$, not the practice's own requirements: "no evidence was declared" fires
only when the attempt supplied no usable fresh or stale evidence at all. When
some evidence exists but none of it satisfies $p$, control reaches the fourth
branch — `NEEDS_REWORK`, all required labels missing and none stale — not the
first. An attempt that has *begun* work but omitted a practice's evidence is
therefore told to rework it, not that it declared nothing. *Evidence:*
`tests/test_manuscript_bindings.py::test_method_prose_matches_the_global_emptiness_branch`.
:::

::: {.proposition #prop:fresh-monotonicity title="Conditional fresh-evidence monotonicity"}
Fix $p$, $\Sigma$, and let $F \subseteq F'$ be two fresh sets. Once
$F \cup \Sigma \neq \emptyset$, adding fresh labels cannot move a finding toward
a more demanding status under the order
$\texttt{NEEDS\_REWORK} \prec \texttt{NEEDS\_EVIDENCE} \prec \texttt{ALIGNED}$;
adding required labels can only shrink $\mathrm{missing}$. There is one
intentional boundary case: when both $F$ and $\Sigma$ are empty, adding an
irrelevant fresh label changes the global branch from `NEEDS_EVIDENCE` to
`NEEDS_REWORK`, because the attempt has now declared something while still
omitting the practice's requirements. *Evidence:* the conditional claim follows
from [@def:finding-rule] and is exercised as a seeded sampled property by
`tests/test_analytics.py::test_sampled_permutations_never_regress_after_first_declaration`
and
`tests/test_analytics.py::test_declaration_path_under_staleness_never_regresses_after_first_step`;
the boundary case is exercised by
`tests/test_evaluator.py::test_irrelevant_evidence_only_needs_rework_without_present_reason`.
The same sweep is drawn as
[the monotonicity lattice](#fig:black-monotonicity-lattice) in the worked
examples, where the per-row monotonicity mark and the inversion count are read
off executed paths rather than asserted.
:::

::: {.proposition #prop:determinism title="Determinism and archivability"}
For fixed ordinary data values $(W, R, d, \omega)$ with a materialized registry
tuple, `evaluate_work` is a pure function, and `canonical_assessment` serializes
the result — including the registry digest — to byte-identical JSON across runs,
so an assessment can be diffed and cited in a review record. *Evidence:*
`tests/test_serialization.py::test_canonical_assessment_is_deterministic_and_complete`.
:::

::: {.proposition #prop:strict-staleness title="Strict staleness boundary"}
Fix $\omega \neq \bot$ and a dated item $(\ell, \tau)$ with $\tau \le d$. The
item is stale if and only if $(d - \tau) > \omega$; the equality case
$(d - \tau) = \omega$ is fresh. Executed witness: a full `data` declaration
aged exactly $51$ days is fresh under $\omega = 51$ (overall status `ALIGNED`)
and stale under $\omega = 50$ (overall status `NEEDS_EVIDENCE`, every gap being
merely stale); with $\omega = \bot$ staleness is disabled and the status is
again `ALIGNED`. The boundary is a fact about date arithmetic inside the
evaluator, not a judgment that $51$-day-old evidence is trustworthy. *Evidence:*
`tests/test_analytics.py::test_staleness_profile_pins_the_strict_inequality_boundary`
and `tests/test_evaluator.py::test_fully_stale_evidence_needs_refresh_not_rework`.
:::

::: {.proposition #prop:window-monotonicity title="Window monotonicity, sampled"}
Fix an attempt whose dated evidence parses (no future or unreadable dates).
Widening the freshness window never lowers the declaration-coverage rank of
[@prop:ladder]: enlarging $\omega$ can only move labels from $\Sigma$ to $F$.
For the aged-$51$ witness of [@prop:strict-staleness], sweeping every integer
window $\omega \in \{0, \dots, 90\}$ and then $\omega = \bot$ yields
`NEEDS_EVIDENCE` for every $\omega < 51$ and `ALIGNED` for every
$\omega \ge 51$, including $\omega = \bot$, and the coverage rank is
non-decreasing along the sweep. Beyond this fully-enumerated witness the claim
is exercised as a seeded sampled property, not proven for all inputs; and a
wider window is a more permissive review setting, not better work. *Evidence:*
`tests/test_analytics.py::test_widening_the_window_never_regresses_coverage_rank`
and the sweep re-derivation in
`tests/test_manuscript_bindings.py::test_formalism_window_sweep_witness_re_derives`.
:::

::: {.proposition #prop:coverage-algebra title="Coverage-matrix algebra"}
For the shipped registry $R$ ($n = 11$) with tag vocabulary $V$ ($|V| = 5$),
`coverage_matrix` returns one row per declared tag, sorted alphabetically, each
row carrying the tag's *reach* (practices selected) and *burden* (total required
labels a declarer of only that tag is scored against). Two identities hold by
execution: (i) the rows fill
$\sum_{t} \mathrm{reach}(t) = \sum_{p \in R} |p.\mathrm{tags}|$, which is $27$
of the $55$ tag-practice cells; (ii) since every shipped practice requires
exactly two labels, $\mathrm{burden}(t) = 2 \cdot \mathrm{reach}(t)$ for every
tag. The executed rows, as (tag, reach, burden), are (`analysis`, 7, 14),
(`data`, 1, 2), (`engineering`, 6, 12), (`research`, 8, 16), and
(`writing`, 5, 10). The matrix describes declared applicability only — a heavily
reached tag is a costlier declaration, not a safer or better-reviewed domain.
*Evidence:*
`tests/test_analytics.py::test_coverage_matrix_pins_the_registry_reach_and_burden`
and
`tests/test_analytics.py::test_coverage_matrix_total_cells_match_tag_declarations`.
:::

::: {.proposition #prop:digest title="Digest order-independence and drift visibility"}
`canonical_registry` sorts practices by id before serializing, so
`registry_digest` is invariant under any permutation of the registry tuple. The
digest is a SHA-256 value rendered as 64 lowercase hexadecimal characters, and
editing any single practice field changes it, which is what makes silent method
drift visible in review. The universal clause is checked field by field: the
test table is closed against `dataclasses.fields(BlackPractice)`, so a field
added to the record but omitted from `canonical()` fails rather than quietly
making the proposition false. The digest identifies method content only; it is
not a signature of evidence, of work, or of any person. *Evidence:*
`tests/test_serialization.py::test_digest_is_order_independent_and_hex_shaped`,
`tests/test_serialization.py::test_digest_changes_when_any_practice_field_changes`,
and `tests/test_serialization.py::test_field_edit_table_covers_every_serialized_field`.
:::

::: {.proposition #prop:ladder title="The coverage ladder is partial"}
The exported `DECLARATION_STATUS_ORDER` fixes
$\texttt{NEEDS\_REWORK} \prec \texttt{NEEDS\_EVIDENCE} \prec \texttt{ALIGNED}$
with ranks $0$, $1$, and $2$ under `status_rank`. `OUTSIDE_SCOPE` has no rank:
`status_rank` raises `ValueError` rather than comparing it, because an
outside-scope assessment says no practice applied — a statement about tag
coverage, not a position below or above any coverage status. *Evidence:*
`tests/test_analytics.py::test_declaration_status_order_ranks_rework_lowest_and_aligned_highest`
and `tests/test_analytics.py::test_status_rank_rejects_outside_scope`.
:::

## Structural invariants

The invariants battery checks the *shape* of the registry rather than any single
attempt. Each check returns a `RegistryCheck`, and each is validated by a
*proof-of-detection* pair: a test asserting it passes on the real registry and
at least one test planting a counter-example that makes it fail. A green check
that never saw a bad input does not count.

::: {.proposition #prop:invariants title="Invariants with proof of detection"}
The battery `all_invariants` runs exactly the following seven checks, in order,
and the real registry passes all seven:

- **I1 — ids distinct.** Every practice id is a distinct, non-blank string.
  Planted: a duplicated, blank, and non-string id.
- **I2 — fields populated.** Title and wire are non-blank, and required evidence
  is a non-empty tuple of non-blank strings. Planted: a blank title, an empty
  evidence tuple, a blank label, and a string evidence field.
- **I3 — tags reachable.** Every practice has at least one tag, and every tag is
  in $V$. Planted: a zero-tag practice, a string tag field, and an
  out-of-vocabulary tag.
- **I4 — kind valid.** Every $\mathrm{kind}$ is a real family member. Planted: a
  string kind.
- **I5 — family coverage.** Every family in $K$ retains at least one practice.
  Planted: a registry with all `STEWARDSHIP` practices removed.
- **I6 — labels matchable.** Required labels are distinct per practice and
  already lowercase-normalized (the evaluator lowercases declared evidence, so
  an uppercase registry label could never match), and the evidence field keeps
  its declared tuple shape. Planted: a duplicate label, an uppercase label, and
  a non-tuple field.
- **I7 — digest computable.** Canonical serialization and digesting succeed; a
  registry that cannot be digested cannot be reviewed for drift. Planted: a
  non-serializable tag field.

*Evidence:* `tests/test_invariants.py` contains the pass-on-real and
fail-on-planted tests for each check, and asserts the battery has exactly seven
uniquely named checks that are all green with detail `ok` on the real registry.
`invariants_hold` is the conjunction of the seven and is `True` on $R$.
:::

The plate below runs that battery eight times — once on the shipped registry and
once on each planted registry — so proof of detection is visible as a matrix
rather than asserted as a policy.

![The 7-check structural battery run over 8 registries: the shipped registry, which passes every check, and 7 registries each carrying one planted defect. Every plant fails the check it targets, boxed in its row, which is what makes the battery a proof of detection rather than a record of greenness. 2 plants also fail a check they were not aimed at — the practice_kind_valid plant also fails kind_coverage and registry_digest_computable; the registry_digest_computable plant also fails practice_tags_reachable — because a single planted value can break more than one structural property at once; those cells are drawn rather than designed away. A firing check shows the battery can reject a malformed registry, not that the practices are the right ones, that their evidence is adequate, or that any work was done well.](../output/figures/black_invariant_detection.png){#fig:black-invariant-detection width=100%}

The off-diagonal cells are the honest part. A kind that is not a `PracticeKind`
member drops its practice out of family coverage *and* breaks canonical
serialization, so that one plant fails three checks; a `None` tag field is both
unreachable and unserializable. Plants chosen to trip exactly one check each
would have produced a cleaner diagonal and a less accurate figure.

## Claim-to-test binding

Each definition and proposition above names the executable test that verifies
it. The two tables below collect those bindings so a reader can go from claim to
failing condition without searching. A claim whose test cannot fail is not
admitted — the invariants battery makes the same demand of itself through
planted counter-examples. Every row is a statement about code behaviour under
declared inputs; none is a claim about the world, about safety, or about
persons.

| Definition | What the code must still do | Verifying test |
| --- | --- | --- |
| [@def:practice] | Field names, order, and the `METHOD` default | `tests/test_formalism_definitions.py::test_practice_record_matches_the_definition` |
| [@def:tag-vocabulary] | $V$ is exactly the five reviewed tags | `tests/test_formalism_definitions.py::test_tag_vocabulary_matches_the_definition` |
| [@def:registry] | $R$ is an ordered tuple of eleven practices with a digest | `tests/test_formalism_definitions.py::test_registry_matches_the_definition` |
| [@def:craft-families] | $K$ is exactly the six declared families | `tests/test_formalism_definitions.py::test_craft_families_match_the_definition` |
| [@def:work-attempt] | $W$ and the dated-item pair keep their shape | `tests/test_formalism_definitions.py::test_work_attempt_matches_the_definition` |
| [@def:assessment-record] | $A$ and its finding triples keep their shape | `tests/test_formalism_definitions.py::test_assessment_record_matches_the_definition` |
| [@def:practice-status] | $S_p$ has exactly three members | `tests/test_formalism_definitions.py::test_practice_status_codomain_matches_the_definition` |
| [@def:assessment-status] | $S_a = S_p \cup \{\texttt{OUTSIDE\_SCOPE}\}$ | `tests/test_formalism_definitions.py::test_assessment_status_codomain_matches_the_definition` |
| [@def:review-config] | Each named bad configuration raises rather than coerces | `tests/test_formalism_definitions.py::test_review_configuration_refuses_what_the_definition_names` |
| [@def:intake] | `clean` strips, lowercases, and notes every drop | `tests/test_formalism_definitions.py::test_intake_normalization_matches_the_definition` |
| [@def:freshness] | Each of the five partition rules, executed | `tests/test_formalism_definitions.py::test_freshness_partition_matches_the_definition` |
| [@def:applicability] | Selection is exactly non-empty tag intersection | `tests/test_formalism_definitions.py::test_applicability_matches_the_definition` |
| [@def:finding-rule] | All four branches, in order, with ordered trails | `tests/test_formalism_definitions.py::test_practice_finding_rule_matches_the_definition` |
| [@def:aggregation] | All four aggregation branches, in order | `tests/test_formalism_definitions.py::test_overall_aggregation_matches_the_definition` |
| [@def:evidence-surfaces] | Field names, order, stale ⊆ missing, declared evidence order | `tests/test_formalism_definitions.py::test_evidence_surfaces_match_the_definition` |
| [@def:report-envelope] | The ten fields, the digest pointer, the travelling non-claims | `tests/test_formalism_definitions.py::test_report_envelope_matches_the_definition` |

| Proposition | Statement essence | Verifying test | Boundary kept |
| --- | --- | --- | --- |
| [@prop:surfaces-projection] | Status and reasons are projections of the typed surfaces; both public forms report one staged computation | `tests/test_witness_surfaces.py::test_both_public_forms_report_one_staged_computation`, `tests/test_witness_surfaces.py::test_surfaces_align_one_to_one_with_findings_and_generate_their_reasons` | surfaces of declarations, never evidence quality or a cross-line rank |
| [@prop:registry-fail-closed] | An unscoreable registry blocks, with a note | `tests/test_evaluator.py::test_custom_registry_failures_are_blocking` | shape of the registry, not merit of its practices |
| [@prop:intake] | Malformed intake is noted, never raised | `tests/test_evaluator.py::test_malformed_label_tokens_are_dropped_but_good_ones_kept`, `tests/test_evaluator.py::test_string_tag_declaration_is_ignored_with_a_note` | supported hostile branches only, not a sandbox |
| [@prop:blocking] | Blank description blocks all scoring | `tests/test_evaluator.py::test_blank_description_is_a_blocking_intake_defect` | no honest scoring without a described work item |
| [@prop:scope] | `OUTSIDE_SCOPE` $\iff$ no tag intersects | `tests/test_evaluator.py::test_no_matching_tags_is_outside_scope_with_review_date` | coverage statement, never safety or permission |
| [@prop:global-local] | The first branch is global, not per-practice | `tests/test_manuscript_bindings.py::test_method_prose_matches_the_global_emptiness_branch` | rule about the code path, not about the work |
| [@prop:fresh-monotonicity] | Fresh labels never demote a finding (conditional) | `tests/test_analytics.py::test_sampled_permutations_never_regress_after_first_declaration`, `tests/test_evaluator.py::test_irrelevant_evidence_only_needs_rework_without_present_reason` | sampled property; empty-declaration boundary is intentional |
| [@prop:determinism] | Evaluation and serialization are deterministic | `tests/test_serialization.py::test_canonical_assessment_is_deterministic_and_complete` | byte-identity of records, not correctness of work |
| [@prop:strict-staleness] | Staleness is strict: age $> \omega$, equality fresh | `tests/test_analytics.py::test_staleness_profile_pins_the_strict_inequality_boundary` | date arithmetic, not trustworthiness of old evidence |
| [@prop:window-monotonicity] | Widening $\omega$ never lowers coverage rank | `tests/test_analytics.py::test_widening_the_window_never_regresses_coverage_rank` | permissiveness of review setting, not work quality |
| [@prop:coverage-algebra] | Coverage rows: $27$ of $55$ cells; burden $= 2 \cdot$ reach | `tests/test_analytics.py::test_coverage_matrix_pins_the_registry_reach_and_burden` | declared applicability, not domain safety |
| [@prop:digest] | Digest is permutation-invariant and drift-visible in every field | `tests/test_serialization.py::test_digest_is_order_independent_and_hex_shaped`, `tests/test_serialization.py::test_digest_changes_when_any_practice_field_changes` | identifies method content, signs nothing else |
| [@prop:ladder] | Ladder ranks $0 \prec 1 \prec 2$; `OUTSIDE_SCOPE` unranked | `tests/test_analytics.py::test_status_rank_rejects_outside_scope` | ordering of statuses, not of people or work |
| [@prop:invariants] | Registry shape checks, each with planted failures | `tests/test_invariants.py::test_battery_runs_every_check_once_and_passes_on_real_registry` | shape of the registry, not merit of its practices |

The named tests are themselves checked: a suite test re-reads this section and
fails if any referenced `tests/…::function` does not exist, so a renamed or
deleted binding surfaces as a red test rather than silent prose drift. A second
test refuses any formalism block without a label, any reference to a label no
block declares, and any hand-written block number anywhere in the manuscript.

These claims bound what the instrument establishes under its declared inputs and
implementation. The tests establish that the registry is well-shaped and that
scoring is deterministic, staged, and conditionally monotone in fresh evidence.
They do not establish that a declared source is real, that a `test` label
corresponds to a passing test, or that an `ALIGNED` status means the work is
correct — only that the declared Black labels are present.
