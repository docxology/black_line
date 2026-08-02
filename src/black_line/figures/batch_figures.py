"""The batch panel: what a registry demands across differently-tagged work.

Every other figure in this project draws either the registry's structure or a
single work attempt swept along one axis. This one runs the ordinary evaluator
over a pinned battery of attempts and draws the distribution that comes back,
so the question it answers — which wires go unsatisfied most often across
differently-tagged work — is a property of the registry's demands rather than
of any one declaration.

Nothing here restates a count. The status distribution is
:func:`summarize_assessments` output, the family concentration is its
``open_finding_kind_counts``, and the per-practice gap ranking is recounted
from the same executed findings. Ordering is total and explicit at every step,
so the plate is byte-identical across runs.
"""

from __future__ import annotations

from black_line import (
    BLACK_PRACTICES,
    PracticeStatus,
    summarize_assessments,
)
from black_line.figures.scenarios import (
    BATCH_AS_OF,
    BATCH_ATTEMPTS,
    BATCH_WINDOW,
    batch_assessments,
)
from black_line.figures.svg import (
    BLACK,
    BODY_FONT,
    GRID,
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


def batch_summary(assessments: tuple | None = None):
    """The :class:`AssessmentSummary` for the pinned battery.

    ``assessments`` overrides the battery, which lets a caller check that this
    panel follows its data instead of a baked-in ranking.
    """

    return summarize_assessments(
        batch_assessments() if assessments is None else assessments, BLACK_PRACTICES
    )


def batch_gap_counts(assessments: tuple | None = None) -> tuple[tuple[str, int], ...]:
    """Non-``ALIGNED`` finding counts per practice, most gapped first.

    Ties are broken by practice id, so the ranking is a total order and the
    drawn figure cannot depend on dictionary insertion order.
    """

    batch = batch_assessments() if assessments is None else assessments
    counts: dict[str, int] = {}
    for assessment in batch:
        for finding in assessment.findings:
            if finding.status is PracticeStatus.ALIGNED:
                continue
            counts[finding.practice_id] = counts.get(finding.practice_id, 0) + 1
    return tuple(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


def batch_never_gapped(assessments: tuple | None = None) -> tuple[str, ...]:
    """Applicable practices the battery never left open, in registry order."""

    batch = batch_assessments() if assessments is None else assessments
    gapped = {practice_id for practice_id, _count in batch_gap_counts(batch)}
    applied = {
        finding.practice_id for assessment in batch for finding in assessment.findings
    }
    return tuple(
        practice.id
        for practice in BLACK_PRACTICES
        if practice.id in applied and practice.id not in gapped
    )


def batch_summary_svg(assessments: tuple | None = None) -> str:
    """Draw the executed batch: status distribution and the wires most often open."""

    batch = batch_assessments() if assessments is None else assessments
    summary = batch_summary(batch)
    gaps = batch_gap_counts(batch)
    never = batch_never_gapped(batch)
    width = 1400
    text, headline, _pill, floor = canvas_writers(width)

    left_x, right_x = 64, 716
    panel_w = 620
    body = [f'<rect width="100%" height="100%" fill="{PAPER}"/>']
    body.append(headline(left_x, 58, "One registry, eight differently-tagged attempts"))
    body.append(
        text(
            left_x,
            88,
            "Each row is counted from real evaluate_work calls over a pinned battery, not from a stored total.",
            size=17,
            fill=MUTED,
        )
    )
    body.append(
        text(
            left_x,
            114,
            f"EXECUTED BATCH · REVIEW DATE {BATCH_AS_OF.isoformat()} · WINDOW {BATCH_WINDOW} DAYS · "
            f"{summary.total} ATTEMPTS · {len(BLACK_PRACTICES)} PRACTICES",
            size=17,
            fill=MUTED,
            weight="700",
        )
    )

    # --- left column: status distribution, then family concentration ---------
    status_y = 190
    body.append(
        text(left_x, status_y - 24, "Overall status", size=18, weight="700", fill=BLACK)
    )
    body.append(
        text(
            left_x,
            status_y + 2,
            "one per attempt; every status the enum defines has a row",
            size=17,
            fill=MUTED,
        )
    )
    status_row_h = 58
    status_bar_x = left_x + 250
    status_bar_max = panel_w - 250 - 96
    status_max = max((count for _value, count in summary.status_counts), default=1) or 1
    for index, (value, count) in enumerate(summary.status_counts):
        y = status_y + 44 + index * status_row_h
        fill = STATUS_FILL.get(value, MUTED)
        body.append(
            f'<rect x="{left_x}" y="{y}" width="{panel_w}" height="{status_row_h - 12}" '
            f'rx="10" fill="{PANEL if index % 2 == 0 else PALE}" stroke="{GRID}" '
            f'stroke-width="1"/>'
        )
        body.append(
            f'<rect x="{left_x + 14}" y="{y + 9}" width="28" height="28" rx="6" '
            f'fill="{fill}"/>'
        )
        body.append(
            f'<text x="{left_x + 28}" y="{y + 9 + 14 + floor / 3}" fill="{WHITE}" '
            f'text-anchor="middle" font-family="{BODY_FONT}" font-size="{floor}px" '
            f'font-weight="700">{esc(STATUS_GLYPH.get(value, "?"))}</text>'
        )
        body.append(text(left_x + 56, y + 29, value, size=17, weight="700"))
        bar_w = max(6, status_bar_max * count / status_max)
        body.append(
            f'<rect x="{status_bar_x}" y="{y + 12}" width="{bar_w}" height="22" '
            f'rx="6" fill="{fill}"/>'
        )
        body.append(
            text(
                status_bar_x + bar_w + 12,
                y + 30,
                f"{count} of {summary.total}",
                size=17,
                weight="700",
            )
        )

    family_y = status_y + 44 + len(summary.status_counts) * status_row_h + 54
    body.append(
        text(
            left_x,
            family_y - 24,
            "Open findings by craft family",
            size=18,
            weight="700",
            fill=BLACK,
        )
    )
    body.append(
        text(
            left_x,
            family_y + 2,
            "every non-ALIGNED finding in the batch, attributed through the registry",
            size=17,
            fill=MUTED,
        )
    )
    family_row_h = 40
    family_bar_x = left_x + 250
    family_bar_max = panel_w - 250 - 96
    family_max = (
        max((count for _name, count in summary.open_finding_kind_counts), default=1)
        or 1
    )
    for index, (name, count) in enumerate(summary.open_finding_kind_counts):
        y = family_y + 40 + index * family_row_h
        body.append(text(left_x + 4, y + 18, name, size=17, weight="700"))
        bar_w = max(6, family_bar_max * count / family_max)
        body.append(
            f'<rect x="{family_bar_x}" y="{y + 3}" width="{bar_w}" height="20" '
            f'rx="6" fill="{TEAL}"/>'
        )
        body.append(
            text(family_bar_x + bar_w + 12, y + 19, str(count), size=17, weight="700")
        )
    left_bottom = family_y + 40 + len(summary.open_finding_kind_counts) * family_row_h

    # --- right column: which wire is open most often -------------------------
    body.append(
        text(
            right_x,
            status_y - 24,
            "Practices most often left open",
            size=18,
            weight="700",
            fill=BLACK,
        )
    )
    body.append(
        text(
            right_x,
            status_y + 2,
            "count of non-ALIGNED findings across the batch, ties broken by practice id",
            size=17,
            fill=MUTED,
        )
    )
    gap_row_h = 44
    gap_bar_x = right_x + 300
    gap_bar_max = panel_w - 300 - 84
    gap_max = max((count for _name, count in gaps), default=1) or 1
    for index, (practice_id, count) in enumerate(gaps):
        y = status_y + 40 + index * gap_row_h
        body.append(
            f'<rect x="{right_x}" y="{y}" width="{panel_w}" height="{gap_row_h - 8}" '
            f'rx="10" fill="{PANEL if index % 2 == 0 else PALE}" stroke="{GRID}" '
            f'stroke-width="1"/>'
        )
        body.append(text(right_x + 14, y + 24, practice_id, size=17, weight="700"))
        bar_w = max(6, gap_bar_max * count / gap_max)
        body.append(
            f'<rect x="{gap_bar_x}" y="{y + 8}" width="{bar_w}" height="20" rx="6" '
            f'fill="{STATUS_FILL["NEEDS_REWORK"]}"/>'
        )
        body.append(
            text(gap_bar_x + bar_w + 12, y + 24, str(count), size=17, weight="700")
        )
    right_bottom = status_y + 40 + len(gaps) * gap_row_h

    never_y = right_bottom + 34
    body.append(rect(right_x, never_y, panel_w, 76, fill=PALE))
    body.append(
        text(
            right_x + 20,
            never_y + 30,
            f"Never left open ({len(never)} of the {len(BLACK_PRACTICES)} practices)",
            size=17,
            weight="700",
            fill=BLACK,
        )
    )
    body.append(
        text(
            right_x + 20,
            never_y + 56,
            ", ".join(never) if never else "none",
            size=17,
            fill=MUTED,
        )
    )

    boundary_y = max(left_bottom, never_y + 76) + 56
    body.append(text(left_x, boundary_y, "Boundary", size=17, fill=BLACK, weight="700"))
    body.append(
        text(
            left_x + 136,
            boundary_y,
            "A gap frequency is a declaration statistic over this battery. It does not rank the practices by",
            size=17,
            fill=MUTED,
        )
    )
    body.append(
        text(
            left_x + 136,
            boundary_y + 24,
            "importance, and a frequently-open wire is one the declarers did not declare, not one that failed.",
            size=17,
            fill=MUTED,
        )
    )
    height = boundary_y + 60
    tags = sorted({tag for attempt in BATCH_ATTEMPTS for tag in attempt.tags})
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="bs-title bs-desc">'
        f'<title id="bs-title">Status distribution and open wires across a batch</title>'
        f'<desc id="bs-desc">A two-column panel: on the left the {len(summary.status_counts)} '
        f"overall statuses with their counts across {summary.total} evaluated attempts and open "
        f"findings by craft family; on the right {len(gaps)} practices ranked by how often the "
        f"batch left them open, with a band naming the practices never left open. The attempts "
        f"declare the tags {', '.join(tags)}.</desc>"
        f'<rect width="100%" height="100%" fill="{PAPER}"/>'
        f"{''.join(body)}</svg>"
    )
