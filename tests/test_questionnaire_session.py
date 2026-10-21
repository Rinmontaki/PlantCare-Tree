
"""Unit tests for diagnostic questionnaire session management."""

from pathlib import Path

import pytest

from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.diagnosis.questionnaire_session import QuestionnaireSession


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUESTIONNAIRE_PATH = PROJECT_ROOT / "data" / "questionnaire.json"


@pytest.fixture
def session() -> QuestionnaireSession:
    """Create a session using the validated questionnaire."""
    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)
    return QuestionnaireSession(questionnaire)


def test_session_starts_with_first_question(
    session: QuestionnaireSession,
) -> None:
    """Display the first question when the session starts."""
    assert session.current_question is not None
    assert session.current_question["id"] == "leaf_symptoms"
    assert session.is_finished is False
    assert session.context.question_count == 0


def test_session_activates_insect_question(
    session: QuestionnaireSession,
) -> None:
    """Display insect follow-up when visible insects are selected."""
    session.submit_answer(("visible_insects",))

    assert session.current_question is not None
    assert session.current_question["id"] == "insect_appearance"
    assert session.context.question_count == 1


def test_session_skips_irrelevant_questions(
    session: QuestionnaireSession,
) -> None:
    """Skip conditional questions whose triggers are not selected."""
    session.submit_answer(("yellowing",))

    assert session.current_question is not None
    assert session.current_question["id"] == "soil_condition"


def test_session_preserves_multiple_symptoms(
    session: QuestionnaireSession,
) -> None:
    """Store multiple selected symptoms without losing their order."""
    selections = ("yellowing", "visible_insects", "leaf_holes")

    session.submit_answer(selections)

    assert session.context.get_answers()["leaf_symptoms"] == selections
    assert session.current_question is not None
    assert session.current_question["id"] == "insect_appearance"


def test_session_rejects_invalid_option(
    session: QuestionnaireSession,
) -> None:
    """Reject options that do not belong to the active question."""
    with pytest.raises(ValueError, match="Invalid option"):
        session.submit_answer(("invalid_symptom",))

    assert session.context.question_count == 0
    assert session.current_question is not None
    assert session.current_question["id"] == "leaf_symptoms"


def test_session_rejects_empty_answer(
    session: QuestionnaireSession,
) -> None:
    """Prevent advancing without selecting an option."""
    with pytest.raises(ValueError, match="At least one"):
        session.submit_answer(())

    assert session.context.question_count == 0
    assert session.is_finished is False



def test_session_rejects_multiple_soil_answers(
    session: QuestionnaireSession,
) -> None:
    """Reject multiple answers for a single-choice soil question."""
    session.submit_answer(("yellowing",))

    assert session.current_question is not None
    assert session.current_question["id"] == "soil_condition"

    with pytest.raises(ValueError, match="exactly one"):
        session.submit_answer(("wet_soil", "dry_soil"))

    assert session.context.question_count == 1
    assert session.current_question["id"] == "soil_condition"

def test_session_finishes_without_hidden_questions(
    session: QuestionnaireSession,
) -> None:
    """Complete a session with only the applicable questions."""
    session.submit_answer(("yellowing",))
    session.submit_answer(("normal_soil",))

    assert session.is_finished is True
    assert session.current_question is None
    assert session.context.question_count == 2

    with pytest.raises(ValueError, match="already finished"):
        session.submit_answer(("yellowing",))


def test_session_completes_full_conditional_route(
    session: QuestionnaireSession,
) -> None:
    """Process every relevant question on a complete symptom route."""
    session.submit_answer(
        ("visible_insects", "leaf_holes")
    )
    session.submit_answer(("chewing_insects",))
    session.submit_answer(("irregular_holes",))
    session.submit_answer(("normal_soil",))

    answers = session.context.get_answers()

    assert session.is_finished is True
    assert session.context.question_count == 4
    assert answers["leaf_symptoms"] == (
        "visible_insects",
        "leaf_holes",
    )
    assert answers["insect_appearance"] == ("chewing_insects",)
    assert answers["leaf_damage"] == ("irregular_holes",)
    assert answers["soil_condition"] == ("normal_soil",)


