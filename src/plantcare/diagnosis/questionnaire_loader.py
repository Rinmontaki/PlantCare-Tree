
"""Load and validate PlantCare diagnostic questionnaires."""

import json
from pathlib import Path
from typing import Any


MIN_OPTIONS_PER_QUESTION = 3
MAX_OPTIONS_PER_QUESTION = 5
MAX_DIAGNOSTIC_QUESTIONS = 10

VALID_SELECTION_MODES = {"single", "multiple"}


def load_questionnaire(file_path: str | Path) -> dict[str, Any]:
    """Load and validate a questionnaire from a JSON file."""
    # Read the questionnaire using UTF-8 encoding.
    with Path(file_path).open("r", encoding="utf-8") as file:
        questionnaire = json.load(file)

    # Validate the complete structure before returning it.
    _validate_questionnaire(questionnaire)

    return questionnaire


def _validate_questionnaire(data: object) -> None:
    """Validate the questionnaire structure and its questions."""
    if not isinstance(data, dict):
        raise ValueError("Questionnaire must be a JSON object.")

    max_questions = data.get("max_questions")
    questions = data.get("questions")

    # Enforce the maximum number of visible questions.
    if (
        type(max_questions) is not int
        or not 1 <= max_questions <= MAX_DIAGNOSTIC_QUESTIONS
    ):
        raise ValueError("max_questions must be between 1 and 10.")

    if not isinstance(questions, list) or not questions:
        raise ValueError("Questionnaire must contain questions.")

    if len(questions) > max_questions:
        raise ValueError("Question count exceeds max_questions.")

    registered_questions: set[str] = set()
    registered_options: set[str] = set()

    for question in questions:
        _validate_question(
            question,
            registered_questions,
            registered_options,
        )


def _validate_question(
    question: object,
    registered_questions: set[str],
    registered_options: set[str],
) -> None:
    """Validate a question and register its option identifiers."""
    if not isinstance(question, dict):
        raise ValueError("Each question must be a JSON object.")

    question_id = _require_text(question.get("id"), "Question ID")
    _require_text(question.get("text"), "Question text")

    # Prevent duplicated question identifiers.
    if question_id in registered_questions:
        raise ValueError(f"Duplicate question ID: {question_id}")

    selection_mode = question.get("selection_mode")

    if selection_mode not in VALID_SELECTION_MODES:
        raise ValueError(
            f"Invalid selection mode for question: {question_id}"
        )

    # Conditional questions may only reference earlier options.
    condition = question.get("show_if")

    if condition is not None:
        _validate_visibility_condition(
            condition,
            registered_options,
        )

    options = question.get("options")

    if not isinstance(options, list):
        raise ValueError("Question options must be a list.")

    if not MIN_OPTIONS_PER_QUESTION <= len(options) <= MAX_OPTIONS_PER_QUESTION:
        raise ValueError("Questions must contain 3 to 5 options.")

    for option in options:
        if not isinstance(option, dict):
            raise ValueError("Each option must be a JSON object.")

        option_id = _require_text(option.get("id"), "Option ID")
        _require_text(option.get("label"), "Option label")

        # Keep option IDs unique for binary condition mapping.
        if option_id in registered_options:
            raise ValueError(f"Duplicate option ID: {option_id}")

        registered_options.add(option_id)

    registered_questions.add(question_id)


def _validate_visibility_condition(
    condition: object,
    registered_options: set[str],
) -> None:
    """Validate a dependency on a previously defined option."""
    if not isinstance(condition, dict):
        raise ValueError("show_if must be a JSON object.")

    if set(condition) != {"selected_option"}:
        raise ValueError("Invalid show_if structure.")

    selected_option = _require_text(
        condition["selected_option"],
        "Conditional option",
    )

    # A question must never depend on an undefined or future option.
    if selected_option not in registered_options:
        raise ValueError(
            f"Unknown conditional option: {selected_option}"
        )


def _require_text(value: object, field_name: str) -> str:
    """Return a non-empty string or reject the invalid value."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")

    return value
