"""Rendered point size of figure text, derived from the page it prints on.

A figure is drawn on a canvas of $W$ drawing units and embedded at a declared
fraction of the text width. LaTeX scales the whole image to fit the declared
box, so a label drawn at $N$ canvas units prints at

$$N \\times \\frac{\\text{rendered width in points}}{W}.$$

Everything on the right-hand side is recoverable from sources this project
owns: the page geometry and the figure-occupancy fractions come from
``manuscript/config.yaml``, the declared embed width comes from the manuscript
markdown, and the canvas comes from the generated SVG. This module does that
arithmetic so the legibility floor is re-derived rather than restated, and so a
geometry change moves the floor instead of silently invalidating it.

The floor itself is a legibility contract, not a measurement: text below
:data:`MIN_RENDERED_PT` is present in the file and absent from the page. It
says nothing about whether the label is accurate.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "COVER_WIDTH_FRACTION",
    "MIN_RENDERED_PT",
    "FigureLegibility",
    "PageGeometry",
    "check_figure_legibility",
    "figure_legibility_report",
    "min_font_units",
    "page_geometry",
    "rendered_width_pt",
    "smallest_font_units",
    "svg_canvas",
]

#: TeX points per inch. This is the ``pt`` LaTeX reports for ``\textwidth``.
PT_PER_INCH = 72.27

#: ``article`` class default stock, which the rendered preamble uses.
PAPER_WIDTH_IN = 8.5
PAPER_HEIGHT_IN = 11.0

#: The smallest text that still reads at print scale. Below this a label is in
#: the file but not on the page, which makes the "shape and text repeat the
#: meaning" accessibility contract untrue rather than merely weak.
MIN_RENDERED_PT = 6.0

#: The renderer places the title-page cover at ``0.98\textwidth``
#: (``infrastructure/rendering/_pdf_title_page_images.py``). The cover is not a
#: manuscript embed, so its width is not declared in the markdown.
COVER_WIDTH_FRACTION = 0.98

_LENGTH_RE = re.compile(r"([-+]?\d*\.?\d+)\s*(in|cm|mm|pt)")
_FONT_SIZE_RE = re.compile(r'font-size="([\d.]+)px"')
_VIEWBOX_RE = re.compile(r'viewBox="0 0 ([\d.]+) ([\d.]+)"')


@dataclass(frozen=True)
class PageGeometry:
    """The text block a full-width figure is scaled into, in TeX points."""

    text_width_pt: float
    text_height_pt: float


def _length_in_inches(value: str) -> float:
    match = _LENGTH_RE.search(value)
    if not match:
        raise ValueError(f"unreadable LaTeX length: {value!r}")
    number = float(match.group(1))
    unit = match.group(2)
    if unit == "in":
        return number
    if unit == "cm":
        return number / 2.54
    if unit == "mm":
        return number / 25.4
    return number / PT_PER_INCH


def page_geometry(config_text: str) -> PageGeometry:
    """Derive the text block from the ``metadata.geometry`` string in config.

    Only the margin keys the project actually declares are honoured; an
    unreadable or absent geometry raises instead of falling back to a guess,
    because a wrong page size silently invalidates every point size below.
    """

    match = re.search(r'geometry:\s*"([^"]+)"', config_text)
    if not match:
        raise ValueError("manuscript config declares no metadata.geometry string")
    options = {}
    for part in match.group(1).split(","):
        if "=" not in part:
            continue
        key, _, value = part.partition("=")
        options[key.strip()] = value.strip()
    margin = options.get("margin")
    left = options.get("left", margin)
    right = options.get("right", margin)
    top = options.get("top", margin)
    bottom = options.get("bottom", margin)
    if not all((left, right, top, bottom)):
        raise ValueError(f"geometry {match.group(1)!r} does not fix all four margins")
    width_in = (
        PAPER_WIDTH_IN - _length_in_inches(str(left)) - _length_in_inches(str(right))
    )
    height_in = (
        PAPER_HEIGHT_IN - _length_in_inches(str(top)) - _length_in_inches(str(bottom))
    )
    return PageGeometry(width_in * PT_PER_INCH, height_in * PT_PER_INCH)


def render_fraction(config_text: str, key: str, default: float) -> float:
    """Read one ``rendering.<key>`` occupancy fraction from the manuscript config."""

    match = re.search(rf"^\s+{re.escape(key)}:\s*([\d.]+)\s*$", config_text, re.M)
    if not match:
        return default
    value = float(match.group(1))
    return value if 0.0 < value <= 1.0 else default


def rendered_width_pt(
    canvas_width: float,
    canvas_height: float,
    *,
    width_fraction: float,
    height_fraction: float,
    page: PageGeometry,
) -> float:
    """Width in points the image occupies after ``keepaspectratio``.

    The renderer emits ``width=<f>\\linewidth,height=<g>\\textheight,
    keepaspectratio``, so the image is scaled by whichever bound binds first.
    """

    box_width = width_fraction * page.text_width_pt
    box_height = height_fraction * page.text_height_pt
    aspect = canvas_width / canvas_height
    return min(box_width, box_height * aspect)


def min_font_units(canvas_width: float, rendered_pt: float) -> int:
    """Smallest canvas-unit font size that still prints at the floor."""

    return math.ceil(MIN_RENDERED_PT * canvas_width / rendered_pt)


def svg_canvas(svg_text: str) -> tuple[float, float]:
    """Return the drawing canvas (viewBox extent) of a generated SVG."""

    match = _VIEWBOX_RE.search(svg_text)
    if not match:
        raise ValueError("generated SVG has no origin-anchored viewBox")
    return float(match.group(1)), float(match.group(2))


def smallest_font_units(svg_text: str) -> float:
    """Return the smallest ``font-size`` in canvas units drawn in an SVG."""

    sizes = [float(value) for value in _FONT_SIZE_RE.findall(svg_text)]
    if not sizes:
        raise ValueError("generated SVG draws no sized text")
    return min(sizes)


@dataclass(frozen=True)
class FigureLegibility:
    """One figure's smallest text, in canvas units and in rendered points."""

    name: str
    canvas_width: float
    canvas_height: float
    width_fraction: float
    rendered_width_pt: float
    smallest_units: float
    smallest_pt: float

    @property
    def passes(self) -> bool:
        return self.smallest_pt >= MIN_RENDERED_PT


