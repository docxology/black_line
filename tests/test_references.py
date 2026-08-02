"""Close the manuscript's citation set against its bibliography, both ways.

Nothing in this project used to read `manuscript/references.bib`. An entry could
be added and never cited, or a citation key could be misspelled and simply
vanish from the rendered bibliography — the PDF still builds, and the only
symptom is a reference a reader cannot follow.

Two directions are checked. Every prose citation must resolve to an entry, so a
typo is a test failure rather than a silently dropped reference. Every entry
must be cited somewhere, so the bibliography stays a record of what this
manuscript actually uses rather than a reading list. Each entry is also checked
for the fields that make a citation verifiable at all: an author, a title, a
year, and a locator (DOI, ISBN, or URL). None of that establishes the citation
is *apt* — only that it is resolvable and used.
"""

from __future__ import annotations

import re
from pathlib import Path

MANUSCRIPT = Path(__file__).resolve().parent.parent / "manuscript"
BIB = MANUSCRIPT / "references.bib"

_ENTRY = re.compile(r"^@(\w+)\s*\{\s*([^,\s]+)\s*,", re.MULTILINE)
_FIELD = re.compile(r"^\s*(\w+)\s*=", re.MULTILINE)
_CITATION = re.compile(r"\[@([^\]]+)\]")
_LOCATORS = ("doi", "url", "isbn")

#: Prefixes the renderer's formalism filter owns. A citation using one of them
#: names a block in the manuscript, not a bibliography entry.
_FORMALISM_PREFIXES = ("def:", "prop:", "thm:", "lem:", "cor:", "rem:")


def _bib_text() -> str:
    return BIB.read_text(encoding="utf-8")


def bib_entries() -> dict[str, tuple[str, str]]:
    """``key -> (entry type, entry body)`` for every entry in the bibliography."""

    text = _bib_text()
    starts = [
        (match.start(), match.group(1), match.group(2))
        for match in _ENTRY.finditer(text)
    ]
    entries: dict[str, tuple[str, str]] = {}
    for index, (start, kind, key) in enumerate(starts):
        end = starts[index + 1][0] if index + 1 < len(starts) else len(text)
        entries[key] = (kind, text[start:end])
    return entries


def prose_citations() -> dict[str, set[str]]:
    """``citation key -> the manuscript files that cite it``."""

    found: dict[str, set[str]] = {}
    for path in sorted(MANUSCRIPT.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        for group in _CITATION.findall(text):
            for raw in group.split(";"):
                key = raw.strip().lstrip("@").strip()
                if not key or key.startswith(_FORMALISM_PREFIXES):
                    continue
                found.setdefault(key, set()).add(path.name)
    return found


def test_the_citation_scan_is_not_vacuous() -> None:
    """A sweep that found no citations would make both directions meaningless."""

    entries = bib_entries()
    cited = prose_citations()
    assert len(entries) >= 30, len(entries)
    assert len(cited) >= 25, sorted(cited)


def test_every_prose_citation_resolves_to_a_bibliography_entry() -> None:
    unresolved = sorted(set(prose_citations()) - set(bib_entries()))
    assert unresolved == [], unresolved


def test_every_bibliography_entry_is_cited_in_the_prose() -> None:
    """An uncited entry is a reading list, not a reference."""

    uncited = sorted(set(bib_entries()) - set(prose_citations()))
    assert uncited == [], uncited


def test_every_entry_carries_the_fields_a_reader_needs_to_check_it() -> None:
    """Author, title, year, and at least one locator, for every entry."""

    defects: list[str] = []
    for key, (_kind, body) in sorted(bib_entries().items()):
        fields = {name.lower() for name in _FIELD.findall(body)}
        for required in ("author", "title", "year"):
            if required not in fields:
                defects.append(f"{key}: no {required}")
        if not fields.intersection(_LOCATORS):
            defects.append(f"{key}: no doi, url, or isbn")
        year = re.search(r"^\s*year\s*=\s*\{(\d{4})\}", body, re.MULTILINE)
        if year is None:
            defects.append(f"{key}: year is not a four-digit literal")
        elif not 1900 <= int(year.group(1)) <= 2026:
            defects.append(f"{key}: implausible year {year.group(1)}")
    assert defects == [], defects


def test_entry_keys_are_unique() -> None:
    """Duplicate keys silently shadow one another in every BibTeX engine."""

    keys = [match.group(2) for match in _ENTRY.finditer(_bib_text())]
    duplicates = sorted({key for key in keys if keys.count(key) > 1})
    assert duplicates == [], duplicates


def test_the_scholarship_section_situates_every_source_it_introduces() -> None:
    """Each new craft and replication source is named in prose, not only cited.

    A citation key alone can decorate a sentence without saying what the source
    establishes. These entries were added to close two named gaps, so the check
    is that the surname appears in the scholarship prose beside its key.
    """

    scholarship = (MANUSCRIPT / "01c_scholarship.md").read_text(encoding="utf-8")
    for key, surname in (
        ("ryle1949concept", "Ryle"),
        ("aristotle1999ethics", "Aristotle"),
        ("dreyfus1986mind", "Dreyfus"),
        ("schon1983reflective", "Schön"),
        ("sennett2008craftsman", "Sennett"),
        ("collins2010tacit", "Collins"),
        ("claerbout1992electronic", "Claerbout"),
        ("plesser2018reproducibility", "Plesser"),
        ("baker2016survey", "survey"),
        ("osc2015estimating", "psychology studies"),
    ):
        assert f"[@{key}]" in scholarship, key
        assert surname in " ".join(scholarship.split()), surname


def test_the_citation_checks_can_fail() -> None:
    """Positive controls for both directions and for the field check."""

    # A citation the parser must see, and a formalism reference it must not.
    sample = "text [@popper1959logic; @polanyi1958personal] and [@prop:ladder]"
    keys = set()
    for group in _CITATION.findall(sample):
        for raw in group.split(";"):
            key = raw.strip().lstrip("@").strip()
            if key and not key.startswith(_FORMALISM_PREFIXES):
                keys.add(key)
    assert keys == {"popper1959logic", "polanyi1958personal"}

    # A planted entry missing its locator and year must be reported.
    planted = (
        "@book{planted2020nothing,\n  author = {Nobody},\n  title = {Untitled}\n}\n"
    )
    fields = {name.lower() for name in _FIELD.findall(planted)}
    assert "year" not in fields
    assert not fields.intersection(_LOCATORS)
