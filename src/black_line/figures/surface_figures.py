"""The surfaces panel: one status word over distinguishable surface shapes.

Every status figure in this project draws the projection — the word the
evaluator selects for action. This one draws the state the word projects
from: each matched practice's typed :class:`~black_line.EvidenceSurfaces`,
with present labels filled, missing labels hollow, and merely-stale labels in
a distinct refresh marking, beside the per-practice status and the single
overall word. The point the plate makes is the review's point: strong support
and strong resistance co-present on one practice are not the same as no
evidence, and one projected word can cover several distinguishable shapes.

Nothing here is restated. Every chip, status, and count is read off one real
:func:`~black_line.evaluate_with_surfaces` call over the shipped registry at
a pinned review date and freshness window.
"""

from __future__ import annotations

from black_line import (
    BLACK_PRACTICES,
    PracticeStatus,
    WorkAttempt,
    evaluate_with_surfaces,
)
from black_line.figures.scenarios import (
    SURFACES_AS_OF,
    SURFACES_WINDOW,
    surfaces_result,
)
from black_line.figures.svg import (
    AMBER,
    BLACK,
    BODY_FONT,
    GRID,
    INK,
    MUTED,
    PALE,
    PANEL,
    PAPER,
    RED,
    STATUS_FILL,
    STATUS_GLYPH,
    TEAL,
    WHITE,
    canvas_writers,
    esc,
)

WIDTH = 1400
#: The refresh marking for a stale chip: an amber fill under a dashed outline,
#: so the state stays distinguishable from present (solid fill) and missing
#: (hollow) even in greyscale print.
STALE_FILL = AMBER


def _result(attempt: WorkAttempt | None):
    """Evaluate an override attempt, or return the pinned scenario result.

    The override is what lets a test prove this plate follows its data: a
    panel that agreed with the pinned scenario by coincidence would survive
    every assertion about the pinned scenario alone. Overrides run through
    the same public call at the same pinned review date and window.
    """

    if attempt is None:
        return surfaces_result()
    return evaluate_with_surfaces(
        attempt,
        BLACK_PRACTICES,
        as_of=SURFACES_AS_OF,
        max_evidence_age_days=SURFACES_WINDOW,
    )


def surfaces_rows(
    attempt: WorkAttempt | None = None,
) -> tuple[tuple[str, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]], ...]:
    """One row per matched practice: id, projected status, and its surfaces."""

    assessment, surfaces = _result(attempt)
    return tuple(
        (
            surface.practice_id,
            finding.status.value,
            surface.present,
            surface.missing,
            surface.stale,
        )
        for finding, surface in zip(assessment.findings, surfaces)
    )


def surfaces_overall(attempt: WorkAttempt | None = None) -> str:
    """The single overall status word projected for the whole attempt."""

    assessment, _surfaces = _result(attempt)
    return assessment.status.value


def surfaces_label_totals(attempt: WorkAttempt | None = None) -> tuple[int, int, int]:
    """Total present, missing, and stale labels across every matched practice."""

    rows = surfaces_rows(attempt)
    return (
        sum(len(present) for _id, _status, present, _missing, _stale in rows),
        sum(len(missing) for _id, _status, _present, missing, _stale in rows),
        sum(len(stale) for _id, _status, _present, _missing, stale in rows),
    )


def surfaces_shape_counts(
    attempt: WorkAttempt | None = None,
) -> tuple[tuple[str, int], ...]:
    """Distinct (present, missing, stale) count shapes behind each status word.

    Returned in ``PracticeStatus`` enum order, only for statuses the battery
    reaches. A count above one is the plate's whole point: several
    distinguishable surface shapes sharing one projected word.
    """

    rows = surfaces_rows(attempt)
    counts: list[tuple[str, int]] = []
    for status in PracticeStatus:
        shapes = {
            (len(present), len(missing), len(stale))
            for _id, value, present, missing, stale in rows
            if value == status.value
        }
        if shapes:
            counts.append((status.value, len(shapes)))
    return tuple(counts)


def _chip(
    x: float,
    y: float,
    label: str,
    state: str,
    size: int,
) -> tuple[str, float]:
    """Draw one evidence-label chip; return the markup and its width."""

    width = 26 + int(9.2 * len(label))
    height = 32
    if state == "present":
        fill, stroke, tfill, dash = TEAL, TEAL, WHITE, ""
    elif state == "stale":
        fill, stroke, tfill, dash = (
            STALE_FILL,
            STALE_FILL,
            WHITE,
            ' stroke-dasharray="6 4"',
        )
    else:
        fill, stroke, tfill, dash = PAPER, RED, INK, ' stroke-dasharray="6 4"'
    markup = (
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="1.8"{dash}/>'
        f'<text x="{x + width / 2}" y="{y + height / 2 + size / 3}" fill="{tfill}" '
        f'text-anchor="middle" font-family="{BODY_FONT}" font-size="{size}px" '
        f'font-weight="700">{esc(label)}</text>'
    )
    return markup, width


