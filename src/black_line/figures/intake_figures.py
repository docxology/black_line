"""The intake plate: what Stage 1 does with a declaration it cannot use.

Every other executed figure in this project feeds the evaluator declarations
it can read. This one feeds it declarations it cannot — a blank description, a
tag set declared as a bare string, an evidence collection that is a number, a
date the parser refuses — and draws what comes back. The point is that
something does come back: intake normalization is written to turn malformed
input into a status plus review notes rather than into an exception, and the
only honest way to show that is to run it.

Nothing here is restated. The status, the note text, and the finding count in
every row are read off a real :func:`~black_line.evaluate_work` call over the
shipped registry at a pinned review date.
"""

from __future__ import annotations

from black_line import BLACK_PRACTICES, WorkAttempt, evaluate_work
from black_line.figures.scenarios import INTAKE_AS_OF, intake_assessments
from black_line.figures.svg import (
    BLACK,
    BODY_FONT,
    GRID,
    INK,
    MUTED,
    PALE,
    PANEL,
    PAPER,
    STATUS_FILL,
    STATUS_GLYPH,
    WHITE,
    canvas_writers,
    esc,
)

WIDTH = 1400


def _assessed(
    cases: tuple[tuple[str, WorkAttempt], ...] | None,
) -> tuple[tuple[str, object], ...]:
    """Evaluate an override battery, or return the pinned one.

    The override is what lets a test prove this plate follows its data: a panel
    that agreed with the pinned battery by coincidence would survive every
    assertion about the pinned battery alone.
    """

    if cases is None:
        return intake_assessments()
    return tuple(
        (label, evaluate_work(attempt, BLACK_PRACTICES, as_of=INTAKE_AS_OF))
        for label, attempt in cases
    )


def intake_rows(
    cases: tuple[tuple[str, WorkAttempt], ...] | None = None,
) -> tuple[tuple[str, str, int, tuple[str, ...]], ...]:
    """One row per malformed declaration: label, status, findings, notes."""

    return tuple(
        (
            label,
            assessment.status.value,
            len(assessment.findings),
            assessment.intake_notes,
        )
        for label, assessment in _assessed(cases)
    )


def intake_blocked(
    cases: tuple[tuple[str, WorkAttempt], ...] | None = None,
) -> tuple[str, ...]:
    """Declarations whose intake defect stops scoring outright, in battery order.

    A blocking defect is a ``NEEDS_REWORK`` with no findings: the evaluator
    refused to score rather than reaching a practice and failing it.
    """

    return tuple(
        label
        for label, status, findings, _notes in intake_rows(cases)
        if not findings and status == "NEEDS_REWORK"
    )


def intake_unmatched(
    cases: tuple[tuple[str, WorkAttempt], ...] | None = None,
) -> tuple[str, ...]:
    """Declarations that reach no practice at all rather than being blocked.

    Distinct from :func:`intake_blocked`: dropping a malformed tag declaration
    leaves an attempt with no tags, so no practice applies and the status is a
    coverage statement, not a rejection.
    """

    return tuple(
        label
        for label, status, _findings, _notes in intake_rows(cases)
        if status == "OUTSIDE_SCOPE"
    )


def intake_scored(
    cases: tuple[tuple[str, WorkAttempt], ...] | None = None,
) -> tuple[str, ...]:
    """The declarations that are still scored after the malformed part is dropped."""

    return tuple(
        label for label, _status, findings, _notes in intake_rows(cases) if findings
    )


def intake_note_total(cases: tuple[tuple[str, WorkAttempt], ...] | None = None) -> int:
    """Every intake note the battery produces."""

    return sum(len(notes) for _label, _status, _findings, notes in intake_rows(cases))


