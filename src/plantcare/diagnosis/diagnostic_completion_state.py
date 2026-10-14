
"""Represent the readiness of a plant diagnostic session."""

from dataclasses import dataclass

from plantcare.tree.traversal_state import TraversalState


@dataclass(frozen=True, slots=True)
class DiagnosticCompletionState:
    """Track whether a diagnostic session can safely finish."""

    # Store the current binary tree traversal result.
    traversal_state: TraversalState

    # Identify required questions that remain unanswered.
    pending_required_questions: tuple[str, ...]

    @property
    def is_ready_to_finish(self) -> bool:
        """Check whether all completion requirements are satisfied."""
        return (
            self.traversal_state.is_complete
            and not self.pending_required_questions
        )

    @property
    def requires_more_information(self) -> bool:
        """Check whether the diagnostic session must continue."""
        return not self.is_ready_to_finish
