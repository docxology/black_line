# Operating protocol: the smallest honest loop {#sec:protocol}

The protocol operationalizes the distinction among the five epistemic layers of
[the method](#sec:method) through five review actions. Neither the layers nor
the actions are the registry's six practice families.

The instrument is designed around a short operating loop rather than a final
score. Begin with the object of work, the decision it is meant to inform, and the
constraints or exclusions that make the question meaningful. Choose the smallest
method whose output could change that decision. Name the evidence a collaborator
could inspect, including what would falsify or materially weaken the result. Run
the method, keep the negative path, and leave a handoff that another reader can
continue without private context.

The executable protocol has five review actions:

1. **Frame.** Construct a `WorkAttempt` with a non-blank description and
   reviewed tags. An unknown tag is not an implicit approval; it simply may
   produce `OUTSIDE_SCOPE` when no practice is reached.
2. **Declare.** Add coarse evidence labels and, when observations can age, dated
   `EvidenceItem` records. Labels are pointers to artifacts for review, not the
   artifacts or their proof.
3. **Evaluate.** Pin `as_of`, optionally set a non-negative freshness window,
   and read every finding's reasons and the intake notes.
4. **Repair or refresh.** Treat missing evidence as a request to do work and
   stale evidence as a request to repeat an observation. Do not convert either
   into a success by changing a label alone.
5. **Archive.** Retain an `EvaluationRecord` using `evaluation_record`, then
   serialize it with `canonical_evaluation_record`. It preserves the original
   declaration, normalized intake, effective review date and freshness window,
   producing package version, complete ordered registry, assessment, surfaces,
   and attempt-wide `evidence_declared` context. Retain the source or observation
   artifact behind each label separately. A registry digest identifies a matching
   retained snapshot; it cannot recover a missing snapshot or authenticate evidence.

For the supported text/set/dated intake and the existing serialization,
loading, and replay recipe, see
[Replay records and migration](https://github.com/docxology/black_line/blob/main/docs/usage.md#replay-records-and-migration).
Exact replay requires the recorded package version. Result-only
`canonical_assessment/1.0` bytes do not retain the declaration or configuration
and cannot be upgraded into faithful replay inputs without them.

![The smallest honest operating loop: frame the decision, declare pointers to inspectable artifacts, evaluate with a pinned date and registry digest, repair or refresh gaps, and archive the trail. The dark panel makes explicit what remains outside the instrument's authority.](../output/figures/black_operating_loop.png){#fig:black-operating-loop width=100%}

This loop is deliberately asymmetric. The evaluator can block an empty work
description and can refuse to call an unknown or stale declaration fresh, but
it cannot establish semantic truth from a label. The decisive review therefore
remains with the collaborator who follows the evidence trail. The evidence
matrix figure makes that boundary visible: it is a map of what the evaluator
asks for, not a certificate of what the world contains.
