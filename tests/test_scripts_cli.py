"""Every script under ``scripts/`` must succeed on a good run and fail closed.

The helpers take no options or operands. Real subprocess pairs exercise their
argument boundary: a valid invocation succeeds and invalid arguments reject
without reporting a result. A broken import cannot stand in for that contrast.

The roster is discovered from the directory rather than listed, so a script
added without an argument guard fails here instead of shipping unguarded.

Writing scripts execute against copied source and manuscript inputs under
``tmp_path``. The suite must not rewrite the checkout's generated artifacts or
require its source tree to be writable.
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
WRITING_SCRIPTS = frozenset({"build_figures.py", "gen_formalism_ledger.py"})

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
    shutil.copytree(ROOT / "docs" / "manuscript", tmp_path / "docs" / "manuscript")
    (tmp_path / "data").mkdir()
    return tmp_path


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
    assert result.returncode == 2, (
        f"{script.name} exited {result.returncode} on {argument!r}; "
        "unexpected arguments must be a usage error"
    )
    assert result.stdout == "", "a rejected invocation must not report a result"


@pytest.mark.parametrize("script", SCRIPT_PATHS, ids=lambda path: path.name)
def test_every_script_fails_closed_on_multiple_unexpected_arguments(
    script: Path,
) -> None:
    result = _run(script, "--nope", "also-garbage")
    assert result.returncode == 2


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

    bad = _run(script, "--nope", root=root)
    assert bad.returncode == 2
