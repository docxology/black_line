# Introduction

Red Line answers what a practitioner must refuse. Black Line asks a different
question: when a project is allowed to proceed, what makes its reasoning clear
enough for another person to inspect and continue?

The answer is not maximal process. A strong method makes its question, evidence,
failure modes, and next action visible with as little machinery as the decision
allows — a positive discipline that gives work a constructive shape without
pretending a checklist can guarantee truth. Black Line resists the belief that
adding process is the same as adding rigor: more apparatus can hide a weak
question as easily as a strong one. The discipline is to expose the load-bearing
parts of the work, not to bury them.

Black Line uses the word *wire* for a bounded practice that carries work from
intention to inspectable evidence. A wire can be tested, repaired, or cut. It is
not a moral score, and a work can satisfy Black Line while still violating Red
Line. Each wire names a coarse review surface a collaborator could inspect — a
declared source, a rerun from a clean environment, a recorded null result — so
that review begins with visible declarations rather than assumed diligence.

Three commitments organize the rest of the paper. First, I do not present the
practices as personal taste: the
[intellectual-lineage section](#sec:scholarship) situates each one against
scholarship on falsification, scientific norms, literate programming, craft
knowledge, situated action, and reproducible computation, and says where the
borrowing stops. Second, the instrument states its own reach: the
[formal method section](#sec:formalism) gives the exact decision rules the
evaluator applies, each bound to a test that can fail, and the
[limits](#sec:limits) section executes the attacks that gaming it would use.
Third, the boundary is firm — Black Line describes how to work well and never
grants permission to cross Red Line. The four-line relationship is mapped in the
companion `line_set` work,
[github.com/docxology/line_set](https://github.com/docxology/line_set), and
restated for this paper in the next section.

The paper states the method; the package makes the same declarations and
boundaries repeatable, so a reader can run what the prose describes.

The rest of this paper is organised as follows. [Section @sec:method](#sec:method) defines the method and its evidence wires. [Section @sec:formalism](#sec:formalism) states the evaluator formally as definitions and propositions. The worked examples in [Section @sec:examples](#sec:examples) demonstrate the instrument over real declarations, and [Section @sec:limits](#sec:limits) names the epistemic boundaries that the instrument cannot cross.
