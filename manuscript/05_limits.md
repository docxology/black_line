# Limits and Epistemic Boundaries {#sec:limits}

Black Line is self-declared and lexical. A person can choose the wrong tags,
provide weak sources, write a ceremonial limitation, or declare a handoff that
another reader cannot use. The evaluator matches labels; it does not inspect
semantic truth, power relations, labor conditions, or downstream harm. An
`ALIGNED` status is therefore a statement about the *presence* of declared
evidence and nothing more — the strongest honest reading of it is "this work has
laid out the pieces a reviewer would want," not "this work is correct." The
formal propositions are careful about exactly this:
[@prop:surfaces-projection] states that the finding is a projection of its
surfaces — a reading of declared labels, not of the work — and
[@prop:determinism] pins the scoring as deterministic. Under fixed inputs, the
tests establish registry shape and deterministic scoring. Conditional
monotonicity is exercised rather than asserted ([@prop:fresh-monotonicity]):
seeded permutation sweeps over
incremental declarations confirm that once a declaration is non-empty the
status never regresses, with the empty-declaration boundary pinned as the one
intentional exception ([@prop:strict-staleness]), and the same sweep is drawn as
[the monotonicity lattice](#fig:black-monotonicity-lattice). None of that
establishes anything about the world the labels point to (developed in
[the scholarship section](#sec:scholarship)).

The registry digest narrows one archival ambiguity but does not solve it. It
shows which practice content was used and makes disagreement visible; it is not
a signature, an external timestamp, or proof that the evidence record was not
altered. Independent provenance would require a separate trust boundary and is
left explicitly deferred.

## Adversarial declarations {#sec:adversarial}

Because every input is self-declared, the instrument can be gamed by
construction, and the honest response is to demonstrate the attacks rather
than deny them. Each of the following was executed against the real evaluator.

**Label-stuffing.** The registry's evidence vocabulary contains 22 distinct
labels. A `research`-tagged attempt that simply declares all 22 — with no
artifact behind any of them — returns `ALIGNED`. The evaluator matches
declared labels against required ones; it has no access to whether a declared
`rerun` was ever run or a declared `reviewer` ever read anything. A stuffed
declaration is lexically indistinguishable from a diligent one.

**Tag-minimization.** Tags select the practices an attempt is scored against,
so narrowing the declared tags shrinks the review surface
(see the [coverage matrix](#sec:coverage-burden)). Executed: the same
description with the same two declared labels (`data_origin`,
`transform_log`) returns `NEEDS_REWORK` across 7 applicable practices when
tagged `analysis` and `data`, and `ALIGNED` against the single applicable
practice when tagged `data` alone. Both statuses are true statements about
declaration coverage; the second is simply earned against a sevenfold smaller
burden — 7 practices and 14 required labels narrowed to 1 and 2. (The registry's
widest spread is eightfold, `research` at 8 practices against `data` at 1; this
executed contrast starts from `analysis`, which reaches 7.) Whether the narrow
tag set honestly describes the work is not a question the evaluator can pose.

**Refresh-date laundering.** Staleness reads declared dates, and dates are
declarations too. Executed with the `data-provenance` practice under a
30-day window and review date 2026-07-01: a full two-label declaration whose
evidence is 70 days old returns `NEEDS_EVIDENCE`, and the identical
declaration with its dates rewritten to the review date returns `ALIGNED`.
The evaluator cannot distinguish a genuine refresh — re-observing the data
origin — from an edit to a date string.

These are instances of a well-documented dynamic, not defects unique to this
design. Campbell observed that the more a quantitative indicator is used for
decision-making, the more subject it becomes to corruption pressures that
distort the very process it monitors [@campbell1979assessing]; Strathern
compressed the same dynamic into the aphorism that when a measure becomes a
target, it ceases to be a good measure [@strathern1997improving]; and Power's
study of audit cultures shows how systems built on checkable declarations
drift toward producing auditable form rather than the substance the audit was
meant to secure [@power1997audit]. A practice registry that certified quality
would make these failure modes catastrophic, because a gamed status would
launder bad work into apparent good work. Black Line's design response is to
refuse the certifying role entirely: a status reports declaration coverage,
so a gamed `ALIGNED` overstates nothing but coverage. The attacks also stay
inspectable rather than hidden — the declared tag set, the declared labels,
and the declared dates are the very record a reviewer reads, so a reviewer
who asks "do 22 labels correspond to 22 artifacts?", "do these tags describe
this work?", or "what changed at this refresh?" is asking questions the
declaration itself exposes. The instrument narrows what gaming can
counterfeit; it cannot remove the need for the human judgment those
questions require, and it never converts any status into a safety score,
an accreditation, or a permission.

## Legibility bias

The instrument also has a bias toward legibility. Some important work is slow,
embodied, tacit, relational, or not safely compressible into evidence labels, and
a discipline that rewards what is easy to declare can quietly devalue what is
hard to. The coarse-label design is a deliberate guard against false precision —
it refuses to pretend it can score truth — but it cannot recover the aspects of
strong work that resist declaration at all. Polanyi's account of tacit knowledge
is a useful warning here: participation and skilled judgment are not merely
missing fields waiting to be added to a form [@polanyi1958personal]. Situated
action also means that a written plan cannot determine all later action
[@suchman1987plans]. The White Line work exists partly to record what such a
method leaves out.

## A design claim, not an outcome claim

I am making a design and implementation claim, not an outcome claim. I have not
run a user study, compared teams working with and without Black Line, or
measured whether the practices improve correctness, speed, equity, or downstream
decisions. Those are empirical questions needing a defined population, a
comparator, an outcome measure, and governance review, and none of that is here.
The evidence in this repository supports what the package computes and what its
documentation asks a reviewer to inspect. It does not support a causal claim
that using the instrument improves anything.

## Bounded by the line set

Finally, Black Line is bounded by the rest of the line set on purpose. Golden
Line addresses direction and aspiration; Red Line holds the refusal boundary;
White Line marks absence, restraint, and unknowability. Black Line should not
absorb those questions merely because they are difficult to measure, and a
passing Black Line assessment never licenses anything a Red Line refusal would
forbid. The discipline's contribution is to make ordinary rigor inspectable —
not to guarantee it.
