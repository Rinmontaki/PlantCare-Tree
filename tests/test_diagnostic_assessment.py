
"""Unit tests for the diagnostic assessment workflow."""

import pytest

from plantcare.diagnosis.diagnostic_assessment import (
    assess_diagnosis,
)
from plantcare.diagnosis.diagnostic_completion_policy import (
    DiagnosticCompletionPolicy,
)
from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.diagnostic_engine import DiagnosticEngine
from plantcare.diagnosis.diagnostic_engine_factory import (
    create_diagnostic_engine,
)
from plantcare.tree.node import DecisionNode, DiagnosisNode


SYMPTOM_KEYS = frozenset({
    "yellowing",
    "visible_insects",
})


@pytest.fixture
def diagnostic_components() -> tuple[
    DiagnosticEngine,
    DiagnosticCompletionPolicy,
]:
    """Build a small diagnostic workflow for isolated testing."""
    questionnaire = {
        "max_questions": 2,
        "questions": [
            {
                "id": "plant_symptoms",
                "text": "What symptoms are visible?",
                "selection_mode": "single",
                "options": [
                    {"id": "yellowing", "label": "Yellow leaves"},
                    {"id": "visible_insects", "label": "Insects"},
                    {"id": "no_symptoms", "label": "No symptoms"},
                ],
            },
            {
                "id": "soil_condition",
                "text": "What is the soil condition?",
                "selection_mode": "single",
                "options": [
                    {"id": "normal_soil", "label": "Normal"},
                    {"id": "wet_soil", "label": "Wet"},
                    {"id": "dry_soil", "label": "Dry"},
                ],
            },
        ],
    }

    root = DecisionNode(
        node_id="decision_yellowing",
        condition_key="yellowing",
        left=DiagnosisNode(
            node_id="leaf_yellowing",
            problem_codes=("PC-001",),
        ),
        right=DecisionNode(
            node_id="decision_insects",
            condition_key="visible_insects",
            left=DiagnosisNode(
                node_id="leaf_insects",
                problem_codes=("PC-002",),
            ),
            right=DiagnosisNode(
                node_id="leaf_without_symptoms",
                problem_codes=("PC-003",),
            ),
        ),
    )

    engine = create_diagnostic_engine(
        questionnaire=questionnaire,
        root=root,
    )

    policy = DiagnosticCompletionPolicy(questionnaire)

    return engine, policy


def test_assessment_waits_for_pending_questions(
    diagnostic_components: tuple[
        DiagnosticEngine,
        DiagnosticCompletionPolicy,
    ],
) -> None:
    """Prevent diagnosis before all required questions are answered."""
    engine, policy = diagnostic_components
    context = DiagnosticContext()

    context.record_answer(
        "plant_symptoms",
        ("yellowing",),
    )

    result = assess_diagnosis(
        context=context,
        engine=engine,
        completion_policy=policy,
        symptom_keys=SYMPTOM_KEYS,
    )

    assert result.status == "pending"
    assert result.diagnosis is None
    assert result.pending_questions == ("soil_condition",)


def test_assessment_rejects_missing_evidence(
    diagnostic_components: tuple[
        DiagnosticEngine,
        DiagnosticCompletionPolicy,
    ],
) -> None:
    """Prevent unsupported diagnoses when no symptoms are present."""
    engine, policy = diagnostic_components
    context = DiagnosticContext()

    context.record_answer(
        "plant_symptoms",
        ("no_symptoms",),
    )

    context.record_answer(
        "soil_condition",
        ("normal_soil",),
    )

    result = assess_diagnosis(
        context=context,
        engine=engine,
        completion_policy=policy,
        symptom_keys=SYMPTOM_KEYS,
    )

    assert result.status == "insufficient_evidence"
    assert result.diagnosis is None


def test_assessment_returns_valid_diagnosis(
    diagnostic_components: tuple[
        DiagnosticEngine,
        DiagnosticCompletionPolicy,
    ],
) -> None:
    """Return the tree diagnosis when valid evidence is available."""
    engine, policy = diagnostic_components
    context = DiagnosticContext()

    context.record_answer(
        "plant_symptoms",
        ("yellowing",),
    )

    context.record_answer(
        "soil_condition",
        ("normal_soil",),
    )

    result = assess_diagnosis(
        context=context,
        engine=engine,
        completion_policy=policy,
        symptom_keys=SYMPTOM_KEYS,
    )

    assert result.status == "diagnosed"
    assert result.diagnosis is not None
    assert result.diagnosis.problem_codes == ("PC-001",)
    assert result.pending_questions == ()
