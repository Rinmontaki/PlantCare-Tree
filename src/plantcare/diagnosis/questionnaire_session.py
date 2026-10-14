
"""Manage the state and navigation of a diagnostic questionnaire."""

from collections.abc import Sequence
from typing import Any

from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.questionnaire_navigator import QuestionnaireNavigator


class QuestionnaireSession:
    """Coordinate questionnaire answers without UI dependencies."""

    def __init__(self, questionnaire: dict[str, Any]) -> None:
        """Create a questionnaire session from validated configuration."""
        self._context = DiagnosticContext()
        self._navigator = QuestionnaireNavigator(questionnaire)

        self._questions = tuple(questionnaire["questions"])

        self._question_by_id = {
            question["id"]: question
            for question in self._questions
        }

        self._question_positions = {
            question["id"]: index
            for index, question in enumerate(self._questions)
        }

        self._current_question = self._navigator.get_next_question(
            self._context
        )

        # Track visited questions without deleting recorded answers.
        self._navigation_history: list[str] = []

        if self._current_question is not None:
            self._navigation_history.append(
                self._current_question["id"]
            )

    @property
    def context(self) -> DiagnosticContext:
        """Return the context containing recorded answers."""
        return self._context

    @property
    def current_question(self) -> dict[str, Any] | None:
        """Return the currently active question."""
        return self._current_question

    @property
    def is_finished(self) -> bool:
        """Check whether the questionnaire has been completed."""
        return self._current_question is None

    @property
    def can_go_back(self) -> bool:
        """Check whether a previously visited question is available."""
        if self._current_question is None:
            return bool(self._navigation_history)

        return len(self._navigation_history) > 1

    def go_back(self) -> bool:
        """Return to the previous question without removing its answer."""
        if not self.can_go_back:
            return False

        if self._current_question is None:
            # Reopen the last question after finishing the questionnaire.
            previous_id = self._navigation_history[-1]
        else:
            # Remove the current question from the navigation path.
            self._navigation_history.pop()
            previous_id = self._navigation_history[-1]

        self._current_question = self._question_by_id[previous_id]
        return True

    def submit_answer(
        self,
        selected_option_ids: Sequence[str],
    ) -> None:
        """Validate, save, and advance to the next applicable question."""
        question = self._current_question

        if question is None:
            raise ValueError("The questionnaire is already finished.")

        if isinstance(selected_option_ids, (str, bytes)):
            raise TypeError("Selected options must be a sequence.")

        selections = tuple(selected_option_ids)

        if not selections:
            raise ValueError("At least one option must be selected.")

        available_options = {
            option["id"]
            for option in question["options"]
        }

        if any(
            option_id not in available_options
            for option_id in selections
        ):
            raise ValueError("Invalid option for the current question.")

        # Single-choice questions accept exactly one option.
        if question["selection_mode"] == "single" and len(selections) != 1:
            raise ValueError(
                "Single-choice questions require exactly one answer."
            )

        # Reject contradictory multiple-choice selections.
        exclusive_options = {
            "insect_appearance": {"unknown_insects"},
        }

        exclusive_ids = exclusive_options.get(
            question["id"],
            set(),
        )

        if len(selections) > 1 and exclusive_ids.intersection(selections):
            raise ValueError(
                "Exclusive options cannot be combined "
                "with other selections."
            )

        # Save the new answer or replace a previously recorded one.
        self._context.record_answer(
            question_id=question["id"],
            selected_option_ids=selections,
        )

        # Remove answers made irrelevant by the updated selection.
        self._remove_inapplicable_answers()

        # Find the following question while preserving saved answers.
        next_question = self._find_next_question_after(question["id"])

        self._current_question = next_question

        if next_question is not None:
            self._navigation_history.append(next_question["id"])

    def _remove_inapplicable_answers(self) -> None:
        """Remove answers whose visibility conditions are no longer met."""
        answers = self._context.get_answers()

        for question in self._questions:
            visibility = question.get("show_if")

            if visibility is None:
                continue

            required_option = visibility["selected_option"]

            is_applicable = any(
                required_option in selected_options
                for selected_options in answers.values()
            )

            if not is_applicable:
                question_id = question["id"]

                self._context.remove_answer(question_id)
                answers.pop(question_id, None)

    def _find_next_question_after(
        self,
        question_id: str,
    ) -> dict[str, Any] | None:
        """Find the next applicable question while retaining later answers."""
        current_position = self._question_positions[question_id]
        saved_answers = self._context.get_answers()

        # Use a temporary context containing answers through the
        # current question. Later answers remain in the real context.
        partial_context = DiagnosticContext()

        for question in self._questions[:current_position + 1]:
            saved_selection = saved_answers.get(question["id"])

            if saved_selection is not None:
                partial_context.record_answer(
                    question_id=question["id"],
                    selected_option_ids=saved_selection,
                )

        return self._navigator.get_next_question(partial_context)
