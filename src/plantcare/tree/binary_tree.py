
"""Binary decision tree traversal for PlantCare diagnostics."""

from collections.abc import Mapping

from plantcare.tree.node import DecisionNode, DiagnosisNode, TreeNode
from plantcare.tree.traversal_state import TraversalState


class BinaryDecisionTree:
    """Navigate a binary tree using observable plant conditions."""

    def __init__(self, root: TreeNode) -> None:
        """Initialize the decision tree with its root node."""
        self.root = root

    def traverse(self, answers: Mapping[str, bool]) -> DiagnosisNode:
        """Find a diagnostic leaf using the provided binary answers."""
        current_node = self.root

        # Evaluate conditions until reaching a diagnostic leaf.
        while isinstance(current_node, DecisionNode):
            condition_key = current_node.condition_key

            # Missing answers must not be interpreted as negative.
            if condition_key not in answers:
                raise ValueError(
                    f"Missing answer for condition: {condition_key}"
                )

            answer = answers[condition_key]

            # Only Boolean values are valid for binary decisions.
            if not isinstance(answer, bool):
                raise TypeError(
                    f"Condition '{condition_key}' must be a boolean."
                )

            # Follow the left branch for YES and right for NO.
            current_node = (
                current_node.left if answer else current_node.right
            )

        return current_node

    def traverse_partial(
        self,
        answers: Mapping[str, bool],
    ) -> TraversalState:
        """Evaluate known conditions without requiring a complete path."""
        current_node = self.root
        visited_node_ids: list[str] = []

        # Continue while the current node represents a decision.
        while isinstance(current_node, DecisionNode):
            condition_key = current_node.condition_key

            # Stop when the next required condition is unknown.
            if condition_key not in answers:
                return TraversalState(
                    diagnosis=None,
                    pending_condition_key=condition_key,
                    visited_node_ids=tuple(visited_node_ids),
                )

            answer = answers[condition_key]

            # Reject invalid values instead of coercing them to Boolean.
            if not isinstance(answer, bool):
                raise TypeError(
                    f"Condition '{condition_key}' must be a boolean."
                )

            # Register the decision node evaluated on this path.
            visited_node_ids.append(current_node.node_id)

            # Use the binary structure to select the next node.
            current_node = (
                current_node.left if answer else current_node.right
            )

        # Reaching a leaf means the binary traversal is complete.
        return TraversalState(
            diagnosis=current_node,
            pending_condition_key=None,
            visited_node_ids=tuple(visited_node_ids),
        )
