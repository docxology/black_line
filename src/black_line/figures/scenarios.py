"""Shared scenario fixtures for figures and manuscript binding tests."""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from functools import lru_cache
from random import Random

from black_line import (
    BLACK_PRACTICES,
    AssessmentStatus,
    BlackPractice,
    EvidenceItem,
    PracticeKind,
    WorkAttempt,
    all_invariants,
    evaluate_with_surfaces,
    evaluate_work,
)

#: Review date and age sweep for the decay figure; pinned so the figure is
#: byte-identical across runs and the manuscript can cite exact ages.
DECAY_AS_OF = date(2026, 7, 1)
DECAY_MAX_AGE = 70
DECAY_TAG = "data"
DECAY_PRACTICE = next(p for p in BLACK_PRACTICES if DECAY_TAG in p.tags)
#: Decay grid geometry, hoisted so tests can assert the canvas is wide enough
#: for the full declared age sweep (a fixed 1400px canvas once clipped the
#: age-70 column and its axis tick out of the viewBox).
DECAY_CELL_W = 15
DECAY_GRID_X = 400


def decay_attempt(age_days: int, labels: tuple[str, ...]) -> WorkAttempt:
    noted = (DECAY_AS_OF - timedelta(days=age_days)).isoformat()
    return WorkAttempt(
        "dated provenance declaration for the decay sweep",
        frozenset({DECAY_TAG}),
        dated_evidence=tuple(EvidenceItem(label, noted) for label in labels),
    )


PATH_TAG = "research"
PATH_DESCRIPTION = "literature synthesis on staleness semantics"
PATH_LABELS = (
    "question",
    "scope",
    "source",
    "claim",
    "failure",
    "test",
    "uncertainty",
    "limits",
    "negative_result",
    "log",
    "environment",
    "rerun",
    "next_step",
    "handoff",
    "reviewer",
    "review_note",
)

PATH_PRACTICES = tuple(p for p in BLACK_PRACTICES if PATH_TAG in p.tags)
if sorted(PATH_LABELS) != sorted(
    label for practice in PATH_PRACTICES for label in practice.required_evidence
):  # pragma: no cover
    raise RuntimeError(
        "PATH_LABELS no longer matches the registry's research-tag required labels"
    )


@lru_cache(maxsize=1)
def path_assessments():
    return tuple(
        evaluate_work(
            WorkAttempt(
                PATH_DESCRIPTION, frozenset({PATH_TAG}), frozenset(PATH_LABELS[:step])
            ),
            BLACK_PRACTICES,
        )
        for step in range(len(PATH_LABELS) + 1)
    )


def path_first_aligned() -> int:
    return next(
        step
        for step, assessment in enumerate(path_assessments())
        if assessment.status is AssessmentStatus.ALIGNED
    )


# --- refresh-horizon scenario -----------------------------------------------
#: Review date and window for the refresh-queue figure. Pinned so the figure is
#: byte-identical across runs and the manuscript can cite exact day counts.
HORIZON_AS_OF = date(2026, 7, 1)
HORIZON_WINDOW = 120
HORIZON_TAGS = frozenset({"data", "research"})
#: One dated declaration per class the horizon distinguishes: several required
#: labels at different ages, one label the registry does not require, one
#: undated label, and one label already past the window. The omitted classes are
#: declared here on purpose — the figure names them rather than dropping them.
HORIZON_EVIDENCE = (
    EvidenceItem("data_origin", "2026-03-20"),
    EvidenceItem("transform_log", "2026-06-10"),
    EvidenceItem("question", "2026-05-02"),
    EvidenceItem("scope", "2026-06-24"),
    EvidenceItem("source", "2026-04-11"),
    EvidenceItem("rerun", "2026-02-01"),
    EvidenceItem("handoff", None),
    EvidenceItem("dashboard_link", "2026-06-05"),
)
HORIZON_ATTEMPT = WorkAttempt(
    "quarterly provenance and literature refresh",
    HORIZON_TAGS,
    dated_evidence=HORIZON_EVIDENCE,
)


