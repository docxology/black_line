"""The detection plate: every structural check, run against a planted defect.

The manuscript's standard for the invariants battery is proof of detection —
a check that has only ever seen a good registry has not been shown to work.
This figure is that standard drawn: the shipped registry on the top row, then
one planted registry per check, with the real battery run over each and every
outcome read off the returned :class:`~black_line.RegistryCheck` records.

The matrix is deliberately not diagonal. Two plants cannot avoid tripping a
further check. A kind that is not a ``PracticeKind`` member drops its practice
out of family coverage and breaks canonical serialization, so that row fails
three checks; a ``None`` tag field is both unreachable and unserializable. Those
cells are drawn, because a figure showing a clean diagonal would be describing a
battery this project does not ship.
"""

from __future__ import annotations

from black_line.figures.scenarios import detection_check_names, detection_rows
from black_line.figures.svg import (
    BLACK,
    BODY_FONT,
    CRIMSON,
    GRID,
    INK,
    MUTED,
    PALE,
    PANEL,
    PAPER,
    TEAL,
    WHITE,
    canvas_writers,
    esc,
)

#: Redundant to the fill, so the plate reads in greyscale and under colour
#: vision deficiency: every cell carries a letter as well as a colour.
PASS_GLYPH = "P"
FAIL_GLYPH = "F"
FAIL_FILL = CRIMSON

LABEL_X = 64
GRID_X = 500
CELL_W = 116
CELL_H = 62
GRID_Y = 430
MARGIN_W = 200


#: One row of the detection matrix: ``(row label, what was planted, results)``.
DetectionRow = tuple[str, str, tuple[tuple[str, bool], ...]]


