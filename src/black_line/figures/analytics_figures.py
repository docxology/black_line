"""Analytics-derived figures calling the real evaluator."""

from black_line import (
    BLACK_PRACTICES,
    BlackPractice,
    coverage_matrix,
    staleness_profile,
)
from black_line.figures.scenarios import (
    DECAY_AS_OF,
    DECAY_CELL_W,
    DECAY_GRID_X,
    DECAY_MAX_AGE,
    DECAY_PRACTICE,
    PATH_LABELS,
    PATH_PRACTICES,
    PATH_TAG,
    decay_attempt,
    path_assessments,
    path_first_aligned,
)
from black_line.figures.svg import (
    BLACK,
    BODY_FONT,
    canvas_writers,
    FAMILY_FILL,
    GRID,
    INK,
    MIN_FONT,
    MUTED,
    PAPER,
    SAND,
    STATUS_FILL,
    STATUS_GLYPH,
    TEAL,
    WHITE,
    WIDTH,
    esc,
    headline,
    text,
)


def coverage_heatmap_svg(
    practices: tuple[BlackPractice, ...] = BLACK_PRACTICES,
) -> str:
    """The tag-practice applicability matrix with per-tag reach and burden.

    ``practices`` is injected rather than read from the module so a test can
    render a larger registry and assert the derived canvas still contains it.
    """

    rows = coverage_matrix(practices)
    n_practices = len(practices)
    cell_w, cell_h = 82, 70
    grid_x, grid_y = 250, 400
    grid_w = n_practices * cell_w
    # Canvas derived from the grid the registry actually produces, so adding a
    # practice widens the plate instead of pushing the margin totals out of the
    # viewBox; the font floor is then derived from that width in turn.
    margin_w = 210
    width = max(grid_x + grid_w + 34 + margin_w, WIDTH)
    text, headline, _pill, _floor = canvas_writers(width)
    max_row = max(rows, key=lambda row: row.practice_count)
    min_row = min(rows, key=lambda row: row.practice_count)
    filled = sum(row.practice_count for row in rows)
    body = [
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(64, 58, "Tag choice sets the declaration burden"),
        text(
            64,
            88,
            "Filled cells mark which practices a tag reaches; the margins total each tag's practices and required labels.",
            size=15,
            fill=MUTED,
        ),
        text(
            64,
            114,
            f"DERIVED FROM REGISTRY · {filled} OF {n_practices * len(rows)} CELLS APPLICABLE · APPLICABILITY MAP, NOT A QUALITY OR TRUTH SCORE",
            size=16,
            fill=MUTED,
            weight="700",
        ),
    ]
    # Rotated practice-id column headers, keyed to registry declaration order.
    for index, practice in enumerate(practices):
        cx = grid_x + index * cell_w + cell_w / 2
        accent = FAMILY_FILL.get(practice.kind.value, BLACK)
        body.append(
            f'<text x="{cx}" y="{grid_y - 16}" fill="{accent}" font-family="{BODY_FONT}" '
            f'font-size="{_floor}px" font-weight="700" text-anchor="start" '
            f'transform="rotate(-38 {cx} {grid_y - 16})">{esc(practice.id)}</text>'
        )
    for row_index, row in enumerate(rows):
        y = grid_y + row_index * cell_h
        body.append(
            text(
                grid_x - 20,
                y + cell_h / 2 + 5,
                row.tag,
                size=15,
                weight="700",
                anchor="end",
            )
        )
        for col_index, practice in enumerate(practices):
            x = grid_x + col_index * cell_w
            applicable = practice.id in row.practice_ids
            accent = FAMILY_FILL.get(practice.kind.value, BLACK)
            fill = accent if applicable else SAND
            stroke = INK if applicable else GRID
            opacity = "" if applicable else ' opacity="0.85"'
            body.append(
                f'<rect x="{x + 3}" y="{y + 3}" width="{cell_w - 6}" height="{cell_h - 6}" rx="8" '
                f'fill="{fill}" stroke="{stroke}" stroke-width="1.2"{opacity}/>'
            )
            if applicable:
                body.append(
                    text(
                        x + cell_w / 2,
                        y + cell_h / 2 + 5,
                        str(len(practice.required_evidence)),
                        size=17,
                        fill=WHITE,
                        weight="700",
                        anchor="middle",
                    )
                )
        reach_x = grid_x + grid_w + 34
        body.append(
            text(
                reach_x,
                y + cell_h / 2 - 6,
                f"{row.practice_count} practice"
                + ("" if row.practice_count == 1 else "s"),
                size=16,
                weight="700",
            )
        )
        body.append(
            text(
                reach_x,
                y + cell_h / 2 + 18,
                f"{row.required_label_count} labels",
                size=16,
                fill=MUTED,
            )
        )
    stats_y = grid_y + len(rows) * cell_h + 46
    body.extend(
        (
            text(
                grid_x + grid_w + 34,
                grid_y - 16,
                "tag burden",
                size=16,
                fill=MUTED,
                weight="700",
            ),
            text(64, stats_y, "Asymmetry", size=16, fill=TEAL, weight="700"),
            text(
                190,
                stats_y,
                f"'{max_row.tag}' commits a declarer to {max_row.practice_count} practices ({max_row.required_label_count} labels); "
                f"'{min_row.tag}' to {min_row.practice_count} ({min_row.required_label_count}). "
                "A narrow tag set buys a cheaper ALIGNED —",
                size=16,
                fill=MUTED,
            ),
            text(
                190,
                stats_y + 26,
                "a coverage fact reviewers should read alongside any status.",
                size=16,
                fill=MUTED,
            ),
            text(64, stats_y + 60, "Boundary", size=16, fill=BLACK, weight="700"),
            text(
                190,
                stats_y + 60,
                "Cell numbers are required-label counts. Applicability is not evidence, quality, safety, or permission.",
                size=16,
                fill=MUTED,
            ),
        )
    )
    height = stats_y + 100
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="cov-title cov-desc"><title id="cov-title">Tag-practice coverage matrix</title>'
        f'<desc id="cov-desc">A {len(rows)} by {n_practices} matrix of tags against practices with filled cells marking applicability, '
        f"per-tag practice reach and required-label burden in the margin, and a note that tag choice sets the declaration burden.</desc>"
        f"{''.join(body)}</svg>"
    )


