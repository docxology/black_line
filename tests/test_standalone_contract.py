"""Bind the claims that make this repository standalone.

Black Line is now its own repository, and four of its own statements about
itself were previously true only because a checkout happened to sit inside a
larger tree:

* `output/` was documented as git-ignored, but no `.gitignore` shipped here, so
  a separated copy inherited nothing and a contributor could commit generated
  artifacts against the project's own stated invariant;
* five markdown links pointed at `docs/line-set.md` through `../../` and
  resolved outside the repository root, so they were broken in every separated
  copy — including three that ship inside the rendered manuscript;
* the documented validation contract invoked `ruff`, which was declared in
  neither `pyproject.toml` nor `uv.lock`, so following the contract from a clean
  clone either failed or picked up an ambient, unpinned tool;
* the render instructions were `cd ../../../template`, a path that only resolves
  inside one particular monorepo layout.

Each check below is paired with a positive control, because a checker that
cannot fail proves nothing about the property it claims to hold.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

try:  # ``tomllib`` entered the standard library in 3.11.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - depends on the interpreter
    tomllib = None  # type: ignore[assignment]

#: The package itself runs on the declared ``>=3.10`` floor; only these
#: pyproject-reading gates need a TOML parser, so they skip rather than
#: making the whole module uncollectable on 3.10.
needs_tomllib = pytest.mark.skipif(
    tomllib is None,
    reason="reading pyproject.toml needs tomllib, added to the standard library in Python 3.11",
)

ROOT = Path(__file__).resolve().parent.parent

#: Directories that hold generated, vendored, or environment content. They are
#: not part of the repository's own prose and must not be scanned.
UNSCANNED = frozenset(
    {
        ".git",
        ".venv",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".benchmarks",
        "__pycache__",
        "output",
        "htmlcov",
        "dist",
        "build",
        "node_modules",
    }
)

#: Markdown files this repository is known to ship. Asserted present so a scan
#: that silently found nothing cannot read as a pass.
ANCHOR_DOCS = (
    Path("README.md"),
    Path("AGENTS.md"),
    Path("STANDALONE.md"),
    Path("docs/README.md"),
    Path("docs/development.md"),
    Path("manuscript/01_introduction.md"),
    Path("manuscript/01b_line_set_relationship.md"),
    Path(".agents/skills/black-line/SKILL.md"),
)

_MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
_URL_SCHEME = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]*:")


def _markdown_files(root: Path) -> list[Path]:
    """Every markdown file that is part of the repository's own content."""

    found: list[Path] = []
    for path in sorted(root.rglob("*.md")):
        relative = path.relative_to(root)
        if UNSCANNED.intersection(relative.parts):
            continue
        found.append(path)
    return found


def _escaping_links(root: Path) -> list[tuple[str, str]]:
    """Relative markdown links whose target resolves outside ``root``."""

    escaping: list[tuple[str, str]] = []
    for path in _markdown_files(root):
        text = path.read_text(encoding="utf-8")
        for target in _MARKDOWN_LINK.findall(text):
            if target.startswith("#") or target.startswith("//"):
                continue
            if _URL_SCHEME.match(target):
                continue
            cleaned = target.split("#", 1)[0].split("{", 1)[0]
            if not cleaned:
                continue
            resolved = (path.parent / cleaned).resolve()
            try:
                resolved.relative_to(root)
            except ValueError:
                escaping.append((str(path.relative_to(root)), target))
    return escaping


# --- the repository ships its own ignore rules --------------------------------

#: Generated paths the project's own documentation asserts are ignored.
MUST_BE_IGNORED = (
    "output/figures/figure_registry.json",
    "output/pdf/black_line_combined.pdf",
    "src/black_line/__pycache__/evaluator.cpython-312.pyc",
    "src/black_line.egg-info/PKG-INFO",
    ".coverage",
    ".coverage.project",
    "coverage_project.json",
    "htmlcov/index.html",
    ".venv/bin/python",
    "dist/black_line-0.4.0.tar.gz",
)

#: Paths that are the repository's actual content. If the ignore rules swallow
#: one of these, the rules are wrong in the other direction.
MUST_NOT_BE_IGNORED = (
    "src/black_line/evaluator.py",
    "tests/test_standalone_contract.py",
    "manuscript/01_introduction.md",
    "data/claim_ledger.yaml",
    "README.md",
    "STANDALONE.md",
    "pyproject.toml",
)


def _ignored_by(repository: Path, paths: tuple[str, ...]) -> set[str]:
    """Return which of ``paths`` git considers ignored inside ``repository``."""

    result = subprocess.run(  # noqa: S603
        ["git", "check-ignore", "--stdin"],
        cwd=repository,
        input="\n".join(paths),
        capture_output=True,
        text=True,
        timeout=60,
    )
    # git exits 1 when nothing matched, which is a real answer, not an error.
    assert result.returncode in (0, 1), result.stderr
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _throwaway_repository(tmp_path: Path, gitignore: str | None) -> Path:
    """A real empty git repository, optionally carrying one ``.gitignore``.

    Rules are evaluated against a repository that contains nothing else, so the
    answer is attributable to the file under test rather than to whatever tree
    this checkout is sitting in — which is exactly the confusion that let the
    missing ``.gitignore`` go unnoticed.
    """

    repository = tmp_path / "probe"
    repository.mkdir()
    subprocess.run(  # noqa: S603
        ["git", "init", "--quiet"], cwd=repository, check=True, timeout=60
    )
    if gitignore is not None:
        (repository / ".gitignore").write_text(gitignore, encoding="utf-8")
    return repository