def detection_collateral(
    rows: tuple[DetectionRow, ...] | None = None,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Plants that fail a check other than the one they target, and which."""

    extra: list[tuple[str, tuple[str, ...]]] = []
    for target, _planted, results in (rows or detection_rows())[1:]:
        others = tuple(
            name for name, passed in results if not passed and name != target
        )
        if others:
            extra.append((target, others))
    return tuple(extra)


def detection_targets_all_fire(
    rows: tuple[DetectionRow, ...] | None = None,
) -> bool:
    """True when every planted registry fails the check it was built to fail."""

    return all(
        dict(results)[target] is False
        for target, _planted, results in (rows or detection_rows())[1:]
    )


def invariant_detection_svg(
    rows: tuple[DetectionRow, ...] | None = None,
) -> str:
    """Draw the battery against the shipped registry and every planted defect.

    ``rows`` overrides the executed matrix, which is what lets a test prove the
    plate follows its data rather than agreeing with it by construction.
    """

    checks = detection_check_names()
    rows = rows or detection_rows()
    width = GRID_X + len(checks) * CELL_W + MARGIN_W
    text, headline, _pill, floor = canvas_writers(width)
    collateral = detection_collateral(rows)
    body = [
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(
            LABEL_X, 58, "Every check, shown failing on a registry built to break it"
        ),
        text(
            LABEL_X,
            88,
            "Each row runs the whole battery once. The top row is the shipped registry; the rest each carry one planted defect.",
            size=17,
            fill=MUTED,
        ),
        text(
            LABEL_X,
            114,
            f"EXECUTED BATTERY · {len(checks)} CHECKS × {len(rows)} REGISTRIES · "
            f"{len(rows) * len(checks)} OUTCOMES · READ OFF RegistryCheck RECORDS",
            size=17,
            fill=MUTED,
            weight="700",
        ),
        text(
            LABEL_X,
            152,
            "A boxed cell is the check the row was planted to break. A green check that never saw a bad registry proves nothing.",
            size=17,
            fill=MUTED,
        ),
    ]
    for index, name in enumerate(checks):
        cx = GRID_X + index * CELL_W + CELL_W / 2
        body.append(
            f'<text x="{cx}" y="{GRID_Y - 16}" fill="{INK}" font-family="{BODY_FONT}" '
            f'font-size="{floor}px" font-weight="700" text-anchor="start" '
            f'transform="rotate(-38 {cx} {GRID_Y - 16})">{esc(name)}</text>'
        )
    body.append(
        text(
            GRID_X + len(checks) * CELL_W + 24,
            GRID_Y - 16,
            "checks failed",
            size=16,
            fill=MUTED,
            weight="700",
        )
    )

    for row_index, (label, planted, results) in enumerate(rows):
        y = GRID_Y + row_index * CELL_H
        body.append(
            f'<rect x="{LABEL_X}" y="{y + 2}" width="{GRID_X - LABEL_X - 20}" '
            f'height="{CELL_H - 6}" rx="10" fill="{PANEL if row_index % 2 == 0 else PALE}" '
            f'stroke="{GRID}" stroke-width="1"/>'
        )
        body.append(text(LABEL_X + 14, y + 26, label, size=16, weight="700"))
        body.append(text(LABEL_X + 14, y + 48, planted, size=16, fill=MUTED))
        failures = 0
        for col_index, (name, passed) in enumerate(results):
            x = GRID_X + col_index * CELL_W
            fill = TEAL if passed else FAIL_FILL
            if not passed:
                failures += 1
            body.append(
                f'<rect x="{x + 4}" y="{y + 4}" width="{CELL_W - 8}" height="{CELL_H - 12}" '
                f'rx="8" fill="{fill}"/>'
            )
            body.append(
                text(
                    x + CELL_W / 2,
                    y + CELL_H / 2 + 2,
                    PASS_GLYPH if passed else FAIL_GLYPH,
                    size=18,
                    fill=WHITE,
                    weight="700",
                    anchor="middle",
                )
            )
            if row_index and name == label:
                body.append(
                    f'<rect x="{x + 1}" y="{y + 1}" width="{CELL_W - 2}" height="{CELL_H - 6}" '
                    f'rx="10" fill="none" stroke="{INK}" stroke-width="2.5" stroke-dasharray="5 4"/>'
                )
        body.append(
            text(
                GRID_X + len(checks) * CELL_W + 24,
                y + CELL_H / 2 + 4,
                f"{failures} of {len(checks)}",
                size=16,
                weight="700",
                fill=INK if failures else MUTED,
            )
        )

    legend_y = GRID_Y + len(rows) * CELL_H + 42
    legend_x = GRID_X
    for glyph, fill, caption in (
        (PASS_GLYPH, TEAL, "check passed"),
        (FAIL_GLYPH, FAIL_FILL, "check failed"),
    ):
        body.append(
            f'<rect x="{legend_x}" y="{legend_y - 17}" width="22" height="22" rx="5" fill="{fill}"/>'
        )
        body.append(
            f'<text x="{legend_x + 11}" y="{legend_y - 2}" fill="{WHITE}" text-anchor="middle" '
            f'font-family="{BODY_FONT}" font-size="{floor}px" font-weight="700">{esc(glyph)}</text>'
        )
        body.append(
            text(legend_x + 32, legend_y, caption, size=17, fill=INK, weight="700")
        )
        legend_x += 260

    collateral_y = legend_y + 40
    body.append(
        text(LABEL_X, collateral_y, "Collateral", size=17, fill=BLACK, weight="700")
    )
    if collateral:
        body.append(
            text(
                LABEL_X + 150,
                collateral_y,
                f"{len(collateral)} of the {len(rows) - 1} plants also fail a check they were not aimed at:",
                size=17,
                fill=MUTED,
            )
        )
        for index, (target, others) in enumerate(collateral):
            body.append(
                text(
                    LABEL_X + 150,
                    collateral_y + 24 + index * 24,
                    f"· the {target} plant also fails " + " and ".join(others),
                    size=17,
                    fill=MUTED,
                )
            )
        collateral_bottom = collateral_y + 24 + len(collateral) * 24
    else:
        body.append(
            text(
                LABEL_X + 150,
                collateral_y,
                "no plant fails a check it was not aimed at.",
                size=17,
                fill=MUTED,
            )
        )
        collateral_bottom = collateral_y

    boundary_y = collateral_bottom + 40
    body.append(
        text(LABEL_X, boundary_y, "Boundary", size=17, fill=BLACK, weight="700")
    )
    body.append(
        text(
            LABEL_X + 150,
            boundary_y,
            "A firing check shows the battery can reject a malformed registry. It says nothing about whether the",
            size=17,
            fill=MUTED,
        )
    )
    body.append(
        text(
            LABEL_X + 150,
            boundary_y + 24,
            "practices are the right ones, whether their evidence is adequate, or whether any work was done well.",
            size=17,
            fill=MUTED,
        )
    )
    height = boundary_y + 60
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="det-title det-desc">'
        f'<title id="det-title">Structural checks against planted counter-examples</title>'
        f'<desc id="det-desc">A {len(rows)} by {len(checks)} matrix. The top row is the shipped '
        f"registry and every cell passes. Each remaining row is a registry carrying one planted defect, "
        f"and the check that defect targets is boxed and failing. {len(collateral)} rows fail a second "
        f"check as well, because the planted value also breaks canonical serialization.</desc>"
        f"{''.join(body)}</svg>"
    )
