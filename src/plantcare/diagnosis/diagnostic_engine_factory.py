
"""Create diagnostic engines from questionnaire and tree data."""

from typing import Any

from plantcare.diagnosis.condition_mapper import ConditionMapper
from plantcare.diagnosis.diagnostic_engine import DiagnosticEngine
from plantcare.tree.binary_tree import BinaryDecisionTree
from plantcare.tree.node import TreeNode


def create_diagnostic_engine(
    questionnaire: dict[str, Any],
    root: TreeNode,
) -> DiagnosticEngine:
    """Build a diagnostic engine using the supplied configurations."""

    # Extract the valid option IDs from each questionnaire question.
    question_options = {
        question["id"]: tuple(
            option["id"]
            for option in question["options"]
        )
        for question in questionnaire["questions"]
    }

    # Convert the questionnaire options into binary conditions.
    condition_mapper = ConditionMapper(question_options)

    # Initialize tree traversal from the JSON-loaded root node.
    decision_tree = BinaryDecisionTree(root)

    # Keep the diagnostic engine independent from the user interface.
    return DiagnosticEngine(
        decision_tree=decision_tree,
        condition_mapper=condition_mapper,
    )
