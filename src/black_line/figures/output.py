#!/usr/bin/env python3
"""Filesystem and rasterization adapter for deterministic figure builds."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def resolve_converter() -> Path:
    """Resolve ``rsvg-convert`` from ``PATH`` or fail with an actionable message."""

    converter = shutil.which("rsvg-convert")
    if converter is None:
        raise RuntimeError(
            "rsvg-convert is required to rasterize deterministic SVG figures"
        )
    return Path(converter)


def rasterize_svg(svg_path: Path, png_path: Path, converter: Path) -> None:
    """Rasterize one deterministic SVG through the pinned shared converter."""

    subprocess.run(
        [str(converter), str(svg_path), "--output", str(png_path)], check=True
    )


def write_registry(figures_dir: Path, registry: dict[str, Any]) -> Path:
    """Write the generated figure registry and return its path."""

    registry_path = figures_dir / "figure_registry.json"
    registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    return registry_path
