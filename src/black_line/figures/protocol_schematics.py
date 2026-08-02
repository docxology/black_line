"""Protocol schematic figures (status path, operating loop, claim layers)."""

from __future__ import annotations

from black_line import (
    AssessmentStatus,
    PracticeStatus,
)
from black_line.figures.svg import (
    BLACK,
    CREAM,
    CRIMSON,
    DARK_RED,
    GRID,
    INK,
    MUTED,
    PALE,
    PAPER,
    PANEL,
    PURPLE,
    RED,
    SIENNA,
    STATUS_FILL,
    TEAL,
    TITLE_FONT,
    WARM_PALE,
    WHITE,
    _defs,
    headline,
    line,
    pill,
    rect,
    text,
    wrap,
)


def status_path_svg() -> str:
    """The staged evaluator decision path, keyed to the package enums."""

    practice_statuses = [status.value for status in PracticeStatus]
    assessment_statuses = [status.value for status in AssessmentStatus]
    width = 1400
    body = [
        _defs(),
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(64, 58, "How evaluate_work maps declarations to a review status"),
        text(
            64,
            88,
            "A staged pipeline: normalize intake, match practices by tag, score each, then take the most demanding status.",
            size=15,
            fill=MUTED,
        ),
        text(
            64,
            114,
            f"DERIVED FROM EVALUATOR RULES · {len(practice_statuses)} PRACTICE STATUSES · {len(assessment_statuses)} ASSESSMENT STATUSES",
            size=11,
            fill=MUTED,
            weight="700",
        ),
    ]
    stages = [
        (
            "Stage 1",
            "Intake normalization",
            "Malformed tags, labels, dates become notes, not crashes.",
        ),
        (
            "Stage 2",
            "Freshness partition",
            "Dated evidence splits into fresh and stale at the review date.",
        ),
        (
            "Stage 3",
            "Tag matching",
            "Select practices whose tags intersect the attempt's tags.",
        ),
        (
            "Stage 4",
            "Scoring + aggregation",
            "Score each applicable practice, then take the most demanding status.",
        ),
    ]
    sx = 70
    sy = 175
    sw = 330
    sh = 168
    stage_gap = 196
    for index, (tag, name, note) in enumerate(stages):
        x = sx
        y = sy + index * stage_gap
        body.append(rect(x, y, sw, sh, fill=PANEL, stroke=BLACK))
        body.append(text(x + 18, y + 34, tag, size=16, fill=TEAL, weight="700"))
        for li, ln in enumerate(wrap(name, 22)):
            body.append(text(x + 18, y + 66 + li * 24, ln, size=18, weight="700"))
        for li, ln in enumerate(wrap(note, 32)):
            body.append(text(x + 18, y + 116 + li * 21, ln, size=16, fill=MUTED))
        if index < len(stages) - 1:
            body.append(
                line(
                    x + sw / 2,
                    y + sh,
                    x + sw / 2,
                    y + stage_gap,
                    stroke=BLACK,
                    width=2.2,
                )
            )
    branch_x = 418
    branch_w = 332
    # Branch: blocking description -> NEEDS_REWORK
    body.append(line(sx + sw, sy + 60, branch_x, sy + 62, stroke=CRIMSON, dash=True))
    body.append(
        pill(
            branch_x,
            sy + 38,
            branch_w,
            48,
            "blank desc -> NEEDS_REWORK",
            fill=STATUS_FILL["NEEDS_REWORK"],
            stroke=DARK_RED,
            size=16,
        )
    )
    # Branch: malformed custom registry fails closed before any scoring.
    body.append(line(sx + sw, sy + 118, branch_x, sy + 120, stroke=CRIMSON, dash=True))
    body.append(
        pill(
            branch_x,
            sy + 96,
            branch_w,
            48,
            "malformed registry -> NEEDS_REWORK",
            fill=STATUS_FILL["NEEDS_REWORK"],
            stroke=DARK_RED,
            size=16,
        )
    )
    # Branch: no applicable practice -> OUTSIDE_SCOPE
    body.append(
        line(
            sx + sw,
            sy + 3 * stage_gap + 40,
            branch_x,
            sy + 3 * stage_gap + 40,
            stroke=MUTED,
            dash=True,
        )
    )
    body.append(
        pill(
            branch_x,
            sy + 3 * stage_gap + 16,
            branch_w,
            48,
            "no match -> OUTSIDE_SCOPE",
            fill=STATUS_FILL["OUTSIDE_SCOPE"],
            stroke=INK,
            size=16,
        )
    )
    # Right column: per-practice statuses and rules
    rx = 760
    body.append(text(rx, 175, "Per-practice status", size=19, fill=BLACK, weight="700"))
    rules = {
        "ALIGNED": "all required labels declared fresh",
        "NEEDS_EVIDENCE": "no usable declaration, or only stale gaps",
        "NEEDS_REWORK": "required labels missing beyond stale refreshes",
    }
    for index, status in enumerate(practice_statuses):
        y = 200 + index * 86
        body.append(
            pill(
                rx,
                y,
                266,
                48,
                status,
                fill=STATUS_FILL.get(status, MUTED),
                stroke=INK,
                size=16,
            )
        )
        for li, ln in enumerate(wrap(rules.get(status, ""), 30)):
            body.append(text(rx + 286, y + 22 + li * 22, ln, size=16, fill=INK))
    # Aggregation box
    ay = 200 + 3 * 86 + 30
    body.append(rect(rx, ay, 570, 112, fill=PALE, stroke=BLACK))
    body.append(
        text(
            rx + 18,
            ay + 32,
            "Overall = most demanding per-practice status",
            size=18,
            weight="700",
        )
    )
    body.append(
        text(
            rx + 18,
            ay + 62,
            "NEEDS_REWORK > NEEDS_EVIDENCE > ALIGNED;",
            size=16,
            fill=MUTED,
        )
    )
    body.append(
        text(
            rx + 18,
            ay + 88,
            "empty findings -> OUTSIDE_SCOPE.",
            size=16,
            fill=MUTED,
        )
    )
    # Assessment status legend
    ly = ay + 158
    body.append(text(rx, ly, "Assessment statuses", size=19, fill=BLACK, weight="700"))
    for index, status in enumerate(assessment_statuses):
        y = ly + 26 + index * 58
        body.append(
            pill(
                rx,
                y,
                266,
                46,
                status,
                fill=STATUS_FILL.get(status, MUTED),
                stroke=INK,
                size=16,
            )
        )
    body.append(
        text(
            rx + 300,
            ly + 26 + 42,
            "The status describes declaration coverage;",
            size=16,
            fill=MUTED,
        )
    )
    body.append(
        text(
            rx + 300,
            ly + 26 + 66,
            "it never becomes truth or permission.",
            size=16,
            fill=MUTED,
        )
    )
    # Derive the canvas height from the drawn content so neither column can be
    # clipped and no dead band accumulates when a column grows or shrinks.
    left_bottom = sy + (len(stages) - 1) * stage_gap + sh
    right_bottom = ly + 26 + (len(assessment_statuses) - 1) * 58 + 46
    height = max(left_bottom, right_bottom) + 50
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Staged evaluator decision path">{"".join(body)}</svg>'


