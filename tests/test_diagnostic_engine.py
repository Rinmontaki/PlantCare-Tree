
"""Unit tests for the PlantCare diagnostic engine."""

from pathlib import Path

import pytest

from plantcare.diagnosis.condition_mapper import ConditionMapper
from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.diagnostic_engine import DiagnosticEngine
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.tree.binary_tree import BinaryDecisionTree
from plantcare.tree.tree_loader import load_tree


# Locate configuration files relative to the project root.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

QUESTIONNAIRE_PATH = PROJECT_ROOT / "data" / "questionnaire.json"
TREE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "sample_tree.json"


@pytest.fixture
def diagnostic_engine() -> DiagnosticEngine:
    """Create a diagnostic engine using the existing JSON files."""
    # Load the questionnaire and extract its option identifiers.
    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)

    question_options = {
        question["id"]: tuple(
            option["id"]
            for option in question["options"]
        )
        for question in questionnaire["questions"]
    }

    # Build the existing binary tree from its JSON definition.
    root = load_tree(TREE_PATH)
    decision_tree = BinaryDecisionTree(root)

    # Connect the condition mapper and binary tree.
    condition_mapper = ConditionMapper(question_options)

    return DiagnosticEngine(
        decision_tree=decision_tree,
        condition_mapper=condition_mapper,
    )


def test_diagnosis_with_multiple_symptoms(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Identify a leaf when multiple symptoms are selected."""
    context = DiagnosticContext()

    # Register multiple symptoms from the same visible question.
    context.record_answer(
        "leaf_symptoms",
        ("yellowing", "visible_insects", "leaf_holes"),
    )

    diagnosis = diagnostic_engine.evaluate(context)

    assert diagnosis.node_id == "diagnosis_001"
    assert diagnosis.problem_codes == ("PC-031",)

    # Ensure the original observations remain available.
    assert context.question_count == 1
    assert len(context.get_answers()["leaf_symptoms"]) == 3


def test_diagnosis_with_insects_without_holes(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Follow the negative leaf-hole branch when insects exist."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("visible_insects",),
    )

    diagnosis = diagnostic_engine.evaluate(context)

    assert diagnosis.node_id == "diagnosis_002"


def test_diagnosis_without_visible_insects(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Follow the negative insect branch when insects are absent."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )

    diagnosis = diagnostic_engine.evaluate(context)

    assert diagnosis.node_id == "diagnosis_003"


def test_diagnosis_requires_answered_question(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Prevent diagnosis when a required condition is unknown."""
    context = DiagnosticContext()

    with pytest.raises(ValueError, match="visible_insects"):
        diagnostic_engine.evaluate(context)


def test_diagnosis_rejects_unknown_question(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Reject answers to questions outside the questionnaire."""
    context = DiagnosticContext()

    context.record_answer(
        "unknown_question",
        ("visible_insects",),
    )

    with pytest.raises(ValueError, match="Unknown question"):
        diagnostic_engine.evaluate(context)


def test_diagnosis_rejects_invalid_option(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Reject selections that are not valid questionnaire options."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("invalid_symptom",),
    )

    with pytest.raises(ValueError, match="Invalid selection"):
        diagnostic_engine.evaluate(context)
