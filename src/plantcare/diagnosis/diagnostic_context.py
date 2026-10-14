
"""Manage user responses during the plant diagnostic process."""

from collections.abc import Sequence


MAX_DIAGNOSTIC_QUESTIONS = 10


class DiagnosticContext:
    """Store multiple selections for each diagnostic question."""

    def __init__(self) -> None:
        """Initialize an empty diagnostic context."""
        self._answers: dict[str, tuple[str, ...]] = {}

    def record_answer(
        self,
        question_id: str,
        selected_option_ids: Sequence[str],
    ) -> None:
        """Record or update the selected options for a question."""

        # Every diagnostic question must have a valid identifier.
        if not isinstance(question_id, str) or not question_id.strip():
            raise ValueError("Question ID cannot be empty.")

        # A string alone is not a valid collection of option IDs.
        if isinstance(selected_option_ids, (str, bytes)):
            raise TypeError("Selected options must be a sequence.")

        selections = tuple(selected_option_ids)

        # Each answered question must have at least one selection.
        if not selections:
            raise ValueError("At least one option must be selected.")

        # Reject invalid or duplicated option identifiers.
        if any(
            not isinstance(option_id, str) or not option_id.strip()
            for option_id in selections
        ):
            raise ValueError("Option IDs must be non-empty strings.")

        if len(set(selections)) != len(selections):
            raise ValueError("Duplicate selections are not allowed.")

        # Allow updates without counting the same question twice.
        if (
            question_id not in self._answers
            and len(self._answers) >= MAX_DIAGNOSTIC_QUESTIONS
        ):
            raise ValueError("Maximum diagnostic questions reached.")

        # Store immutable selections to preserve response consistency.
        self._answers[question_id] = selections
        
    
    def remove_answer(self, question_id: str) -> None:
        """Remove a previously recorded diagnostic answer."""
        self._answers.pop(question_id, None)

    @property
    def question_count(self) -> int:
        """Return the number of answered diagnostic questions."""
        return len(self._answers)

    def get_answers(self) -> dict[str, tuple[str, ...]]:
        """Return a copy of all recorded diagnostic answers."""
        return self._answers.copy()