# --- monotonicity permutation sweep ------------------------------------------
#: Seed and row count for the declaration-order sweep. A fixed seed makes the
#: sampled property reproducible; it does not make it exhaustive.
LATTICE_SEED = 20260727
LATTICE_ROWS = 12


# --- multi-attempt battery ---------------------------------------------------
#: Review date for the batch panel. Pinned like the other scenarios so the
#: figure is byte-identical across runs.
BATCH_AS_OF = date(2026, 7, 1)
BATCH_WINDOW = 30

#: A small battery of work attempts, one per reviewed tag plus three boundary
#: attempts. Every attempt is an ordinary ``WorkAttempt``; the practices each
#: one is scored against, and therefore every status and gap the figure counts,
#: come from the registry rather than from anything declared here. The last
#: entry carries a tag outside the reviewed vocabulary so the ``OUTSIDE_SCOPE``
#: row of the distribution is populated by a real call rather than a zero.
BATCH_ATTEMPTS = (
    WorkAttempt(
        "data pipeline refresh with full provenance",
        frozenset({"data"}),
        frozenset({"data_origin", "transform_log"}),
    ),
    WorkAttempt(
        "writing pass on the handoff section",
        frozenset({"writing"}),
        frozenset({"question", "scope", "source", "claim", "next_step"}),
    ),
    WorkAttempt(
        "engineering change to the freshness partition",
        frozenset({"engineering"}),
        frozenset(
            {
                "method",
                "decision",
                "failure",
                "test",
                "next_step",
                "handoff",
                "environment",
                "rerun",
                "diff",
                "log",
                "reviewer",
                "review_note",
            }
        ),
    ),
    WorkAttempt(
        "analysis of the coverage asymmetry",
        frozenset({"analysis"}),
        frozenset({"question", "scope", "uncertainty", "limits"}),
    ),
    WorkAttempt(
        "literature synthesis on staleness semantics",
        frozenset({"research"}),
        frozenset(PATH_LABELS),
    ),
    WorkAttempt(
        "quarterly provenance re-review with an aged origin note",
        frozenset({"data"}),
        dated_evidence=(
            EvidenceItem("data_origin", "2026-04-01"),
            EvidenceItem("transform_log", "2026-04-01"),
        ),
    ),
    WorkAttempt(
        "cross-tag review of the analysis and engineering surfaces",
        frozenset({"analysis", "engineering"}),
        frozenset({"question", "scope"}),
    ),
    WorkAttempt(
        "studio recording session log",
        frozenset({"music"}),
        frozenset({"log"}),
    ),
)


@lru_cache(maxsize=1)
def batch_assessments() -> tuple:
    """Evaluate the pinned battery through the ordinary public evaluator."""

    return tuple(
        evaluate_work(
            attempt,
            BLACK_PRACTICES,
            as_of=BATCH_AS_OF,
            max_evidence_age_days=BATCH_WINDOW,
        )
        for attempt in BATCH_ATTEMPTS
    )


@lru_cache(maxsize=1)
def lattice_orders() -> tuple[tuple[str, ...], ...]:
    """Return the seeded declaration orders the lattice figure sweeps.

    The registry's own order is row 0 — the order the incremental-path figure
    draws — so the sweep is visibly a superset of that single trace.
    """

    rng = Random(LATTICE_SEED)
    orders = [PATH_LABELS]
    while len(orders) < LATTICE_ROWS:
        shuffled = list(PATH_LABELS)
        rng.shuffle(shuffled)
        orders.append(tuple(shuffled))
    return tuple(orders)


# --- co-present surfaces panel -------------------------------------------------
#: Review date and freshness window for the surfaces panel. Pinned like the
#: other scenarios so the plate is byte-identical across runs.
SURFACES_AS_OF = date(2026, 7, 1)
SURFACES_WINDOW = 30