def evidence_decay_svg() -> str:
    """Status versus evidence age under several freshness windows, from real sweeps."""

    full = DECAY_PRACTICE.required_evidence
    partial = DECAY_PRACTICE.required_evidence[:1]
    rows = (
        ("full declaration · window 30", 30, full),
        ("full declaration · window 51", 51, full),
        ("full declaration · no window", None, full),
        ("one label never declared · window 30", 30, partial),
    )
    ages = range(DECAY_MAX_AGE + 1)
    cell_w, cell_h = DECAY_CELL_W, 58
    grid_x, grid_y = DECAY_GRID_X, 268
    row_gap = 26
    # Derived from the sweep itself: the canvas always contains every age
    # column and the final axis tick, whatever DECAY_MAX_AGE is set to.
    width = grid_x + (DECAY_MAX_AGE + 1) * cell_w + 40
    text, headline, _pill, _floor = canvas_writers(width)
    body = [
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(64, 58, "Evidence decays by a strict day count"),
        text(
            64,
            88,
            "Each cell is one real evaluate_work call: the same declaration, re-reviewed as its evidence ages one day at a time.",
            size=17,
            fill=MUTED,
        ),
        text(
            64,
            114,
            f"EXECUTED SWEEP · PRACTICE '{DECAY_PRACTICE.id}' · REVIEW DATE {DECAY_AS_OF.isoformat()} · AGES 0–{DECAY_MAX_AGE} DAYS",
            size=17,
            fill=MUTED,
            weight="700",
        ),
        text(
            64,
            152,
            "Fresh means age ≤ window; only age > window is stale.",
            size=17,
            fill=MUTED,
        ),
        text(
            64,
            176,
            "Stale-only gaps ask for a refresh (NEEDS_EVIDENCE); an undeclared label is missing work (NEEDS_REWORK) at every age.",
            size=17,
            fill=MUTED,
        ),
    ]
    for row_index, (label, window, labels) in enumerate(rows):
        y = grid_y + row_index * (cell_h + row_gap)
        body.append(
            text(grid_x - 20, y + 24, label, size=17, weight="700", anchor="end")
        )
        window_text = "window: none" if window is None else f"window: {window}d"
        body.append(
            text(grid_x - 20, y + 48, window_text, size=17, fill=MUTED, anchor="end")
        )
        statuses = []
        for age in ages:
            (point,) = staleness_profile(
                decay_attempt(age, labels), (window,), as_of=DECAY_AS_OF
            )
            statuses.append(point.status)
            fill = STATUS_FILL.get(point.status.value, MUTED)
            body.append(
                f'<rect x="{grid_x + age * cell_w}" y="{y}" width="{cell_w - 1}" height="{cell_h}" fill="{fill}"/>'
            )
        # Redundant to the fill: name each contiguous status run in the strip,
        # so the figure carries its meaning in greyscale as well as in colour.
        run_start = 0
        for index in range(len(statuses) + 1):
            if index < len(statuses) and statuses[index] is statuses[run_start]:
                continue
            run_width = (index - run_start) * cell_w
            if run_width >= 200:
                body.append(
                    text(
                        grid_x + run_start * cell_w + run_width / 2,
                        y + cell_h / 2 + 6,
                        statuses[run_start].value,
                        size=17,
                        fill=WHITE,
                        weight="700",
                        anchor="middle",
                    )
                )
            run_start = index
        if window is not None and window + 1 <= DECAY_MAX_AGE:
            boundary_x = grid_x + (window + 1) * cell_w
            if statuses[window] != statuses[window + 1]:
                body.append(
                    f'<line x1="{boundary_x}" y1="{y - 6}" x2="{boundary_x}" y2="{y + cell_h + 6}" stroke="{INK}" stroke-width="2" stroke-dasharray="4 4"/>'
                )
                body.append(
                    text(
                        boundary_x + 6,
                        y - 10,
                        f"age {window} fresh · age {window + 1} stale",
                        size=17,
                        fill=INK,
                        weight="700",
                    )
                )
            else:
                # An honest annotation instead of an inert boundary marker: on
                # this strip the executed statuses do not change at the window,
                # because the undeclared label dominates at every age.
                body.append(
                    text(
                        boundary_x + 6,
                        y - 10,
                        "window has no effect here: an undeclared label is missing at every age",
                        size=17,
                        fill=MUTED,
                    )
                )
    axis_y = grid_y + len(rows) * (cell_h + row_gap) + 6
    for tick in range(0, DECAY_MAX_AGE + 1, 10):
        tx = grid_x + tick * cell_w
        body.append(
            f'<line x1="{tx}" y1="{axis_y}" x2="{tx}" y2="{axis_y + 8}" stroke="{MUTED}" stroke-width="1.5"/>'
        )
        body.append(
            text(tx, axis_y + 30, str(tick), size=17, fill=MUTED, anchor="middle")
        )
    body.append(
        text(
            grid_x + DECAY_MAX_AGE * cell_w / 2,
            axis_y + 60,
            "evidence age at review (days)",
            size=17,
            fill=MUTED,
            anchor="middle",
        )
    )
    legend_y = axis_y + 84
    legend_x = grid_x
    for status_value in ("ALIGNED", "NEEDS_EVIDENCE", "NEEDS_REWORK"):
        body.append(
            f'<rect x="{legend_x}" y="{legend_y - 16}" width="20" height="20" rx="4" fill="{STATUS_FILL[status_value]}"/>'
        )
        body.append(
            text(legend_x + 28, legend_y, status_value, size=17, fill=INK, weight="700")
        )
        legend_x += 220
    body.append(text(64, legend_y + 42, "Boundary", size=17, fill=BLACK, weight="700"))
    body.append(
        text(
            200,
            legend_y + 42,
            "A fresh date is a declaration property. It does not show the underlying observation was ever adequate or still holds.",
            size=17,
            fill=MUTED,
        )
    )
    height = legend_y + 76
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="decay-title decay-desc"><title id="decay-title">Evidence decay under the freshness window</title>'
        f'<desc id="decay-desc">Four status strips from real evaluator sweeps: full declarations flip from ALIGNED to NEEDS_EVIDENCE one day after the window, '
        f"a declaration with no window never goes stale, and a declaration missing one label is NEEDS_REWORK at every age.</desc>"
        f"{''.join(body)}</svg>"
    )


