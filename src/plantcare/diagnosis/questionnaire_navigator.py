
"""Control dynamic navigation through diagnostic questions."""

from typing import Any

from plantcare.diagnosis.diagnostic_context import DiagnosticContext


class QuestionnaireNavigator:
    """Find the next applicable question using previous answers."""

    def __init__(self, questionnaire: dict[str, Any]) -> None:
        """Initialize the navigator with a validated questionnaire."""
        # Preserve the question order defined in the JSON file.
        self._questions = tuple(questionnaire["questions"])

    def get_next_question(
        self,
        context: DiagnosticContext,
    ) -> dict[str, Any] | None:
        """Return the next visible unanswered question."""

        # Retrieve previously recorded answers.
        answers = context.get_answers()

        # Collect all selected option IDs across answered questions.
        selected_options = {
            option_id
            for selections in answers.values()
            for option_id in selections
        }

        # Evaluate questions in their original JSON order.
        for question in self._questions:
            question_id = question["id"]

            # Skip questions that have already been answered.
            if question_id in answers:
                continue

            # Skip conditional questions when their trigger is absent.
            if not self._is_visible(question, selected_options):
                continue

            return question

        # None indicates that no applicable questions remain.
        return None

    @staticmethod
    def _is_visible(
        question: dict[str, Any],
        selected_options: set[str],
    ) -> bool:
        """Check whether a question meets its visibility condition."""

        visibility_condition = question.get("show_if")

        # Questions without conditions are always eligible.
        if visibility_condition is None:
            return True

        # Conditional questions require a previously selected option.
        required_option = visibility_condition["selected_option"]

        return required_option in selected_options
