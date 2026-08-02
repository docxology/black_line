"""Binding tests for the figure contract fields and derived canvases.

Two gaps this file closes. First, the on-disk gate used to compare only
``label``, ``filename``, and ``caption``, so blanking ``alt``,
``interpretive_claim``, or ``epistemic_boundary`` in the shipped registry left
``check_figures.py`` green while the fields the documentation credits with
stopping an outclaiming caption were gone. Second, two builders carried a fixed
canvas while laying out one row or column per registry entry, so a larger
registry would silently clip content out of the viewBox.
"""

import json
import re
from dataclasses import replace
from pathlib import Path
from xml.dom.minidom import parseString

from black_line import BLACK_PRACTICES, BlackPractice, PracticeKind
from black_line.figures import FIGURE_SPECS, build_figures
from black_line.figures.legibility import svg_canvas
from black_line.figures.validate import (
    _configured_cover_image,
    validate_generated_figures,
)

ROOT = Path(__file__).resolve().parent.parent
CONTRACT_FIELDS = ("caption", "alt", "interpretive_claim", "epistemic_boundary")


def _bundle(tmp_path: Path) -> Path:
    build_figures(tmp_path)
    manuscript = tmp_path / "manuscript"
    manuscript.mkdir(parents=True, exist_ok=True)
    (manuscript / "config.yaml").write_text(
        (ROOT / "manuscript" / "config.yaml").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    return tmp_path


def _registry(root: Path) -> tuple[Path, dict]:
    path = root / "output" / "figures" / "figure_registry.json"
    return path, json.loads(path.read_text(encoding="utf-8"))


def test_blanking_any_contract_field_fails_the_on_disk_gate(tmp_path: Path) -> None:
    """Proof of detection, one planted blank at a time, for every figure field."""

    root = _bundle(tmp_path)
    assert validate_generated_figures(root) == []
    path, pristine = _registry(root)
    # The `figures` list carries the manuscript figures and the cover plate, so
    # the expected error count is derived from the list rather than restated.
    entry_count = len(pristine["figures"])
    assert entry_count == len(FIGURE_SPECS) + 1, "manuscript figures plus cover"
    for field in CONTRACT_FIELDS:
        registry = json.loads(json.dumps(pristine))
        for entry in registry["figures"]:
            entry[field] = ""
        path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
        errors = validate_generated_figures(root)
        assert len(errors) == entry_count, field
        assert all(f"registry {field} drifted" in error for error in errors), field
    path.write_text(json.dumps(pristine, indent=2), encoding="utf-8")
    assert validate_generated_figures(root) == []


def test_blanking_a_cover_contract_field_fails_the_gate(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    path, pristine = _registry(root)
    for field in CONTRACT_FIELDS:
        registry = json.loads(json.dumps(pristine))
        registry["cover"][field] = "   "
        path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
        assert validate_generated_figures(root) == [
            f"figure registry cover has a blank {field}"
        ], field


def test_cover_config_key_is_bound_to_the_registry_cover(tmp_path: Path) -> None:
    """The title-page cover key is a real dependency, so a mismatch must fail."""

    root = _bundle(tmp_path)
    assert validate_generated_figures(root) == []
    config = root / "manuscript" / "config.yaml"
    original = config.read_text(encoding="utf-8")
    assert _configured_cover_image(config) == "figures/cover_art.png"

    config.write_text(
        original.replace('image: "figures/cover_art.png"', 'image: "figures/gone.png"'),
        encoding="utf-8",
    )
    errors = validate_generated_figures(root)
    assert any("paper.cover.image" in error for error in errors)

    config.write_text(
        original.replace('  cover:\n    image: "figures/cover_art.png"\n', ""),
        encoding="utf-8",
    )
    errors = validate_generated_figures(root)
    assert any("paper.cover.image is None" in error for error in errors)

    config.write_text(original, encoding="utf-8")
    assert validate_generated_figures(root) == []


def test_configured_cover_image_reads_nothing_from_a_missing_config(
    tmp_path: Path,
) -> None:
    assert _configured_cover_image(tmp_path / "absent.yaml") is None
    other = tmp_path / "other.yaml"
    other.write_text('book:\n  cover:\n    image: "figures/x.png"\n', encoding="utf-8")
    assert _configured_cover_image(other) is None


def test_the_shipped_cover_reaches_a_reader_with_its_caption(
    shipped_figures: Path,
) -> None:
    """The cover is exempt from the FIGURE_SPECS embed gate, not from readers.

    Reads the ignored ``output/figures`` mirror, so it takes ``shipped_figures``
    (see ``tests/conftest.py``): the mirror is rebuilt when it can be, and the
    gate skips with a named reason only on a checkout that provably cannot
    build one.
    """

    assert shipped_figures.is_dir()
    _path, registry = _registry(ROOT)
    cover = registry["cover"]
    prose = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((ROOT / "manuscript").glob("*.md"))
    )
    assert f"figures/{cover['filename']}" in prose
    matches = re.findall(
        r"!\[([^\]]*)\]\(\.\./output/figures/" + re.escape(cover["filename"]) + r"\)",
        prose,
    )
    assert len(matches) == 1
    assert matches[0] == cover["caption"]


def _grown_registry(extra: int) -> tuple[BlackPractice, ...]:
    """A registry with synthetic practices appended, ids and labels distinct."""

    template = BLACK_PRACTICES[0]
    grown = list(BLACK_PRACTICES)
    for index in range(extra):
        grown.append(
            replace(
                template,
                id=f"synthetic-practice-{index}",
                title=f"Synthetic practice {index} for canvas fit",
                required_evidence=(f"synthetic_{index}_a", f"synthetic_{index}_b"),
                kind=PracticeKind.STEWARDSHIP,
            )
        )
    return tuple(grown)


def _last_drawn_extent(svg_text: str) -> tuple[float, float]:
    """The furthest right and lowest coordinates any element in the SVG uses."""

    xs = [float(value) for value in re.findall(r'\sx="(-?[\d.]+)"', svg_text)]
    ys = [float(value) for value in re.findall(r'\sy="(-?[\d.]+)"', svg_text)]
    return max(xs), max(ys)


def test_registry_derived_canvases_grow_with_the_registry() -> None:
    """A larger registry must widen or lengthen the canvas, never clip content.

    The evidence matrix and the coverage heatmap both lay out one row or column
    per practice. Before this test they carried fixed canvases, so a thirteenth
    practice pushed the heatmap grid and a fourteenth pushed the matrix legend —
    which carries the figure's boundary sentence — outside the viewBox.
    """

    from black_line.figures.analytics_figures import coverage_heatmap_svg
    from black_line.figures.registry_schematics import evidence_matrix_svg

    grown = _grown_registry(6)
    assert len(grown) > len(BLACK_PRACTICES)

    matrix = evidence_matrix_svg(grown)
    parseString(matrix)
    width, height = svg_canvas(matrix)
    max_x, max_y = _last_drawn_extent(matrix)
    assert max_y <= height, "evidence matrix clips its boundary sentence"
    assert max_x <= width
    assert "it cannot confirm that a source is real" in matrix

    heatmap = coverage_heatmap_svg(grown)
    parseString(heatmap)
    width, height = svg_canvas(heatmap)
    max_x, max_y = _last_drawn_extent(heatmap)
    assert max_x <= width, "coverage heatmap clips its margin totals"
    assert max_y <= height


def test_the_canvas_fit_check_can_fail() -> None:
    """Positive control: the fit assertion rejects a canvas that is too small."""

    svg_text = '<svg viewBox="0 0 100 100"><rect x="10" y="140" /></svg>'
    width, height = svg_canvas(svg_text)
    max_x, max_y = _last_drawn_extent(svg_text)
    assert max_x <= width
    assert max_y > height


def test_an_unreadable_registry_file_is_reported(tmp_path: Path) -> None:
    """A directory where the registry should be is a read failure, not a pass."""

    figures = tmp_path / "output" / "figures"
    figures.mkdir(parents=True)
    (figures / "figure_registry.json").mkdir()
    errors = validate_generated_figures(tmp_path)
    assert len(errors) == 1
    assert (
        "cannot read" in errors[0] or "missing generated figure registry" in errors[0]
    )


def test_an_unexpected_registry_entry_is_reported(tmp_path: Path) -> None:
    root = _bundle(tmp_path)
    path, registry = _registry(root)
    registry["figures"].append({"filename": "stowaway.png", "label": "fig:stowaway"})
    path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    errors = validate_generated_figures(root)
    assert any("unexpected figures: stowaway" in error for error in errors)


def test_configured_cover_image_exits_a_cover_block_without_an_image(
    tmp_path: Path,
) -> None:
    """A ``cover:`` block that ends without an image yields None, not a leak.

    The scoped parser must notice a sibling key at cover-block depth, close
    the block, and not read an ``image:`` that belongs to a later mapping.
    """

    config = tmp_path / "config.yaml"
    config.write_text(
        "paper:\n"
        "  cover:\n"
        '  title: "no image inside the cover block"\n'
        "other:\n"
        '  image: "figures/should_never_be_read.png"\n',
        encoding="utf-8",
    )
    assert _configured_cover_image(config) is None
    deep = tmp_path / "deep.yaml"
    deep.write_text(
        "paper:\n"
        "  cover:\n"
        "      note: deeper non-image content stays inside the block\n"
        '      image: "figures/cover_art.png"\n',
        encoding="utf-8",
    )
    assert _configured_cover_image(deep) == "figures/cover_art.png"
