"""Execute every documented recipe and compare its real output to the doc.

``docs/usage.md`` promises specific behaviour from specific snippets. Nothing
bound those snippets before, and one of them promised a status sweep while
demonstrating a flat one — three independent reasons (a label outside the
registry vocabulary, a label also declared undated, and unrelated unsatisfied
practices) each pinned the status on their own. This module runs each fenced
``python`` block and asserts the printed lines equal the ``text`` block that
follows it, so a broken recipe is a red test rather than a reader's dead end.
"""

import io
import re
from contextlib import redirect_stdout
from pathlib import Path

import pytest

DOCS = Path(__file__).resolve().parent.parent / "docs"

_BLOCK = re.compile(
    r"```python\n(?P<code>.*?)```\n\n```text\n(?P<expected>.*?)```", re.DOTALL
)


def _recipes(name: str) -> list[tuple[int, str, str]]:
    text = (DOCS / name).read_text(encoding="utf-8")
    return [
        (text[: match.start()].count("\n") + 1, match["code"], match["expected"])
        for match in _BLOCK.finditer(text)
    ]


def _run(code: str) -> str:
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        exec(compile(code, "<usage.md>", "exec"), {"__name__": "__usage__"})  # noqa: S102
    return buffer.getvalue()


def test_usage_has_the_expected_number_of_executable_recipes() -> None:
    """A vacuous sweep is itself a defect, so pin that the scan set is non-empty."""

    assert len(_recipes("usage.md")) == 5


@pytest.mark.parametrize("line, code, expected", _recipes("usage.md"))
def test_usage_recipe_prints_what_the_doc_says(
    line: int, code: str, expected: str
) -> None:
    assert _run(code) == expected, f"docs/usage.md recipe near line {line} drifted"


def test_the_recipe_comparison_can_fail() -> None:
    """Positive control: a wrong expected block must not pass."""

    _line, code, expected = _recipes("usage.md")[0]
    assert _run(code) != expected.replace("NEEDS_REWORK", "ALIGNED")


def test_the_staleness_recipe_actually_sweeps() -> None:
    """The recipe's stated purpose — a status that moves — is itself bound."""

    staleness = next(
        (code, expected)
        for _line, code, expected in _recipes("usage.md")
        if "staleness_profile" in code
    )
    statuses = [line.split()[-1] for line in staleness[1].strip().splitlines()]
    assert len(set(statuses)) > 1, "the documented sweep is flat"
