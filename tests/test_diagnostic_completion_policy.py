
"""Unit tests for diagnostic completion requirements."""

from pathlib import Path

import pytest

from plantcare.diagnosis.diagnostic_completion_policy import (
    DiagnosticCompletionPolicy,
)
from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.diagnostic_engine import DiagnosticEngine
from plantcare.diagnosis.diagnostic_engine_factory import (
    create_diagnostic_engine,
)
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.tree.traversal_state import TraversalState
from plantcare.tree.tree_loader import load_tree


PROJECT_ROOT = Path(__file__).resolve().parents[1]
QUESTIONNAIRE_PATH = PROJECT_ROOT / "data" / "questionnaire.json"
TREE_PATH = PROJECT_ROOT / "tests" / "fixtures" / "sample_tree.json"


@pytest.fixture
def diagnostic_components() -> tuple[
    DiagnosticCompletionPolicy,
    DiagnosticEngine,
]:
    """Create a completion policy and engine from test configurations."""
    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)
    root = load_tree(TREE_PATH)

    policy = DiagnosticCompletionPolicy(questionnaire)

    engine = create_diagnostic_engine(
        questionnaire=questionnaire,
        root=root,
    )

    return policy, engine


def test_empty_context_requires_initial_questions(
    diagnostic_components: tuple[
        DiagnosticCompletionPolicy,
        DiagnosticEngine,
    ],
) -> None:
    """Require unconditional questions before completing a session."""
    policy, engine = diagnostic_components
    context = DiagnosticContext()

    traversal = engine.evaluate_partial(context)
    state = policy.evaluate(context, traversal)

    assert state.is_ready_to_finish is False
    assert state.requires_more_information is True
    assert state.pending_required_questions == (
        "leaf_symptoms",
        "soil_condition",
    )
    assert state.traversal_state.is_complete is False


def test_completed_tree_still_requires_follow_up_questions(
    diagnostic_components: tuple[
        DiagnosticCompletionPolicy,
        DiagnosticEngine,
    ],
) -> None:
    """Keep the questionnaire open after reaching a demo leaf."""
    policy, engine = diagnostic_components
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("visible_insects", "leaf_holes"),
    )

    traversal = engine.evaluate_partial(context)
    state = policy.evaluate(context, traversal)

    assert traversal.is_complete is True
    assert state.is_ready_to_finish is False
    assert state.pending_required_questions == (
        "insect_appearance",
        "leaf_damage",
        "soil_condition",
    )


def test_hidden_questions_are_not_required(
    diagnostic_components: tuple[
        DiagnosticCompletionPolicy,
        DiagnosticEngine,
    ],
) -> None:
    """Ignore conditional questions when their triggers are absent."""
    policy, engine = diagnostic_components
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )

    traversal = engine.evaluate_partial(context)
    state = policy.evaluate(context, traversal)

    assert traversal.is_complete is True
    assert state.pending_required_questions == ("soil_condition",)
    assert "insect_appearance" not in state.pending_required_questions
    assert "leaf_damage" not in state.pending_required_questions


def test_only_relevant_conditional_questions_are_required(
    diagnostic_components: tuple[
        DiagnosticCompletionPolicy,
        DiagnosticEngine,
    ],
) -> None:
    """Require insect follow-up without requiring leaf-damage follow-up."""
    policy, engine = diagnostic_components
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("visible_insects",),
    )

    traversal = engine.evaluate_partial(context)
    state = policy.evaluate(context, traversal)

    assert state.pending_required_questions == (
        "insect_appearance",
        "soil_condition",
    )
    assert state.is_ready_to_finish is False


def test_completion_with_all_applicable_questions(
    diagnostic_components: tuple[
        DiagnosticCompletionPolicy,
        DiagnosticEngine,
    ],
) -> None:
    """Allow completion after answering all applicable questions."""
    policy, engine = diagnostic_components
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

    traversal = engine.evaluate_partial(context)
    state = policy.evaluate(context, traversal)

    assert traversal.is_complete is True
    assert state.pending_required_questions == ()
    assert state.is_ready_to_finish is True
    assert state.requires_more_information is False
    assert context.question_count == 4


def test_completion_without_irrelevant_questions(
    diagnostic_components: tuple[
        DiagnosticCompletionPolicy,
        DiagnosticEngine,
    ],
) -> None:
    """Allow completion without answering hidden questions."""
    policy, engine = diagnostic_components
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )
    context.record_answer(
        "soil_condition",
        ("normal_soil",),
    )

    traversal = engine.evaluate_partial(context)
    state = policy.evaluate(context, traversal)

    assert state.is_ready_to_finish is True
    assert state.pending_required_questions == ()
    assert context.question_count == 2


def test_pending_tree_prevents_completion(
    diagnostic_components: tuple[
        DiagnosticCompletionPolicy,
        DiagnosticEngine,
    ],
) -> None:
    """Reject completion when the binary traversal remains pending."""
    policy, _ = diagnostic_components
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )
    context.record_answer(
        "soil_condition",
        ("normal_soil",),
    )

    # Simulate a tree that requires an additional condition.
    traversal = TraversalState(
        diagnosis=None,
        pending_condition_key="additional_condition",
        visited_node_ids=(),
    )

    state = policy.evaluate(context, traversal)

    assert state.pending_required_questions == ()
    assert state.traversal_state.is_complete is False
    assert state.is_ready_to_finish is False
    assert state.requires_more_information is True
