"""The versioned Black Line practice registry.

Every entry names one positive practice, the tags that make it applicable,
and the evidence labels a collaborator could inspect. The registry is a
method instrument: it describes how to do strong work and never grants
permission for anything.
"""

from __future__ import annotations

from .model import BlackPractice, PracticeKind

#: The reviewed tag vocabulary. Practice tags outside this set are
#: unreviewable drift; the invariants battery enforces membership.
PRACTICE_TAG_VOCABULARY: frozenset[str] = frozenset(
    {"analysis", "data", "engineering", "research", "writing"}
)


BLACK_PRACTICES: tuple[BlackPractice, ...] = (
    BlackPractice(
        "question-first",
        "State the question before the method",
        "Name the decision, object, and boundary before choosing tools.",
        frozenset({"research", "analysis", "writing"}),
        ("question", "scope"),
        PracticeKind.FRAMING,
    ),
    BlackPractice(
        "source-traceable",
        "Make substantive claims traceable",
        "Point each substantive claim to a source, local observation, or explicit hypothesis label.",
        frozenset({"research", "analysis", "writing"}),
        ("source", "claim"),
        PracticeKind.TRACEABILITY,
    ),
    BlackPractice(
        "smallest-sufficient-method",
        "Use the smallest method that can answer the question",
        "Do not add machinery whose output cannot change the decision.",
        frozenset({"engineering", "analysis"}),
        ("method", "decision"),
        PracticeKind.METHOD,
    ),
    BlackPractice(
        "failure-visible",
        "Make failure conditions explicit",
        "Record what would falsify, break, or materially weaken the result.",
        frozenset({"engineering", "research", "analysis"}),
        ("failure", "test"),
        PracticeKind.VERIFICATION,
    ),
    BlackPractice(
        "concise-handoff",
        "Leave a handoff another person can continue",
        "A collaborator should recover the purpose, next action, and evidence without private context.",
        frozenset({"engineering", "writing", "research"}),
        ("next_step", "handoff"),
        PracticeKind.COMMUNICATION,
    ),
    BlackPractice(
        "reproducible-from-clean",
        "Rerun the result from a clean environment",
        "Treat a result that appears only in one warm environment as provisional until rerun.",
        frozenset({"engineering", "research"}),
        ("environment", "rerun"),
        PracticeKind.VERIFICATION,
    ),
    BlackPractice(
        "versioned-increments",
        "Keep changes small and reviewable",
        "Record each increment so its history can be read, reverted, and reviewed.",
        frozenset({"engineering", "writing"}),
        ("commit", "diff"),
        PracticeKind.STEWARDSHIP,
    ),
    BlackPractice(
        "stated-uncertainty",
        "State uncertainty and limits with results",
        "A number without its uncertainty and boundary conditions can overstate what is known.",
        frozenset({"research", "analysis"}),
        ("uncertainty", "limits"),
        PracticeKind.TRACEABILITY,
    ),
    BlackPractice(
        "negative-results-kept",
        "Record null and negative results",
        "A documented non-result can narrow the hypothesis space and guide the next attempt.",
        frozenset({"research", "analysis"}),
        ("negative_result", "log"),
        PracticeKind.VERIFICATION,
    ),
    BlackPractice(
        "review-before-reliance",
        "Invite review before relying on a result",
        "A second reader can expose omissions the author no longer sees.",
        frozenset({"engineering", "research", "writing"}),
        ("reviewer", "review_note"),
        PracticeKind.COMMUNICATION,
    ),
    BlackPractice(
        "data-provenance",
        "Keep data origin and transformations explicit",
        "State where each dataset came from and which transformations produced the analyzed form.",
        frozenset({"data", "analysis"}),
        ("data_origin", "transform_log"),
        PracticeKind.TRACEABILITY,
    ),
)


def registry_ids() -> tuple[str, ...]:
    """Return registry ids in declaration order."""

    return tuple(practice.id for practice in BLACK_PRACTICES)
