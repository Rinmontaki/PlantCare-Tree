
"""Unit tests for dynamic diagnostic questionnaire navigation."""

from pathlib import Path

import pytest

from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.diagnosis.questionnaire_navigator import (
    QuestionnaireNavigator,
)


# Locate the questionnaire configuration relative to this test file.
QUESTIONNAIRE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "questionnaire.json"
)


@pytest.fixture
def navigator() -> QuestionnaireNavigator:
    """Create a navigator using the validated questionnaire."""
    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)

    return QuestionnaireNavigator(questionnaire)


def test_first_question_is_leaf_symptoms(
    navigator: QuestionnaireNavigator,
) -> None:
    """Return the first question when no answers exist."""
    context = DiagnosticContext()

    question = navigator.get_next_question(context)

    assert question is not None
    assert question["id"] == "leaf_symptoms"


def test_show_insect_question_when_insects_selected(
    navigator: QuestionnaireNavigator,
) -> None:
    """Show the insect follow-up when insects are reported."""
    context = DiagnosticContext()

    # The user reports visible insects.
    context.record_answer(
        "leaf_symptoms",
        ("visible_insects",),
    )

    question = navigator.get_next_question(context)

    assert question is not None
    assert question["id"] == "insect_appearance"


def test_show_leaf_damage_when_holes_selected(
    navigator: QuestionnaireNavigator,
) -> None:
    """Show the leaf damage question when holes are reported."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("leaf_holes",),
    )

    question = navigator.get_next_question(context)

    assert question is not None
    assert question["id"] == "leaf_damage"


def test_follow_question_order_when_both_symptoms_selected(
    navigator: QuestionnaireNavigator,
) -> None:
    """Preserve JSON question order when multiple triggers are active."""
    context = DiagnosticContext()

    # Both symptoms activate separate follow-up questions.
    context.record_answer(
        "leaf_symptoms",
        ("visible_insects", "leaf_holes"),
    )

    first_follow_up = navigator.get_next_question(context)

    assert first_follow_up is not None
    assert first_follow_up["id"] == "insect_appearance"

    # After answering the insect question, show leaf damage.
    context.record_answer(
        "insect_appearance",
        ("clustered_insects",),
    )

    second_follow_up = navigator.get_next_question(context)

    assert second_follow_up is not None
    assert second_follow_up["id"] == "leaf_damage"


def test_skip_unrelated_conditional_questions(
    navigator: QuestionnaireNavigator,
) -> None:
    """Skip conditional questions when their triggers are absent."""
    context = DiagnosticContext()

    # Yellowing does not activate insect or hole follow-ups.
    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )

    question = navigator.get_next_question(context)

    assert question is not None
    assert question["id"] == "soil_condition"


def test_finish_questionnaire_without_conditional_triggers(
    navigator: QuestionnaireNavigator,
) -> None:
    """Return None after completing all applicable questions."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )

    context.record_answer(
        "soil_condition",
        ("wet_soil",),
    )

    # No other question is applicable to this answer combination.
    question = navigator.get_next_question(context)

    assert question is None


def test_finish_questionnaire_with_multiple_symptoms(
    navigator: QuestionnaireNavigator,
) -> None:
    """Finish after answering all activated follow-up questions."""
    context = DiagnosticContext()

    # Activate both conditional branches.
    context.record_answer(
        "leaf_symptoms",
        ("visible_insects", "leaf_holes"),
    )

    context.record_answer(
        "insect_appearance",
        ("chewing_insects",),
    )

    context.record_answer(
        "leaf_damage",
        ("irregular_holes", "damaged_edges"),
    )

    context.record_answer(
        "soil_condition",
        ("normal_soil",),
    )

    question = navigator.get_next_question(context)

    assert question is None
    assert context.question_count == 4
