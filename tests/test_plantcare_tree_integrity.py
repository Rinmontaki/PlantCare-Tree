
"""Validate the structural integrity of the full PlantCare tree."""
import pytest

from plantcare.tree.binary_tree import BinaryDecisionTree
from pathlib import Path

from plantcare.tree.node import DecisionNode, TreeNode
from plantcare.tree.tree_loader import load_tree


PROJECT_ROOT = Path(__file__).resolve().parents[1]
TREE_PATH = PROJECT_ROOT / "data" / "PlantCareTree.json"


def test_no_repeated_conditions_along_a_path() -> None:
    """Ensure a condition is not evaluated twice on one path."""
    root = load_tree(TREE_PATH)

    def check_path(
        node: TreeNode,
        evaluated_conditions: frozenset[str],
    ) -> None:
        if not isinstance(node, DecisionNode):
            return

        assert node.condition_key not in evaluated_conditions, (
            f"Repeated condition '{node.condition_key}' "
            f"at node '{node.node_id}'."
        )

        updated_conditions = evaluated_conditions | {
            node.condition_key
        }

        check_path(node.left, updated_conditions)
        check_path(node.right, updated_conditions)

    check_path(root, frozenset())


@pytest.mark.parametrize(
    ("active_symptoms", "expected_codes"),
    [
        ({"sign_022"}, {"PC-022"}),
        ({"sign_024"}, {"PC-024"}),
        (
            {"sign_022", "sign_024"},
            {"PC-022", "PC-024"},
        ),
    ],
)
def test_corrected_overlap_diagnoses(
    active_symptoms: set[str],
    expected_codes: set[str],
) -> None:
    """Verify diagnoses after correcting overlapping symptoms."""
    root = load_tree(TREE_PATH)
    tree = BinaryDecisionTree(root)

    # Build all 50 binary conditions.
    conditions = {
        f"sign_{index:03d}": (
            f"sign_{index:03d}" in active_symptoms
        )
        for index in range(1, 51)
    }

    # Traverse the binary tree using the selected symptoms.
    diagnosis = tree.traverse(conditions)

    # Verify the exact set of diagnosed problems.
    assert set(diagnosis.problem_codes) == expected_codes
