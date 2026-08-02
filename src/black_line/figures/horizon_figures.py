"""Figures derived from the scheduling and monotonicity analytics.

Both builders call the shipped analytics helpers on pinned scenarios and draw
whatever comes back. Nothing here restates a status, a day count, or an
omission reason as a literal: if the evaluator changes, these plates change
with it or the binding tests fail.
"""

from __future__ import annotations

from black_line import (
    declaration_status_path,
    no_status_regression,
    refresh_horizon,
    refresh_horizon_omissions,
    status_rank,
)
from black_line.figures.scenarios import (
    HORIZON_AS_OF,
    HORIZON_ATTEMPT,
    HORIZON_WINDOW,
    LATTICE_SEED,
    PATH_LABELS,
    PATH_TAG,
    lattice_orders,
)
from black_line.figures.svg import (
    BLACK,
    BODY_FONT,
    GRID,
    INK,
    MUTED,
    PALE,
    PANEL,
    PAPER,
    STATUS_FILL,
    STATUS_GLYPH,
    TEAL,
    WHITE,
    canvas_writers,
    esc,
    rect,
)


def horizon_rows() -> tuple:
    """The kept refresh-horizon rows, in the helper's own ascending order."""

    return refresh_horizon(
        HORIZON_ATTEMPT,
        as_of=HORIZON_AS_OF,
        max_evidence_age_days=HORIZON_WINDOW,
    )


def horizon_omissions() -> tuple:
    """The declarations the horizon leaves out, each with its reason.

    Not all of them are dated: an undated declaration is one of the three
    omitted classes, so calling this set "dated" would misdescribe it.
    """

    return refresh_horizon_omissions(
        HORIZON_ATTEMPT,
        as_of=HORIZON_AS_OF,
        max_evidence_age_days=HORIZON_WINDOW,
    )


def refresh_queue_svg() -> str:
    """Draw the refresh queue: which declared label reaches its boundary first."""

    rows = horizon_rows()
    omitted = horizon_omissions()
    width = 1400
    text, headline, _pill, _floor = canvas_writers(width)
    label_x = 400
    bar_x = 430
    bar_max = 720
    row_h = 62
    grid_y = 268
    longest = max((row.days_until_stale for row in rows), default=1) or 1
    body = [
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(64, 58, "Which declaration goes stale first"),
        text(
            64,
            88,
            "One bar per dated label refresh_horizon keeps, in its own ascending nearest-to-stale order.",
            size=17,
            fill=MUTED,
        ),
        text(
            64,
            114,
            f"EXECUTED VIEW · REVIEW DATE {HORIZON_AS_OF.isoformat()} · WINDOW {HORIZON_WINDOW} DAYS · "
            f"{len(rows)} SCHEDULED · {len(omitted)} OMITTED",
            size=17,
            fill=MUTED,
            weight="700",
        ),
        text(
            64,
            152,
            "Bar length is days until the freshness boundary, not the importance of the evidence or the",
            size=17,
            fill=MUTED,
        ),
        text(
            64,
            176,
            "quality of the observation behind it.",
            size=17,
            fill=MUTED,
        ),
        text(64, grid_y - 26, "evidence label", size=17, fill=MUTED, weight="700"),
        text(bar_x, grid_y - 26, "days until stale", size=17, fill=MUTED, weight="700"),
    ]
    for index, row in enumerate(rows):
        y = grid_y + index * row_h
        bar_w = max(24, bar_max * row.days_until_stale / longest)
        body.append(
            f'<rect x="64" y="{y - 22}" width="{label_x - 64 + bar_max + 210}" '
            f'height="{row_h - 10}" rx="10" fill="{PANEL if index % 2 == 0 else PALE}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        body.append(text(84, y + 4, row.label, size=18, weight="700"))
        body.append(
            text(
                84,
                y + 26,
                "required by " + ", ".join(row.practice_ids),
                size=16,
                fill=MUTED,
            )
        )
        body.append(
            f'<rect x="{bar_x}" y="{y - 12}" width="{bar_w}" height="34" rx="8" '
            f'fill="{TEAL}"/>'
        )
        body.append(
            text(
                bar_x + bar_w + 14,
                y + 12,
                f"{row.days_until_stale} days · noted {row.noted_on}",
                size=17,
                weight="700",
            )
        )
    band_y = grid_y + len(rows) * row_h + 24
    body.append(rect(64, band_y, width - 128, 44 + len(omitted) * 30, fill=PALE))
    body.append(
        text(
            88,
            band_y + 32,
            f"Omitted from the queue ({len(omitted)} declarations)",
            size=18,
            weight="700",
            fill=BLACK,
        )
    )
    for index, row in enumerate(omitted):
        body.append(
            text(
                88,
                band_y + 62 + index * 30,
                f"{row.label} — {row.reason}",
                size=17,
                fill=MUTED,
            )
        )
    boundary_y = band_y + 44 + len(omitted) * 30 + 46
    body.append(text(64, boundary_y, "Boundary", size=17, fill=BLACK, weight="700"))
    body.append(
        text(
            200,
            boundary_y,
            "A schedule of declared dates. It does not show that any observation was made, or that",
            size=17,
            fill=MUTED,
        )
    )
    body.append(
        text(
            200,
            boundary_y + 24,
            "refreshing the date will re-establish anything the label points to.",
            size=17,
            fill=MUTED,
        )
    )
    height = boundary_y + 60
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="rq-title rq-desc">'
        f'<title id="rq-title">The refresh queue for one declaration</title>'
        f'<desc id="rq-desc">{len(rows)} dated evidence labels ordered from nearest to furthest '
        f"from the {HORIZON_WINDOW}-day freshness boundary, each naming the practice that requires it, "
        f"with a named band listing the {len(omitted)} declarations the queue omits and why.</desc>"
        f'<rect width="100%" height="100%" fill="{PAPER}"/>'
        f"{''.join(body)}</svg>"
    )