@pytest.fixture()
def _git() -> None:
    if shutil.which("git") is None:
        pytest.skip("git is not installed, so ignore rules cannot be evaluated")


def test_the_repository_ships_its_own_gitignore() -> None:
    """A separated copy must not inherit this invariant from a parent tree."""

    ignore_file = ROOT / ".gitignore"
    assert ignore_file.is_file(), (
        "docs assert that output/ is git-ignored; without a .gitignore in this "
        "repository that is only true inside some larger tree"
    )
    assert ignore_file.read_text(encoding="utf-8").strip(), "an empty ignore file"


def test_the_shipped_gitignore_covers_every_documented_generated_path(
    _git: None, tmp_path: Path
) -> None:
    """Real git semantics, in a repository holding nothing but this file."""

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    repository = _throwaway_repository(tmp_path, gitignore)

    ignored = _ignored_by(repository, MUST_BE_IGNORED)
    assert set(MUST_BE_IGNORED) - ignored == set(), sorted(
        set(MUST_BE_IGNORED) - ignored
    )

    kept = _ignored_by(repository, MUST_NOT_BE_IGNORED)
    assert kept == set(), f"the ignore rules swallow real content: {sorted(kept)}"


def test_without_the_shipped_gitignore_nothing_is_ignored(
    _git: None, tmp_path: Path
) -> None:
    """Positive control: the file under test is what produces the result above.

    Without it the same probe repository ignores none of the generated paths —
    which is precisely the state a clone of this project used to arrive in.
    """

    repository = _throwaway_repository(tmp_path, gitignore=None)
    assert _ignored_by(repository, MUST_BE_IGNORED) == set()


# --- every relative link resolves inside this repository ----------------------


def test_the_markdown_scan_is_not_vacuous() -> None:
    """A link sweep over zero files would make the next test meaningless."""

    scanned = {path.relative_to(ROOT) for path in _markdown_files(ROOT)}
    missing = [str(doc) for doc in ANCHOR_DOCS if doc not in scanned]
    assert not missing, missing
    assert len(scanned) >= 30, len(scanned)

    links = sum(
        len(_MARKDOWN_LINK.findall(path.read_text(encoding="utf-8")))
        for path in _markdown_files(ROOT)
    )
    assert links >= 20, links


def test_no_relative_markdown_link_escapes_the_repository_root() -> None:
    """Orientation links must name a repository, not a path out of this one."""

    escaping = _escaping_links(ROOT)
    assert escaping == [], escaping


def test_the_escaping_link_check_can_fail(tmp_path: Path) -> None:
    """Positive control: a planted `../../` link must be reported."""

    inner = tmp_path / "repo" / "manuscript"
    inner.mkdir(parents=True)
    (tmp_path / "repo" / "ok.md").write_text(
        "[inside](manuscript/planted.md)\n", encoding="utf-8"
    )
    (inner / "planted.md").write_text(
        "[out](../../docs/line-set.md) and [url](https://example.org/x)\n",
        encoding="utf-8",
    )
    escaping = _escaping_links(tmp_path / "repo")
    assert [target for _path, target in escaping] == ["../../docs/line-set.md"]


# --- the documented contract runs from this repository's declarations ---------

#: Files whose fenced shell blocks are the project's stated validation contract.
CONTRACT_DOCS = (
    Path("README.md"),
    Path("AGENTS.md"),
    Path("docs/development.md"),
)

#: Invocation shapes that name no external tool.
_PYTHON_RUNNERS = frozenset({"python", "python3", "-m"})

_FENCE = re.compile(r"```(?:bash|sh|console)\n(.*?)```", re.DOTALL)


def _declared_dev_tools() -> set[str]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    group = data["dependency-groups"]["dev"]
    return {re.split(r"[<>=!\[ ]", item, maxsplit=1)[0].strip() for item in group}


def _invoked_tools(text: str) -> set[str]:
    """External tools a ``uv run`` line in a fenced block would execute."""

    tools: set[str] = set()
    for block in _FENCE.findall(text):
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped.startswith("uv run "):
                continue
            words = stripped.split()[2:]
            if not words or words[0] in _PYTHON_RUNNERS:
                continue
            tools.add(words[0])
    return tools