def _declared_embed_fraction(prose: str, filename: str) -> float | None:
    """Read the ``width=NN%`` a manuscript embed declares for one figure."""

    pattern = re.escape(f"figures/{filename}") + r"\)\{[^}]*?width=(\d+)%"
    match = re.search(pattern, prose)
    return None if match is None else int(match.group(1)) / 100.0


def figure_legibility_report(
    project_root: Path,
    *,
    svg_by_name: dict[str, str] | None = None,
) -> tuple[FigureLegibility, ...]:
    """Measure every generated figure, cover included, against the page.

    ``svg_by_name`` overrides the on-disk SVG text for a figure, which lets a
    caller measure a mutated canvas without writing it to the output mirror.
    """

    root = Path(project_root).resolve()
    manuscript = (
        root / "docs" / "manuscript"
        if (root / "docs" / "manuscript").is_dir()
        else root / "manuscript"
    )
    config_text = (manuscript / "config.yaml").read_text(encoding="utf-8")
    page = page_geometry(config_text)
    figure_height = render_fraction(config_text, "figure_height_fraction", 0.50)
    cover_height = render_fraction(config_text, "cover_height_fraction", 0.60)
    prose = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(manuscript.glob("*.md"))
    )
    figures_dir = root / "output" / "figures"
    overrides = svg_by_name or {}
    rows: list[FigureLegibility] = []
    for svg_path in sorted(figures_dir.glob("*.svg")):
        name = svg_path.stem
        svg_text = overrides.get(name) or svg_path.read_text(encoding="utf-8")
        width, height = svg_canvas(svg_text)
        is_cover = name == "cover_art"
        declared = _declared_embed_fraction(prose, f"{name}.png")
        width_fraction = COVER_WIDTH_FRACTION if is_cover else (declared or 1.0)
        if is_cover and declared is not None:
            # The cover prints twice: once as the title-page plate at the
            # renderer's fixed width, once as an ordinary manuscript embed.
            # The smaller surface is the one legibility has to survive.
            width_fraction = min(COVER_WIDTH_FRACTION, declared)
        rendered = rendered_width_pt(
            width,
            height,
            width_fraction=width_fraction,
            height_fraction=cover_height if is_cover else figure_height,
            page=page,
        )
        units = smallest_font_units(svg_text)
        rows.append(
            FigureLegibility(
                name=name,
                canvas_width=width,
                canvas_height=height,
                width_fraction=width_fraction,
                rendered_width_pt=rendered,
                smallest_units=units,
                smallest_pt=units * rendered / width,
            )
        )
    return tuple(rows)


def check_figure_legibility(
    project_root: Path,
    *,
    svg_by_name: dict[str, str] | None = None,
) -> list[str]:
    """Return one actionable error per figure whose smallest text is unreadable."""

    rows = figure_legibility_report(project_root, svg_by_name=svg_by_name)
    if not rows:
        return ["no generated figures were measured for legibility"]
    return [
        f"{row.name}: smallest text is {row.smallest_units:g} canvas units on a "
        f"{row.canvas_width:g}-unit canvas rendered at {row.rendered_width_pt:.1f}pt, "
        f"which prints at {row.smallest_pt:.2f}pt (floor {MIN_RENDERED_PT:g}pt); "
        f"raise it to at least {min_font_units(row.canvas_width, row.rendered_width_pt)} units"
        for row in rows
        if not row.passes
    ]
