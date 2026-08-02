"""Rendered-legibility gate for every generated figure.

The gate re-derives the point size of the smallest label in each figure from
three sources the project owns — the PNG/SVG canvas, the declared embed width
in the manuscript, and the page geometry in ``manuscript/config.yaml`` — and
fails below the floor. Every test that asserts a pass is paired with a planted
shrunken font proving the measurement can reject.
"""

import re
import struct
from pathlib import Path

import pytest

from black_line.figures import FIGURE_SPECS, build_figures
from black_line.figures.cover import cover_art_svg
from black_line.figures.legibility import (
    MIN_RENDERED_PT,
    PageGeometry,
    check_figure_legibility,
    figure_legibility_report,
    min_font_units,
    page_geometry,
    rendered_width_pt,
    render_fraction,
    smallest_font_units,
    svg_canvas,
)
from black_line.figures.svg import COVER_MIN_FONT, MIN_FONT, PAGE

ROOT = Path(__file__).resolve().parent.parent


def _project_copy(tmp_path: Path) -> Path:
    """Build a self-contained figure bundle plus the config it is measured against."""

    build_figures(tmp_path)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(parents=True, exist_ok=True)
    for name in ("config.yaml",):
        (manuscript / name).write_text(
            (ROOT / "manuscript" / name).read_text(encoding="utf-8"), encoding="utf-8"
        )
    for path in sorted((ROOT / "manuscript").glob("*.md")):
        (manuscript / path.name).write_text(
            path.read_text(encoding="utf-8"), encoding="utf-8"
        )
    return tmp_path


def test_page_geometry_is_derived_from_the_declared_margins() -> None:
    """The text block comes from config, not from a restated point literal."""

    geometry = page_geometry('  geometry: "margin=0.5in,top=0.58in,bottom=0.58in"')
    assert geometry.text_width_pt == pytest.approx((8.5 - 1.0) * 72.27)
    assert geometry.text_height_pt == pytest.approx((11.0 - 1.16) * 72.27)
    # A different declared margin must move the block, or the derivation is fake.
    wider = page_geometry('  geometry: "margin=1in,top=1in,bottom=1in"')
    assert wider.text_width_pt < geometry.text_width_pt


def test_page_geometry_refuses_an_unusable_declaration() -> None:
    with pytest.raises(ValueError, match="no metadata.geometry"):
        page_geometry("paper:\n  title: nothing\n")
    with pytest.raises(ValueError, match="does not fix all four margins"):
        page_geometry('  geometry: "top=0.5in"')


def test_height_cap_can_bind_before_width_and_shrink_the_plate() -> None:
    """The defect this gate exists for: a height cap shrinking a tall plate."""

    page = PageGeometry(542.025, 711.1368)
    tall = rendered_width_pt(
        1400, 1230, width_fraction=1.0, height_fraction=0.5, page=page
    )
    assert tall < page.text_width_pt
    released = rendered_width_pt(
        1400, 1230, width_fraction=1.0, height_fraction=0.95, page=page
    )
    assert released == pytest.approx(page.text_width_pt)
    # And the shrink is exactly what pushes an 11-unit label under the floor.
    assert 11 * tall / 1400 < MIN_RENDERED_PT
    assert 16 * released / 1400 >= MIN_RENDERED_PT


