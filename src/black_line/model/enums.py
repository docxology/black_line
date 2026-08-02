"""Enumerations for practice outcomes and practice families."""

from __future__ import annotations

from enum import Enum


class PracticeStatus(str, Enum):
    """Outcome for a single practice that applies to a work attempt."""

    ALIGNED = "ALIGNED"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
    NEEDS_REWORK = "NEEDS_REWORK"


class AssessmentStatus(str, Enum):
    """Overall outcome for a work attempt."""

    ALIGNED = "ALIGNED"
    NEEDS_EVIDENCE = "NEEDS_EVIDENCE"
    NEEDS_REWORK = "NEEDS_REWORK"
    OUTSIDE_SCOPE = "OUTSIDE_SCOPE"


class PracticeKind(str, Enum):
    """The family of craft a practice belongs to.

    Families exist so the registry can be reviewed for balance: a registry
    that only rewards framing but never verification has drifted from the
    Black Line's purpose of making strong work inspectable end to end.
    """

    FRAMING = "FRAMING"
    TRACEABILITY = "TRACEABILITY"
    METHOD = "METHOD"
    VERIFICATION = "VERIFICATION"
    COMMUNICATION = "COMMUNICATION"
    STEWARDSHIP = "STEWARDSHIP"
