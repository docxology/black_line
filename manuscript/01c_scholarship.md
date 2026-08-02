# Intellectual lineage: where the practices come from {#sec:scholarship}

Black Line does not invent its practices. It collects disciplines that recur,
under different names, across the philosophy of science, the sociology of
knowledge, the study of craft, and the literature on reproducible computation,
and makes them mechanically inspectable. Situating the registry in that lineage
does two things: it shows the practices are not personal taste, and it fixes
which older idea each wire operationalizes — and, just as often, where the older
idea reaches further than any wire here can.

## Framing and falsification

The demand to *state the question before the method* and to *expose failure
conditions* is informed by the falsificationist tradition. Popper proposed
falsifiability as a criterion for empirical claims: a claim should rule out some
observable state so that experience could in principle bear against it
[@popper1959logic]. That is a philosophical criterion, not a sufficient condition
for good work. Black Line therefore translates only the practical question — what
would weaken this result? — into the `question-first` and `failure-visible`
practices, keeping a useful demand at the surface of ordinary work without
claiming to implement Popper's philosophy wholesale.

Feynman gave the same idea its ethical edge in his 1974 "Cargo Cult Science"
address, where the missing ingredient in imitation science is "a kind of
scientific integrity \ldots a leaning over backwards" to report everything that
might invalidate a result, not only what confirms it [@feynman1974cargo]. That
injunction is the reason Black Line treats `stated-uncertainty` and
`negative-results-kept` as first-class practices rather than optional courtesies:
a number without its boundary conditions, or a study that files away only its
successes, is exactly the self-deception Feynman warned against.

## Traceability, review, and the norms of science

The practices that concern *sourcing*, *review*, and *stewardship* draw on
Merton's account of the ethos of science. His norms — communalism, universalism,
disinterestedness, and organized skepticism — describe science as a community
that holds claims in common and subjects them to structured, impersonal scrutiny
as a social ideal [@merton1973normative]. `source-traceable`,
`review-before-reliance`, and `negative-results-kept` are small mechanical
echoes of organized skepticism: they make a claim's provenance and its exposure
to a second reader into declared, checkable evidence rather than assumed virtue.
Stewardship of a shared record has a parallel, not identical, lineage in Ostrom's
study of how communities sustain common-pool resources through monitoring,
graduated accountability, and locally legible rules [@ostrom1990governing]. A
research record can function as a commons for a collaborating group;
`versioned-increments` and `review-before-reliance` are small monitoring practices
for that setting, not a claim that every record has the same governance structure.

## Traceable prose and the smallest sufficient method

Knuth's literate programming reframed a program as a work of exposition — a
document woven so that a human reader can follow the reasoning and the machine
can still run it [@knuth1984literate]. Black Line's `concise-handoff` and
`source-traceable` practices extend that design problem beyond code: the
deliverable should let a collaborator recover purpose, evidence, and next action
without private context. The complementary discipline of not over-building is the
pragmatic-engineering counsel to prefer the simplest thing that works and to
resist speculative machinery [@hunt1999pragmatic]; `smallest-sufficient-method`
is that counsel stated as an inspectable wire — do not add apparatus whose output
cannot change the decision.

## Reproducibility as the load-bearing modern practice

The strongest recent influence is the reproducible-research literature. Peng
framed reproducibility — the ability to recompute results from data and code — as
a minimum standard that sits between a single study and full independent
replication [@peng2011reproducible]. Sandve and colleagues distilled the working
habits that make computation reproducible: track provenance, record exactly how
every result was produced, and version the analysis end to end
[@sandve2013ten]. Wilson and colleagues added the pragmatic layer of "good
enough" practices — data management, modest automation, and version control that
a working scientist can actually sustain [@wilson2017good]. Black Line's
`reproducible-from-clean`, `data-provenance`, and `versioned-increments`
practices are small operationalizations of that literature, and its evidence
labels (`environment`, `rerun`, `data_origin`, `transform_log`) are named to
match its vocabulary. Finally, the discipline of honest presentation — refusing
charts and summaries that imply more certainty than the data support — informs the
figures in this paper and the `data-provenance` practice alike
[@cairo2016truthful].

