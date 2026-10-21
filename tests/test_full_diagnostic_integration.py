
"""Integration tests for the complete 50-symptom diagnostic workflow."""

from pathlib import Path

import pytest

from plantcare.diagnosis.diagnostic_assessment import assess_diagnosis
from plantcare.diagnosis.diagnostic_completion_policy import (
    DiagnosticCompletionPolicy,
)
from plantcare.diagnosis.diagnostic_engine_factory import (
    create_diagnostic_engine,
)
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.diagnosis.questionnaire_session import QuestionnaireSession
from plantcare.tree.tree_loader import load_tree


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUESTIONNAIRE_PATH = PROJECT_ROOT / "data" / "questionnaire_50_draft.json"
TREE_PATH = PROJECT_ROOT / "data" / "PlantCareTree.json"


@pytest.mark.parametrize(
    ("selected_symptoms", "expected_status", "expected_codes"),
    [
        (set(), "insufficient_evidence", None),
        ({"sign_022"}, "diagnosed", {"PC-022"}),
        ({"sign_024"}, "diagnosed", {"PC-024"}),
        (
            {"sign_022", "sign_024"},
            "diagnosed",
            {"PC-022", "PC-024"},
        ),
    ],
)
def test_complete_diagnostic_workflow(
    selected_symptoms: set[str],
    expected_status: str,
    expected_codes: set[str] | None,
) -> None:
    """Verify complete questionnaire and binary tree integration."""

    questionnaire = load_questionnaire(str(QUESTIONNAIRE_PATH))
    root = load_tree(str(TREE_PATH))

    engine = create_diagnostic_engine(questionnaire, root)
    completion_policy = DiagnosticCompletionPolicy(questionnaire)

    symptom_keys = {
        option["id"]
        for question in questionnaire["questions"]
        for option in question["options"]
    }

    session = QuestionnaireSession(questionnaire)

    # Complete the questionnaire using the selected symptoms.
    while not session.is_finished:
        question = session.current_question

        selections = tuple(
            option["id"]
            for option in question["options"]
            if option["id"] in selected_symptoms
        )

        if selections:
            session.submit_answer(selections)
        else:
            session.submit_no_symptoms()

    # Verify that all ten questions were answered.
    assert session.context.question_count == 10

    # Evaluate the diagnostic result.
    assessment = assess_diagnosis(
        context=session.context,
        engine=engine,
        completion_policy=completion_policy,
        symptom_keys=symptom_keys,
    )

    assert assessment.status == expected_status
    assert assessment.pending_questions == ()

    if expected_codes is None:
        assert assessment.diagnosis is None
    else:
        assert assessment.diagnosis is not None
        assert set(assessment.diagnosis.problem_codes) == expected_codes