def intake_notes_svg(
    cases: tuple[tuple[str, WorkAttempt], ...] | None = None,
) -> str:
    """Draw the executed intake battery: malformed input to status plus notes."""

    rows = intake_rows(cases)
    text, headline, _pill, floor = canvas_writers(WIDTH)
    left_x = 64
    status_x = 470
    notes_x = 760
    body = [
        f'<rect width="100%" height="100%" fill="{PAPER}"/>',
        headline(left_x, 58, "A declaration the evaluator cannot read still returns"),
        text(
            left_x,
            88,
            "Each row is one real evaluate_work call on a deliberately malformed WorkAttempt; the notes are the ones it returned.",
            size=17,
            fill=MUTED,
        ),
        text(
            left_x,
            114,
            f"EXECUTED INTAKE BATTERY · REVIEW DATE {INTAKE_AS_OF.isoformat()} · "
            f"{len(rows)} DECLARATIONS · {intake_note_total(cases)} NOTES · 0 EXCEPTIONS",
            size=17,
            fill=MUTED,
            weight="700",
        ),
        text(
            left_x,
            152,
            f"{len(intake_blocked(cases))} of the {len(rows)} block scoring outright and "
            f"{len(intake_unmatched(cases))} reaches no practice once its tag declaration is dropped; "
            f"the other {len(intake_scored(cases))} are scored normally.",
            size=17,
            fill=MUTED,
        ),
    ]
    header_y = 200
    for label, x in (
        ("malformed declaration", left_x),
        ("status", status_x),
        ("intake notes returned", notes_x),
    ):
        body.append(text(x, header_y, label, size=17, weight="700", fill=BLACK))
    body.append(
        f'<line x1="{left_x}" y1="{header_y + 12}" x2="{WIDTH - left_x}" '
        f'y2="{header_y + 12}" stroke="{GRID}" stroke-width="1.6"/>'
    )

    y = header_y + 30
    for index, (label, status, findings, notes) in enumerate(rows):
        row_h = 40 + 26 * len(notes)
        body.append(
            f'<rect x="{left_x}" y="{y}" width="{WIDTH - 2 * left_x}" height="{row_h - 8}" '
            f'rx="10" fill="{PANEL if index % 2 == 0 else PALE}" stroke="{GRID}" stroke-width="1"/>'
        )
        body.append(text(left_x + 16, y + 30, label, size=17, weight="700"))
        body.append(
            text(
                left_x + 16,
                y + 54,
                f"{findings} practice finding" + ("" if findings == 1 else "s"),
                size=17,
                fill=MUTED,
            )
        )
        fill = STATUS_FILL.get(status, MUTED)
        body.append(
            f'<rect x="{status_x}" y="{y + 12}" width="28" height="28" rx="6" fill="{fill}"/>'
        )
        body.append(
            f'<text x="{status_x + 14}" y="{y + 12 + 14 + floor / 3}" fill="{WHITE}" '
            f'text-anchor="middle" font-family="{BODY_FONT}" font-size="{floor}px" '
            f'font-weight="700">{esc(STATUS_GLYPH.get(status, "?"))}</text>'
        )
        body.append(text(status_x + 40, y + 32, status, size=17, weight="700"))
        for note_index, note in enumerate(notes):
            body.append(
                text(notes_x, y + 32 + note_index * 26, f"· {note}", size=17, fill=INK)
            )
        y += row_h

    boundary_y = y + 44
    body.append(text(left_x, boundary_y, "Boundary", size=17, fill=BLACK, weight="700"))
    body.append(
        text(
            left_x + 136,
            boundary_y,
            "Surviving malformed input is a robustness property of the intake stage, not tolerance of a bad declaration.",
            size=17,
            fill=MUTED,
        )
    )
    body.append(
        text(
            left_x + 136,
            boundary_y + 24,
            "A note asks the declarer to fix something; it does not verify anything that was declared correctly.",
            size=17,
            fill=MUTED,
        )
    )
    height = boundary_y + 60
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-labelledby="intake-title intake-desc">'
        f'<title id="intake-title">Intake normalization over malformed declarations</title>'
        f'<desc id="intake-desc">A table of {len(rows)} deliberately malformed work attempts, each '
        f"evaluated once at review date {INTAKE_AS_OF.isoformat()}, listing the returned status, the "
        f"number of practice findings, and every intake note. {len(intake_blocked(cases))} rows are blocked "
        f"before scoring and {len(intake_unmatched(cases))} reaches no practice at all; the remaining "
        f"{len(intake_scored(cases))} are scored after the unusable part of the declaration is dropped and "
        f"named in a note.</desc>"
        f"{''.join(body)}</svg>"
    )
