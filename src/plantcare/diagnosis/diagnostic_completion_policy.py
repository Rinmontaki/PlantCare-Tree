
"""Determine when a plant diagnostic session can finish."""

from typing import Any

from plantcare.diagnosis.diagnostic_completion_state import (
    DiagnosticCompletionState,
)
from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.tree.traversal_state import TraversalState


class DiagnosticCompletionPolicy:
    """Evaluate the completion requirements of a diagnostic session."""

    def __init__(
        self,
        questionnaire: dict[str, Any],
    ) -> None:
        """Initialize the policy using a validated questionnaire."""
        self._questions = tuple(questionnaire["questions"])

    def evaluate(
        self,
        context: DiagnosticContext,
        traversal_state: TraversalState,
    ) -> DiagnosticCompletionState:
        """Determine whether the diagnostic session can finish."""
        answers = context.get_answers()

        # Collect all option IDs selected by the user.
        selected_options = {
            option_id
            for selections in answers.values()
            for option_id in selections
        }

        # All currently applicable questions are required.
        pending_questions = tuple(
            question["id"]
            for question in self._questions
            if question["id"] not in answers
            and self._is_applicable(question, selected_options)
        )

        return DiagnosticCompletionState(
            traversal_state=traversal_state,
            pending_required_questions=pending_questions,
        )

    @staticmethod
    def _is_applicable(
        question: dict[str, Any],
        selected_options: set[str],
    ) -> bool:
        """Check whether a question applies to the current answers."""
        visibility_condition = question.get("show_if")

        # Questions without visibility conditions always apply.
        if visibility_condition is None:
            return True

        required_option = visibility_condition["selected_option"]

        # Conditional questions apply only when their trigger is selected.
        return required_option in selected_options
