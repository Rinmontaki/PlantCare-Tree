
"""Unit tests for binary decision tree traversal."""

from pathlib import Path

import pytest

from plantcare.tree.binary_tree import BinaryDecisionTree
from plantcare.tree.node import DiagnosisNode
from plantcare.tree.tree_loader import load_tree


# Locate the JSON fixture used by the tree traversal tests.
SAMPLE_TREE_PATH = (
    Path(__file__).parent / "fixtures" / "sample_tree.json"
)


@pytest.fixture
def decision_tree() -> BinaryDecisionTree:
    """Create a binary decision tree from the sample JSON."""
    root = load_tree(SAMPLE_TREE_PATH)

    return BinaryDecisionTree(root)


@pytest.mark.parametrize(
    ("answers", "expected_diagnosis"),
    [
        (
            {"visible_insects": True, "leaf_holes": True},
            "diagnosis_001",
        ),
        (
            {"visible_insects": True, "leaf_holes": False},
            "diagnosis_002",
        ),
        (
            {"visible_insects": False},
            "diagnosis_003",
        ),
    ],
)
def test_traverse_reaches_expected_leaf(
    decision_tree: BinaryDecisionTree,
    answers: dict[str, bool],
    expected_diagnosis: str,
) -> None:
    """Verify that binary decisions reach the correct leaf."""
    result = decision_tree.traverse(answers)

    assert isinstance(result, DiagnosisNode)
    assert result.node_id == expected_diagnosis


def test_traverse_rejects_missing_answer(
    decision_tree: BinaryDecisionTree,
) -> None:
    """Reject traversal when a required condition has no answer."""
    answers = {"visible_insects": True}

    # The left branch requires an answer for leaf_holes.
    with pytest.raises(ValueError, match="leaf_holes"):
        decision_tree.traverse(answers)


def test_traverse_rejects_non_boolean_answer(
    decision_tree: BinaryDecisionTree,
) -> None:
    """Reject answers that are not Boolean values."""
    answers = {"visible_insects": "yes"}

    with pytest.raises(TypeError, match="must be a boolean"):
        decision_tree.traverse(answers)


def test_traverse_ignores_unused_answers(
    decision_tree: BinaryDecisionTree,
) -> None:
    """Ignore conditions that are not evaluated on the selected path."""
    answers = {
        "visible_insects": False,
        "leaf_holes": True,
    }

    result = decision_tree.traverse(answers)

    assert result.node_id == "diagnosis_003"


def test_traverse_accepts_diagnosis_as_root() -> None:
    """Support a tree containing only one diagnostic leaf."""
    root = DiagnosisNode(
        node_id="diagnosis_single",
        problem_codes=("PC-001",),
    )

    decision_tree = BinaryDecisionTree(root)
    result = decision_tree.traverse({})

    assert result is root
