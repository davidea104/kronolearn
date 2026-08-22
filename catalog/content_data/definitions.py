"""Strict parsing for the versioned learning-content corpus."""

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

PRIMARY_TRACK_TITLE = "Crea tu registro de gastos con agentes y SDD"
SECONDARY_TRACK_TITLE = "Fundamentos de negocio para equipos técnicos"
SECONDARY_LEGACY_TITLE = "Fundamentos de negocio para equipos tecnicos"
RATINGS = frozenset({"OPTIMAL", "PARTIAL", "INCORRECT"})


@dataclass(frozen=True, slots=True)
class ChoiceDefinition:
    position: int
    text: str
    rating: str
    consequence: str
    explanation: str


@dataclass(frozen=True, slots=True)
class LabDefinition:
    objective: str
    initial_prompt: str
    expected_artifact: str
    verification_checklist: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LegacyFingerprintDefinition:
    title: str
    learning_objective: str
    lesson_text: str
    case_prompt: str
    source: str
    choices: tuple[ChoiceDefinition, ...]
    lab: LabDefinition | None


@dataclass(frozen=True, slots=True)
class ContentUnitDefinition:
    position: int
    source_marker: str
    title: str
    learning_objective: str
    lesson_text: str
    case_prompt: str
    source: str
    reviewed_on: date
    choices: tuple[ChoiceDefinition, ...]
    lab: LabDefinition | None
    legacy_fingerprint: LegacyFingerprintDefinition | None


@dataclass(frozen=True, slots=True)
class ModuleDefinition:
    title: str
    objective: str
    source: str
    reviewed_on: date
    units: tuple[ContentUnitDefinition, ...]


@dataclass(frozen=True, slots=True)
class TrackDefinition:
    title: str
    description: str
    audience: str
    source: str
    reviewed_on: date
    legacy_titles: tuple[str, ...]
    module: ModuleDefinition


def _mapping(value: Any, path: str) -> dict[str, Any]:
    if type(value) is not dict:
        raise ValueError(f"{path} must be an object.")
    return value


def _list(value: Any, path: str) -> list[Any]:
    if type(value) is not list:
        raise ValueError(f"{path} must be an array.")
    return value


def _closed(mapping: dict[str, Any], keys: set[str], path: str) -> None:
    missing = keys - mapping.keys()
    unknown = mapping.keys() - keys
    if missing or unknown:
        raise ValueError(
            f"{path} has invalid keys; missing={sorted(missing)}, "
            f"unknown={sorted(unknown)}."
        )


def _text(value: Any, path: str) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{path} must be a non-empty string.")
    return value.strip()


def _positive_int(value: Any, path: str) -> int:
    if type(value) is not int or value < 1:
        raise ValueError(f"{path} must be a positive integer.")
    return value


def _reviewed_on(value: Any, path: str) -> date:
    text = _text(value, path)
    try:
        parsed = date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"{path} must be an ISO date.") from None
    if parsed > datetime.now(UTC).date():
        raise ValueError(f"{path} cannot be in the future.")
    return parsed


def _choice(value: Any, path: str) -> ChoiceDefinition:
    item = _mapping(value, path)
    _closed(
        item,
        {"position", "text", "rating", "consequence", "explanation"},
        path,
    )
    rating = _text(item["rating"], f"{path}.rating")
    if rating not in RATINGS:
        raise ValueError(f"{path}.rating is invalid.")
    return ChoiceDefinition(
        position=_positive_int(item["position"], f"{path}.position"),
        text=_text(item["text"], f"{path}.text"),
        rating=rating,
        consequence=_text(item["consequence"], f"{path}.consequence"),
        explanation=_text(item["explanation"], f"{path}.explanation"),
    )


def _choices(value: Any, path: str) -> tuple[ChoiceDefinition, ...]:
    choices = tuple(
        _choice(item, f"{path}[{index}]")
        for index, item in enumerate(_list(value, path))
    )
    if len(choices) not in (3, 4):
        raise ValueError(f"{path} must contain three or four choices.")
    if tuple(choice.position for choice in choices) != tuple(
        range(1, len(choices) + 1)
    ):
        raise ValueError(f"{path} positions must be consecutive from one.")
    normalized_texts = {choice.text.casefold() for choice in choices}
    if len(normalized_texts) != len(choices):
        raise ValueError(f"{path} choice texts must be unique.")
    if not any(choice.rating == "OPTIMAL" for choice in choices):
        raise ValueError(f"{path} must contain an optimal choice.")
    return choices


def _lab(value: Any, path: str) -> LabDefinition | None:
    if value is None:
        return None
    item = _mapping(value, path)
    _closed(
        item,
        {
            "objective",
            "initial_prompt",
            "expected_artifact",
            "verification_checklist",
        },
        path,
    )
    checklist = tuple(
        _text(entry, f"{path}.verification_checklist[{index}]")
        for index, entry in enumerate(
            _list(item["verification_checklist"], f"{path}.verification_checklist")
        )
    )
    if not checklist:
        raise ValueError(f"{path}.verification_checklist cannot be empty.")
    return LabDefinition(
        objective=_text(item["objective"], f"{path}.objective"),
        initial_prompt=_text(item["initial_prompt"], f"{path}.initial_prompt"),
        expected_artifact=_text(item["expected_artifact"], f"{path}.expected_artifact"),
        verification_checklist=checklist,
    )