def surfaces_panel_svg(attempt: WorkAttempt | None = None) -> str:
    """Draw the executed surfaces panel: typed state beside its projections."""

    rows = surfaces_rows(attempt)
    overall = surfaces_overall(attempt)
    present_total, missing_total, stale_total = surfaces_label_totals(attempt)
    shape_counts = surfaces_shape_counts(attempt)
    text, headline, _pill, floor = canvas_writers(WIDTH)
    chip_size = max(15, floor)
    left_x = 64
    chips_x = 430
    status_x = 1060
    body = [
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(left_x, 58, "The state a status word projects from"),
        text(
            left_x,
            88,
            "One real evaluate_with_surfaces call; every chip and every status below is read off its returned surfaces.",
            size=17,
            fill=MUTED,
        ),
        text(
            left_x,
            114,
            f"EXECUTED SURFACES PANEL · REVIEW DATE {SURFACES_AS_OF.isoformat()} · "
            f"{SURFACES_WINDOW}-DAY WINDOW · {len(rows)} MATCHED PRACTICES · "
            f"{present_total + missing_total} REQUIRED LABELS",
            size=17,
            fill=MUTED,
            weight="700",
        ),
    ]
    legend_y = 146
    legend_items = (
        ("present", "present (declared fresh)"),
        ("missing", "missing (hollow)"),
        ("stale", "stale — refresh due"),
    )
    legend_x = float(left_x)
    for state, description in legend_items:
        markup, width = _chip(legend_x, legend_y, state, state, chip_size)
        body.append(markup)
        body.append(
            text(legend_x + width + 10, legend_y + 22, description, size=15, fill=MUTED)
        )
        legend_x += width + 10 + 8.4 * len(description) + 34

    header_y = 222
    for label, x in (
        ("matched practice", left_x),
        ("evidence surfaces, in declared order", chips_x),
        ("projected status", status_x),
    ):
        body.append(text(x, header_y, label, size=17, weight="700", fill=BLACK))
    body.append(
        f'<line x1="{left_x}" y1="{header_y + 12}" x2="{WIDTH - left_x}" '
        f'y2="{header_y + 12}" stroke="{GRID}" stroke-width="1.6"/>'
    )

    row_h = 58
    y = header_y + 28
    for index, (practice_id, status, present, _missing, stale) in enumerate(rows):
        body.append(
            f'<rect x="{left_x}" y="{y}" width="{WIDTH - 2 * left_x}" height="{row_h - 8}" '
            f'rx="10" fill="{PANEL if index % 2 == 0 else PALE}" stroke="{GRID}" stroke-width="1"/>'
        )
        body.append(text(left_x + 16, y + 32, practice_id, size=17, weight="700"))
        practice = next(p for p in BLACK_PRACTICES if p.id == practice_id)
        chip_x = float(chips_x)
        for label in practice.required_evidence:
            if label in present:
                state = "present"
            elif label in stale:
                state = "stale"
            else:
                state = "missing"
            markup, width = _chip(chip_x, y + 9, label, state, chip_size)
            body.append(markup)
            chip_x += width + 12
        fill = STATUS_FILL.get(status, MUTED)
        body.append(
            f'<rect x="{status_x}" y="{y + 11}" width="28" height="28" rx="6" fill="{fill}"/>'
        )
        body.append(
            f'<text x="{status_x + 14}" y="{y + 11 + 14 + floor / 3}" fill="{WHITE}" '
            f'text-anchor="middle" font-family="{BODY_FONT}" font-size="{floor}px" '
            f'font-weight="700">{esc(STATUS_GLYPH.get(status, "?"))}</text>'
        )
        body.append(text(status_x + 40, y + 32, status, size=17, weight="700"))
        y += row_h

    overall_y = y + 20
    body.append(
        f'<rect x="{left_x}" y="{overall_y}" width="{WIDTH - 2 * left_x}" height="58" '
        f'rx="10" fill="{BLACK}" stroke="{BLACK}" stroke-width="1"/>'
    )
    body.append(
        text(
            left_x + 16,
            overall_y + 36,
            "OVERALL — one word for the whole attempt:",
            size=17,
            fill=WHITE,
            weight="700",
        )
    )
    body.append(
        text(left_x + 430, overall_y + 36, overall, size=17, fill=WHITE, weight="700")
    )
    compression = " · ".join(f"{status} {count}" for status, count in shape_counts)
    body.append(
        text(
            left_x,
            overall_y + 88,
            f"Distinct surface shapes per projected word: {compression} — the words compress; the surfaces keep the shapes.",
            size=17,
            fill=MUTED,
        )
    )

    boundary_y = overall_y + 132
    body.append(text(left_x, boundary_y, "Boundary", size=17, fill=BLACK, weight="700"))
    body.append(
        text(
            left_x + 136,
            boundary_y,
            f"Present, missing, and stale ({stale_total} of the {missing_total} missing here) are declaration-coverage surfaces at the pinned review date.",
            size=17,
            fill=MUTED,
        )
    )
    body.append(
        text(
            left_x + 136,
            boundary_y + 24,
            "A present label is a declaration, never verified evidence, and no surface shape grants permission.",
            size=17,
            fill=MUTED,
        )
    )
    height = boundary_y + 60
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="surfaces-title surfaces-desc">'
        f'<title id="surfaces-title">Typed evidence surfaces beside their projected statuses</title>'
        f'<desc id="surfaces-desc">A panel of {len(rows)} matched practices from one '
        f"evaluate_with_surfaces call at review date {SURFACES_AS_OF.isoformat()} under a "
        f"{SURFACES_WINDOW}-day window. Each row draws the practice's required labels in declared "
        f"order as filled present chips, hollow missing chips, or amber dashed stale chips, beside "
        f"the projected per-practice status; a band below names {overall} as the single overall "
        f"word, and the footer counts the distinct surface shapes each status word covers.</desc>"
        f"{''.join(body)}</svg>"
    )
