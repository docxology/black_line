"""Every script under ``scripts/`` must succeed on a good run and fail closed.

The three CLIs take no options and no operands, but each one used to accept an
unknown flag or a garbage operand and exit 0 — an exit code a CI line, a
Makefile, or a reader would read as a pass. This module drives the real
scripts as subprocesses (no patching, no in-process argv rewriting): the
good-input run is asserted to exit 0 and print its real summary, and every
script is fed several argument shapes and must exit non-zero for each.

The roster is discovered from the directory rather than listed, so a script
added without an argument guard fails here instead of shipping unguarded.

``build_figures.py`` writes, and ``build_figures()`` resolves its output root
from the package's own location rather than from the working directory. Its
good-input run therefore executes against a copied source tree under
``tmp_path`` — the real script, the real builder, a throwaway output root — so
running the suite never rewrites the checkout's shipped mirror and never needs
the checkout to be writable.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

#: Scripts are private helpers, not entry points, when they start with ``_``.
SCRIPT_PATHS = tuple(
    sorted(path for path in SCRIPTS.glob("*.py") if not path.name.startswith("_"))
)

#: Scripts whose good-input run writes, and so must run against a copied tree.
WRITING_SCRIPTS = frozenset({"build_figures.py"})

#: Scripts whose good-input run reads the ignored ``output/figures`` mirror.
#: Only these need the ``shipped_figures`` fixture; the others must keep
#: running on a checkout that has no mirror and cannot build one.
MIRROR_READING_SCRIPTS = frozenset({"check_figures.py"})

#: Argument shapes a mistyped or copy-pasted command line actually produces.
BAD_ARGUMENTS = ("--nope", "garbage", "--project=working/black_line", "-x", "--help=1")


def _run(
    script: Path, *arguments: str, root: Path | None = None
) -> subprocess.CompletedProcess[str]:
    """Run one script as an operator would, rooted at ``root`` (default: this checkout)."""

    base = ROOT if root is None else root
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(base / "src")
    return subprocess.run(  # noqa: S603
        [sys.executable, str(base / "scripts" / script.name), *arguments],
        cwd=base,
        env=environment,
        capture_output=True,
        text=True,
        timeout=300,
    )


def _sandbox(tmp_path: Path) -> Path:
    """Copy the source and scripts into a throwaway root the build may write to."""

    shutil.copytree(ROOT / "src", tmp_path / "src")
    shutil.copytree(ROOT / "scripts", tmp_path / "scripts")
    # The page geometry the font floors are derived from is read at import
    # time, so the copied tree needs the real config and nothing else.
    (tmp_path / "docs" / "manuscript").mkdir(parents=True, exist_ok=True)
    shutil.copy(
        ROOT / "docs" / "manuscript" / "config.yaml",
        tmp_path / "docs" / "manuscript",
    )
    return tmp_path


def test_the_script_roster_is_not_empty() -> None:
    """A sweep over zero scripts would make every assertion below vacuous."""

    assert len(SCRIPT_PATHS) >= 3
    assert {path.name for path in SCRIPT_PATHS} == {
        "build_figures.py",
        "check_figures.py",
        "check_registry.py",
    }
    assert WRITING_SCRIPTS <= {path.name for path in SCRIPT_PATHS}


def test_check_registry_passes_on_the_real_registry() -> None:
    result = _run(SCRIPTS / "check_registry.py")
    assert result.returncode == 0, result.stderr
    assert "FAIL" not in result.stdout
    assert "digest=" in result.stdout


def test_check_figures_passes_on_the_shipped_output_mirror(
    shipped_figures: Path,
) -> None:
    """Requires a built ``output/figures``.

    ``shipped_figures`` (``tests/conftest.py``) rebuilds the ignored mirror when
    this checkout can, and skips with a named reason — after asserting the
    mirror really is absent — when it cannot.
    """

    assert shipped_figures.is_dir()
    result = _run(SCRIPTS / "check_figures.py")
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.startswith("PASS generated figure contract:")


def test_build_figures_writes_the_bundle_it_reports(tmp_path: Path) -> None:
    """Executed against a copied tree, so the checkout's mirror is untouched."""

    from black_line.figures import FIGURE_SPECS

    root = _sandbox(tmp_path)
    result = _run(SCRIPTS / "build_figures.py", root=root)
    assert result.returncode == 0, result.stderr
    expected = len(FIGURE_SPECS) + 1
    assert result.stdout.strip() == f"generated {expected} figures under output/figures"
    written = sorted((root / "output" / "figures").glob("*.png"))
    assert len(written) == expected, "the reported count must be what reached disk"
    assert not (ROOT / "output" / "figures" / "unexpected.png").exists()


@pytest.mark.parametrize("script", SCRIPT_PATHS, ids=lambda path: path.name)
@pytest.mark.parametrize("argument", BAD_ARGUMENTS)
def test_every_script_fails_closed_on_unexpected_arguments(
    script: Path, argument: str
) -> None:
    """Garbage in must not read as a pass out.

    Rejection happens before any script body runs, so even the writing script
    is safe to invoke here against the checkout: nothing is opened.
    """

    result = _run(script, argument)
    assert result.returncode != 0, (
        f"{script.name} exited 0 on {argument!r}; a gate that accepts garbage "
        "is not a gate"
    )
    assert "takes no arguments" in result.stderr
    assert result.stdout == "", "a rejected invocation must not report a result"


@pytest.mark.parametrize("script", SCRIPT_PATHS, ids=lambda path: path.name)
def test_every_script_fails_closed_on_multiple_unexpected_arguments(
    script: Path,
) -> None:
    result = _run(script, "--nope", "also-garbage")
    assert result.returncode != 0
    assert "--nope also-garbage" in result.stderr


@pytest.mark.parametrize("script", SCRIPT_PATHS, ids=lambda path: path.name)
def test_the_guard_is_what_rejects_and_not_an_import_error(
    script: Path, tmp_path: Path, request: pytest.FixtureRequest
) -> None:
    """Proof the rejection is the guard: the same run without args succeeds.

    Without this pairing, a script that crashed on import would satisfy every
    non-zero assertion above while never running its check at all.

    The good run of a mirror-reading script needs ``output/figures``, so that
    one parameter — and only that one — pulls in ``shipped_figures``. Requesting
    it for the whole sweep would skip the two scripts that read nothing.
    """

    if script.name in MIRROR_READING_SCRIPTS:
        request.getfixturevalue("shipped_figures")
    root = _sandbox(tmp_path) if script.name in WRITING_SCRIPTS else None
    good = _run(script, root=root)
    assert good.returncode == 0, f"{script.name}: {good.stderr}"
    assert good.stdout.strip(), f"{script.name} produced no result on a good run"

    bad = _run(script, "--nope", root=root)
    assert bad.returncode != 0
    assert bad.returncode != good.returncode
    assert "Traceback" not in bad.stderr, "the guard must reject, not crash"
