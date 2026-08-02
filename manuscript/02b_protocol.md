# Operating protocol: the smallest honest loop {#sec:protocol}

The protocol operationalizes the six practice families of [the method](#sec:method).

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
5. **Archive.** Serialize the assessment and retain the source or observation
   record behind each label. The assessment carries the registry digest so a
   later reader can distinguish a changed method from a changed result, while
   the retained artifacts make the declaration inspectable.

![The smallest honest operating loop: frame the decision, declare pointers to inspectable artifacts, evaluate with a pinned date and registry digest, repair or refresh gaps, and archive the trail. The dark panel makes explicit what remains outside the instrument's authority.](../output/figures/black_operating_loop.png){#fig:black-operating-loop width=100%}

This loop is deliberately asymmetric. The evaluator can block an empty work
description and can refuse to call an unknown or stale declaration fresh, but
it cannot establish semantic truth from a label. The decisive review therefore
remains with the collaborator who follows the evidence trail. The evidence
matrix figure makes that boundary visible: it is a map of what the evaluator
asks for, not a certificate of what the world contains.