def operating_loop_svg() -> str:
    """Show the smallest honest loop and its explicit epistemic boundary."""

    width, height = 1400, 860
    body = [
        _defs(),
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(64, 58, "The smallest honest loop"),
        text(
            64,
            88,
            "Frame the decision, declare what can be inspected, evaluate the record, repair the gap, and archive the trail.",
            size=15,
            fill=MUTED,
        ),
        text(
            64,
            114,
            "POSITIVE OPERATING DISCIPLINE · THE LOOP GUIDES REVIEW; IT DOES NOT CERTIFY THE WORLD",
            size=11,
            fill=MUTED,
            weight="700",
        ),
        rect(50, 145, 890, 660, fill=PANEL, stroke=GRID),
        rect(960, 145, 400, 660, fill=BLACK, stroke=BLACK),
    ]

    # The slightly irregular path is intentional: a living review loop, not a
    # corporate process chevron. Every arrow is still deterministic and legible.
    loop_segments = (
        ("M 330 324 C 338 276 344 250 355 242", PURPLE, "arrow_purple"),
        ("M 565 242 C 615 244 641 274 670 324", TEAL, "arrow_teal"),
        ("M 780 382 C 772 433 742 471 695 500", PURPLE, "arrow_purple"),
        ("M 565 556 C 525 575 485 574 445 559", TEAL, "arrow_teal"),
        ("M 335 502 C 291 468 263 424 220 382", PURPLE, "arrow_purple"),
    )
    for path_data, colour, marker in loop_segments:
        body.append(
            f'<path d="{path_data}" fill="none" stroke="{colour}" stroke-width="4" stroke-linecap="round" marker-end="url(#{marker})"/>'
        )

    # Center question: the decision is the organising object, not the score.
    body.append(
        '<circle cx="500" cy="382" r="92" fill="#2d2d2d" stroke="#4a148c" stroke-width="4"/>'
    )
    body.append(
        text(
            500,
            365,
            "CAN THIS CHANGE",
            size=16,
            fill=PAPER,
            weight="700",
            anchor="middle",
        )
    )
    body.append(
        text(
            500,
            391,
            "the decision?",
            size=22,
            fill=WHITE,
            weight="700",
            family=TITLE_FONT,
            italic=True,
            anchor="middle",
        )
    )
    body.append(
        text(
            500,
            418,
            "keep the smallest",
            size=16,
            fill=WARM_PALE,
            anchor="middle",
        )
    )
    body.append(
        text(
            500,
            442,
            "method",
            size=16,
            fill=WARM_PALE,
            anchor="middle",
        )
    )

    nodes = (
        (110, 270, "01", "FRAME", "object · decision · boundary", PURPLE),
        (345, 185, "02", "DECLARE", "labels · dates · falsifiers", TEAL),
        (670, 270, "03", "EVALUATE", "as_of · freshness · digest", PURPLE),
        (565, 500, "04", "REPAIR / REFRESH", "missing work · stale work", RED),
        (225, 500, "05", "ARCHIVE", "assessment · source trail", TEAL),
    )
    for x, y, number, label, note, accent in nodes:
        body.append(rect(x, y, 220, 112, fill=CREAM, stroke=accent))
        body.append(
            f'<rect x="{x}" y="{y}" width="220" height="8" rx="4" fill="{accent}"/>'
        )
        body.append(f'<circle cx="{x + 24}" cy="{y + 33}" r="13" fill="{accent}"/>')
        body.append(
            text(
                x + 24,
                y + 37,
                number,
                size=10,
                fill=CREAM,
                weight="700",
                anchor="middle",
            )
        )
        body.append(text(x + 46, y + 40, label, size=16, fill=accent, weight="700"))
        for index, line_value in enumerate(wrap(note, 20)):
            body.append(
                text(x + 18, y + 78 + index * 21, line_value, size=16, fill=MUTED)
            )

    body.extend(
        (
            text(78, 690, "Reading the loop", size=16, fill=TEAL, weight="700"),
            text(
                78,
                718,
                "A gap is a next action. A stale observation is a reason to rerun.",
                size=16,
                fill=MUTED,
            ),
            text(
                78,
                742,
                "A label alone is never a shortcut to truth.",
                size=16,
                fill=MUTED,
            ),
            f'<path d="M 78 764 C 230 748 375 776 540 760 S 760 772 900 754" fill="none" stroke="{PURPLE}" stroke-width="2" opacity="0.7"/>',
        )
    )

    # The dark panel is a compact reviewer ledger: what the package can pin
    # mechanically, and what remains outside its authority.
    body.extend(
        (
            headline(990, 193, "What gets pinned", size=24, fill=PAPER),
            text(
                990,
                226,
                "A compact record for the next reader",
                size=13,
                fill=WARM_PALE,
            ),
            text(990, 267, "INPUT", size=11, fill="#9ce0cc", weight="700"),
            text(
                990,
                291,
                "description + reviewed tags",
                size=16,
                fill=WHITE,
                weight="700",
            ),
            text(990, 323, "FRAME", size=11, fill="#cfb5e9", weight="700"),
            text(990, 347, "decision + boundary", size=16, fill=WHITE, weight="700"),
            text(990, 379, "EVIDENCE", size=11, fill="#9ce0cc", weight="700"),
            text(
                990,
                403,
                "source or observation behind labels",
                size=16,
                fill=WHITE,
                weight="700",
            ),
            text(990, 435, "METHOD", size=11, fill="#cfb5e9", weight="700"),
            text(
                990,
                459,
                "registry digest + schema",
                size=16,
                fill=WHITE,
                weight="700",
            ),
            text(990, 491, "TIME", size=11, fill="#9ce0cc", weight="700"),
            text(
                990,
                515,
                "as_of + freshness window",
                size=16,
                fill=WHITE,
                weight="700",
            ),
            '<line x1="990" y1="540" x2="1330" y2="540" stroke="#75685f" stroke-width="1.5"/>',
            rect(988, 555, 364, 186, fill="#5b2626", stroke=RED),
            text(
                1010,
                586,
                "OUTSIDE THE INSTRUMENT",
                size=11,
                fill="#ffb4a9",
                weight="700",
            ),
            text(1010, 618, "semantic truth", size=16, fill=WHITE, weight="700"),
            text(1010, 645, "source authenticity", size=16, fill=WHITE, weight="700"),
            text(1010, 672, "safety permission", size=16, fill=WHITE, weight="700"),
            text(
                1010,
                712,
                "The reviewer follows the trail.",
                size=13,
                fill="#ffd8d2",
                family=TITLE_FONT,
                italic=True,
            ),
        )
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="loop-title loop-desc"><title id="loop-title">The smallest honest Black Line review loop</title><desc id="loop-desc">Five-step loop from framing through declaration, evaluation, repair or refresh, and archiving, with a reviewer ledger and a boundary around semantic truth, source authenticity, and safety permission.</desc>{"".join(body)}</svg>'


def claim_layers_svg() -> str:
    """Show the layers a declaration-status instrument can and cannot reach."""

    width = 1400
    # Derived from the drawn content: the layer row plus the ALIGNED panel.
    panel_y, panel_h = 520, 160
    height = panel_y + panel_h + 40
    body = [
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
        headline(64, 58, "What the instrument can say—and what it cannot"),
        text(
            64,
            88,
            "Black Line structures the path from a decision to a reviewable record; it does not certify the world or grant authority.",
            size=15,
            fill=MUTED,
        ),
        text(
            64,
            114,
            "FIRST-PRINCIPLES MAP · DECLARATION STATUS IS NOT WORLD VALIDATION",
            size=11,
            fill=MUTED,
            weight="700",
        ),
    ]
    left = (
        (
            70,
            190,
            235,
            250,
            PURPLE,
            "01 · DECISION",
            "What choice could this work change?",
            "frame the object and boundary",
        ),
        (
            315,
            190,
            235,
            250,
            TEAL,
            "02 · PROCEDURE",
            "What is the smallest method that could inform it?",
            "name the method and failure path",
        ),
        (
            560,
            190,
            235,
            250,
            SIENNA,
            "03 · RECORD",
            "What can another reader inspect?",
            "trace sources, observations, and review",
        ),
    )
    right = (
        (
            860,
            190,
            235,
            250,
            RED,
            "04 · WORLD",
            "Are the source, observation, and inference adequate?",
            "requires domain and independent judgment",
        ),
        (
            1105,
            190,
            235,
            250,
            RED,
            "05 · AUTHORITY",
            "Is the work safe, lawful, or permitted?",
            "belongs to governance and refusal boundaries",
        ),
    )
    for x, y, w, h, accent, label, question, note in left + right:
        is_outside = accent == RED
        fill = "#f4e7df" if is_outside else PANEL
        body.append(rect(x, y, w, h, fill=fill, stroke=accent))
        body.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="9" rx="4" fill="{accent}"/>'
        )
        body.append(text(x + 18, y + 40, label, size=16, fill=accent, weight="700"))
        for index, line_value in enumerate(wrap(question, 21)):
            body.append(
                text(x + 18, y + 86 + index * 24, line_value, size=16, weight="700")
            )
        for index, line_value in enumerate(wrap(note, 21)):
            body.append(
                text(x + 18, y + 182 + index * 21, line_value, size=16, fill=MUTED)
            )

    for x1, x2 in ((290, 315), (535, 560), (780, 860), (1080, 1105)):
        colour = RED if x1 == 780 else MUTED
        body.append(
            f'<line x1="{x1}" y1="315" x2="{x2}" y2="315" stroke="{colour}" stroke-width="3" stroke-dasharray="8 7" marker-end="url(#arrow)"/>'
        )
    body.insert(1, _defs())
    body.extend(
        (
            f'<line x1="820" y1="160" x2="820" y2="470" stroke="{RED}" stroke-width="2.5" stroke-dasharray="10 8"/>',
            text(
                820,
                150,
                "BLACK LINE STOPS HERE",
                size=12,
                fill=RED,
                weight="700",
                anchor="middle",
            ),
            rect(70, panel_y, 1270, panel_h, fill=BLACK, stroke=BLACK),
            text(98, 560, "What ALIGNED means", size=15, fill="#f7eee4", weight="700"),
            text(
                98,
                595,
                "For every applicable practice, the required labels were declared as fresh under the chosen review date.",
                size=17,
                fill=WHITE,
                weight="700",
            ),
            text(
                98,
                628,
                "What it does not mean: the source is authentic, the inference is sound, the result generalizes, or the work is permitted.",
                size=14,
                fill=WARM_PALE,
            ),
            text(
                98,
                656,
                "The reviewer still has to follow the trail.",
                size=13,
                fill="#ffd8d2",
                family=TITLE_FONT,
                italic=True,
            ),
        )
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="layers-title layers-desc"><title id="layers-title">What Black Line can say and what it cannot</title><desc id="layers-desc">Five layers separate decision, procedure, and record, which Black Line structures, from world adequacy and authority, which remain outside its scope. A bottom note defines ALIGNED as fresh declaration coverage rather than truth or permission.</desc>{"".join(body)}</svg>'
