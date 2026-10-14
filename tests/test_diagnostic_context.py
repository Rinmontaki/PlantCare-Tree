
"""Unit tests for PlantCare diagnostic context management."""

import pytest

from plantcare.diagnosis.diagnostic_context import DiagnosticContext


def test_record_multiple_symptoms() -> None:
    """Store multiple symptoms selected in one question."""
    context = DiagnosticContext()

    # Record three symptoms belonging to the same question.
    context.record_answer(
        question_id="leaf_symptoms",
        selected_option_ids=(
            "yellowing",
            "visible_insects",
            "leaf_holes",
        ),
    )

    answers = context.get_answers()

    assert answers["leaf_symptoms"] == (
        "yellowing",
        "visible_insects",
        "leaf_holes",
    )
    assert context.question_count == 1


def test_update_existing_answer() -> None:
    """Update a question without increasing the question count."""
    context = DiagnosticContext()

    context.record_answer("leaf_symptoms", ("yellowing",))

    # Replace the previous selection with updated observations.
    context.record_answer(
        "leaf_symptoms",
        ("yellowing", "leaf_holes"),
    )

    assert context.question_count == 1
    assert context.get_answers()["leaf_symptoms"] == (
        "yellowing",
        "leaf_holes",
    )


def test_accept_ten_questions() -> None:
    """Allow the maximum number of diagnostic questions."""
    context = DiagnosticContext()

    for index in range(10):
        context.record_answer(
            f"question_{index}",
            (f"option_{index}",),
        )

    assert context.question_count == 10


def test_reject_more_than_ten_questions() -> None:
    """Prevent registering more than ten different questions."""
    context = DiagnosticContext()

    for index in range(10):
        context.record_answer(
            f"question_{index}",
            ("selected_option",),
        )

    with pytest.raises(
        ValueError,
        match="Maximum diagnostic questions reached",
    ):
        context.record_answer(
            "question_11",
            ("selected_option",),
        )


def test_reject_empty_question_id() -> None:
    """Reject questions without a valid identifier."""
    context = DiagnosticContext()

    with pytest.raises(ValueError, match="Question ID"):
        context.record_answer("", ("yellowing",))


def test_reject_empty_selections() -> None:
    """Require at least one selected option."""
    context = DiagnosticContext()

    with pytest.raises(ValueError, match="At least one"):
        context.record_answer("leaf_symptoms", ())


def test_reject_duplicate_selections() -> None:
    """Reject duplicate symptom identifiers in one answer."""
    context = DiagnosticContext()

    with pytest.raises(ValueError, match="Duplicate selections"):
        context.record_answer(
            "leaf_symptoms",
            ("yellowing", "yellowing"),
        )


def test_reject_string_as_selection_collection() -> None:
    """Prevent treating a string as multiple option identifiers."""
    context = DiagnosticContext()

    with pytest.raises(TypeError, match="must be a sequence"):
        context.record_answer("leaf_symptoms", "yellowing")


def test_reject_invalid_option_id() -> None:
    """Reject empty option identifiers."""
    context = DiagnosticContext()

    with pytest.raises(ValueError, match="Option IDs"):
        context.record_answer(
            "leaf_symptoms",
            ("yellowing", ""),
        )


def test_get_answers_returns_copy() -> None:
    """Protect internal answers from external dictionary changes."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )

    # Modifying the returned dictionary must not change the context.
    answers = context.get_answers()
    answers["leaf_symptoms"] = ("leaf_holes",)

    assert context.get_answers()["leaf_symptoms"] == (
        "yellowing",
    )
    
    
def test_remove_existing_answer() -> None:
    """Remove an existing diagnostic answer."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing", "visible_insects"),
    )

    context.remove_answer("leaf_symptoms")

    assert context.question_count == 0
    assert "leaf_symptoms" not in context.get_answers()


def test_remove_answer_preserves_other_answers() -> None:
    """Preserve unrelated answers when removing one question."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("visible_insects",),
    )
    context.record_answer(
        "soil_condition",
        ("normal_soil",),
    )

    context.remove_answer("leaf_symptoms")

    assert context.question_count == 1
    assert context.get_answers() == {
        "soil_condition": ("normal_soil",),
    }


def test_remove_nonexistent_answer() -> None:
    """Ignore attempts to remove an unanswered question."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )

    context.remove_answer("unknown_question")

    assert context.question_count == 1
    assert context.get_answers()["leaf_symptoms"] == (
        "yellowing",
    )

