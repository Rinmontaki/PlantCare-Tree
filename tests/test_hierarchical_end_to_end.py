"""End-to-end confirmation of the active questionnaire and tree."""

from pathlib import Path
import json

import pytest

from plantcare.diagnosis.hierarchical_classifier import HierarchicalClassifier
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.diagnosis.questionnaire_session import QuestionnaireSession

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("selected, expected", [
    (set(), set()),
    ({"sign_022"}, {"PC-022"}),
    ({"sign_001", "sign_050"}, {"PC-001", "PC-050"}),
    ({"sign_003", "sign_022", "sign_024"}, {"PC-003", "PC-022", "PC-024"}),
])
def test_ten_questions_flow_to_active_hierarchical_tree(selected, expected):
    """Exercise questionnaire, recorded answers, and active classifier."""
    questionnaire = load_questionnaire(ROOT / "data" / "questionnaire_50_draft.json")
    session = QuestionnaireSession(questionnaire)
    while not session.is_finished:
        question = session.current_question
        matching = tuple(
            option["id"] for option in question["options"]
            if option["id"] in selected
        )
        if matching:
            session.submit_answer(matching)
        else:
            session.submit_no_symptoms()
    assert session.context.question_count == 10
    classifier = HierarchicalClassifier.from_data_directory(ROOT / "data")
    result = classifier.classify_context(session.context)
    if expected:
        assert result.diagnosis is not None
        assert set(result.diagnosis.problem_codes) == expected
    else:
        assert result.diagnosis is None


def test_augmented_structural_cases_are_reproducible():
    """Synthetic variants are software regression cases, not plant validation."""
    data = json.loads((ROOT / "data" / "augmented_test_cases.json").read_text(encoding="utf-8"))
    classifier = HierarchicalClassifier.from_data_directory(ROOT / "data")
    assert len(data["cases"]) == 151
    for case in data["cases"]:
        result = classifier.classify(case["selected_symptoms"])
        codes = set(result.diagnosis.problem_codes) if result.diagnosis else set()
        assert codes == set(case["expected_codes"]), case["case_id"]