#: One declaration chosen so the practices it matches carry distinguishable
#: surface shapes under shared status words: full support, support beside
#: resistance, full resistance, support beside a stale gap, and an all-stale
#: gap. Every status and every chip the panel draws comes from one real
#: ``evaluate_with_surfaces`` call over this record — nothing is staged per row.
SURFACES_ATTEMPT = WorkAttempt(
    "co-present support and resistance across one analysis attempt",
    frozenset({"analysis"}),
    frozenset({"question", "scope", "source", "data_origin"}),
    dated_evidence=(
        EvidenceItem("failure", "2026-06-20"),
        EvidenceItem("test", "2026-04-01"),
        EvidenceItem("negative_result", "2026-05-12"),
        EvidenceItem("log", "2026-05-12"),
    ),
)


@lru_cache(maxsize=1)
def surfaces_result():
    """The pinned surfaces evaluation: one assessment plus its typed surfaces."""

    return evaluate_with_surfaces(
        SURFACES_ATTEMPT,
        BLACK_PRACTICES,
        as_of=SURFACES_AS_OF,
        max_evidence_age_days=SURFACES_WINDOW,
    )


# --- intake-normalization battery --------------------------------------------
#: Review date for the intake figure. Pinned like the other scenarios so the
#: plate is byte-identical across runs.
INTAKE_AS_OF = date(2026, 7, 1)
INTAKE_TAGS = frozenset({"data"})
INTAKE_DESCRIPTION = "provenance note for the intake battery"
#: A complete `data` declaration, so every row below differs from the others
#: only in the malformation it carries.
INTAKE_EVIDENCE = frozenset({"data_origin", "transform_log"})

#: One declaration per branch of Stage 1 that the evaluator is written to
#: survive. Every collection here is an ordered tuple rather than a set: the
#: intake notes come back in iteration order, and set iteration depends on
#: string hashing, which would make the drawn plate differ between runs.
#:
#: These are ordinary ``WorkAttempt`` records with deliberately wrong field
#: values — the same records a caller could construct by accident. Nothing is
#: patched, and the notes the figure draws are whatever the real evaluator
#: returns.
INTAKE_CASES: tuple[tuple[str, WorkAttempt], ...] = (
    (
        "description is blank",
        WorkAttempt("   ", INTAKE_TAGS, INTAKE_EVIDENCE),
    ),
    (
        "description is not text",
        WorkAttempt(42, INTAKE_TAGS, INTAKE_EVIDENCE),  # type: ignore[arg-type]
    ),
    (
        "tags declared as one string",
        WorkAttempt(INTAKE_DESCRIPTION, "data", INTAKE_EVIDENCE),  # type: ignore[arg-type]
    ),
    (
        "evidence declared as a number",
        WorkAttempt(INTAKE_DESCRIPTION, INTAKE_TAGS, 7),  # type: ignore[arg-type]
    ),
    (
        "evidence tokens blank and non-text",
        WorkAttempt(
            INTAKE_DESCRIPTION,
            INTAKE_TAGS,
            ("data_origin", "transform_log", "  ", 5),  # type: ignore[arg-type]
        ),
    ),
    (
        "dated record carries no label",
        WorkAttempt(
            INTAKE_DESCRIPTION,
            INTAKE_TAGS,
            INTAKE_EVIDENCE,
            (EvidenceItem("", "2026-06-01"),),
        ),
    ),
    (
        "evidence date is unreadable",
        WorkAttempt(
            INTAKE_DESCRIPTION,
            INTAKE_TAGS,
            frozenset({"transform_log"}),
            (EvidenceItem("data_origin", "last tuesday"),),
        ),
    ),
    (
        "evidence date is in the future",
        WorkAttempt(
            INTAKE_DESCRIPTION,
            INTAKE_TAGS,
            frozenset({"transform_log"}),
            (EvidenceItem("data_origin", "2026-12-01"),),
        ),
    ),
    (
        "dated evidence is one string",
        WorkAttempt(
            INTAKE_DESCRIPTION,
            INTAKE_TAGS,
            INTAKE_EVIDENCE,
            "data_origin",  # type: ignore[arg-type]
        ),
    ),
)