def incremental_path_svg() -> str:
    """The executed incremental-declaration path as a per-finding status grid."""

    assessments = path_assessments()
    practice_ids = [finding.practice_id for finding in assessments[0].findings]
    n_steps = len(assessments)
    cell_w, cell_h = 60, 44
    grid_x, grid_y = 330, 300
    width = 1400
    body = [
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(64, 58, "One declaration, re-evaluated after every label"),
        text(
            64,
            88,
            f"Each column is one real evaluate_work call on the same attempt as labels accumulate from none to all {len(PATH_LABELS)}.",
            size=16,
            fill=MUTED,
        ),
        text(
            64,
            114,
            f"EXECUTED PATH · TAG '{PATH_TAG}' · {len(PATH_PRACTICES)} APPLICABLE PRACTICES · {len(PATH_LABELS)} REQUIRED LABELS · {n_steps} EVALUATOR CALLS",
            size=16,
            fill=MUTED,
            weight="700",
        ),
        text(
            64,
            152,
            "Rows are per-practice findings; the bottom row is the overall status — the most demanding per-practice status at each step.",
            size=16,
            fill=MUTED,
        ),
    ]
    # Rotated per-step headers naming the label added at that step.
    for step in range(1, n_steps):
        hx = grid_x + step * cell_w + cell_w / 2
        body.append(
            f'<text x="{hx}" y="{grid_y - 14}" fill="{MUTED}" font-family="{BODY_FONT}" '
            f'font-size="{MIN_FONT}px" text-anchor="start" '
            f'transform="rotate(-52 {hx} {grid_y - 14})">+{esc(PATH_LABELS[step - 1])}</text>'
        )
    body.append(
        text(
            grid_x + cell_w / 2,
            grid_y - 14,
            "empty",
            size=16,
            fill=MUTED,
            anchor="middle",
        )
    )
    for row_index, practice_id in enumerate(practice_ids):
        y = grid_y + row_index * cell_h
        body.append(
            text(
                grid_x - 16,
                y + cell_h / 2 + 5,
                practice_id,
                size=16,
                weight="700",
                anchor="end",
            )
        )
        for step, assessment in enumerate(assessments):
            finding = next(
                f for f in assessment.findings if f.practice_id == practice_id
            )
            fill = STATUS_FILL.get(finding.status.value, MUTED)
            body.append(
                f'<rect x="{grid_x + step * cell_w + 2}" y="{y + 2}" width="{cell_w - 4}" '
                f'height="{cell_h - 4}" rx="6" fill="{fill}"/>'
            )
            body.append(
                text(
                    grid_x + step * cell_w + cell_w / 2,
                    y + cell_h / 2 + 6,
                    STATUS_GLYPH[finding.status.value],
                    size=16,
                    fill=WHITE,
                    weight="700",
                    anchor="middle",
                )
            )
    overall_y = grid_y + len(practice_ids) * cell_h + 18
    body.append(
        text(
            grid_x - 16,
            overall_y + cell_h / 2 + 5,
            "OVERALL",
            size=16,
            fill=BLACK,
            weight="700",
            anchor="end",
        )
    )
    for step, assessment in enumerate(assessments):
        fill = STATUS_FILL.get(assessment.status.value, MUTED)
        body.append(
            f'<rect x="{grid_x + step * cell_w + 2}" y="{overall_y + 2}" width="{cell_w - 4}" '
            f'height="{cell_h - 4}" rx="6" fill="{fill}"/>'
        )
        body.append(
            text(
                grid_x + step * cell_w + cell_w / 2,
                overall_y + cell_h / 2 + 6,
                STATUS_GLYPH[assessment.status.value],
                size=16,
                fill=WHITE,
                weight="700",
                anchor="middle",
            )
        )
    first_aligned_x = grid_x + path_first_aligned() * cell_w
    body.append(
        f'<rect x="{first_aligned_x}" y="{overall_y}" width="{cell_w}" height="{cell_h}" rx="8" '
        f'fill="none" stroke="{INK}" stroke-width="2.5" stroke-dasharray="5 4"/>'
    )
    axis_y = overall_y + cell_h + 24
    for step in range(n_steps):
        body.append(
            text(
                grid_x + step * cell_w + cell_w / 2,
                axis_y,
                str(step),
                size=16,
                fill=MUTED,
                anchor="middle",
            )
        )
    body.append(
        text(
            grid_x + n_steps * cell_w / 2,
            axis_y + 28,
            "step (labels declared so far)",
            size=16,
            fill=MUTED,
            anchor="middle",
        )
    )
    body.append(
        text(
            first_aligned_x + cell_w,
            overall_y - 6,
            f"first ALIGNED at step {path_first_aligned()}",
            size=16,
            fill=INK,
            weight="700",
            anchor="end",
        )
    )
    legend_y = axis_y + 62
    legend_x = grid_x
    for status_value in ("ALIGNED", "NEEDS_EVIDENCE", "NEEDS_REWORK"):
        body.append(
            f'<rect x="{legend_x}" y="{legend_y - 15}" width="19" height="19" rx="4" fill="{STATUS_FILL[status_value]}"/>'
        )
        body.append(
            text(
                legend_x + 27,
                legend_y,
                f"{STATUS_GLYPH[status_value]} = {status_value}",
                size=16,
                fill=INK,
                weight="700",
            )
        )
        legend_x += 230
    boundary_y = legend_y + 40
    body.append(text(64, boundary_y, "Boundary", size=16, fill=BLACK, weight="700"))
    body.append(
        text(
            180,
            boundary_y,
            "Every cell reports declaration coverage from a real evaluator call;",
            size=16,
            fill=MUTED,
        )
    )
    body.append(
        text(
            180,
            boundary_y + 24,
            "accumulated ALIGNED findings verify no source, test, or claim, and grant nothing.",
            size=16,
            fill=MUTED,
        )
    )
    height = boundary_y + 66
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="inc-title inc-desc"><title id="inc-title">The incremental declaration path as a status grid</title>'
        f'<desc id="inc-desc">A {len(PATH_PRACTICES)}-practice by {n_steps}-step grid of per-practice statuses plus an overall row: '
        f"practices flip to ALIGNED as their labels complete while the overall status stays NEEDS_REWORK until step {path_first_aligned()}, "
        f"and the empty first column is NEEDS_EVIDENCE.</desc>"
        f"{''.join(body)}</svg>"
    )
