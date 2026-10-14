
"""Load binary decision trees from JSON files."""

import json
from pathlib import Path

from plantcare.tree.node import DecisionNode, DiagnosisNode, TreeNode


def load_tree(file_path: str | Path) -> TreeNode:
    """Load a JSON file and construct its binary decision tree."""

    # Read the tree definition using UTF-8 encoding.
    with Path(file_path).open("r", encoding="utf-8") as file:
        tree_data = json.load(file)

    # Convert the JSON structure into Python tree nodes.
    return _build_node(tree_data)


def _build_node(node_data: object) -> TreeNode:
    """Recursively construct a decision or diagnosis node."""

    # Each node must be represented by a JSON object.
    if not isinstance(node_data, dict):
        raise ValueError("Tree nodes must be JSON objects.")

    node_type = node_data.get("type")
    node_id = node_data.get("node_id")

    # Every node needs a valid identifier.
    if not isinstance(node_id, str) or not node_id.strip():
        raise ValueError("Every node must have a valid node_id.")

    if node_type == "decision":
        return _build_decision_node(node_data, node_id)

    if node_type == "diagnosis":
        return _build_diagnosis_node(node_data, node_id)

    raise ValueError(f"Unknown node type: {node_type}")


def _build_decision_node(
    node_data: dict,
    node_id: str,
) -> DecisionNode:
    """Build an internal node containing two binary branches."""

    condition_key = node_data.get("condition_key")

    # A decision must reference an observable condition.
    if not isinstance(condition_key, str) or not condition_key.strip():
        raise ValueError(
            f"Decision node '{node_id}' requires a valid condition_key."
        )

    # Internal nodes must have both binary branches.
    if "left" not in node_data or "right" not in node_data:
        raise ValueError(
            f"Decision node '{node_id}' requires left and right children."
        )

    # Recursively construct both child nodes.
    return DecisionNode(
        node_id=node_id,
        condition_key=condition_key,
        left=_build_node(node_data["left"]),
        right=_build_node(node_data["right"]),
    )


def _build_diagnosis_node(
    node_data: dict,
    node_id: str,
) -> DiagnosisNode:
    """Build a terminal node containing candidate problem codes."""

    problem_codes = node_data.get("problem_codes")

    # A diagnostic leaf must contain at least one valid problem code.
    if (
        not isinstance(problem_codes, list)
        or not problem_codes
        or any(
            not isinstance(code, str) or not code.strip()
            for code in problem_codes
        )
    ):
        raise ValueError(
            f"Diagnosis node '{node_id}' requires valid problem_codes."
        )

    # Terminal nodes cannot have child branches.
    if "left" in node_data or "right" in node_data:
        raise ValueError(
            f"Diagnosis node '{node_id}' cannot have children."
        )

    return DiagnosisNode(
        node_id=node_id,
        problem_codes=tuple(problem_codes),
    )
