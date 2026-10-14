
"""Binary decision tree traversal for PlantCare diagnostics."""

from collections.abc import Mapping

from plantcare.tree.node import DecisionNode, DiagnosisNode, TreeNode


class BinaryDecisionTree:
    """Navigate a binary tree using observable plant conditions."""

    def __init__(self, root: TreeNode) -> None:
        """Initialize the decision tree with its root node."""
        self.root = root

    def traverse(self, answers: Mapping[str, bool]) -> DiagnosisNode:
        """Find a diagnostic leaf using the provided binary answers."""
        current_node = self.root

        # Evaluate one binary condition at a time until reaching a leaf.
        while isinstance(current_node, DecisionNode):
            condition_key = current_node.condition_key

            # Missing answers must not be interpreted as negative answers.
            if condition_key not in answers:
                raise ValueError(
                    f"Missing answer for condition: {condition_key}"
                )

            answer = answers[condition_key]

            # Only Boolean values are valid for internal tree decisions.
            if not isinstance(answer, bool):
                raise TypeError(
                    f"Condition '{condition_key}' must be a boolean."
                )

            # Follow the left branch for YES and the right branch for NO.
            current_node = (
                current_node.left if answer else current_node.right
            )

        return current_node