@lru_cache(maxsize=1)
def intake_assessments() -> tuple[tuple[str, object], ...]:
    """Evaluate every malformed declaration through the ordinary evaluator."""

    return tuple(
        (label, evaluate_work(attempt, BLACK_PRACTICES, as_of=INTAKE_AS_OF))
        for label, attempt in INTAKE_CASES
    )


# --- planted-registry detection battery --------------------------------------
def _replace_first(**changes: object) -> tuple[BlackPractice, ...]:
    """The real registry with its first practice mutated in place."""

    return (replace(BLACK_PRACTICES[0], **changes),) + BLACK_PRACTICES[1:]


def _drop_family(kind: PracticeKind) -> tuple[BlackPractice, ...]:
    """The real registry with one whole craft family removed."""

    return tuple(practice for practice in BLACK_PRACTICES if practice.kind is not kind)


#: One planted counter-example per structural check, in battery order. Each
#: entry is ``(target check name, what was planted, the planted registry)``.
#:
#: The plants are chosen to target one check, not to trip exactly one. Two of
#: them cannot help tripping a second: a non-``PracticeKind`` kind and a
#: ``None`` tag field both break canonical serialization, so the digest check
#: fails alongside the intended one. That collateral is drawn rather than
#: designed away, because hiding it would misrepresent what the battery does.
INVARIANT_PLANTS: tuple[tuple[str, str, tuple[BlackPractice, ...]], ...] = (
    (
        "practice_ids_distinct",
        "first practice appended a second time",
        BLACK_PRACTICES + (replace(BLACK_PRACTICES[0]),),
    ),
    (
        "practice_fields_populated",
        "title blanked",
        _replace_first(title="   "),
    ),
    (
        "practice_tags_reachable",
        "tag set emptied",
        _replace_first(tags=frozenset()),
    ),
    (
        "practice_kind_valid",
        "kind replaced by a string",
        _replace_first(kind="FRAMING"),
    ),
    (
        "kind_coverage",
        f"every {PracticeKind.STEWARDSHIP.value} practice removed",
        _drop_family(PracticeKind.STEWARDSHIP),
    ),
    (
        "evidence_labels_matchable",
        "required label given a capital letter",
        _replace_first(
            required_evidence=(BLACK_PRACTICES[0].required_evidence[0].capitalize(),)
            + BLACK_PRACTICES[0].required_evidence[1:]
        ),
    ),
    (
        "registry_digest_computable",
        "tag field set to None",
        _replace_first(tags=None),
    ),
)


@lru_cache(maxsize=1)
def detection_rows() -> tuple[tuple[str, str, tuple[tuple[str, bool], ...]], ...]:
    """Run the real battery on the real registry and on every planted registry.

    Returns one row per registry as ``(row label, what was planted, results)``,
    where ``results`` is ``(check name, passed)`` in battery order. Row 0 is the
    unmutated registry, so the plate carries its own positive control.
    """

    rows = [
        (
            "the shipped registry",
            "nothing planted",
            tuple(
                (check.name, check.passed) for check in all_invariants(BLACK_PRACTICES)
            ),
        )
    ]
    for target, planted, practices in INVARIANT_PLANTS:
        rows.append(
            (
                target,
                planted,
                tuple(
                    (check.name, check.passed) for check in all_invariants(practices)
                ),
            )
        )
    return tuple(rows)


def detection_check_names() -> tuple[str, ...]:
    """The battery's check names, in the order ``all_invariants`` returns them."""

    return tuple(check.name for check in all_invariants(BLACK_PRACTICES))
