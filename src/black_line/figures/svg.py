"""SVG primitives, palette, and layout constants for Black Line figures.

Font sizes here are canvas units, not points. What a reader actually sees is
the unit size scaled by the page the figure prints on, so every drawing helper
takes a ``floor`` derived from its canvas by
:func:`black_line.figures.legibility.min_font_units`. The floor is clamped
rather than advisory: a layout that needs text below it has too much text for
the width it is allotted, and the clamp turns that into a visible collision
instead of an invisible label.
"""

from __future__ import annotations

import html
from collections.abc import Callable
from functools import partial
from pathlib import Path

from black_line import BLACK_PRACTICES, __version__
from black_line.figures.legibility import (
    COVER_WIDTH_FRACTION,
    min_font_units,
    page_geometry,
)

#: Cover marker version, derived from the package version so a bump cannot
#: leave the cover silently claiming an older method.
SHORT_VERSION = ".".join(__version__.split(".")[:2])

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
#: The page these figures are scaled into, read from the same manuscript config
#: the renderer reads, so a geometry change moves the legibility floor with it.
PAGE = page_geometry(
    (_PROJECT_ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8")
)

COLS = 4
CARD_W = 300
CARD_H = 270
CARD_GAP_X = 325
CARD_GAP_Y = 295
GRID_X = 78
GRID_Y = 205
ROWS = (len(BLACK_PRACTICES) + COLS - 1) // COLS
WIDTH = 1400
FOOTER_Y = GRID_Y + ROWS * CARD_GAP_Y + 30
HEIGHT = FOOTER_Y + 110


def canvas_min_font(canvas_width: float, width_fraction: float = 1.0) -> int:
    """Smallest legible font, in canvas units, for a canvas of this width."""

    return min_font_units(canvas_width, width_fraction * PAGE.text_width_pt)


#: Font floor for the standard full-width figure canvas.
MIN_FONT = canvas_min_font(WIDTH)
#: The cover prints at the renderer's fixed title-page width on a wider canvas,
#: so it carries its own, larger floor.
COVER_WIDTH = 1800
COVER_MIN_FONT = canvas_min_font(COVER_WIDTH, COVER_WIDTH_FRACTION)
PAPER = "#f5e6d3"
PANEL = "#fffaf2"
INK = "#211c1b"
MUTED = "#5a504a"
GRID = "#cbbeaf"
BLACK = "#2d2d2d"
PALE = "#eadfd1"
PURPLE = "#4a148c"
TEAL = "#00796b"
RED = "#b42318"
SIENNA = "#8b4513"
#: General-purpose white for text on dark backgrounds and rect fills.
WHITE = "#ffffff"
#: Amber for intermediate/attention states (NEEDS_EVIDENCE, VERIFICATION, stale).
AMBER = "#b45309"
#: Crimson for critical/rework states (NEEDS_REWORK, detection fails).
CRIMSON = "#b91c1c"
#: Dark red stroke accent paired with CRIMSON fills.
DARK_RED = "#7f1d1d"
#: Warm pale tone for card fills on dark panels.
WARM_PALE = "#d6c7ba"
#: Warm off-white for card fills inside operating-loop nodes.
CREAM = "#fffdf8"
#: Sand tone for non-applicable cell backgrounds in heatmaps.
SAND = "#f2ebe0"
#: Cool grey for tag chip fills in the evidence matrix.
COOL_GREY = "#f4f6f7"
#: Mint for evidence-label chip fills in the evidence matrix.
MINT = "#e4f2ef"
#: Family accent: Framing (dark teal).
FRAMING_TEAL = "#0f766e"
#: Family accent: Traceability (blue).
TRACE_BLUE = "#1d4ed8"
#: Family accent: Method (violet).
METHOD_PURPLE = "#7c3aed"
#: Family accent: Communication (teal).
COMM_TEAL = "#0e7490"
#: Family accent: Stewardship (olive green).
STEWARD_GREEN = "#4d7c0f"
BODY_FONT = "Arial,Helvetica,sans-serif"
TITLE_FONT = "Georgia,Times New Roman,serif"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def text(
    x: float,
    y: float,
    value: str,
    *,
    size: int = 18,
    fill: str = INK,
    weight: str = "400",
    family: str = BODY_FONT,
    italic: bool = False,
    anchor: str | None = None,
    floor: int = MIN_FONT,
) -> str:
    size = max(size, floor)
    attrs = [
        f'x="{x}"',
        f'y="{y}"',
        f'fill="{fill}"',
        f'font-family="{family}"',
        f'font-size="{size}px"',
        f'font-weight="{weight}"',
    ]
    if italic:
        attrs.append('font-style="italic"')
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    return f"<text {' '.join(attrs)}>{esc(value)}</text>"


def headline(
    x: float,
    y: float,
    value: str,
    *,
    size: int = 28,
    fill: str = INK,
    floor: int = MIN_FONT,
) -> str:
    """Use an editorial serif for visual hierarchy without external assets."""

    return text(
        x,
        y,
        value,
        size=size,
        fill=fill,
        weight="700",
        family=TITLE_FONT,
        italic=True,
        floor=floor,
    )


def rect(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str = PANEL,
    stroke: str = GRID,
    dash: bool = False,
) -> str:
    dashed = ' stroke-dasharray="8 7"' if dash else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" stroke="{stroke}" stroke-width="1.6"{dashed}/>'


def wrap(value: str, width: int = 40) -> list[str]:
    """Deterministic greedy word wrap for card body text."""

    lines: list[str] = []
    current = ""
    for word in value.split():
        candidate = (current + " " + word).strip()
        if len(candidate) > width and current:
            lines.append(current)
            current = word
        else:
            current = candidate
    lines.append(current)
    return lines


def line(
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    *,
    stroke: str = MUTED,
    width: float = 1.8,
    dash: bool = False,
) -> str:
    dashed = ' stroke-dasharray="7 6"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{width}"{dashed} marker-end="url(#arrow)"/>'


def pill(
    x: float,
    y: float,
    w: float,
    h: float,
    label: str,
    *,
    fill: str,
    stroke: str,
    tfill: str = "white",
    size: int = 15,
    floor: int = MIN_FONT,
) -> str:
    size = max(size, floor)
    r = h / 2
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.8"/>'
        + f'<text x="{x + w / 2}" y="{y + h / 2 + size / 3}" fill="{tfill}" text-anchor="middle" font-family="{BODY_FONT}" font-size="{size}px" font-weight="700">{esc(label)}</text>'
    )


