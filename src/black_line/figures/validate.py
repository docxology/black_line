"""Fail-closed validation for generated Black Line figure bundles."""

from __future__ import annotations

import json
import re
from pathlib import Path

from black_line import (
    BLACK_PRACTICES,
    PRACTICE_TAG_VOCABULARY,
    __version__,
    registry_digest,
)
from black_line.figures.specs import COVER_SPEC, FIGURE_SPECS

ROOT = Path(__file__).resolve().parents[3]


def _configured_cover_image(config_path: Path) -> str | None:
    """Read ``paper.cover.image`` from the manuscript config with a scoped parse."""

    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError:
        return None
    in_paper = False
    in_cover = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped and not line.startswith(" "):
            in_paper = stripped == "paper:"
            in_cover = False
            continue
        if not in_paper:
            continue
        if stripped == "cover:":
            in_cover = True
            continue
        if in_cover:
            match = re.match(r'\s+image:\s*"([^"]+)"\s*$', line)
            if match:
                return match.group(1)
            if re.match(r"\s{0,2}\S", line):
                in_cover = False
    return None


def validate_generated_figures(project_root: Path | None = None) -> list[str]:
    """Return actionable drift errors for one generated figure bundle."""

    root = (project_root or ROOT).resolve()
    figures_dir = root / "output" / "figures"
    registry_path = figures_dir / "figure_registry.json"
    errors: list[str] = []
    if not registry_path.is_file():
        return [f"missing generated figure registry: {registry_path}"]
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"cannot read generated figure registry {registry_path}: {exc}"]

    # The contract is every reader-facing field a spec declares, not only the
    # three that name the file. `alt`, `interpretive_claim`, and
    # `epistemic_boundary` are what keep a caption from outclaiming the method,
    # so blanking them on disk has to fail here rather than pass silently.
    expected = {
        spec.name: {
            "label": spec.label,
            "filename": f"{spec.name}.png",
            "caption": spec.caption,
            "alt": spec.alt,
            "interpretive_claim": spec.interpretive_claim,
            "epistemic_boundary": spec.epistemic_boundary,
        }
        for spec in (*FIGURE_SPECS, COVER_SPEC)
    }
    actual_entries = registry.get("figures")
    if not isinstance(actual_entries, list):
        errors.append("figure registry has no list-valued 'figures' entry")
        actual_entries = []
    actual = {
        Path(str(entry.get("filename", ""))).stem: entry
        for entry in actual_entries
        if isinstance(entry, dict)
    }
    missing = sorted(set(expected) - set(actual))
    unexpected = sorted(set(actual) - set(expected))
    if missing:
        errors.append(f"figure registry is missing: {', '.join(missing)}")
    if unexpected:
        errors.append(
            f"figure registry has unexpected figures: {', '.join(unexpected)}"
        )

    for name, contract in expected.items():
        entry = actual.get(name)
        if entry is None:
            continue
        for field, expected_value in contract.items():
            if entry.get(field) != expected_value:
                errors.append(
                    f"{name} registry {field} drifted: "
                    f"expected {expected_value!r}, got {entry.get(field)!r}"
                )
        for suffix in (".png", ".svg"):
            path = figures_dir / f"{name}{suffix}"
            if not path.is_file():
                errors.append(f"missing generated figure file: {path}")

    for suffix in (".png", ".svg"):
        cover_path = figures_dir / f"cover_art{suffix}"
        if not cover_path.is_file():
            errors.append(f"missing generated cover file: {cover_path}")
    cover = registry.get("cover")
    if not isinstance(cover, dict) or cover.get("filename") != "cover_art.png":
        errors.append("figure registry cover does not point to cover_art.png")
    else:
        for field in ("caption", "alt", "interpretive_claim", "epistemic_boundary"):
            if not str(cover.get(field, "")).strip():
                errors.append(f"figure registry cover has a blank {field}")
        # The cover's only PDF-side consumer is the title-page key; bind it
        # here so renaming or deleting the file cannot leave the rendered
        # cover silently missing while every other gate stays green.
        manuscript = (
            root / "docs" / "manuscript"
            if (root / "docs" / "manuscript").is_dir()
            else root / "manuscript"
        )
        declared = _configured_cover_image(manuscript / "config.yaml")
        expected_cover = f"figures/{cover.get('filename')}"
        if declared != expected_cover:
            errors.append(
                f"manuscript/config.yaml paper.cover.image is {declared!r}, "
                f"expected {expected_cover!r} from the registry cover entry"
            )

    metadata = {
        "package_version": __version__,
        "registry_digest": registry_digest(BLACK_PRACTICES),
        "practice_count": len(BLACK_PRACTICES),
        "tag_vocabulary": sorted(PRACTICE_TAG_VOCABULARY),
    }
    for field, expected_value in metadata.items():
        if registry.get(field) != expected_value:
            errors.append(
                f"figure registry {field} drifted: "
                f"expected {expected_value!r}, got {registry.get(field)!r}"
            )
    return errors