def test_manuscript_config_releases_the_figure_height_cap() -> None:
    config = (ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8")
    figure_fraction = render_fraction(config, "figure_height_fraction", 0.50)
    cover_fraction = render_fraction(config, "cover_height_fraction", 0.60)
    assert figure_fraction > 0.5, "the default cap binds before width on tall plates"
    assert cover_fraction > 0.6


def test_font_floors_are_derived_from_the_page_not_restated() -> None:
    assert MIN_FONT == min_font_units(1400, PAGE.text_width_pt)
    assert COVER_MIN_FONT == min_font_units(1800, 0.98 * PAGE.text_width_pt)
    assert MIN_FONT * PAGE.text_width_pt / 1400 >= MIN_RENDERED_PT


def test_every_generated_figure_prints_above_the_floor(shipped_figures: Path) -> None:
    """The shipped output mirror passes the gate with measured numbers.

    ``shipped_figures`` (``tests/conftest.py``) rebuilds the ignored mirror when
    the checkout can build it and skips with a named reason when it provably
    cannot, so a missing rasterizer reports as unrun rather than as a failed
    legibility floor.
    """

    assert shipped_figures.is_dir()
    rows = figure_legibility_report(ROOT)
    assert len(rows) == len(FIGURE_SPECS) + 1, "cover included"
    assert check_figure_legibility(ROOT) == []
    assert min(row.smallest_pt for row in rows) >= MIN_RENDERED_PT


def test_gate_rejects_a_planted_shrunken_font(tmp_path: Path) -> None:
    """Proof of detection: shrink one label and the gate must name that figure."""

    root = _project_copy(tmp_path)
    assert check_figure_legibility(root) == []

    victim = FIGURE_SPECS[0]
    svg_text = (root / "output" / "figures" / f"{victim.name}.svg").read_text(
        encoding="utf-8"
    )
    shrunk = svg_text.replace(f'font-size="{MIN_FONT}px"', 'font-size="9px"', 1)
    assert shrunk != svg_text, "no floor-sized label to shrink"
    errors = check_figure_legibility(root, svg_by_name={victim.name: shrunk})
    assert len(errors) == 1
    assert victim.name in errors[0]
    assert "floor 6pt" in errors[0]


def test_gate_rejects_a_canvas_that_outgrows_its_text(tmp_path: Path) -> None:
    """Widening the canvas without growing the text is the same defect."""

    root = _project_copy(tmp_path)
    victim = FIGURE_SPECS[1]
    svg_text = (root / "output" / "figures" / f"{victim.name}.svg").read_text(
        encoding="utf-8"
    )
    width, height = svg_canvas(svg_text)
    doubled = svg_text.replace(
        f'viewBox="0 0 {width:g} {height:g}"',
        f'viewBox="0 0 {width * 2:g} {height:g}"',
        1,
    )
    assert doubled != svg_text
    errors = check_figure_legibility(root, svg_by_name={victim.name: doubled})
    assert any(victim.name in error for error in errors)


def _png_pixel_size(path: Path) -> tuple[int, int]:
    """Read width and height from a PNG's IHDR chunk."""

    header = path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n", path.name
    return struct.unpack(">II", header[16:24])


def test_the_rasterized_pixel_size_is_the_canvas_the_gate_measures(
    shipped_figures: Path,
) -> None:
    """The point-size derivation reads the SVG canvas; the PDF embeds the PNG.

    Those are the same number only because the rasterizer maps one canvas unit
    to one pixel. Nothing asserted that, so a converter that scaled — or a
    figure whose SVG and PNG fell out of step — would leave every measured
    point size above a fiction while the gate stayed green.

    Reads the ignored mirror, so it takes ``shipped_figures``
    (``tests/conftest.py``) rather than assuming one is on disk.
    """

    figures = shipped_figures
    svgs = sorted(figures.glob("*.svg"))
    assert len(svgs) == len(FIGURE_SPECS) + 1, "cover included; an empty sweep is a bug"
    for svg_path in svgs:
        png_path = svg_path.with_suffix(".png")
        assert png_path.is_file(), png_path.name
        canvas = svg_canvas(svg_path.read_text(encoding="utf-8"))
        assert _png_pixel_size(png_path) == (int(canvas[0]), int(canvas[1])), (
            f"{svg_path.stem}: rasterized pixels differ from the measured canvas"
        )


def test_the_pixel_size_check_can_fail(tmp_path: Path) -> None:
    """Positive control: a PNG rasterized at a different scale must be rejected."""

    from black_line.figures.output import rasterize_svg, resolve_converter

    svg_text = FIGURE_SPECS[0].builder()
    width, height = svg_canvas(svg_text)
    svg_path = tmp_path / "scaled.svg"
    svg_path.write_text(svg_text, encoding="utf-8")
    png_path = tmp_path / "scaled.png"
    rasterize_svg(svg_path, png_path, resolve_converter())
    assert _png_pixel_size(png_path) == (int(width), int(height))

    scaled = svg_text.replace(
        f'width="{width:g}" height="{height:g}"',
        f'width="{width * 2:g}" height="{height * 2:g}"',
        1,
    )
    assert scaled != svg_text, "no top-level width/height pair to rescale"
    scaled_path = tmp_path / "doubled.svg"
    scaled_path.write_text(scaled, encoding="utf-8")
    doubled_png = tmp_path / "doubled.png"
    rasterize_svg(scaled_path, doubled_png, resolve_converter())
    # Same viewBox, twice the raster: exactly the drift the check above catches.
    assert svg_canvas(scaled) == (width, height)
    assert _png_pixel_size(doubled_png) != (int(width), int(height))


def test_measurement_helpers_refuse_unmeasurable_input() -> None:
    with pytest.raises(ValueError, match="origin-anchored viewBox"):
        svg_canvas("<svg width='10'></svg>")
    with pytest.raises(ValueError, match="no sized text"):
        smallest_font_units('<svg viewBox="0 0 10 10"></svg>')


def test_no_builder_emits_text_below_its_own_canvas_floor() -> None:
    """Raw f-string text elements are covered too, not just the helpers."""

    for spec in FIGURE_SPECS:
        svg_text = spec.builder()
        width, _height = svg_canvas(svg_text)
        floor = min_font_units(width, PAGE.text_width_pt)
        assert smallest_font_units(svg_text) >= floor, spec.name
    cover = cover_art_svg()
    cover_width, _ = svg_canvas(cover)
    assert smallest_font_units(cover) >= min_font_units(
        cover_width, 0.98 * PAGE.text_width_pt
    )


def test_every_manuscript_embed_declares_a_full_width() -> None:
    """The gate measures the declared width; an undeclared one would be a guess."""

    prose = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "manuscript").glob("*.md"))
    )
    embeds = re.findall(r"\.\./output/figures/(\w+)\.png\)\{#[^}]*?width=(\d+)%", prose)
    names = {name for name, _ in embeds}
    assert {spec.name for spec in FIGURE_SPECS} <= names
    assert "cover_art" in names
    assert {int(width) for _, width in embeds} == {100}