def lattice_paths() -> tuple[tuple[tuple[str, ...], tuple, bool, int], ...]:
    """Execute the seeded declaration-order sweep.

    Returns one ``(order, statuses, monotone_after_first, inversions)`` row per
    seeded order, where ``inversions`` counts adjacent rank decreases across the
    whole path, including the intentional empty-declaration boundary.
    """

    rows = []
    for order in lattice_orders():
        statuses = declaration_status_path(
            "declaration order sweep", (PATH_TAG,), order
        )
        ranks = [status_rank(status) for status in statuses]
        inversions = sum(
            1 for earlier, later in zip(ranks, ranks[1:]) if later < earlier
        )
        rows.append((order, statuses, no_status_regression(statuses[1:]), inversions))
    return tuple(rows)


def monotonicity_lattice_svg() -> str:
    """Draw conditional fresh-evidence monotonicity as a sweep, not one trace."""

    rows = lattice_paths()
    n_steps = len(PATH_LABELS) + 1
    width = 1400
    text, headline, _pill, floor = canvas_writers(width)
    cell_w, cell_h = 56, 44
    grid_x, grid_y = 300, 316
    monotone_rows = sum(1 for _, _, monotone, _ in rows)
    total_inversions = sum(inversions for _, _, _, inversions in rows)
    boundary_inversions = sum(
        1
        for _, statuses, _, _ in rows
        if status_rank(statuses[1]) < status_rank(statuses[0])
    )
    body = [
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(64, 58, "The same property, swept over declaration orders"),
        text(
            64,
            88,
            f"Every cell is one real evaluate_work call: {len(rows)} seeded orders of the same {len(PATH_LABELS)} labels.",
            size=16,
            fill=MUTED,
        ),
        text(
            64,
            114,
            f"EXECUTED SWEEP · SEED {LATTICE_SEED} · TAG '{PATH_TAG}' · "
            f"{len(rows)} ORDERS × {n_steps} STEPS · {len(rows) * n_steps} EVALUATOR CALLS",
            size=16,
            fill=MUTED,
            weight="700",
        ),
        text(
            64,
            152,
            "Row 0 is the registry's own declaration order — the single trace the incremental-path figure draws.",
            size=16,
            fill=MUTED,
        ),
        text(
            64,
            176,
            "The remaining rows are seeded permutations of it, so the claim is sampled rather than proven.",
            size=16,
            fill=MUTED,
        ),
        text(64, grid_y - 30, "order", size=16, fill=MUTED, weight="700"),
        text(
            width - 40,
            grid_y - 30,
            "monotone after step 1",
            size=16,
            fill=MUTED,
            weight="700",
            anchor="end",
        ),
    ]
    for step in range(n_steps):
        body.append(
            text(
                grid_x + step * cell_w + cell_w / 2,
                grid_y - 8,
                str(step),
                size=16,
                fill=MUTED,
                anchor="middle",
            )
        )
    for row_index, (order, statuses, monotone, _inversions) in enumerate(rows):
        y = grid_y + 8 + row_index * cell_h
        body.append(
            text(
                grid_x - 20,
                y + cell_h / 2 + 6,
                f"{row_index:02d} · +{order[0]}",
                size=16,
                weight="700",
                anchor="end",
            )
        )
        for step, status in enumerate(statuses):
            fill = STATUS_FILL.get(status.value, MUTED)
            body.append(
                f'<rect x="{grid_x + step * cell_w + 2}" y="{y + 2}" '
                f'width="{cell_w - 4}" height="{cell_h - 4}" rx="6" fill="{fill}"/>'
            )
            body.append(
                f'<text x="{grid_x + step * cell_w + cell_w / 2}" y="{y + cell_h / 2 + 6}" '
                f'fill="{WHITE}" text-anchor="middle" font-family="{BODY_FONT}" '
                f'font-size="{floor}px" font-weight="700">'
                f"{esc(STATUS_GLYPH[status.value])}</text>"
            )
        body.append(
            text(
                grid_x + n_steps * cell_w + 24,
                y + cell_h / 2 + 6,
                "yes" if monotone else "NO",
                size=17,
                weight="700",
                fill=TEAL if monotone else STATUS_FILL["NEEDS_REWORK"],
            )
        )
    footer_y = grid_y + 8 + len(rows) * cell_h + 48
    legend_x = grid_x
    for status_value in ("ALIGNED", "NEEDS_EVIDENCE", "NEEDS_REWORK"):
        body.append(
            f'<rect x="{legend_x}" y="{footer_y - 15}" width="19" height="19" rx="4" '
            f'fill="{STATUS_FILL[status_value]}"/>'
        )
        body.append(
            text(
                legend_x + 27,
                footer_y,
                f"{STATUS_GLYPH[status_value]} = {status_value}",
                size=16,
                fill=INK,
                weight="700",
            )
        )
        legend_x += 230
    body.append(text(64, footer_y + 40, "Counted", size=16, fill=BLACK, weight="700"))
    body.append(
        text(
            190,
            footer_y + 40,
            f"{monotone_rows} of {len(rows)} orders are monotone from step 1 onward; "
            f"{total_inversions} rank decreases occur in the whole sweep,",
            size=16,
            fill=MUTED,
        )
    )
    body.append(
        text(
            190,
            footer_y + 64,
            f"and {boundary_inversions} of them are the step 0 to step 1 empty-declaration boundary.",
            size=16,
            fill=MUTED,
        )
    )
    body.append(text(64, footer_y + 104, "Boundary", size=16, fill=BLACK, weight="700"))
    body.append(
        text(
            190,
            footer_y + 104,
            "A seeded sample of orders, not a proof over all of them, and a statement about status",
            size=16,
            fill=MUTED,
        )
    )
    body.append(
        text(
            190,
            footer_y + 128,
            "ordering only — no cell shows that a declared label points at anything.",
            size=16,
            fill=MUTED,
        )
    )
    height = footer_y + 160
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="ml-title ml-desc">'
        f'<title id="ml-title">Conditional monotonicity swept over declaration orders</title>'
        f'<desc id="ml-desc">A {len(rows)} by {n_steps} grid of assessment statuses, one row per seeded '
        f"declaration order and one column per step, with a per-row monotonicity mark and a footer counting "
        f"{total_inversions} rank decreases of which {boundary_inversions} are the empty-declaration boundary.</desc>"
        f'<rect width="100%" height="100%" fill="{PAPER}"/>'
        f"{''.join(body)}</svg>"
    )
