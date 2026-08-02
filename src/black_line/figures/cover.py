"""Cover art figure."""

from functools import partial

from black_line.figures.svg import (
    BLACK,
    COVER_MIN_FONT,
    COVER_WIDTH,
    INK,
    MUTED,
    PAPER,
    PURPLE,
    RED,
    SHORT_VERSION,
    SIENNA,
    TEAL,
    TITLE_FONT,
    headline as _headline,
    text as _text,
)


#: The cover prints at the renderer's title-page width, which is narrower than
#: a full-width manuscript embed, so it carries the larger of the two floors.
text = partial(_text, floor=COVER_MIN_FONT)
headline = partial(_headline, floor=COVER_MIN_FONT)


def cover_art_svg() -> str:
    """Render the cover's thesis metaphor: noise becoming a followable line."""

    width, height = COVER_WIDTH, 1100
    body = [
        f'<rect width="{width}" height="{height}" fill="{PAPER}"/>',
        text(
            92, 96, "BLACK LINE · A POSITIVE METHOD", size=14, fill=PURPLE, weight="700"
        ),
        headline(92, 154, "A line that can be followed", size=44),
        text(
            96,
            194,
            "From intention to inspection to handoff",
            size=20,
            fill=MUTED,
            family=TITLE_FONT,
            italic=True,
        ),
        text(
            96,
            236,
            "The work becomes reviewable where another reader can pick up the trail.",
            size=15,
            fill=MUTED,
        ),
        text(
            1510,
            96,
            f"{SHORT_VERSION} · LIVING METHOD",
            size=12,
            fill=BLACK,
            weight="700",
            anchor="end",
        ),
        f'<path d="M 96 266 C 350 248 620 278 890 256 S 1410 270 1700 248" fill="none" stroke="{PURPLE}" stroke-width="3" opacity="0.72"/>',
    ]

    # The left field is deliberately crowded: unframed intention has many
    # possible directions. The central line reduces that ambiguity by making
    # each transition inspectable.
    for index in range(18):
        y = 520 + index * 19
        bend = 24 + (index % 4) * 17
        body.append(
            f'<path d="M 110 {y} C 220 {y - bend} 250 {y + bend} 365 {y - 12} '
            f'S 450 {y + 52} 548 {y + (index % 3) * 12 - 24}" fill="none" '
            f'stroke="{BLACK}" stroke-width="{1.3 + (index % 3) * 0.45:.2f}" opacity="{0.16 + (index % 5) * 0.035:.3f}"/>'
        )

    main_path = "M 125 790 C 278 760 362 602 520 660 C 670 718 744 486 900 540 C 1060 594 1120 374 1290 442 C 1440 500 1562 326 1712 354"
    body.extend(
        (
            f'<path d="{main_path}" fill="none" stroke="{INK}" stroke-width="15" stroke-linecap="round"/>',
            f'<path d="M 520 660 C 670 718 744 486 900 540" fill="none" stroke="{PURPLE}" stroke-width="5" stroke-linecap="round"/>',
            f'<path d="M 900 540 C 1060 594 1120 374 1290 442" fill="none" stroke="{TEAL}" stroke-width="5" stroke-linecap="round"/>',
            f'<path d="M 1290 442 C 1440 500 1562 326 1712 354" fill="none" stroke="{SIENNA}" stroke-width="5" stroke-linecap="round"/>',
            f'<path d="M 535 530 C 690 356 940 340 1080 492 C 1150 568 1050 690 895 676" fill="none" stroke="{SIENNA}" stroke-width="5" stroke-linecap="round" stroke-dasharray="12 16" opacity="0.78"/>',
            f'<path d="M 92 920 C 430 900 690 938 970 916 S 1450 932 1708 902" fill="none" stroke="{RED}" stroke-width="3" stroke-dasharray="15 13" opacity="0.85"/>',
            text(
                96,
                960,
                "RED LINE remains a boundary, not a score",
                size=13,
                fill=RED,
                weight="700",
            ),
            text(
                1705,
                960,
                "the reviewer follows the trail",
                size=14,
                fill=SIENNA,
                family=TITLE_FONT,
                italic=True,
                anchor="end",
            ),
        )
    )

    stations = (
        (520, 660, "FRAME", PURPLE, "question"),
        (708, 601, "METHOD", PURPLE, "smallest"),
        (900, 540, "EVIDENCE", TEAL, "inspectable"),
        (1290, 442, "REVIEW", TEAL, "second reader"),
        (1578, 367, "HANDOFF", SIENNA, "next action"),
    )
    for x, y, label, accent, note in stations:
        body.append(
            f'<circle cx="{x}" cy="{y}" r="22" fill="{PAPER}" stroke="{accent}" stroke-width="6"/>'
        )
        body.append(f'<circle cx="{x}" cy="{y}" r="7" fill="{accent}"/>')
        body.append(
            text(x, y - 46, label, size=21, fill=accent, weight="700", anchor="middle")
        )
        body.append(text(x, y + 54, note, size=21, fill=MUTED, anchor="middle"))

    body.extend(
        (
            text(
                122,
                1030,
                "noise → frame → method → evidence → review → handoff",
                size=15,
                fill=BLACK,
                weight="700",
            ),
            text(
                1675,
                1030,
                "BLACK LINE",
                size=15,
                fill=PURPLE,
                weight="700",
                anchor="end",
            ),
        )
    )
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="cover-title cover-desc"><title id="cover-title">Black Line: a line that can be followed</title><desc id="cover-desc">A dense field of unresolved marks narrows into one inspectable black line through frame, method, evidence, review, and handoff, with a warm human gesture and a red boundary.</desc>{"".join(body)}</svg>'
