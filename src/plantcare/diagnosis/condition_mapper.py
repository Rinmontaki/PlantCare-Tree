
"""Convert diagnostic selections into binary tree conditions."""

from collections.abc import Mapping, Sequence

from plantcare.diagnosis.diagnostic_context import DiagnosticContext


MIN_OPTIONS_PER_QUESTION = 3
MAX_OPTIONS_PER_QUESTION = 5


class ConditionMapper:
    """Map multiple-choice answers to Boolean tree conditions."""

    def __init__(
        self,
        question_options: Mapping[str, Sequence[str]],
    ) -> None:
        """Initialize and validate the available question options."""
        self._question_options: dict[str, tuple[str, ...]] = {}
        registered_options: set[str] = set()

        for question_id, option_ids in question_options.items():
            # Ensure every question has a valid identifier.
            if not isinstance(question_id, str) or not question_id.strip():
                raise ValueError("Question IDs must be non-empty strings.")

            # Prevent treating a single string as a list of options.
            if isinstance(option_ids, (str, bytes)):
                raise TypeError("Question options must be a sequence.")

            options = tuple(option_ids)

            # Each visible question must contain 3 to 5 alternatives.
            if not MIN_OPTIONS_PER_QUESTION <= len(options) <= MAX_OPTIONS_PER_QUESTION:
                raise ValueError("Questions must contain 3 to 5 options.")

            # Ensure all options are valid and uniquely identified.
            if any(
                not isinstance(option, str) or not option.strip()
                for option in options
            ):
                raise ValueError("Option IDs must be non-empty strings.")

            if len(set(options)) != len(options):
                raise ValueError("Duplicate options are not allowed.")

            # Option IDs must be globally unique to avoid collisions.
            if registered_options.intersection(options):
                raise ValueError("Option IDs must be unique across questions.")

            registered_options.update(options)
            self._question_options[question_id] = options

    def build_conditions(
        self,
        context: DiagnosticContext,
    ) -> dict[str, bool]:
        """Convert answered questions into Boolean conditions."""
        conditions: dict[str, bool] = {}

        for question_id, selected_options in context.get_answers().items():
            # Only registered questions can produce binary conditions.
            if question_id not in self._question_options:
                raise ValueError(f"Unknown question: {question_id}")

            available_options = self._question_options[question_id]
            selected_set = set(selected_options)

            # Reject options that do not belong to this question.
            if selected_set.difference(available_options):
                raise ValueError(
                    f"Invalid selection for question: {question_id}"
                )

            # Selected options become True; unselected options become False.
            for option_id in available_options:
                conditions[option_id] = option_id in selected_set

        return conditions