@needs_tomllib
def test_every_tool_the_contract_invokes_is_declared_and_pinned() -> None:
    """`ruff` was in the contract and in neither pyproject.toml nor uv.lock."""

    declared = _declared_dev_tools()
    lock = (ROOT / "uv.lock").read_text(encoding="utf-8")
    invoked: set[str] = set()
    for document in CONTRACT_DOCS:
        invoked |= _invoked_tools((ROOT / document).read_text(encoding="utf-8"))

    assert {"pytest", "ruff"} <= invoked, (
        f"the contract scan found {sorted(invoked)}; it must see the real "
        "commands or the check below is vacuous"
    )
    undeclared = sorted(tool for tool in invoked if tool not in declared)
    assert not undeclared, undeclared
    unpinned = sorted(
        tool for tool in invoked if f'name = "{tool}"' not in lock.replace("_", "-")
    )
    assert not unpinned, unpinned


@needs_tomllib
def test_the_undeclared_tool_check_can_fail() -> None:
    """Positive control: an undeclared tool in a contract block is reported."""

    planted = "```bash\nuv run mypy src\nuv run python scripts/check_registry.py\n```\n"
    assert _invoked_tools(planted) == {"mypy"}
    assert "mypy" not in _declared_dev_tools()


@needs_tomllib
def test_ruff_carries_a_configuration_in_this_repository() -> None:
    """An unconfigured ruff makes "ruff clean" a claim about someone's defaults."""

    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    ruff = data["tool"]["ruff"]
    assert ruff["target-version"] == "py310", ruff
    assert data["project"]["requires-python"] == ">=3.10"
    assert ruff["lint"]["select"], "an empty rule selection lints nothing"


# --- the code the contract lints is actually lint-clean and format-clean ------

#: The trees the documented contract lints. Extending the contract needs to
#: keep the gate running the same roots, or the gate and the prose can drift.
CONTRACT_LINT_TREES = ("src", "tests", "scripts")


@pytest.fixture()
def _ruff() -> None:
    if shutil.which("ruff") is None:
        pytest.skip("ruff is not installed, so the lint and format gates cannot run")


def _run_ruff(*args: str) -> subprocess.CompletedProcess[str]:
    """Run pinned ruff from the repository root, which carries its config."""
    return subprocess.run(  # noqa: S603
        ["ruff", *args], cwd=ROOT, capture_output=True, text=True, timeout=120
    )


def test_the_shipped_code_is_ruff_lint_clean(_ruff: None) -> None:
    """`ruff check src tests scripts` is the documented gate; it must pass.

    Declaring `ruff` in the dev extra (the check above) is not the same as the
    code actually being clean: a lint regression can ship with every declaration
    test green. This is the executable half of that claim.
    """
    result = _run_ruff("check", *CONTRACT_LINT_TREES)
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_shipped_code_is_ruff_format_clean(_ruff: None) -> None:
    """`ruff format --check src tests scripts` is the documented gate; it must pass.

    Formatting regressed silently once (two figure modules shipped unformatted
    while `ruff check` stayed green, because check does not see layout). This
    test is the reason that class of drift now fails the suite instead of a
    separate manual step.
    """
    result = _run_ruff("format", "--check", *CONTRACT_LINT_TREES)
    assert result.returncode == 0, result.stdout + result.stderr


def test_the_ruff_format_gate_can_fail(_ruff: None, tmp_path: Path) -> None:
    """Positive control: a file ruff would reformat must fail the gate.

    The two gates above prove nothing if they cannot fail; this shows the
    underlying ``ruff format --check`` really does reject drifting layout.
    """
    bad = tmp_path / "unformatted.py"
    bad.write_text("def f():\n    return  1\n", encoding="utf-8")
    result = subprocess.run(  # noqa: S603
        ["ruff", "format", "--check", str(bad)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode != 0


# --- rendering is documented path-independently -------------------------------

#: The engine that renders the manuscript. Named as a repository, so the
#: instruction survives being read outside any particular directory layout.
TEMPLATE_REPO = "https://github.com/docxology/template"

_MONOREPO_CD = re.compile(r"cd\s+(?:\.\./)+template\b")


def test_no_document_tells_a_reader_to_cd_into_a_sibling_template() -> None:
    """`cd ../../../template` resolves only inside one private layout."""

    offenders = [
        str(path.relative_to(ROOT))
        for path in _markdown_files(ROOT)
        if _MONOREPO_CD.search(path.read_text(encoding="utf-8"))
    ]
    assert not offenders, offenders


def test_the_monorepo_cd_check_can_fail() -> None:
    """Positive control: the pattern really does match the shape it forbids."""

    assert _MONOREPO_CD.search("cd ../../../template")
    assert _MONOREPO_CD.search("cd ../template")
    assert not _MONOREPO_CD.search("cd ${TEMPLATE_ROOT}")


def test_rendering_is_documented_as_a_named_external_repository() -> None:
    """The external dependency must be declared, not hidden and not implied."""

    development = (ROOT / "docs" / "development.md").read_text(encoding="utf-8")
    assert TEMPLATE_REPO in development
    assert "TEMPLATE_ROOT" in development, (
        "the render recipe must take the engine's location as a parameter"
    )
    assert "cannot produce" in development, (
        "the limit must be stated plainly, not left for a reader to infer"
    )

    standalone = (ROOT / "STANDALONE.md").read_text(encoding="utf-8")
    assert TEMPLATE_REPO in standalone
    assert "unrun" in standalone
