
"""Integration tests for the PlantCare diagnostic engine factory."""

from pathlib import Path

import pytest

from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.diagnostic_engine import DiagnosticEngine
from plantcare.diagnosis.diagnostic_engine_factory import (
    create_diagnostic_engine,
)
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.tree.tree_loader import load_tree


# Locate the project files independently of the working directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

QUESTIONNAIRE_PATH = PROJECT_ROOT / "data" / "questionnaire.json"
TREE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "sample_tree.json"


@pytest.fixture
def diagnostic_engine() -> DiagnosticEngine:
    """Build the diagnostic engine from existing JSON configurations."""
    # Load the validated questionnaire configuration.
    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)

    # Construct the binary tree using the sample JSON.
    root = load_tree(TREE_PATH)

    # Create the engine without exposing its internal dependencies.
    return create_diagnostic_engine(questionnaire, root)


def test_factory_processes_multiple_symptoms(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Verify that the generated engine evaluates multiple symptoms."""
    context = DiagnosticContext()

    # Simulate three symptoms selected in the same question.
    context.record_answer(
        "leaf_symptoms",
        ("yellowing", "visible_insects", "leaf_holes"),
    )

    diagnosis = diagnostic_engine.evaluate(context)

    assert diagnosis.node_id == "diagnosis_001"
    assert diagnosis.problem_codes == ("PC-031",)


def test_factory_processes_negative_branch(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Verify that unselected symptoms follow negative branches."""
    context = DiagnosticContext()

    # Answer the symptom question without selecting insects.
    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )

    diagnosis = diagnostic_engine.evaluate(context)

    assert diagnosis.node_id == "diagnosis_003"
    assert diagnosis.problem_codes == ("PC-001",)


def test_factory_rejects_missing_answers(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Prevent evaluation when a required question is unanswered."""
    context = DiagnosticContext()

    # An empty context must not imply a negative answer.
    with pytest.raises(ValueError, match="visible_insects"):
        diagnostic_engine.evaluate(context)