def canvas_writers(
    canvas_width: float, width_fraction: float = 1.0
) -> tuple[Callable[..., str], Callable[..., str], Callable[..., str], int]:
    """Return ``text``/``headline``/``pill`` bound to one canvas's font floor.

    Builders that derive their canvas from content use this so the floor grows
    with the canvas instead of being restated as a literal.
    """

    floor = canvas_min_font(canvas_width, width_fraction)
    return (
        partial(text, floor=floor),
        partial(headline, floor=floor),
        partial(pill, floor=floor),
        floor,
    )


def _defs() -> str:
    markers = []
    for marker_id, colour in (
        ("arrow", MUTED),
        ("arrow_teal", TEAL),
        ("arrow_purple", PURPLE),
        ("arrow_red", RED),
    ):
        markers.append(
            f'<marker id="{marker_id}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
            f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{colour}"/></marker>'
        )
    return f"<defs>{''.join(markers)}</defs>"


#: Deterministic status colours keyed by enum value, so a renamed enum shows up.
STATUS_FILL = {
    "ALIGNED": TEAL,
    "NEEDS_EVIDENCE": AMBER,
    "NEEDS_REWORK": CRIMSON,
    "OUTSIDE_SCOPE": MUTED,
}

#: A one-letter status channel drawn on top of the fill, so a status grid
#: still reads when the colour does not (greyscale printing, colour vision
#: deficiency). The glyph repeats the fill; it never adds a distinction the
#: colour does not already make.
STATUS_GLYPH = {
    "ALIGNED": "A",
    "NEEDS_EVIDENCE": "E",
    "NEEDS_REWORK": "R",
    "OUTSIDE_SCOPE": "O",
}

#: Deterministic family accent colours keyed by PracticeKind value.
FAMILY_FILL = {
    "FRAMING": FRAMING_TEAL,
    "TRACEABILITY": TRACE_BLUE,
    "METHOD": METHOD_PURPLE,
    "VERIFICATION": AMBER,
    "COMMUNICATION": COMM_TEAL,
    "STEWARDSHIP": STEWARD_GREEN,
}