def test_session_accepts_multiple_insect_characteristics(
    session: QuestionnaireSession,
) -> None:
    """Allow multiple compatible insect characteristics."""
    session.submit_answer(("visible_insects",))

    session.submit_answer(
        ("clustered_insects", "flying_insects")
    )

    answers = session.context.get_answers()

    assert answers["insect_appearance"] == (
        "clustered_insects",
        "flying_insects",
    )

    assert session.current_question is not None
    assert session.current_question["id"] == "soil_condition"


def test_session_rejects_exclusive_insect_combination(
    session: QuestionnaireSession,
) -> None:
    """Prevent unknown insects from combining with known types."""
    session.submit_answer(("visible_insects",))

    with pytest.raises(
        ValueError,
        match="Exclusive options cannot be combined",
    ):
        session.submit_answer(
            ("clustered_insects", "unknown_insects")
        )

    # Invalid selections must not be stored.
    assert session.context.question_count == 1

    assert session.current_question is not None
    assert session.current_question["id"] == "insect_appearance"


def test_go_back_preserves_previous_answers(
    session: QuestionnaireSession,
) -> None:
    """Go back without losing previously recorded answers."""
    session.submit_answer(("visible_insects",))

    assert session.can_go_back is True
    assert session.current_question["id"] == "insect_appearance"

    assert session.go_back() is True

    assert session.current_question["id"] == "leaf_symptoms"
    assert session.context.get_answers()["leaf_symptoms"] == (
        "visible_insects",
    )

    assert session.can_go_back is False
    assert session.go_back() is False


def test_go_back_after_questionnaire_completion(
    session: QuestionnaireSession,
) -> None:
    """Allow reopening the last question after completion."""
    session.submit_answer(("yellowing",))
    session.submit_answer(("normal_soil",))

    assert session.is_finished is True
    assert session.can_go_back is True

    assert session.go_back() is True

    assert session.is_finished is False
    assert session.current_question["id"] == "soil_condition"
    assert session.context.get_answers()["soil_condition"] == (
        "normal_soil",
    )


def test_changing_previous_answer_removes_hidden_answers(
    session: QuestionnaireSession,
) -> None:
    """Remove answers to questions hidden by an earlier change."""
    session.submit_answer(("visible_insects",))
    session.submit_answer(("clustered_insects",))
    session.submit_answer(("normal_soil",))

    assert session.is_finished is True

    # Navigate backwards to the initial symptom question.
    assert session.go_back() is True
    assert session.go_back() is True
    assert session.go_back() is True

    assert session.current_question["id"] == "leaf_symptoms"

    # Removing visible insects hides the insect appearance question.
    session.submit_answer(("yellowing",))

    answers = session.context.get_answers()

    assert answers["leaf_symptoms"] == ("yellowing",)
    assert "insect_appearance" not in answers

    # Unrelated answers must remain available.
    assert answers["soil_condition"] == ("normal_soil",)

    assert session.current_question["id"] == "soil_condition"


def test_session_advances_with_explicit_no_symptoms(
    session: QuestionnaireSession,
) -> None:
    """Advance after explicitly reporting no symptoms."""
    session.submit_no_symptoms()

    assert session.context.get_answers()["leaf_symptoms"] == ()
    assert session.context.question_count == 1

    assert session.current_question is not None
    assert session.current_question["id"] == "soil_condition"

    session.submit_answer(("normal_soil",))

    assert session.is_finished is True
    assert session.context.question_count == 2


def test_session_changes_previous_no_symptoms_answer(
    session: QuestionnaireSession,
) -> None:
    """Allow replacing an explicit negative answer."""
    session.submit_no_symptoms()

    assert session.go_back() is True
    assert session.current_question is not None
    assert session.current_question["id"] == "leaf_symptoms"

    session.submit_answer(("visible_insects",))

    assert session.context.get_answers()["leaf_symptoms"] == (
        "visible_insects",
    )

    assert session.current_question is not None
    assert session.current_question["id"] == "insect_appearance"
