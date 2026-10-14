
"""Unit tests for partial binary decision tree traversal."""

from pathlib import Path

import pytest

from plantcare.tree.binary_tree import BinaryDecisionTree
from plantcare.tree.node import DiagnosisNode
from plantcare.tree.traversal_state import TraversalState
from plantcare.tree.tree_loader import load_tree


# Locate the sample tree independently of the working directory.
SAMPLE_TREE_PATH = (
    Path(__file__).parent / "fixtures" / "sample_tree.json"
)


@pytest.fixture
def decision_tree() -> BinaryDecisionTree:
    """Build a binary decision tree from the sample JSON."""
    root = load_tree(SAMPLE_TREE_PATH)
    return BinaryDecisionTree(root)


def test_partial_traversal_without_answers(
    decision_tree: BinaryDecisionTree,
) -> None:
    """Identify the first required condition when no answers exist."""
    state = decision_tree.traverse_partial({})

    assert state.is_complete is False
    assert state.diagnosis is None
    assert state.pending_condition_key == "visible_insects"
    assert state.visited_node_ids == ()


def test_partial_traversal_waits_for_next_condition(
    decision_tree: BinaryDecisionTree,
) -> None:
    """Preserve the visited path when another answer is needed."""
    state = decision_tree.traverse_partial(
        {"visible_insects": True}
    )

    assert state.is_complete is False
    assert state.pending_condition_key == "leaf_holes"
    assert state.visited_node_ids == ("decision_001",)


def test_partial_traversal_completes_left_branch(
    decision_tree: BinaryDecisionTree,
) -> None:
    """Reach a diagnostic leaf when both conditions are positive."""
    state = decision_tree.traverse_partial(
        {
            "visible_insects": True,
            "leaf_holes": True,
        }
    )

    assert state.is_complete is True
    assert state.pending_condition_key is None
    assert state.diagnosis is not None
    assert state.diagnosis.node_id == "diagnosis_001"
    assert state.visited_node_ids == (
        "decision_001",
        "decision_002",
    )


def test_partial_traversal_completes_negative_branch(
    decision_tree: BinaryDecisionTree,
) -> None:
    """Reach the correct leaf when the second condition is negative."""
    state = decision_tree.traverse_partial(
        {
            "visible_insects": True,
            "leaf_holes": False,
        }
    )

    assert state.is_complete is True
    assert state.diagnosis is not None
    assert state.diagnosis.node_id == "diagnosis_002"


def test_partial_traversal_finishes_after_first_decision(
    decision_tree: BinaryDecisionTree,
) -> None:
    """Finish early when the first negative branch reaches a leaf."""
    state = decision_tree.traverse_partial(
        {"visible_insects": False}
    )

    assert state.is_complete is True
    assert state.diagnosis is not None
    assert state.diagnosis.node_id == "diagnosis_003"
    assert state.visited_node_ids == ("decision_001",)


def test_partial_traversal_rejects_invalid_boolean(
    decision_tree: BinaryDecisionTree,
) -> None:
    """Reject invalid condition values during partial traversal."""
    with pytest.raises(TypeError, match="must be a boolean"):
        decision_tree.traverse_partial(
            {"visible_insects": "yes"}
        )


def test_partial_traversal_accepts_leaf_as_root() -> None:
    """Handle a tree whose root is already a diagnostic leaf."""
    diagnosis = DiagnosisNode(
        node_id="diagnosis_single",
        problem_codes=("PC-001",),
    )

    decision_tree = BinaryDecisionTree(diagnosis)
    state = decision_tree.traverse_partial({})

    assert state.is_complete is True
    assert state.diagnosis is diagnosis
    assert state.visited_node_ids == ()


def test_traversal_state_rejects_missing_result() -> None:
    """Reject a state without a diagnosis or pending condition."""
    with pytest.raises(ValueError, match="either a diagnosis"):
        TraversalState(
            diagnosis=None,
            pending_condition_key=None,
            visited_node_ids=(),
        )


def test_traversal_state_rejects_conflicting_results() -> None:
    """Prevent a state from being complete and pending simultaneously."""
    diagnosis = DiagnosisNode(
        node_id="diagnosis_test",
        problem_codes=("PC-031",),
    )

    with pytest.raises(ValueError, match="either a diagnosis"):
        TraversalState(
            diagnosis=diagnosis,
            pending_condition_key="leaf_holes",
            visited_node_ids=(),
        )