def _legacy_fingerprint(value: Any, path: str) -> LegacyFingerprintDefinition | None:
    if value is None:
        return None
    item = _mapping(value, path)
    _closed(
        item,
        {
            "title",
            "learning_objective",
            "lesson_text",
            "case_prompt",
            "source",
            "choices",
            "lab",
        },
        path,
    )
    return LegacyFingerprintDefinition(
        title=_text(item["title"], f"{path}.title"),
        learning_objective=_text(
            item["learning_objective"], f"{path}.learning_objective"
        ),
        lesson_text=_text(item["lesson_text"], f"{path}.lesson_text"),
        case_prompt=_text(item["case_prompt"], f"{path}.case_prompt"),
        source=_text(item["source"], f"{path}.source"),
        choices=_choices(item["choices"], f"{path}.choices"),
        lab=_lab(item["lab"], f"{path}.lab"),
    )


def _unit(value: Any, path: str) -> ContentUnitDefinition:
    item = _mapping(value, path)
    _closed(
        item,
        {
            "position",
            "source_marker",
            "title",
            "learning_objective",
            "lesson_text",
            "case_prompt",
            "source",
            "reviewed_on",
            "choices",
            "lab",
            "legacy_fingerprint",
        },
        path,
    )
    source_marker = _text(item["source_marker"], f"{path}.source_marker")
    source = _text(item["source"], f"{path}.source")
    if source_marker not in source:
        raise ValueError(f"{path}.source must contain its source marker.")
    return ContentUnitDefinition(
        position=_positive_int(item["position"], f"{path}.position"),
        source_marker=source_marker,
        title=_text(item["title"], f"{path}.title"),
        learning_objective=_text(
            item["learning_objective"], f"{path}.learning_objective"
        ),
        lesson_text=_text(item["lesson_text"], f"{path}.lesson_text"),
        case_prompt=_text(item["case_prompt"], f"{path}.case_prompt"),
        source=source,
        reviewed_on=_reviewed_on(item["reviewed_on"], f"{path}.reviewed_on"),
        choices=_choices(item["choices"], f"{path}.choices"),
        lab=_lab(item["lab"], f"{path}.lab"),
        legacy_fingerprint=_legacy_fingerprint(
            item["legacy_fingerprint"], f"{path}.legacy_fingerprint"
        ),
    )


def _module(value: Any, path: str) -> ModuleDefinition:
    item = _mapping(value, path)
    _closed(item, {"title", "objective", "source", "reviewed_on", "units"}, path)
    units = tuple(
        _unit(unit, f"{path}.units[{index}]")
        for index, unit in enumerate(_list(item["units"], f"{path}.units"))
    )
    return ModuleDefinition(
        title=_text(item["title"], f"{path}.title"),
        objective=_text(item["objective"], f"{path}.objective"),
        source=_text(item["source"], f"{path}.source"),
        reviewed_on=_reviewed_on(item["reviewed_on"], f"{path}.reviewed_on"),
        units=units,
    )


def _track(value: Any, path: str) -> TrackDefinition:
    item = _mapping(value, path)
    _closed(
        item,
        {
            "title",
            "description",
            "audience",
            "source",
            "reviewed_on",
            "legacy_titles",
            "module",
        },
        path,
    )
    legacy_titles = tuple(
        _text(title, f"{path}.legacy_titles[{index}]")
        for index, title in enumerate(
            _list(item["legacy_titles"], f"{path}.legacy_titles")
        )
    )
    return TrackDefinition(
        title=_text(item["title"], f"{path}.title"),
        description=_text(item["description"], f"{path}.description"),
        audience=_text(item["audience"], f"{path}.audience"),
        source=_text(item["source"], f"{path}.source"),
        reviewed_on=_reviewed_on(item["reviewed_on"], f"{path}.reviewed_on"),
        legacy_titles=legacy_titles,
        module=_module(item["module"], f"{path}.module"),
    )


def _validate_corpus(definitions: tuple[TrackDefinition, ...]) -> None:
    expected = (
        (PRIMARY_TRACK_TITLE, 7, True),
        (SECONDARY_TRACK_TITLE, 3, False),
    )
    if len(definitions) != len(expected):
        raise ValueError("The corpus must contain exactly two tracks.")

    markers = []
    for definition, (title, unit_count, requires_labs) in zip(
        definitions, expected, strict=True
    ):
        if definition.title != title:
            raise ValueError("The corpus track titles or order are invalid.")
        units = definition.module.units
        if len(units) != unit_count:
            raise ValueError(f"{title} has an invalid unit count.")
        if tuple(unit.position for unit in units) != tuple(range(1, unit_count + 1)):
            raise ValueError(f"{title} unit positions must be consecutive from one.")
        if any((unit.lab is not None) != requires_labs for unit in units):
            raise ValueError(f"{title} has an invalid laboratory distribution.")
        markers.extend(unit.source_marker for unit in units)

    if SECONDARY_LEGACY_TITLE not in definitions[1].legacy_titles:
        raise ValueError("The secondary legacy title alias is required.")
    if len(markers) != len(set(markers)):
        raise ValueError("Source markers must be unique.")


def load_definitions(path: str | Path | None = None) -> tuple[TrackDefinition, ...]:
    """Load and fully validate immutable definitions from a JSON document."""
    source_path = (
        Path(path)
        if path is not None
        else Path(__file__).with_name("learning_units.json")
    )
    try:
        document = json.loads(source_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("The learning-content document is not valid JSON.") from exc

    root = _mapping(document, "document")
    _closed(root, {"tracks"}, "document")
    definitions = tuple(
        _track(track, f"document.tracks[{index}]")
        for index, track in enumerate(_list(root["tracks"], "document.tracks"))
    )
    _validate_corpus(definitions)
    return definitions
