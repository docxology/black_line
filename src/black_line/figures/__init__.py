"""Deterministic Black Line figure builders and registry."""

from __future__ import annotations

from pathlib import Path

from black_line import (
    BLACK_PRACTICES,
    PRACTICE_TAG_VOCABULARY,
    __version__,
    registry_digest,
)
from black_line.figures.cover import cover_art_svg
from black_line.figures.output import rasterize_svg, resolve_converter, write_registry
from black_line.figures.specs import COVER_SPEC, FIGURE_SPECS, FigureSpec
from black_line.figures.validate import validate_generated_figures

ROOT = Path(__file__).resolve().parents[3]

__all__ = [
    "COVER_SPEC",
    "FIGURE_SPECS",
    "FigureSpec",
    "build_figures",
    "cover_art_svg",
    "validate_generated_figures",
]


def build_figures(project_root: Path | None = None) -> list[Path]:
    """Write every deterministic figure and the registry; return generated PNGs."""

    root = (project_root or ROOT).resolve()
    figures = root / "output" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    converter = resolve_converter()
    generated: list[Path] = []
    entries: list[dict[str, object]] = []
    for spec in (*FIGURE_SPECS, COVER_SPEC):
        svg_path = figures / f"{spec.name}.svg"
        png_path = figures / f"{spec.name}.png"
        svg_path.write_text(spec.builder(), encoding="utf-8")
        rasterize_svg(svg_path, png_path, converter)
        generated.append(png_path)
        entries.append(
            {
                "label": spec.label,
                "filename": png_path.name,
                "caption": spec.caption,
                "alt": spec.alt,
                "interpretive_claim": spec.interpretive_claim,
                "epistemic_boundary": spec.epistemic_boundary,
                "source": "black_line registry, evaluator rules, and manuscript protocol",
                "generated_by": "black_line.figures.build_figures",
                "format": "PNG rasterized from deterministic SVG",
            }
        )
    registry = {
        "schema_version": "1.5",
        "package_version": __version__,
        "registry_digest": registry_digest(BLACK_PRACTICES),
        "practice_count": len(BLACK_PRACTICES),
        "tag_vocabulary": sorted(PRACTICE_TAG_VOCABULARY),
        "figures": entries,
    }
    # The title-page pointer repeats the cover's registered contract so the
    # renderer's `paper.cover.image` key has something to be bound to.
    registry["cover"] = {
        "label": COVER_SPEC.label,
        "filename": f"{COVER_SPEC.name}.png",
        "caption": COVER_SPEC.caption,
        "alt": COVER_SPEC.alt,
        "interpretive_claim": COVER_SPEC.interpretive_claim,
        "epistemic_boundary": COVER_SPEC.epistemic_boundary,
        "source": "black_line protocol and registry semantics",
        "generated_by": "black_line.figures.build_figures",
        "format": "PNG rasterized from deterministic SVG",
    }
    write_registry(figures, registry)
    return generated
