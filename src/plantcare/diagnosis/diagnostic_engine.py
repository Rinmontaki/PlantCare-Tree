
"""Coordinate diagnostic answers with binary tree traversal."""

from plantcare.diagnosis.condition_mapper import ConditionMapper
from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.tree.binary_tree import BinaryDecisionTree
from plantcare.tree.node import DiagnosisNode


class DiagnosticEngine:
    """Connect user selections with the binary decision tree."""

    def __init__(
        self,
        decision_tree: BinaryDecisionTree,
        condition_mapper: ConditionMapper,
    ) -> None:
        """Initialize the diagnostic engine dependencies."""
        # Keep the tree traversal separate from condition mapping.
        self._decision_tree = decision_tree
        self._condition_mapper = condition_mapper

    def evaluate(
        self,
        context: DiagnosticContext,
    ) -> DiagnosisNode:
        """Evaluate recorded answers and return a diagnostic leaf.

        Raises:
            ValueError: If required answers are missing or invalid.
            TypeError: If a tree condition is not Boolean.
        """
        # Convert selected symptom IDs into binary conditions.
        conditions = self._condition_mapper.build_conditions(context)

        # Evaluate the conditions using the loaded binary tree.
        # Missing conditions are never assumed to be False.
        diagnosis = self._decision_tree.traverse(conditions)

        # Return the leaf containing candidate problem codes.
        return diagnosis