## Reproducibility is not replication

The vocabulary needs one further distinction, and the distinction is the whole
scope of the `reproducible-from-clean` wire. Goodman, Fanelli, and Ioannidis
separate methods reproducibility, results reproducibility, and inferential
reproducibility; the word *reproducible* should not quietly become a synonym for
*true* [@goodman2016reproducibility]. The National Academies report likewise
distinguishes computational reproducibility — consistent computation from the
same inputs, code, methods, and conditions — from replicability in a new study
addressing the same question [@nationalacademies2019rr]. Black Line's clean
rerun is deliberately the first, narrower claim: whether another reader can
re-execute the recorded procedure, not whether the result generalizes or the
inference holds.

The confusion is historical, not careless. Claerbout and Karrenbach coined
*reproducible research* for a specific engineering practice — one-command
figure regeneration [@claerbout1992electronic] — and the term travelled into
fields that already spoke of replication. Plesser traces the cross-
disciplinary swap: the same word names re-running the author's artifacts in
one literature and an independent redo in another
[@plesser2018reproducibility]. Black Line therefore leans on the labels
rather than the word — `environment` and `rerun` name Claerbout's narrow
property whichever term a reader's field attaches to it.

The replication literature is what makes the distinction consequential rather
than pedantic. In the largest coordinated attempt of its kind, 100 psychology
studies were re-run with high-powered designs and original materials where
available; 36 percent of replications reached statistical significance against
97 percent of the original reports [@osc2015estimating]. A survey of 1,576
researchers found a majority had failed to reproduce another scientist's result,
and many their own [@baker2016survey]. Nothing in this instrument addresses
that. A clean rerun of a recorded procedure cannot detect a design that would
not survive a new sample, so an `ALIGNED` finding on the rerun wire is a
statement about a declaration and never a prediction about a future study. The
instrument sits on the near side of that gap on purpose, and says so rather than
letting the shared vocabulary imply otherwise.

## Openness is infrastructure; review is a social act

Open research culture is not produced by a single checkbox. Nosek and
colleagues describe a system in which norms, incentives, reporting practices,
and access to materials have to work together if openness is to improve
credibility [@nosek2015open]. Munafò and colleagues similarly frame
reproducibility as a portfolio spanning methods, reporting, dissemination,
evaluation, and incentives, with reforms requiring ongoing assessment rather
than ceremonial adoption [@munafo2017manifesto]. Black Line translates only a
small operational slice of that program: name a source, preserve a negative
result, invite review, and leave a rerunnable handoff. The translation is useful
because it is small; it is not equivalent to an open-science regime.

## Craft, technē, and legibility as a designed partial view

Polanyi's account of tacit and personal knowledge is the standing counterweight
to any instrument that rewards what can be written down [@polanyi1958personal].
The work that matters may include situated judgment, craft skill, embodied
attention, or a relationship that no finite evidence vocabulary compresses.
Black Line therefore treats legibility as a designed partial view: enough
structure for a collaborator to inspect and continue the work, never a claim
that the visible record exhausts the knowledge in the practice.

Polanyi is one point in a longer argument about craft, and the rest of it
sharpens what a label can hold. Ryle separates knowing how from knowing that: a
competence is not a set of propositions, and someone who can recite every rule
of a craft has not thereby acquired it [@ryle1949concept]. Aristotle's *technē*
already names craft as a distinct kind of knowledge, held in the making rather
than in demonstration [@aristotle1999ethics]. Dreyfus and Dreyfus press the
point developmentally: as skill matures the expert stops consulting the rules a
novice depends on, so a written procedure describes the beginner's practice more
faithfully than the expert's [@dreyfus1986mind]. Schön locates professional
competence in knowing-in-action and reflection-in-action, which happen inside
the doing rather than in a prior specification [@schon1983reflective]. Sennett
supplies the motivational half — the desire to do a job well for its own sake,
and the slow entanglement of hand and judgment — which no checklist installs
[@sennett2008craftsman].

