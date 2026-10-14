
"""Coordinate diagnostic answers with binary tree traversal."""

from plantcare.diagnosis.condition_mapper import ConditionMapper
from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.tree.binary_tree import BinaryDecisionTree
from plantcare.tree.node import DiagnosisNode
from plantcare.tree.traversal_state import TraversalState
from plantcare.diagnosis.diagnostic_completion_policy import (
    DiagnosticCompletionPolicy,
)
from plantcare.diagnosis.diagnostic_completion_state import (
    DiagnosticCompletionState,
)


class DiagnosticEngine:
    """Connect user selections with the binary decision tree."""

    def __init__(
        self,
        decision_tree: BinaryDecisionTree,
        condition_mapper: ConditionMapper,
    ) -> None:
        """Initialize the diagnostic engine dependencies."""
        # Keep tree traversal separate from condition mapping.
        self._decision_tree = decision_tree
        self._condition_mapper = condition_mapper

    def evaluate(
        self,
        context: DiagnosticContext,
    ) -> DiagnosisNode:
        """Evaluate recorded answers and return a diagnostic leaf."""
        # Convert selected symptoms into binary conditions.
        conditions = self._condition_mapper.build_conditions(context)

        # Require a complete path through the binary tree.
        return self._decision_tree.traverse(conditions)

    def evaluate_partial(
        self,
        context: DiagnosticContext,
    ) -> TraversalState:
        """Return the current diagnostic traversal state."""
        # Convert only answered questions into binary conditions.
        conditions = self._condition_mapper.build_conditions(context)

        # Preserve pending conditions instead of raising missing-answer errors.
        return self._decision_tree.traverse_partial(conditions)
    
    
    def evaluate_completion(
        self,
        context: DiagnosticContext,
        completion_policy: DiagnosticCompletionPolicy,
    ) -> DiagnosticCompletionState:
        """Evaluate whether a diagnostic session can finish."""
        # Obtain the current state of the binary tree traversal.
        traversal_state = self.evaluate_partial(context)

        # Apply the completion rules independently of tree traversal.
        return completion_policy.evaluate(
            context=context,
            traversal_state=traversal_state,
        )

