"""Typed figure registry for Black Line manuscript figures."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from black_line import (
    BLACK_PRACTICES,
    PRACTICE_TAG_VOCABULARY,
    AssessmentStatus,
    PracticeKind,
    PracticeStatus,
    coverage_matrix,
)
from black_line.figures.batch_figures import (
    batch_gap_counts,
    batch_never_gapped,
    batch_summary,
    batch_summary_svg,
)
from black_line.figures.cover import cover_art_svg
from black_line.figures.analytics_figures import (
    coverage_heatmap_svg,
    evidence_decay_svg,
    incremental_path_svg,
)
from black_line.figures.horizon_figures import (
    horizon_omissions,
    horizon_rows,
    lattice_paths,
    monotonicity_lattice_svg,
    refresh_queue_svg,
)
from black_line.figures.intake_figures import (
    intake_blocked,
    intake_note_total,
    intake_notes_svg,
    intake_rows,
    intake_scored,
    intake_unmatched,
)
from black_line.figures.invariant_figures import (
    detection_collateral,
    detection_targets_all_fire,
    invariant_detection_svg,
)
from black_line.figures.scenarios import (
    BATCH_AS_OF,
    BATCH_WINDOW,
    DECAY_AS_OF,
    DECAY_PRACTICE,
    HORIZON_AS_OF,
    HORIZON_WINDOW,
    INTAKE_AS_OF,
    LATTICE_SEED,
    PATH_LABELS,
    PATH_TAG,
    PATH_PRACTICES,
    SURFACES_AS_OF,
    SURFACES_WINDOW,
    detection_check_names,
    detection_rows,
    path_assessments,
    path_first_aligned,
)
from black_line.figures.surface_figures import (
    surfaces_label_totals,
    surfaces_overall,
    surfaces_panel_svg,
    surfaces_rows,
    surfaces_shape_counts,
)
from black_line.figures.protocol_schematics import (
    claim_layers_svg,
    operating_loop_svg,
    status_path_svg,
)
from black_line.figures.registry_schematics import (
    evidence_matrix_svg,
    family_taxonomy_svg,
    practice_wires_svg,
)

_COVERAGE_ROWS = coverage_matrix(BLACK_PRACTICES)
_COVERAGE_MAX = max(_COVERAGE_ROWS, key=lambda row: row.practice_count)
_COVERAGE_MIN = min(_COVERAGE_ROWS, key=lambda row: row.practice_count)
_PATH_ASSESSMENTS = path_assessments()
_PATH_FIRST_ALIGNED = path_first_aligned()
_HORIZON_ROWS = horizon_rows()
_HORIZON_OMITTED = horizon_omissions()
_LATTICE = lattice_paths()
_LATTICE_MONOTONE = sum(1 for _, _, monotone, _ in _LATTICE if monotone)
_LATTICE_INVERSIONS = sum(inversions for _, _, _, inversions in _LATTICE)
_LATTICE_STEPS = len(_LATTICE[0][1])
_BATCH = batch_summary()
_BATCH_GAPS = batch_gap_counts()
_BATCH_NEVER = batch_never_gapped()
_BATCH_STATUSES_SEEN = sum(1 for _value, count in _BATCH.status_counts if count)
#: Ties are real here (two practices share the top gap count), so the caption
#: names every practice at the maximum rather than picking one silently.
_BATCH_TOP_COUNT = _BATCH_GAPS[0][1]
_BATCH_TOP_IDS = tuple(
    practice_id for practice_id, count in _BATCH_GAPS if count == _BATCH_TOP_COUNT
)
_BATCH_TOP_FAMILY_COUNT = max(count for _name, count in _BATCH.open_finding_kind_counts)
_BATCH_TOP_FAMILIES = tuple(
    name
    for name, count in _BATCH.open_finding_kind_counts
    if count == _BATCH_TOP_FAMILY_COUNT
)
_INTAKE_ROWS = intake_rows()
_INTAKE_BLOCKED = intake_blocked()
_INTAKE_UNMATCHED = intake_unmatched()
_INTAKE_SCORED = intake_scored()
_INTAKE_NOTES = intake_note_total()
#: Statuses the intake battery actually reaches, in enum order, so the caption
#: names the executed outcome set instead of a remembered one.
_INTAKE_STATUSES = tuple(
    status.value
    for status in AssessmentStatus
    if status.value in {row[1] for row in _INTAKE_ROWS}
)
_DETECTION_CHECKS = detection_check_names()
_DETECTION_ROWS = detection_rows()
_DETECTION_COLLATERAL = detection_collateral()
#: Say "every plant fires" only while every plant does. If one stops firing the
#: caption reports the shortfall instead of repeating a claim the plate refutes.
_DETECTION_FIRING_CLAUSE = (
    "Every plant fails the check it targets, boxed in its row"
    if detection_targets_all_fire()
    else (
        "At least one plant no longer fails the check it targets, which the "
        "boxed cells in each row show directly"
    )
)
#: The collateral failures, named from the executed battery rather than
#: explained from memory: a planted value can break more than one property.
_DETECTION_COLLATERAL_CLAUSE = "; ".join(
    f"the {target} plant also fails " + " and ".join(others)
    for target, others in _DETECTION_COLLATERAL
)
#: The batch battery currently reaches every status; say so plainly when it does
#: and report the shortfall when it does not, rather than printing "4 of the 4".
_STATUS_COVERAGE_CLAUSE = (
    "Every assessment status the enum defines occurs in the batch"
    if _BATCH_STATUSES_SEEN == len(_BATCH.status_counts)
    else (
        f"{_BATCH_STATUSES_SEEN} of the {len(_BATCH.status_counts)} assessment "
        "statuses occur in the batch"
    )
)
_SURFACE_ROWS = surfaces_rows()
_SURFACE_PRESENT, _SURFACE_MISSING, _SURFACE_STALE = surfaces_label_totals()
_SURFACE_OVERALL = surfaces_overall()
_SURFACE_SHAPES = surfaces_shape_counts()
#: The compression the panel exists to show, named from the executed shapes:
#: which status words cover more than one distinguishable surface shape. If
#: the scenario stopped compressing, the caption reports that instead of
#: repeating a claim the plate refutes.
_SURFACE_COMPRESSED = tuple(
    (status, count) for status, count in _SURFACE_SHAPES if count > 1
)
_SURFACE_COMPRESSION_CLAUSE = (
    "One status word covers distinguishable surface shapes: "
    + " and ".join(
        f"{status} is projected from {count} distinct present/missing/stale shapes"
        for status, count in _SURFACE_COMPRESSED
    )
    if _SURFACE_COMPRESSED
    else "In this battery every projected status word covers a single surface shape"
)


@dataclass(frozen=True, slots=True)
class FigureSpec:
    """One deterministic figure contract."""

    name: str
    label: str
    builder: Callable[[], str]
    caption: str
    alt: str
    interpretive_claim: str
    epistemic_boundary: str


FIGURE_SPECS: tuple[FigureSpec, ...] = (
    FigureSpec(
        "black_operating_loop",
        "fig:black-operating-loop",
        operating_loop_svg,
        "The smallest honest operating loop: frame the decision, declare pointers to inspectable artifacts, evaluate with a pinned date and registry digest, repair or refresh gaps, and archive the trail. The dark panel makes explicit what remains outside the instrument's authority.",
        "A five-step Black Line loop from frame to declare to evaluate to repair or refresh to archive, with pinned record fields and an explicit boundary around semantic truth, source authenticity, and safety permission.",
        "The protocol is a review loop whose next action is determined by declaration gaps or stale observations.",
        "The loop does not verify semantic truth, source authenticity, safety, or permission.",
    ),
    FigureSpec(
        "black_practice_wires",
        "fig:black-practice-wires",
        practice_wires_svg,
        f"The {len(BLACK_PRACTICES)} practices drawn as cards in registry declaration order, color-keyed to the {len(PracticeKind)} practice families. The order interleaves families and ends at '{BLACK_PRACTICES[-1].id}': it is a declaration order, not a workflow. Each card names a review surface and its required labels; the figure is not a quality or truth score and does not grant permission to cross Red Line.",
        f"{len(BLACK_PRACTICES)} Black Line practice cards in registry declaration order, color-keyed to {len(PracticeKind)} practice families, each pairing a review surface with its required evidence.",
        "The registry organizes recurring work habits into color-keyed practice families with a stable, inspectable declaration order.",
        "The map does not establish that any practice was performed well or that the work is true.",
    ),
    FigureSpec(
        "black_status_path",
        "fig:black-status-path",
        status_path_svg,
        "The staged evaluation path. Intake normalization can block on a blank description, and a malformed practice registry fails closed as NEEDS_REWORK before any scoring; otherwise practices are matched by tag intersection, each applicable practice is scored ALIGNED, NEEDS_EVIDENCE, or NEEDS_REWORK, and the overall status takes the most demanding per-practice status, or OUTSIDE_SCOPE when no practice applies. The diagram is derived from the evaluator rules and status enums; a status reports declaration coverage and freshness, not verified evidence or authorization.",
        f"A flow diagram of evaluate_work: intake, freshness, tag matching, scoring, aggregation, with fail-closed branches for blank descriptions and malformed registries, plus the {len(PracticeStatus)} practice statuses and {len(AssessmentStatus)} assessment statuses.",
        "Fixed inputs produce a deterministic declaration status through normalization, matching, and aggregation.",
        "A status reports declaration coverage and freshness; it does not verify the underlying evidence or authorize action.",
    ),
    FigureSpec(
        "black_claim_layers",
        "fig:black-claim-layers",
        claim_layers_svg,
        "The six-practice-family boundary map separates the decision, procedure, and record that Black Line can structure from world adequacy and authority that require domain, independent, or governance review. ALIGNED means fresh declaration coverage for applicable practices, not truth or permission.",
        "Five horizontal layers: decision, procedure, record, world, and authority. A red boundary marks where Black Line stops; a lower panel defines ALIGNED as fresh declaration coverage rather than truth or permission.",
        "The instrument has a deliberate epistemic boundary: it structures a review surface without collapsing that surface into world validation or authority.",
        "World adequacy, source authenticity, inferential soundness, safety, legality, and permission remain outside the evaluator.",
    ),
    FigureSpec(
        "black_family_taxonomy",
        "fig:black-family-taxonomy",
        family_taxonomy_svg,
        f"The {len(BLACK_PRACTICES)} practices grouped by {len(PracticeKind)} practice families, with the reviewed {len(PRACTICE_TAG_VOCABULARY)}-tag vocabulary that makes each practice applicable to a work attempt. Family coverage and tag membership are enforced by structural invariants; the taxonomy maps reachability, not evidence quality.",
        f"A taxonomy grouping the {len(BLACK_PRACTICES)} practices into {len(PracticeKind)} practice families, listing each practice's tags and required evidence, with the {len(PRACTICE_TAG_VOCABULARY)}-tag vocabulary shown at the top.",
        "The registry's family and tag structure makes applicability and coverage reviewable.",
        "Family membership and tag reachability do not show that a practice was completed or that its evidence is sound.",
    ),
    FigureSpec(
        "black_evidence_matrix",
        "fig:black-evidence-matrix",
        evidence_matrix_svg,
        "The registry's evidence-label contract: each practice names labels a reviewer can look for, while the instrument explicitly does not treat a declaration as independent verification of a source, test, or claim.",
        "A matrix listing all Black Line practices with their practice families, reviewed tags, and required evidence labels; a boundary note states that labels are declarations rather than verified truth.",
        "The matrix exposes the exact labels required for each applicable practice.",
        "A matched label is a declaration pointer, not an inspected source, passing test, or true claim.",
    ),
    FigureSpec(
        "black_coverage_heatmap",
        "fig:black-coverage-heatmap",
        coverage_heatmap_svg,
        f"The tag-practice coverage matrix derived from the registry: filled cells mark applicability, cell numbers give each practice's required-label count, and the margin totals each tag's reach and declaration burden. The burden is asymmetric — '{_COVERAGE_MAX.tag}' reaches {_COVERAGE_MAX.practice_count} practices ({_COVERAGE_MAX.required_label_count} required labels) while '{_COVERAGE_MIN.tag}' reaches {_COVERAGE_MIN.practice_count} ({_COVERAGE_MIN.required_label_count} labels) — so a narrow tag set buys a cheaper ALIGNED. The matrix maps applicability, not evidence quality, safety, or permission.",
        f"A {len(_COVERAGE_ROWS)} by {len(BLACK_PRACTICES)} heatmap of tags against practices with filled cells marking applicability, per-tag practice reach and required-label totals in the margin, and a note on the coverage asymmetry between the widest and narrowest tags.",
        "Tag choice sets the declaration burden a work attempt is scored against, and the asymmetry is derived from the registry itself.",
        "Applicability and burden say nothing about whether declared evidence exists, is adequate, or authorizes anything; a cheap ALIGNED via narrow tags is a coverage fact reviewers must read alongside the status.",
    ),
    FigureSpec(
        "black_incremental_path",
        "fig:black-incremental-path",
        incremental_path_svg,
        f"The executed incremental-declaration path as a status grid: the '{PATH_TAG}'-tagged attempt selects {len(PATH_PRACTICES)} practices ({len(PATH_LABELS)} required labels), and every cell is one real evaluate_work call as labels accumulate one per step from an empty declaration (step 0, {_PATH_ASSESSMENTS[0].status.value}) to full coverage (step {len(PATH_LABELS)}). Per-practice findings flip to ALIGNED as each practice's labels complete, while the overall status — the most demanding per-practice status — stays NEEDS_REWORK from step 1 through step {_PATH_FIRST_ALIGNED - 1} and first reaches ALIGNED at step {_PATH_FIRST_ALIGNED}: conditional fresh-evidence monotonicity made visible. An ALIGNED cell records declared labels only; it does not show any source is real, any test passed, or any claim is true.",
        f"A {len(PATH_PRACTICES)}-practice by {len(_PATH_ASSESSMENTS)}-step status grid plus an overall row: per-practice cells turn ALIGNED as labels accumulate, the overall row stays NEEDS_REWORK until every label is declared, and the empty first column is NEEDS_EVIDENCE.",
        "Intermediate progress is visible in per-practice findings while the overall status, as the most demanding finding, moves only when the last applicable practice completes.",
        "Each cell reports declaration coverage from a real evaluator call; accumulated ALIGNED findings do not verify sources, tests, or claims, and grant no permission.",
    ),
    FigureSpec(
        "black_evidence_decay",
        "fig:black-evidence-decay",
        evidence_decay_svg,
        f"Evidence decay from executed evaluate_work sweeps over the '{DECAY_PRACTICE.id}' practice with review date {DECAY_AS_OF.isoformat()}: a full declaration stays ALIGNED while its evidence age is at most the freshness window and flips to NEEDS_EVIDENCE (a refresh request) exactly one day past it — the threshold is a strict inequality — while a declaration that never included one required label is NEEDS_REWORK at every age, and a declaration with no window never goes stale. A fresh date is a declaration property; it does not show the underlying observation was ever adequate or still holds.",
        "Four status strips over evidence ages 0 to 70 days: full declarations under 30-day and 51-day windows flip from ALIGNED to NEEDS_EVIDENCE one day past the window, a full declaration with no window stays ALIGNED, and a partial declaration stays NEEDS_REWORK throughout.",
        "Staleness is a strict day-count comparison that separates refresh requests from missing work, and every cell in the figure is the output of a real evaluator call.",
        "A fresh declaration date does not show that the underlying observation was ever adequate or still holds; decay tracks the declaration, not the world.",
    ),
    FigureSpec(
        "black_refresh_queue",
        "fig:black-refresh-queue",
        refresh_queue_svg,
        f"The refresh queue for one declaration, drawn from `refresh_horizon` in its own ascending nearest-to-stale order: at review date {HORIZON_AS_OF.isoformat()} under a {HORIZON_WINDOW}-day window, {len(_HORIZON_ROWS)} dated labels are scheduled, from '{_HORIZON_ROWS[0].label}' at {_HORIZON_ROWS[0].days_until_stale} days to '{_HORIZON_ROWS[-1].label}' at {_HORIZON_ROWS[-1].days_until_stale}, each naming the practice that requires it. The named band below records the {len(_HORIZON_OMITTED)} declarations the queue omits and why — one of them undated, which is itself one of the omitted classes — so the omission rule is visible rather than implicit. Bar length is days until a declared date crosses the window; it is not a measure of how much the underlying observation matters or how good it was.",
        f"A horizontal bar chart of {len(_HORIZON_ROWS)} dated evidence labels sorted from nearest to furthest from the {HORIZON_WINDOW}-day freshness boundary, each row naming the label, the practice requiring it, the days remaining and the noted date, above a named band listing {len(_HORIZON_OMITTED)} omitted declarations with their reasons.",
        "Freshness windows give a declaration a schedule, and the schedule is derived from the registry: only labels some practice requires can appear in it.",
        "The queue orders declared dates. It does not show that any observation was made, that it was adequate, or that re-dating the label re-establishes anything.",
    ),
    FigureSpec(
        "black_monotonicity_lattice",
        "fig:black-monotonicity-lattice",
        monotonicity_lattice_svg,
        f"Conditional fresh-evidence monotonicity executed as a sweep rather than a single trace: {len(_LATTICE)} seeded orders (seed {LATTICE_SEED}) of the same {len(PATH_LABELS)} labels, each evaluated at all {_LATTICE_STEPS} steps through the real evaluator, for {len(_LATTICE) * _LATTICE_STEPS} calls. Every row is monotone from step 1 onward ({_LATTICE_MONOTONE} of {len(_LATTICE)}), and all {_LATTICE_INVERSIONS} rank decreases in the sweep are the step 0 to step 1 empty-declaration boundary. The overall status path is identical across every sampled order, which is a property of taking the most demanding per-practice status, not evidence that order is irrelevant to a reviewer. The sample is seeded and finite; it is not a proof over all {len(PATH_LABELS)}! orders.",
        f"A {len(_LATTICE)} by {_LATTICE_STEPS} grid of assessment statuses, one row per seeded declaration order and one column per step, each cell carrying a status letter as well as a fill, with a per-row monotonicity mark and a footer counting rank decreases and how many are the empty-declaration boundary.",
        "The conditional monotonicity of the declaration path survives reordering the labels, and the count of rank decreases is executed rather than asserted.",
        "A seeded sample of orders is not a proof over all of them, and status ordering says nothing about whether a declared label points at anything.",
    ),
    FigureSpec(
        "black_batch_summary",
        "fig:black-batch-summary",
        batch_summary_svg,
        f"The registry's demands across a batch rather than one attempt: {_BATCH.total} pinned work attempts spanning the {len(PRACTICE_TAG_VOCABULARY)}-tag vocabulary and one tag outside it, each evaluated at review date {BATCH_AS_OF.isoformat()} under a {BATCH_WINDOW}-day window. {_STATUS_COVERAGE_CLAUSE} ({', '.join(f'{value} {count}' for value, count in _BATCH.status_counts)}), open findings concentrate in {' and '.join(_BATCH_TOP_FAMILIES)} ({_BATCH_TOP_FAMILY_COUNT}), and {len(_BATCH_GAPS)} of the {len(BLACK_PRACTICES)} practices are left open at least once, led by {' and '.join(_BATCH_TOP_IDS)} at {_BATCH_TOP_COUNT}. A gap frequency is a declaration statistic over this battery; it is not a ranking of the practices by importance, and a frequently-open wire is one these declarers did not declare, not one that failed.",
        f"A two-column panel: on the left the {len(_BATCH.status_counts)} overall statuses with their counts across {_BATCH.total} evaluated attempts and a breakdown of open findings by craft family; on the right {len(_BATCH_GAPS)} practices ranked by how often the batch left them open, above a band naming the practices the batch never left open ({len(_BATCH_NEVER)} of {len(BLACK_PRACTICES)}).",
        "Which wires stay open is a property of the registry's demands on differently-tagged work, visible only across a batch.",
        "Counting gaps says nothing about whether any declared label points at a real artifact, and it does not rank practices by importance.",
    ),
    FigureSpec(
        "black_intake_notes",
        "fig:black-intake-notes",
        intake_notes_svg,
        f"Stage 1 executed over {len(_INTAKE_ROWS)} deliberately malformed declarations at review date {INTAKE_AS_OF.isoformat()}: each is one real evaluate_work call, together they return {_INTAKE_NOTES} intake notes, and none raises. {len(_INTAKE_BLOCKED)} block scoring outright ({' and '.join(_INTAKE_BLOCKED)}) and {len(_INTAKE_UNMATCHED)} reaches no practice once its dropped tag declaration leaves nothing to match, while the other {len(_INTAKE_SCORED)} are scored normally; across the battery the outcomes are {', '.join(_INTAKE_STATUSES)}. Surviving malformed input is a robustness property of the intake stage, not tolerance of a bad declaration, and a note asks the declarer to fix something rather than verifying anything declared correctly.",
        f"A table of {len(_INTAKE_ROWS)} malformed work attempts with, for each, the returned assessment status, the number of practice findings, and every intake note returned; {len(_INTAKE_BLOCKED) + len(_INTAKE_UNMATCHED)} rows carry no findings and the rest are scored after the unusable part is dropped.",
        "Malformed declarations are normalized into a status plus named review notes rather than into an exception, and which part was dropped stays visible to the declarer.",
        "Returning a status for unusable input is not acceptance of it; an intake note reports what was ignored and verifies nothing that was declared correctly.",
    ),
    FigureSpec(
        "black_invariant_detection",
        "fig:black-invariant-detection",
        invariant_detection_svg,
        f"The {len(_DETECTION_CHECKS)}-check structural battery run over {len(_DETECTION_ROWS)} registries: the shipped registry, which passes every check, and {len(_DETECTION_ROWS) - 1} registries each carrying one planted defect. {_DETECTION_FIRING_CLAUSE}, which is what makes the battery a proof of detection rather than a record of greenness. {len(_DETECTION_COLLATERAL)} plants also fail a check they were not aimed at — {_DETECTION_COLLATERAL_CLAUSE} — because a single planted value can break more than one structural property at once; those cells are drawn rather than designed away. A firing check shows the battery can reject a malformed registry, not that the practices are the right ones, that their evidence is adequate, or that any work was done well.",
        f"A matrix of {len(_DETECTION_ROWS)} registries against {len(_DETECTION_CHECKS)} checks, every cell carrying a letter as well as a colour. The top row is the shipped registry and passes every check; each remaining row is a registry with one planted defect whose targeted check is boxed and failing, and {len(_DETECTION_COLLATERAL)} of those rows fail a further check as well.",
        "Each structural check is shown rejecting a registry built to break it, so the battery is evidence that it can fail rather than only that it currently passes.",
        "Detection is a property of the checks over registry shape; it establishes nothing about the merit of the practices, the adequacy of declared evidence, or any authorization.",
    ),
    FigureSpec(
        "black_surfaces_panel",
        "fig:black-surfaces-panel",
        surfaces_panel_svg,
        f"One declaration's typed evidence surfaces beside the statuses projected from them: a single evaluate_with_surfaces call at review date {SURFACES_AS_OF.isoformat()} under a {SURFACES_WINDOW}-day window matches {len(_SURFACE_ROWS)} practices, whose {_SURFACE_PRESENT + _SURFACE_MISSING} required labels split into {_SURFACE_PRESENT} present (filled), {_SURFACE_MISSING} missing (hollow), and {_SURFACE_STALE} of the missing merely stale (amber refresh marks). {_SURFACE_COMPRESSION_CLAUSE}, while the single overall word for the whole attempt is {_SURFACE_OVERALL}. The surfaces keep what the projection compresses — strong support and strong resistance co-present on one practice are not the same as no evidence — and, like the statuses, they describe declaration coverage only: a present label is a declaration, never verified evidence, and no surface shape grants permission.",
        f"A panel of {len(_SURFACE_ROWS)} practice rows from one executed evaluate_with_surfaces call: each row draws the practice's required labels in declared order as filled present chips, hollow missing chips, or amber dashed stale chips beside its projected status, above an overall band naming {_SURFACE_OVERALL} for the whole attempt and a footer counting the distinct surface shapes behind each status word.",
        "A status word is a projection over typed co-present surfaces, and distinguishable surface shapes can share one projected word; the surfaces keep what the projection compresses.",
        "Present, missing, and stale are declaration-coverage surfaces at a pinned review date; a present label verifies nothing about the world and no surface shape authorizes anything.",
    ),
)


#: The cover is not a manuscript figure — it is the title-page plate named by
#: `paper.cover.image`. It carries the same contract as any other registered
#: visual, and is embedded with its caption so the description reaches a reader
#: instead of only the registry.
COVER_SPEC = FigureSpec(
    "cover_art",
    "fig:black-cover-art",
    cover_art_svg,
    "Cover art showing unresolved intention narrowing into a followable review line through method, evidence, review, and handoff.",
    "A dense field of charcoal marks narrows into a black line through five stations labelled frame, method, evidence, review, and handoff, with purple, teal, sienna, and a red boundary.",
    "A followable method narrows ambiguity by making transitions inspectable and handing the trail to another reader.",
    "The metaphor is not evidence that the work is true, safe, or authorized.",
)
