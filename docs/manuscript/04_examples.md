# Executed examples and boundaries {#sec:examples}

Every status in this section is the output of a real `evaluate_work` call —
the same public API a reviewer would run — with the exact inputs stated so the
transitions can be reproduced. None of the runs changes what a status means:
each is a report on declaration coverage under the registry's tag contract,
never a judgment of work quality, and never a permission.

## An executed incremental-declaration path

The first worked example traces one attempt from an empty declaration to full
coverage. The attempt is tagged `research`, which selects 8 of the 11
practices and commits the declarer to 16 required evidence labels (see the
[coverage matrix](#sec:coverage-burden)). `declaration_status_path` evaluates
the same attempt 17 times — once with no evidence, then once after each label
is added — through the ordinary evaluator. The table reports every step at
which the declaration completes a practice, plus the two boundary steps:

| Step | Labels added since previous row | Labels declared | Practice completed | Practices `ALIGNED` | Overall status |
| ---: | --- | ---: | --- | :---: | --- |
| 0 | — | 0 | — | 0 of 8 | `NEEDS_EVIDENCE` |
| 1 | `question` | 1 | — | 0 of 8 | `NEEDS_REWORK` |
| 2 | `scope` | 2 | `question-first` | 1 of 8 | `NEEDS_REWORK` |
| 4 | `source`, `claim` | 4 | `source-traceable` | 2 of 8 | `NEEDS_REWORK` |
| 6 | `failure`, `test` | 6 | `failure-visible` | 3 of 8 | `NEEDS_REWORK` |
| 8 | `uncertainty`, `limits` | 8 | `stated-uncertainty` | 4 of 8 | `NEEDS_REWORK` |
| 10 | `negative_result`, `log` | 10 | `negative-results-kept` | 5 of 8 | `NEEDS_REWORK` |
| 12 | `environment`, `rerun` | 12 | `reproducible-from-clean` | 6 of 8 | `NEEDS_REWORK` |
| 14 | `next_step`, `handoff` | 14 | `concise-handoff` | 7 of 8 | `NEEDS_REWORK` |
| 16 | `reviewer`, `review_note` | 16 | `review-before-reliance` | 8 of 8 | `ALIGNED` |

Three properties of the path are worth reading directly off the table. First,
the overall status is the most demanding per-practice status, so it stays
`NEEDS_REWORK` from step 1 through step 15 even as completed practices
accumulate from 0 to 7; only the sixteenth label — completing the last
applicable practice — yields `ALIGNED`. The per-practice findings, not the
overall status, are where intermediate progress is visible. Second, the step 0
to step 1 transition is the boundary [@prop:global-local] names: an empty
declaration is `NEEDS_EVIDENCE`, and the first label, although it adds
information, moves the overall status to `NEEDS_REWORK`. Third, executed on this
path, `no_status_regression` returns `True` for steps 1 through 16 and `False`
only when the empty step 0 is included, which is exactly the conditional
monotonicity of [@prop:fresh-monotonicity]: once a declaration is non-empty,
adding fresh labels never regresses the status. As [@prop:surfaces-projection] establishes, an `ALIGNED` reports declared labels — never that any source is real, any test passed, or any claim is correct.

The same path is drawn below as an executed status grid, one column per
`evaluate_work` call, so the per-practice accumulation the table can only
summarize is visible cell by cell:

![The executed incremental-declaration path as a status grid: the `research`-tagged attempt selects 8 practices (16 required labels), and every cell is one real `evaluate_work` call as labels accumulate one per step from an empty declaration (step 0, `NEEDS_EVIDENCE`) to full coverage (step 16). Per-practice findings flip to `ALIGNED` as each practice's labels complete, while the overall status — the most demanding per-practice status — stays `NEEDS_REWORK` from step 1 through step 15 and first reaches `ALIGNED` at step 16: conditional fresh-evidence monotonicity made visible. An `ALIGNED` cell records declared labels only; it does not show any source is real, any test passed, or any claim is true.](../output/figures/black_incremental_path.png){#fig:black-incremental-path width=100%}

One executed order is a trace, not a property. `declaration_status_path` is
cheap enough to run over many orders, so the lattice below sweeps twelve
seeded orders of the same sixteen labels — the registry's own order as row 0,
then eleven permutations of it — and reports `no_status_regression` per row
together with a count of every rank decrease in the sweep:

![Conditional fresh-evidence monotonicity executed as a sweep rather than a single trace: 12 seeded orders (seed 20260727) of the same 16 labels, each evaluated at all 17 steps through the real evaluator, for 204 calls. Every row is monotone from step 1 onward (12 of 12), and all 12 rank decreases in the sweep are the step 0 to step 1 empty-declaration boundary. The overall status path is identical across every sampled order, which is a property of taking the most demanding per-practice status, not evidence that order is irrelevant to a reviewer. The sample is seeded and finite; it is not a proof over all 16! orders.](../output/figures/black_monotonicity_lattice.png){#fig:black-monotonicity-lattice width=100%}

The sweep is what makes the claim falsifiable rather than illustrative: a
single non-monotone row, or a rank decrease anywhere but the first step, would
appear as a `NO` in the right-hand column and a larger count in the footer.
It also shows something the single trace could not — the overall path is the
same whichever order the labels arrive in, because the aggregation takes the
most demanding per-practice status and the last applicable practice completes
at step 16 in every order. That is an aggregation property, not a claim that
declaration order is unimportant to the person doing the work.

That first transition is intentional, and [@prop:global-local] says why: an
attempt with no usable evidence returns `NEEDS_EVIDENCE` because there is
nothing to inspect, while one irrelevant label moves it to `NEEDS_REWORK`
because the attempt has begun declaring and still omits every required label.
The change reports a more specific request, not worse work, which is why the
monotonicity claim is scoped to the non-empty branch. The `ALIGNED` at step 16
carries only its declared labels and the registry digest that pins the method
version behind them.

## The decay sweep, executed

The staleness window shows how the instrument distinguishes decay from
absence. Suppose a practice's evidence was fully declared but one supporting
observation carries a date older than the configured window. Under staleness
the aged observation stops counting as fresh, and because the practice's only
gap is that one stale item, the finding is `NEEDS_EVIDENCE` — a request to
refresh — rather than `NEEDS_REWORK`. The same evidence with no window, or
with a recent date, returns `ALIGNED`. A date in the future, or a date the
parser cannot read, is never counted and is reported as an intake note so the
declarer can correct it.

The threshold is a strict inequality — evidence aged exactly the window is
still fresh; one day older is stale. The sweep below executes
`staleness_profile` over the `data-provenance` practice (required labels
`data_origin` and `transform_log`) with review date 2026-07-01, re-reviewing
the same declaration as its evidence ages. Each cell is one real
`evaluate_work` call:

| Evidence age (days) | Window 30 | Window 51 | No window | One label never declared, window 30 |
| ---: | --- | --- | --- | --- |
| 0 | `ALIGNED` | `ALIGNED` | `ALIGNED` | `NEEDS_REWORK` |
| 30 | `ALIGNED` | `ALIGNED` | `ALIGNED` | `NEEDS_REWORK` |
| 31 | `NEEDS_EVIDENCE` | `ALIGNED` | `ALIGNED` | `NEEDS_REWORK` |
| 51 | `NEEDS_EVIDENCE` | `ALIGNED` | `ALIGNED` | `NEEDS_REWORK` |
| 52 | `NEEDS_EVIDENCE` | `NEEDS_EVIDENCE` | `ALIGNED` | `NEEDS_REWORK` |
| 70 | `NEEDS_EVIDENCE` | `NEEDS_EVIDENCE` | `ALIGNED` | `NEEDS_REWORK` |

The three contrasts fix the semantics. A full declaration flips from
`ALIGNED` to `NEEDS_EVIDENCE` exactly one day past its window — at age 31
under a 30-day window, at age 52 under a 51-day window. With no window, dated
evidence never goes stale. And a declaration that never included one required
label is `NEEDS_REWORK` at every age, because an absent label is missing work
rather than aged work. The figure below traces the same boundary continuously
over ages 0–70.

![Evidence decay from executed `evaluate_work` sweeps over the `data-provenance` practice with review date 2026-07-01: a full declaration stays `ALIGNED` while its evidence age is at most the freshness window and flips to `NEEDS_EVIDENCE` (a refresh request) exactly one day past it — the threshold is a strict inequality — while a declaration that never included one required label is `NEEDS_REWORK` at every age, and a declaration with no window never goes stale. A fresh date is a declaration property; it does not show the underlying observation was ever adequate or still holds.](../output/figures/black_evidence_decay.png){#fig:black-evidence-decay width=100%}

## The refresh queue, executed

Decay describes one label at a time. A reviewer holding a whole declaration
has a different question: which part of it expires first? `refresh_horizon`
answers that by ordering the dated labels from nearest to furthest from the
freshness boundary. The figure below runs it on an attempt tagged `data` and
`research` at review date 2026-07-01 under a 120-day window.

![The refresh queue for one declaration, drawn from `refresh_horizon` in its own ascending nearest-to-stale order: at review date 2026-07-01 under a 120-day window, 5 dated labels are scheduled, from 'data_origin' at 17 days to 'scope' at 113, each naming the practice that requires it. The named band below records the 3 declarations the queue omits and why — one of them undated, which is itself one of the omitted classes — so the omission rule is visible rather than implicit. Bar length is days until a declared date crosses the window; it is not a measure of how much the underlying observation matters or how good it was.](../output/figures/black_refresh_queue.png){#fig:black-refresh-queue width=100%}

Three declarations are absent from the queue, and the band names each one
rather than dropping it. An undated label is treated as current, so it has no
boundary to reach. An already-stale label is a refresh request now, not a
schedule. And a label no practice in the registry requires — `dashboard_link`
here — cannot move any status, so scheduling it would be misleading. The
third case is why `refresh_horizon` takes the practice registry as an
argument: the queue is a view of the registry's demands on a declaration, not
an inventory of the declaration's dates.

## A batch, executed

Every example so far follows one attempt. A reviewer holding a quarter's work
holds many, and the question changes again: across differently-tagged
attempts, which wires stay open? `summarize_assessments` answers the first
half by counting statuses and attributing every non-`ALIGNED` finding to its
craft family; recounting the same findings per practice answers the second.
The panel below runs both over a pinned battery of eight attempts — one for
each reviewed tag, one dated declaration aged past the window, one attempt
declaring two tags at once, and one tagged outside the vocabulary — at review
date 2026-07-01 under a 30-day window.

![The registry's demands across a batch rather than one attempt: 8 pinned work attempts spanning the 5-tag vocabulary and one tag outside it, each evaluated at review date 2026-07-01 under a 30-day window. Every assessment status the enum defines occurs in the batch (`ALIGNED` 2, `NEEDS_EVIDENCE` 1, `NEEDS_REWORK` 4, `OUTSIDE_SCOPE` 1), open findings concentrate in TRACEABILITY (6), and 10 of the 11 practices are left open at least once, led by `data-provenance` and `versioned-increments` at 3. A gap frequency is a declaration statistic over this battery; it is not a ranking of the practices by importance, and a frequently-open wire is one these declarers did not declare, not one that failed.](../output/figures/black_batch_summary.png){#fig:black-batch-summary width=100%}

The batch shows something no single attempt can. `data-provenance` and
`versioned-increments` are open most often not because they are harder
practices but because of which tags reach them — `analysis` and `data` for the
first, `engineering` and `writing` for the second — and the attempts carrying
those tags here rarely declared the matching labels.
`question-first` is the only practice the batch never leaves open, which says
that the attempts declaring `analysis`, `research`, or `writing`
all named a question and a scope, and nothing more.
Read as a review artifact, the panel is a prompt: it names where declarations
are thin across a body of work, and it stops there. It does not say those
wires were done badly, or that the two `ALIGNED` attempts were done well.

## Boundary cases

Two boundary cases fix the instrument's scope. A work item whose description is
blank or non-text is a blocking intake defect: no practice is scored, the overall
status is `NEEDS_REWORK`, and the single note asks the author to restate the work
before assessment. An action tagged only `music` — a tag outside the reviewed
vocabulary and matching no practice — returns `OUTSIDE_SCOPE`. That result does
not mean the action is good, safe, or permitted; it means this positive-practice
registry does not assess it. Red Line remains the separate refusal boundary, and
an `OUTSIDE_SCOPE` verdict from Black Line grants nothing.

Finally, invalid review configuration is not silently normalized: a malformed
ISO `as_of` value or a negative/non-integer freshness window raises before
scoring. This is a configuration defect rather than a work finding, and it
prevents a caller from mistaking an accidental date interpretation for a valid
review.
