
"""Dynamic diagnostic questionnaire interface for PlantCare."""

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk
from typing import Any

from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.questionnaire_navigator import (
    QuestionnaireNavigator,
)
from plantcare.tree.traversal_state import TraversalState


class DiagnosticForm(ttk.Frame):
    """Display and manage dynamic plant diagnostic questions."""

    def __init__(
        self,
        parent: tk.Misc,
        questionnaire: dict[str, Any],
        on_complete: Callable[[DiagnosticContext], None],
        on_progress: (
            Callable[[DiagnosticContext], TraversalState] | None
        ) = None,
    ) -> None:
        """Initialize the diagnostic questionnaire interface."""
        super().__init__(parent, padding=24)

        # Initialize session state and navigation dependencies.
        self._context = DiagnosticContext()
        self._navigator = QuestionnaireNavigator(questionnaire)

        # Keep diagnostic evaluation outside the presentation layer.
        self._on_complete = on_complete
        self._on_progress = on_progress

        self._max_questions = questionnaire["max_questions"]
        self._current_question: dict[str, Any] | None = None

        # Store the controls associated with the current question.
        self._checkbox_variables: dict[str, tk.BooleanVar] = {}
        self._radio_variable = tk.StringVar(value="")

        self._build_layout()
        self._show_next_question()

    def _build_layout(self) -> None:
        """Create reusable questionnaire interface components."""
        self._progress_label = ttk.Label(
            self,
            font=("Segoe UI", 11),
        )
        self._progress_label.pack(
            anchor="w",
            pady=(0, 12),
        )

        self._question_label = ttk.Label(
            self,
            font=("Segoe UI", 16, "bold"),
            wraplength=650,
        )
        self._question_label.pack(
            anchor="w",
            pady=(0, 16),
        )

        self._options_frame = ttk.Frame(self)
        self._options_frame.pack(
            fill="x",
            pady=(0, 20),
        )

        # Show the traversal state without declaring a diagnosis.
        self._tree_status_label = ttk.Label(
            self,
            text="Estado del árbol: pendiente de respuestas.",
            font=("Segoe UI", 10),
            wraplength=650,
        )
        self._tree_status_label.pack(
            anchor="w",
            pady=(0, 16),
        )

        self._next_button = ttk.Button(
            self,
            text="Guardar y continuar",
            command=self._save_and_continue,
        )
        self._next_button.pack(anchor="e")

    def _show_next_question(self) -> None:
        """Display the next applicable unanswered question."""
        question = self._navigator.get_next_question(
            self._context
        )

        # Finish only when no applicable questions remain.
        if question is None:
            self._current_question = None
            self._on_complete(self._context)
            return

        self._current_question = question
        self._render_question(question)

    def _render_question(
        self,
        question: dict[str, Any],
    ) -> None:
        """Render controls for the selected question."""
        for widget in self._options_frame.winfo_children():
            widget.destroy()

        self._checkbox_variables.clear()
        self._radio_variable.set("")

        question_number = self._context.question_count + 1

        self._progress_label.configure(
            text=(
                f"Pregunta {question_number} "
                f"de hasta {self._max_questions}"
            )
        )

        self._question_label.configure(
            text=question["text"]
        )

        selection_mode = question["selection_mode"]

        for option in question["options"]:
            option_id = option["id"]
            option_label = option["label"]

            if selection_mode == "multiple":
                variable = tk.BooleanVar(value=False)
                self._checkbox_variables[option_id] = variable

                control = ttk.Checkbutton(
                    self._options_frame,
                    text=option_label,
                    variable=variable,
                )
            else:
                control = ttk.Radiobutton(
                    self._options_frame,
                    text=option_label,
                    variable=self._radio_variable,
                    value=option_id,
                )

            control.pack(anchor="w", pady=6)

    def _get_selected_options(self) -> tuple[str, ...]:
        """Collect selected option identifiers."""
        if self._current_question is None:
            return ()

        if self._current_question["selection_mode"] == "multiple":
            return tuple(
                option_id
                for option_id, variable
                in self._checkbox_variables.items()
                if variable.get()
            )

        selected_option = self._radio_variable.get()

        return (selected_option,) if selected_option else ()

    def _update_traversal_status(self) -> bool:
        """Evaluate and display the current tree traversal state."""
        if self._on_progress is None:
            return True

        try:
            state = self._on_progress(self._context)
        except (ValueError, TypeError) as error:
            messagebox.showerror(
                "Error de evaluación",
                f"No se pudo evaluar el árbol:\n{error}",
            )
            return False

        if state.is_complete:
            status_text = (
                "Ruta del árbol completada "
                "(resultado preliminar). "
                "Continuaremos recopilando información."
            )
        else:
            status_text = (
                "Ruta del árbol pendiente: "
                "se necesitan más respuestas."
            )

        self._tree_status_label.configure(
            text=status_text
        )
        return True

    def _save_and_continue(self) -> None:
        """Save the current answer and continue the questionnaire."""
        if self._current_question is None:
            return

        selected_options = self._get_selected_options()

        if not selected_options:
            messagebox.showwarning(
                "Respuesta requerida",
                "Selecciona al menos una opción para continuar.",
            )
            return

        self._context.record_answer(
            question_id=self._current_question["id"],
            selected_option_ids=selected_options,
        )

        # Evaluate the current tree state after recording the answer.
        if not self._update_traversal_status():
            return

        # Continue collecting relevant symptoms.
        self._show_next_question()