Collins partitions what Polanyi left whole, splitting tacit knowledge into
*relational* (tellable but untold), *somatic* (embodied), and *collective*
(societally held), and argues only the first can in principle be explicit
[@collins2010tacit]. An evidence label reaches only the relational kind —
and only the portion someone wrote down. A `handoff` label points at a
document, not the somatic skill of analysis or a field's collective
judgment. The registry is therefore a pointer set for the one externalizable
layer of craft, not a compression of it. That is why White Line records what
this instrument leaves out, and why a declared trace must never be read
as the skill that produced it.

## Verification is not validation

The language of checking needs its own boundary. Oreskes, Shrader-Frechette, and
Belitz distinguish the internal assessment of a model or computation from the
much harder question of whether it adequately represents a non-closed world;
they argue that confirmation is necessarily partial and comparative
[@oreskes1994verification]. Black Line uses **verification** in the narrow
engineering sense of checking whether a declared procedure, invariant, or
serialization rule behaves as specified. Its proof-of-detection tests show that a
check can fire on a planted counter-example. They do not validate a research
claim, a model of the world, or a decision made from the result. The distinction
is not a disclaimer added after the method; it is why the evaluator calls its
output a review status rather than a truth verdict.

## Handoffs are situated coordination objects

The concise handoff also has a social-scientific lineage. Suchman's analysis of
plans and situated action warns that an abstract plan does not determine what
people will do in a changing setting [@suchman1987plans]. Star and Griesemer's
account of boundary objects shows how a shared artifact can support cooperation
across social worlds while remaining locally interpretable
[@star1989boundary]. Black Line's handoff is deliberately modest in this sense:
it preserves the decision, evidence trail, current limit, and next action so
another reader can orient themselves, but it does not pretend to transfer the
author's tacit skill or eliminate the need for situated judgment. A handoff is a
coordination surface, not a complete substitute for collaboration.

## Humility is an operational requirement

Jasanoff's call for "technologies of humility" shifts attention from prediction
alone to the unknowns, framing choices, distributional consequences, and
questions that a technical system leaves out [@jasanoff2003humility]. That
orientation sharpens Black Line's limits: a declaration-status instrument should
make its omissions legible, ask who must review what it cannot see, and keep
authority separate from procedural completeness. The `stated-uncertainty`,
`review-before-reliance`, and `concise-handoff` practices are therefore not a
claim to have solved governance; they are small prompts for returning governance
to the people and institutions that hold it.

The literature-to-wire map is therefore deliberately asymmetric:

| Scholarly concern | Black Line operational slice | Boundary preserved |
| --- | --- | --- |
| Falsification and failure visibility | question-first; failure-visible | a declared falsifier is not a successful test |
| Reproducible computation | clean rerun; explicit data origin | same-input rerun is not new-study replication |
| Independent replication | none: the rerun wire stops at the same inputs | a clean rerun predicts nothing about a new sample |
| Open research culture | source traceability; review; negative results | a label is not independent verification |
| Tacit and situated knowledge | concise handoff; explicit limits | the record is not the whole practice |
| Craft and technē | declared traces of externalizable work only | a trace is not the skill that produced it |
| Honest visual communication | evidence matrix; uncertainty notes | clarity does not increase evidential strength |
| Verification versus validation | proof-of-detection tests; clean reruns | a passing check is not world validation |
| Situated coordination | handoff; review note; next action | a plan does not replace local judgment |
| Epistemic humility | uncertainty; limits; review boundary | procedural completeness is not governance |

The table is a design map, not a claim that eleven practices capture these
traditions. Its purpose is to make the borrowing inspectable and the
non-borrowing equally explicit.

## What the lineage does and does not license

Citing these works situates Black Line; it does not borrow their authority. None
of these authors claims that following a practice guarantees a true result, and
neither does this registry. The lineage explains *why* each wire is worth making
visible; the [formal method](#sec:formalism) explains *what the evaluator can
actually check*, which is only whether the declared evidence is present — never
whether the underlying claim is sound.
