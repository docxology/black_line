from dataclasses import dataclass

from .intake import is_scalar_text
from .model import BlackPractice, PracticeKind


@dataclass(frozen=True)
class RegistryDefect:
    code: str
    detail: str


def registry_defects(
    practices: tuple[BlackPractice, ...],
) -> tuple[RegistryDefect, ...]:
    defects = []
    seen = set()
    for index, practice in enumerate(practices):
        if not isinstance(practice, BlackPractice):
            defects.append(
                RegistryDefect(
                    "record_type",
                    f"practice registry entry {index} is not a BlackPractice record",
                )
            )
            continue
        if not is_scalar_text(practice.id) or not practice.id.strip():
            defects.append(
                RegistryDefect(
                    "id_text",
                    f"practice registry entry {index} has blank or non-text id",
                )
            )
        if any(
            not is_scalar_text(value) or not value.strip()
            for value in (practice.title, practice.wire)
        ):
            defects.append(
                RegistryDefect(
                    "title_wire_text",
                    f"practice registry entry {index} has blank or non-text fields (blank title or wire, or unusable id)",
                )
            )
        if is_scalar_text(practice.id):
            if practice.id in seen:
                defects.append(
                    RegistryDefect(
                        "duplicate_id",
                        f"practice registry contains duplicate id '{practice.id}'",
                    )
                )
            seen.add(practice.id)
        tags = practice.tags
        if (
            not isinstance(tags, frozenset)
            or not tags
            or any(not is_scalar_text(tag) or not tag.strip() for tag in tags)
        ):
            defects.append(
                RegistryDefect(
                    "tags_shape", f"entry {index} has malformed tags; unreachable"
                )
            )
        elif any(tag != tag.strip().lower() for tag in tags):
            defects.append(
                RegistryDefect(
                    "tags_not_normalized", f"entry {index} has unmatchable tags"
                )
            )
        labels = practice.required_evidence
        if (
            not isinstance(labels, tuple)
            or not labels
            or any(not is_scalar_text(label) or not label.strip() for label in labels)
        ):
            defects.append(
                RegistryDefect(
                    "required_labels_shape",
                    f"entry {index} has malformed required evidence; expected populated tuple of text",
                )
            )
        else:
            if any(label != label.strip().lower() for label in labels):
                defects.append(
                    RegistryDefect(
                        "required_labels_not_normalized",
                        f"entry {index} has unmatchable required labels",
                    )
                )
            if len(set(labels)) != len(labels):
                defects.append(
                    RegistryDefect(
                        "required_labels_duplicate",
                        f"entry {index} has duplicate required labels",
                    )
                )
        if not isinstance(practice.kind, PracticeKind):
            defects.append(
                RegistryDefect("kind_type", f"entry {index} has an invalid kind")
            )
    return tuple(defects)
