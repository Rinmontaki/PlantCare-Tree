
"""Unit tests for PlantCare questionnaire loading and validation."""

import json
from pathlib import Path
from typing import Any

import pytest

from plantcare.diagnosis.questionnaire_loader import load_questionnaire


# Locate the main questionnaire configuration.
QUESTIONNAIRE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "questionnaire.json"
)


@pytest.fixture
def questionnaire_data() -> dict[str, Any]:
    """Provide a valid questionnaire for testing."""
    with QUESTIONNAIRE_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_questionnaire(
    directory: Path,
    data: dict[str, Any],
) -> Path:
    """Write a questionnaire to a temporary JSON file."""
    file_path = directory / "questionnaire_test.json"

    # Preserve Spanish characters when creating the test file.
    file_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return file_path


def test_load_valid_questionnaire() -> None:
    """Verify that the main questionnaire loads correctly."""
    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)

    assert questionnaire["version"] == 1
    assert questionnaire["max_questions"] == 10
    assert len(questionnaire["questions"]) == 4


@pytest.mark.parametrize("option_count", [2, 6])
def test_reject_invalid_option_count(
    tmp_path: Path,
    questionnaire_data: dict[str, Any],
    option_count: int,
) -> None:
    """Reject questions containing fewer than 3 or more than 5 options."""
    # Generate unique options to isolate the option-count validation.
    questionnaire_data["questions"][0]["options"] = [
        {"id": f"option_{index}", "label": f"Option {index}"}
        for index in range(option_count)
    ]

    file_path = save_questionnaire(tmp_path, questionnaire_data)

    with pytest.raises(ValueError, match="3 to 5 options"):
        load_questionnaire(file_path)


def test_reject_duplicate_question_ids(
    tmp_path: Path,
    questionnaire_data: dict[str, Any],
) -> None:
    """Prevent questions from sharing the same identifier."""
    questions = questionnaire_data["questions"]

    questions[1]["id"] = questions[0]["id"]

    file_path = save_questionnaire(tmp_path, questionnaire_data)

    with pytest.raises(ValueError, match="Duplicate question ID"):
        load_questionnaire(file_path)


def test_reject_invalid_selection_mode(
    tmp_path: Path,
    questionnaire_data: dict[str, Any],
) -> None:
    """Reject unsupported selection modes."""
    questionnaire_data["questions"][0]["selection_mode"] = "invalid"

    file_path = save_questionnaire(tmp_path, questionnaire_data)

    with pytest.raises(ValueError, match="Invalid selection mode"):
        load_questionnaire(file_path)


def test_reject_unknown_visibility_condition(
    tmp_path: Path,
    questionnaire_data: dict[str, Any],
) -> None:
    """Reject conditions referencing nonexistent option identifiers."""
    questionnaire_data["questions"][1]["show_if"] = {
        "selected_option": "nonexistent_option"
    }

    file_path = save_questionnaire(tmp_path, questionnaire_data)

    with pytest.raises(ValueError, match="Unknown conditional option"):
        load_questionnaire(file_path)


def test_reject_question_limit_exceeded(
    tmp_path: Path,
    questionnaire_data: dict[str, Any],
) -> None:
    """Reject questionnaires exceeding their configured limit."""
    questionnaire_data["max_questions"] = 3

    file_path = save_questionnaire(tmp_path, questionnaire_data)

    with pytest.raises(ValueError, match="exceeds max_questions"):
        load_questionnaire(file_path)


def test_reject_duplicate_option_ids(
    tmp_path: Path,
    questionnaire_data: dict[str, Any],
) -> None:
    """Prevent repeated option identifiers."""
    options = questionnaire_data["questions"][0]["options"]

    options[1]["id"] = options[0]["id"]

    file_path = save_questionnaire(tmp_path, questionnaire_data)

    with pytest.raises(ValueError, match="Duplicate option ID"):
        load_questionnaire(file_path)


def test_reject_empty_question_text(
    tmp_path: Path,
    questionnaire_data: dict[str, Any],
) -> None:
    """Require every question to contain readable text."""
    questionnaire_data["questions"][0]["text"] = ""

    file_path = save_questionnaire(tmp_path, questionnaire_data)

    with pytest.raises(ValueError, match="Question text"):
        load_questionnaire(file_path)


def test_reject_malformed_json(tmp_path: Path) -> None:
    """Reject questionnaire files containing invalid JSON."""
    file_path = tmp_path / "invalid_questionnaire.json"

    # Write an incomplete JSON document.
    file_path.write_text(
        '{"questions": [',
        encoding="utf-8",
    )

    with pytest.raises(json.JSONDecodeError):
        load_questionnaire(file_path)