def test_length_units_and_bad_fractions_are_handled() -> None:
    """Metric and point margins convert, and an unusable length is refused."""

    metric = page_geometry(
        '  geometry: "left=2.54cm,right=2.54cm,top=25.4mm,bottom=25.4mm"'
    )
    inches = page_geometry('  geometry: "margin=1in,top=1in,bottom=1in"')
    assert metric.text_width_pt == pytest.approx(inches.text_width_pt, abs=0.01)
    assert metric.text_height_pt == pytest.approx(inches.text_height_pt, abs=0.01)

    points = page_geometry('  geometry: "margin=72.27pt,top=72.27pt,bottom=72.27pt"')
    assert points.text_width_pt == pytest.approx(inches.text_width_pt, abs=0.01)

    with pytest.raises(ValueError, match="unreadable LaTeX length"):
        page_geometry('  geometry: "margin=wide,top=1in,bottom=1in"')


def test_render_fraction_falls_back_on_an_out_of_range_value() -> None:
    assert render_fraction("rendering:\n  x: 0.4\n", "x", 0.5) == 0.4
    assert render_fraction("rendering:\n  x: 3\n", "x", 0.5) == 0.5
    assert render_fraction("rendering:\n  x: 0\n", "x", 0.5) == 0.5
    assert render_fraction("nothing here", "x", 0.5) == 0.5


def test_an_empty_bundle_is_reported_as_unmeasured_not_as_passing(
    tmp_path: Path,
) -> None:
    """A gate over an empty scan set is itself a defect, so say so."""

    (tmp_path / "manuscript").mkdir()
    (tmp_path / "manuscript" / "config.yaml").write_text(
        (ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (tmp_path / "output" / "figures").mkdir(parents=True)
    assert check_figure_legibility(tmp_path) == [
        "no generated figures were measured for legibility"
    ]


def test_page_geometry_skips_a_bare_geometry_token() -> None:
    """A valueless option like ``landscape`` is skipped, not mis-parsed.

    LaTeX geometry strings may carry bare tokens beside ``key=value`` pairs;
    the parser must ignore them and still derive the block from the margins
    that are declared.
    """

    geometry = page_geometry(
        '  geometry: "landscape,margin=0.5in,top=0.58in,bottom=0.58in"'
    )
    assert geometry.text_width_pt == pytest.approx((8.5 - 1.0) * 72.27)
