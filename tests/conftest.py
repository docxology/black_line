"""Session setup for the Black Line suite.

``output/`` is ignored and disposable, so a clean checkout — or a render host
that wipes generated output before running the tests — arrives with no
``output/figures``. Five gates in this suite read that directory: the cover
caption contract, the two legibility floors, and the two ``check_figures.py``
CLI checks. Without this fixture they fail for a reason that has nothing to do
with the property under test, which is why the documented "run pytest first"
order reported failures against a source tree that is in fact correct.

The rebuild uses this project's own deterministic builder and nothing else. It
is a rebuild of an ignored artifact, not a stand-in: the same bytes the
committed registry already pins.

The PNG half of that build needs ``rsvg-convert`` from librsvg, which is a
system package rather than a Python dependency. A machine without it cannot
produce the mirror at all, and a session fixture that raised there took the
whole suite down with it — all 256 tests errored, including the 251 that never
look at ``output/``. So the rasterizer is checked first: when it is missing the
rebuild is skipped and the five gates that need the mirror skip individually
through :func:`shipped_figures`, each after asserting the mirror really is
absent, so the skip is a positive control rather than a silent pass. Every
other failure mode of the builder still propagates, because a broken figure
build is a real defect and must not be masked.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
FIGURES = ROOT / "output" / "figures"
REGISTRY = FIGURES / "figure_registry.json"

#: The one non-Python tool the figure build needs. Named here so the skip
#: reason and the guard cannot drift apart.
RASTERIZER = "rsvg-convert"

MIRROR_SKIP_REASON = (
    f"output/figures is absent and {RASTERIZER} is not installed, so this "
    "checkout cannot build the deterministic PNG mirror this gate measures. "
    "Install librsvg (brew install librsvg, apt-get install librsvg2-bin) and "
    "re-run, or run scripts/build_figures.py first."
)


@pytest.fixture(scope="session", autouse=True)
def _ensure_generated_figures() -> None:
    """Rebuild ``output/figures`` when the ignored directory is absent."""

    if REGISTRY.exists():
        return
    if shutil.which(RASTERIZER) is None:
        # Nothing to build with. Leave the mirror absent and let the gates that
        # need it skip with a named reason instead of erroring the whole suite.
        return

    from black_line.figures import build_figures

    build_figures(ROOT)


@pytest.fixture(scope="session")
def shipped_figures() -> Path:
    """Return the built mirror, or skip with a named reason proving it is absent.

    The two assertions below are the positive control. The skip fires only when
    the registry really is missing *and* the rasterizer that would have built it
    really is unavailable; on any machine that could have produced the mirror,
    reaching this line is a failure rather than a skip.
    """

    if REGISTRY.is_file():
        return FIGURES

    assert not REGISTRY.exists(), (
        f"{REGISTRY} exists but is not a file; the mirror gates cannot read it"
    )
    assert shutil.which(RASTERIZER) is None, (
        f"{RASTERIZER} is installed, so the session fixture should have built "
        f"{REGISTRY}; skipping here would hide a real figure-build failure"
    )
    pytest.skip(MIRROR_SKIP_REASON)
