
"""Unit tests for the PlantCare diagnostic engine."""

from pathlib import Path

import pytest

from plantcare.diagnosis.condition_mapper import ConditionMapper
from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.diagnostic_engine import DiagnosticEngine
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.tree.binary_tree import BinaryDecisionTree
from plantcare.tree.tree_loader import load_tree
from plantcare.tree.node import DecisionNode, DiagnosisNode
from plantcare.diagnosis.diagnostic_completion_policy import (
    DiagnosticCompletionPolicy,
)

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
    
def test_partial_engine_waits_for_first_answer(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Report the first missing condition for an empty context."""
    context = DiagnosticContext()

    state = diagnostic_engine.evaluate_partial(context)

    assert state.is_complete is False
    assert state.diagnosis is None
    assert state.pending_condition_key == "visible_insects"
    assert state.visited_node_ids == ()


def test_partial_engine_resumes_after_second_question() -> None:
    """Resume a pending path using answers from separate questions."""
    # This tree requires one condition from each of two questions.
    positive_diagnosis = DiagnosisNode(
        node_id="diagnosis_positive",
        problem_codes=("PC-031",),
    )
    negative_diagnosis = DiagnosisNode(
        node_id="diagnosis_negative",
        problem_codes=("PC-032",),
    )
    no_insects_diagnosis = DiagnosisNode(
        node_id="diagnosis_no_insects",
        problem_codes=("PC-001",),
    )

    second_decision = DecisionNode(
        node_id="decision_002",
        condition_key="leaf_holes",
        left=positive_diagnosis,
        right=negative_diagnosis,
    )
    root = DecisionNode(
        node_id="decision_001",
        condition_key="visible_insects",
        left=second_decision,
        right=no_insects_diagnosis,
    )

    condition_mapper = ConditionMapper(
        {
            "insect_observation": (
                "visible_insects",
                "yellowing",
                "wilting",
            ),
            "leaf_observation": (
                "leaf_holes",
                "dark_spots",
                "damaged_edges",
            ),
        }
    )

    engine = DiagnosticEngine(
        decision_tree=BinaryDecisionTree(root),
        condition_mapper=condition_mapper,
    )

    context = DiagnosticContext()
    context.record_answer(
        "insect_observation",
        ("visible_insects",),
    )

    pending_state = engine.evaluate_partial(context)

    assert pending_state.is_complete is False
    assert pending_state.pending_condition_key == "leaf_holes"
    assert pending_state.visited_node_ids == ("decision_001",)

    # Answer the second question and resume traversal.
    context.record_answer(
        "leaf_observation",
        ("leaf_holes",),
    )

    completed_state = engine.evaluate_partial(context)

    assert completed_state.is_complete is True
    assert completed_state.pending_condition_key is None
    assert completed_state.diagnosis is not None
    assert completed_state.diagnosis.problem_codes == ("PC-031",)
    assert completed_state.visited_node_ids == (
        "decision_001",
        "decision_002",
    )


def test_partial_engine_completes_multiple_symptom_path(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Reach the expected leaf with multiple selected symptoms."""
    context = DiagnosticContext()
    context.record_answer(
        "leaf_symptoms",
        ("visible_insects", "leaf_holes", "yellowing"),
    )

    state = diagnostic_engine.evaluate_partial(context)

    assert state.is_complete is True
    assert state.diagnosis is not None
    assert state.diagnosis.node_id == "diagnosis_001"
    assert state.diagnosis.problem_codes == ("PC-031",)


def test_partial_engine_completes_negative_branch(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Finish after the first decision when insects are absent."""
    context = DiagnosticContext()
    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )

    state = diagnostic_engine.evaluate_partial(context)

    assert state.is_complete is True
    assert state.diagnosis is not None
    assert state.diagnosis.node_id == "diagnosis_003"
    assert state.visited_node_ids == ("decision_001",)


def test_partial_engine_rejects_invalid_question(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Reject answers outside the configured questionnaire."""
    context = DiagnosticContext()
    context.record_answer(
        "unknown_question",
        ("visible_insects",),
    )

    with pytest.raises(ValueError, match="Unknown question"):
        diagnostic_engine.evaluate_partial(context)


def test_partial_engine_preserves_recorded_answers(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Avoid modifying user selections during partial evaluation."""
    context = DiagnosticContext()
    context.record_answer(
        "leaf_symptoms",
        ("yellowing", "visible_insects"),
    )

    original_answers = context.get_answers()

    diagnostic_engine.evaluate_partial(context)

    assert context.get_answers() == original_answers
    assert context.question_count == 1
    
    
def test_engine_completion_requires_initial_answers(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Prevent completion when the diagnostic context is empty."""
    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)
    completion_policy = DiagnosticCompletionPolicy(questionnaire)
    context = DiagnosticContext()

    state = diagnostic_engine.evaluate_completion(
        context,
        completion_policy,
    )

    assert state.is_ready_to_finish is False
    assert state.traversal_state.is_complete is False
    assert state.traversal_state.pending_condition_key == "visible_insects"
    assert state.pending_required_questions == (
        "leaf_symptoms",
        "soil_condition",
    )


def test_engine_completion_requires_follow_up_questions(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Keep collecting relevant answers after reaching a tree leaf."""
    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)
    completion_policy = DiagnosticCompletionPolicy(questionnaire)
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("visible_insects", "leaf_holes"),
    )

    state = diagnostic_engine.evaluate_completion(
        context,
        completion_policy,
    )

    assert state.traversal_state.is_complete is True
    assert state.is_ready_to_finish is False
    assert state.pending_required_questions == (
        "insect_appearance",
        "leaf_damage",
        "soil_condition",
    )


def test_engine_completion_allows_finished_questionnaire(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Allow completion after all applicable questions are answered."""
    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)
    completion_policy = DiagnosticCompletionPolicy(questionnaire)
    context = DiagnosticContext()

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
        ("irregular_holes",),
    )
    context.record_answer(
        "soil_condition",
        ("normal_soil",),
    )

    state = diagnostic_engine.evaluate_completion(
        context,
        completion_policy,
    )

    assert state.is_ready_to_finish is True
    assert state.pending_required_questions == ()
    assert state.traversal_state.diagnosis is not None
    assert state.traversal_state.diagnosis.node_id == "diagnosis_001"
    assert context.question_count == 4


def test_engine_completion_skips_hidden_questions(
    diagnostic_engine: DiagnosticEngine,
) -> None:
    """Complete a session without requiring irrelevant questions."""
    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)
    completion_policy = DiagnosticCompletionPolicy(questionnaire)
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )
    context.record_answer(
        "soil_condition",
        ("normal_soil",),
    )

    state = diagnostic_engine.evaluate_completion(
        context,
        completion_policy,
    )

    assert state.is_ready_to_finish is True
    assert state.pending_required_questions == ()
    assert state.traversal_state.diagnosis is not None
    assert state.traversal_state.diagnosis.node_id == "diagnosis_003"
    assert context.question_count == 2


