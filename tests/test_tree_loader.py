
"""Unit tests for the PlantCare JSON tree loader."""

import json
from pathlib import Path

import pytest

from plantcare.tree.node import DecisionNode, DiagnosisNode
from plantcare.tree.tree_loader import load_tree


# Locate the sample JSON relative to this test file.
SAMPLE_TREE_PATH = (
    Path(__file__).parent / "fixtures" / "sample_tree.json"
)


def test_load_tree_creates_root_decision_node() -> None:
    """Verify that the JSON root becomes a DecisionNode."""
    root = load_tree(SAMPLE_TREE_PATH)

    assert isinstance(root, DecisionNode)
    assert root.node_id == "decision_001"
    assert root.condition_key == "visible_insects"


def test_load_tree_creates_binary_children() -> None:
    """Verify that both child branches are constructed."""
    root = load_tree(SAMPLE_TREE_PATH)

    assert isinstance(root, DecisionNode)

    # The left branch contains another decision.
    assert isinstance(root.left, DecisionNode)
    assert root.left.condition_key == "leaf_holes"

    # The right branch terminates in a diagnosis.
    assert isinstance(root.right, DiagnosisNode)
    assert root.right.problem_codes == ("PC-001",)


def test_load_tree_creates_diagnostic_leaves() -> None:
    """Verify that terminal nodes contain the expected codes."""
    root = load_tree(SAMPLE_TREE_PATH)

    assert isinstance(root, DecisionNode)
    assert isinstance(root.left, DecisionNode)

    # Both branches of the second decision must be leaves.
    assert isinstance(root.left.left, DiagnosisNode)
    assert isinstance(root.left.right, DiagnosisNode)

    assert root.left.left.problem_codes == ("PC-031",)
    assert root.left.right.problem_codes == ("PC-032",)


def test_load_tree_rejects_missing_child(
    tmp_path: Path,
) -> None:
    """Reject decisions without both binary children."""
    tree_data = {
        "type": "decision",
        "node_id": "decision_invalid",
        "condition_key": "visible_insects",
        "left": {
            "type": "diagnosis",
            "node_id": "diagnosis_001",
            "problem_codes": ["PC-031"],
        },
    }

    # Save a temporary JSON file with a missing right branch.
    file_path = tmp_path / "missing_child.json"
    file_path.write_text(
        json.dumps(tree_data),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="left and right"):
        load_tree(file_path)


def test_load_tree_rejects_unknown_node_type(
    tmp_path: Path,
) -> None:
    """Reject node types outside the supported model."""
    tree_data = {
        "type": "unknown",
        "node_id": "invalid_001",
    }

    file_path = tmp_path / "unknown_type.json"
    file_path.write_text(
        json.dumps(tree_data),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown node type"):
        load_tree(file_path)


def test_load_tree_rejects_invalid_problem_codes(
    tmp_path: Path,
) -> None:
    """Reject diagnostic leaves without valid problem codes."""
    tree_data = {
        "type": "diagnosis",
        "node_id": "diagnosis_invalid",
        "problem_codes": [],
    }

    file_path = tmp_path / "invalid_codes.json"
    file_path.write_text(
        json.dumps(tree_data),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="problem_codes"):
        load_tree(file_path)


def test_load_tree_rejects_leaf_with_children(
    tmp_path: Path,
) -> None:
    """Reject diagnostic leaves containing child branches."""
    tree_data = {
        "type": "diagnosis",
        "node_id": "diagnosis_invalid",
        "problem_codes": ["PC-001"],
        "left": {},
    }

    file_path = tmp_path / "invalid_leaf.json"
    file_path.write_text(
        json.dumps(tree_data),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="cannot have children"):
        load_tree(file_path)


def test_load_tree_rejects_invalid_json(
    tmp_path: Path,
) -> None:
    """Verify that malformed JSON produces a parsing error."""
    file_path = tmp_path / "malformed.json"

    # An incomplete object is not valid JSON.
    file_path.write_text(
        '{"type": "decision",',
        encoding="utf-8",
    )

    with pytest.raises(json.JSONDecodeError):
        load_tree(file_path)
