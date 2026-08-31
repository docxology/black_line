# Abstract

Black Line is a positive operating discipline for concise, inspectable,
revisable work and research. It treats disciplined practice as a set of visible
*wires* rather than a claim about character: state the question, trace
substantive claims, use the smallest sufficient method, expose failure
conditions, verify and steward the result, and leave a handoff another person
can recover. The discipline is not new. It collects habits that recur across the
philosophy of science, the sociology of knowledge, and the reproducible-research
literature, and makes one small operational slice mechanically inspectable
[@popper1959logic; @merton1973normative; @goodman2016reproducibility].

The instrument is executable and modest. A versioned registry names eleven
practices in six practice families, each with coarse review labels a collaborator
could inspect. `evaluate_work` validates the review configuration and the
registry's own shape, then runs four stages — intake normalization, freshness
partition, tag matching, and scoring with aggregation — and returns `ALIGNED`,
`NEEDS_EVIDENCE`, `NEEDS_REWORK`, or `OUTSIDE_SCOPE`. Malformed input becomes
review notes instead of an exception, a blank description blocks scoring
outright, an unscoreable registry fails closed, and an optional staleness window
lets dated evidence age into a refresh request rather than a rework. Seven
structural invariants check the registry's own shape, and each is shown firing
on a planted-bad registry rather than merely passing on the real one. A
deterministic digest makes any edit to a wire visible in a diff and travels on
each serialized assessment, so the method version behind a review stays
recoverable.

What comes back is a prompt for better work, not a safety verdict, an
institutional accreditation, or permission to cross the Red Line security
boundary. An `ALIGNED` status means only that every required label for every
applicable practice was declared as fresh under the chosen review date — never
that a source is real or a claim is true. The clean-rerun wire targets
computational reproducibility and stops well short of independent replication or
inferential agreement. Black Line is the second work in the four-line set: it
cross-references Red Line as the refusal boundary, Golden Line as the
aspirational thread, and White Line as the record of absence, restraint, and
unknowability, and it copies none of their registries, evaluators, or
conclusions.
