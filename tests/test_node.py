
"""Unit tests for PlantCare binary tree nodes."""

from dataclasses import FrozenInstanceError

import pytest

from plantcare.tree.node import DecisionNode, DiagnosisNode


def test_diagnosis_node_is_leaf() -> None:
    """Verify that a diagnosis node is a terminal node."""
    node = DiagnosisNode(
        node_id="diagnosis_001",
        problem_codes=("PC-001",),
    )

    assert node.is_leaf is True
    assert node.problem_codes == ("PC-001",)


def test_diagnosis_node_supports_multiple_problems() -> None:
    """Verify that a leaf can store multiple candidate problems."""
    node = DiagnosisNode(
        node_id="diagnosis_002",
        problem_codes=("PC-001", "PC-031"),
    )

    assert len(node.problem_codes) == 2


def test_decision_node_has_two_children() -> None:
    """Verify that an internal node has left and right children."""
    # Create terminal nodes for both possible decisions.
    left_child = DiagnosisNode(
        node_id="diagnosis_yes",
        problem_codes=("PC-031",),
    )

    right_child = DiagnosisNode(
        node_id="diagnosis_no",
        problem_codes=("PC-001",),
    )

    # Create a binary decision with exactly two children.
    node = DecisionNode(
        node_id="decision_001",
        condition_key="visible_insects",
        left=left_child,
        right=right_child,
    )

    assert node.is_leaf is False
    assert node.left is left_child
    assert node.right is right_child


def test_nodes_are_immutable() -> None:
    """Verify that node attributes cannot be modified."""
    node = DiagnosisNode(
        node_id="diagnosis_003",
        problem_codes=("PC-002",),
    )

    # Frozen dataclasses prevent accidental attribute changes.
    with pytest.raises(FrozenInstanceError):
        node.node_id = "modified_id"
