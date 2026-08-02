"""Registry-map schematic figures (practices, taxonomy, evidence matrix)."""

from __future__ import annotations

from black_line import (
    BLACK_PRACTICES,
    PRACTICE_TAG_VOCABULARY,
    BlackPractice,
    PracticeKind,
)
from black_line.figures.svg import (
    BLACK,
    BODY_FONT,
    CARD_GAP_X,
    CARD_GAP_Y,
    CARD_H,
    CARD_W,
    COLS,
    COOL_GREY,
    CREAM,
    FOOTER_Y,
    GRID,
    GRID_X,
    GRID_Y,
    HEIGHT,
    INK,
    MIN_FONT,
    MINT,
    MUTED,
    PAPER,
    PANEL,
    PURPLE,
    ROWS,
    TEAL,
    WIDTH,
    FAMILY_FILL,
    esc,
    headline,
    rect,
    text,
    wrap,
)


def practice_wires_svg() -> str:
    body = [
        headline(64, 58, "Small wires make a review surface visible"),
        text(
            64,
            88,
            "Each practice names a review surface; a missing label requests work, not a judgment about intent.",
            size=15,
            fill=MUTED,
        ),
        text(
            64,
            116,
            "SOURCE-DRIVEN SCHEMATIC · REGISTRY DECLARATION ORDER · NOT A QUALITY OR TRUTH SCORE",
            size=11,
            fill=MUTED,
            weight="700",
        ),
        rect(50, 150, WIDTH - 100, ROWS * CARD_GAP_Y + 40, fill=PANEL),
        f'<path d="M 70 139 C 240 124 375 146 540 132 S 850 143 1040 129 S 1240 138 1330 126" fill="none" stroke="{PURPLE}" stroke-width="2.5" opacity="0.72"/>',
    ]
    for index, practice in enumerate(BLACK_PRACTICES):
        row, col = divmod(index, COLS)
        x = GRID_X + col * CARD_GAP_X
        y = GRID_Y + row * CARD_GAP_Y
        accent = FAMILY_FILL.get(practice.kind.value, BLACK)
        body.append(rect(x, y, CARD_W, CARD_H, fill=CREAM, stroke=accent))
        body.append(
            f'<rect x="{x}" y="{y}" width="{CARD_W}" height="8" rx="4" fill="{accent}"/>'
        )
        body.append(
            text(
                x + 18,
                y + 32,
                f"{index + 1:02d} · {practice.kind.value}",
                size=12,
                fill=accent,
                weight="700",
            )
        )
        for line_index, title_line in enumerate(wrap(practice.title, 28)):
            body.append(
                text(
                    x + 18, y + 66 + line_index * 24, title_line, size=17, weight="700"
                )
            )
        for line_index, wire_line in enumerate(wrap(practice.wire, 30)):
            body.append(
                text(x + 18, y + 124 + line_index * 21, wire_line, size=16, fill=MUTED)
            )
        body.append(
            text(x + 18, y + 216, "evidence", size=16, fill=accent, weight="700")
        )
        body.append(
            text(
                x + 18,
                y + 242,
                " · ".join(practice.required_evidence),
                size=16,
                fill=INK,
            )
        )
    # Family legend keyed to the shared FAMILY_FILL palette, so the card
    # accents carry the same family language as the taxonomy, matrix, and
    # heatmap siblings instead of an unrelated alternating scheme.
    legend_x = GRID_X
    body.append(
        text(legend_x, FOOTER_Y, "Craft families", size=16, fill=BLACK, weight="700")
    )
    legend_x += 132
    for kind in PracticeKind:
        accent = FAMILY_FILL.get(kind.value, BLACK)
        body.append(
            f'<rect x="{legend_x}" y="{FOOTER_Y - 15}" width="18" height="18" rx="4" fill="{accent}"/>'
        )
        body.append(
            text(legend_x + 26, FOOTER_Y, kind.value, size=16, fill=INK, weight="700")
        )
        legend_x += 46 + len(kind.value) * 10
    body.append(
        text(GRID_X, FOOTER_Y + 48, "Boundary", size=16, fill=BLACK, weight="700")
    )
    body.append(
        text(
            GRID_X + 106,
            FOOTER_Y + 48,
            "Black Line describes how to work well; it never grants permission to cross Red Line.",
            size=16,
            fill=MUTED,
        )
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-labelledby="title desc">
<title id="title">Small wires make a review surface visible</title>
<desc id="desc">{len(BLACK_PRACTICES)} positive Black Line practices drawn as cards in registry declaration order, color-keyed to {len(PracticeKind)} practice families, each naming a review surface and its required evidence.</desc>
<rect width="100%" height="100%" fill="{PAPER}"/>{"".join(body)}</svg>'''


def family_taxonomy_svg() -> str:
    """The registry grouped by craft family, with the reviewed tag vocabulary."""

    families: dict[str, list] = {kind.value: [] for kind in PracticeKind}
    for practice in BLACK_PRACTICES:
        families[practice.kind.value].append(practice)
    ordered = [kind.value for kind in PracticeKind]
    vocab = sorted(PRACTICE_TAG_VOCABULARY)
    col_w = 640
    col_x0 = 50
    col_gap = 20
    row_y0 = 190
    width = 1400
    # Deterministic vertical packing per column. Member rows carry three lines
    # of floor-sized text (title, tags, evidence), so the row pitch is derived
    # from that stack rather than from a smaller historical font.
    member_pitch = 76
    heights = {}
    for name in ordered:
        heights[name] = 72 + max(1, len(families[name])) * member_pitch
    columns: list[list[str]] = [[], []]
    col_heights = [row_y0, row_y0]
    for name in ordered:
        target = 0 if col_heights[0] <= col_heights[1] else 1
        columns[target].append(name)
        col_heights[target] += heights[name] + 26
    body = [
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(64, 58, "The registry as a taxonomy of practice families"),
        text(
            64,
            88,
            f"{len(BLACK_PRACTICES)} practices across {len(ordered)} families; each practice is reached by tags from a reviewed {len(vocab)}-tag vocabulary.",
            size=15,
            fill=MUTED,
        ),
        text(
            64,
            114,
            "SOURCE-DRIVEN SCHEMATIC · FAMILY COVERAGE AND TAG MEMBERSHIP ARE ENFORCED BY THE INVARIANTS",
            size=11,
            fill=MUTED,
            weight="700",
        ),
        text(
            64,
            152,
            "Tag vocabulary: " + "  ".join(vocab),
            size=17,
            fill=TEAL,
            weight="700",
        ),
    ]
    for ci, names in enumerate(columns):
        x = col_x0 + ci * (col_w + col_gap)
        y = row_y0
        for name in names:
            members = families[name]
            accent = FAMILY_FILL.get(name, BLACK)
            box_h = heights[name]
            body.append(rect(x, y, col_w, box_h, fill=PANEL, stroke=accent))
            body.append(
                f'<rect x="{x}" y="{y}" width="10" height="{box_h}" rx="5" fill="{accent}"/>'
            )
            body.append(text(x + 26, y + 38, name, size=19, fill=accent, weight="700"))
            body.append(
                f'<text x="{x + col_w - 18}" y="{y + 38}" fill="{MUTED}" text-anchor="end" '
                f'font-family="{BODY_FONT}" font-size="{MIN_FONT}px" font-weight="400">'
                f"{esc(f'{len(members)} practice' if len(members) == 1 else f'{len(members)} practices')}</text>"
            )
            for mi, practice in enumerate(members):
                py = y + 72 + mi * member_pitch
                body.append(text(x + 26, py, practice.title, size=17, weight="700"))
                body.append(
                    text(
                        x + 26,
                        py + 24,
                        "tags: " + " · ".join(sorted(practice.tags)),
                        size=16,
                        fill=MUTED,
                    )
                )
                body.append(
                    text(
                        x + 26,
                        py + 46,
                        "evidence: " + " · ".join(practice.required_evidence),
                        size=16,
                        fill=MUTED,
                    )
                )
            y += box_h + 26
    height = max(col_heights) + 60
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Registry taxonomy by craft family">{"".join(body)}</svg>'


def evidence_matrix_svg(practices: tuple[BlackPractice, ...] = BLACK_PRACTICES) -> str:
    """Show the registry's evidence contract without implying verification.

    ``practices`` is injected rather than read from the module so a test can
    render a larger registry and assert the derived canvas still contains it.
    """

    width = 1400
    row_y = 214
    # One row carries a two-line practice label and a chip strip at floor-sized
    # text; the pitch, the panel, and the canvas height are all derived from it,
    # so a registry edit cannot push the boundary sentence out of the viewBox.
    row_h = 60
    body = [
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(64, 58, "The registry's evidence-label contract"),
        text(
            64,
            88,
            "Each practice names labels a reviewer can look for; labels are not the underlying artifacts or their verification.",
            size=15,
            fill=MUTED,
        ),
        text(
            64,
            114,
            f"DERIVED FROM REGISTRY · {len(practices)} PRACTICES · {sum(len(p.required_evidence) for p in practices)} REQUIRED LABELS",
            size=11,
            fill=MUTED,
            weight="700",
        ),
        rect(
            50,
            145,
            width - 100,
            len(practices) * row_h + 66,
            fill=PANEL,
            stroke=GRID,
        ),
        text(78, 186, "practice", size=16, fill=MUTED, weight="700"),
        text(610, 186, "reviewed tags", size=16, fill=MUTED, weight="700"),
        text(930, 186, "required evidence labels", size=16, fill=MUTED, weight="700"),
    ]

    def chip(
        x: float, y: float, label: str, *, fill: str, stroke: str, tfill: str = INK
    ) -> float:
        chip_width = max(66, 20 + len(label) * MIN_FONT * 0.56)
        body.append(
            f'<rect x="{x}" y="{y}" width="{chip_width}" height="30" rx="15" fill="{fill}" stroke="{stroke}" stroke-width="1.2"/>'
        )
        body.append(
            f'<text x="{x + chip_width / 2}" y="{y + 21}" fill="{tfill}" text-anchor="middle" font-family="{BODY_FONT}" font-size="{MIN_FONT}px">{esc(label)}</text>'
        )
        return chip_width

    for index, practice in enumerate(practices):
        y = row_y + index * row_h
        accent = FAMILY_FILL.get(practice.kind.value, BLACK)
        body.append(
            f'<rect x="70" y="{y}" width="8" height="36" rx="4" fill="{accent}"/>'
        )
        body.append(
            text(
                94, y + 18, f"{index + 1:02d}  {practice.title}", size=16, weight="700"
            )
        )
        body.append(
            text(94, y + 40, practice.kind.value, size=16, fill=accent, weight="700")
        )
        x = 610
        for tag in sorted(practice.tags):
            x += chip(x, y + 6, tag, fill=COOL_GREY, stroke=GRID) + 6
        x = 930
        for label in practice.required_evidence:
            x += chip(x, y + 6, label, fill=MINT, stroke=TEAL) + 6

    legend_y = row_y + len(practices) * row_h + 46
    body.append(text(78, legend_y, "Boundary", size=16, fill=BLACK, weight="700"))
    for offset, sentence in enumerate(
        (
            "The evaluator can confirm that labels were declared and matched;",
            "it cannot confirm that a source is real, a test passed, or a claim is true.",
        )
    ):
        body.append(text(174, legend_y + offset * 24, sentence, size=16, fill=MUTED))
    height = legend_y + 24 + 44
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Black Line evidence contract matrix">{"".join(body)}</svg>'
