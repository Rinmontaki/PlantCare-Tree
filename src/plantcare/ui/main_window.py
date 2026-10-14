
"""Main desktop window for the PlantCare application."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.ui.diagnostic_form import DiagnosticForm


# Locate project data independently of the current terminal directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
QUESTIONNAIRE_PATH = PROJECT_ROOT / "data" / "questionnaire.json"


class PlantCareApp(tk.Tk):
    """Manage the main window and diagnostic interface."""

    def __init__(self) -> None:
        """Initialize the main application window."""
        super().__init__()

        # Configure the window properties.
        self.title("PlantCare Tree")
        self.geometry("960x640")
        self.minsize(720, 480)

        # Store the questionnaire used during the current session.
        self._questionnaire: dict[str, Any] | None = None

        # Create the main container for application screens.
        self._container = ttk.Frame(self, padding=24)
        self._container.pack(fill="both", expand=True)

        # Display the welcome screen.
        self._show_home()

    def _clear_screen(self) -> None:
        """Remove widgets belonging to the previous screen."""
        for widget in self._container.winfo_children():
            widget.destroy()

    def _show_home(self) -> None:
        """Display the application's welcome screen."""
        self._clear_screen()

        # Display the application name.
        title = ttk.Label(
            self._container,
            text="PlantCare Tree",
            font=("Segoe UI", 26, "bold"),
        )
        title.pack(pady=(65, 16))

        # Introduce the diagnostic questionnaire.
        description = ttk.Label(
            self._container,
            text="Sistema de orientación para el cuidado de plantas",
            font=("Segoe UI", 13),
        )
        description.pack(pady=(0, 24))

        # Allow the user to begin a new diagnostic session.
        start_button = ttk.Button(
            self._container,
            text="Iniciar diagnóstico",
            command=self._start_diagnosis,
        )
        start_button.pack(pady=12)

    def _start_diagnosis(self) -> None:
        """Load the questionnaire and display its first question."""
        try:
            # Load the validated questionnaire from its JSON file.
            questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)
        except (OSError, ValueError) as error:
            # Keep the current screen visible if loading fails.
            messagebox.showerror(
                "Error de configuración",
                f"No se pudo cargar el formulario:\n{error}",
            )
            return

        self._questionnaire = questionnaire
        self._clear_screen()

        # Connect the diagnostic form to the completion callback.
        form = DiagnosticForm(
            parent=self._container,
            questionnaire=questionnaire,
            on_complete=self._show_summary,
        )
        form.pack(fill="both", expand=True)

    def _show_summary(self, context: DiagnosticContext) -> None:
        """Display a summary of the user's recorded answers."""
        self._clear_screen()

        title = ttk.Label(
            self._container,
            text="Resumen de observaciones",
            font=("Segoe UI", 22, "bold"),
        )
        title.pack(pady=(12, 18))

        # Explain that this stage does not produce a diagnosis yet.
        notice = ttk.Label(
            self._container,
            text="Las respuestas se registraron correctamente.",
            font=("Segoe UI", 12),
        )
        notice.pack(pady=(0, 16))

        if self._questionnaire is None:
            return

        # Convert internal IDs into readable labels.
        answers = context.get_answers()

        for question in self._questionnaire["questions"]:
            selected_ids = answers.get(question["id"])

            if selected_ids is None:
                continue

            option_labels = {
                option["id"]: option["label"]
                for option in question["options"]
            }

            selected_labels = [
                option_labels[option_id]
                for option_id in selected_ids
            ]

            # Display each answered question and its selections.
            question_text = ttk.Label(
                self._container,
                text=question["text"],
                font=("Segoe UI", 11, "bold"),
                wraplength=760,
            )
            question_text.pack(anchor="w", pady=(8, 3))

            answer_text = ttk.Label(
                self._container,
                text=", ".join(selected_labels),
                wraplength=760,
            )
            answer_text.pack(anchor="w")

        # Return to the welcome screen for a new session.
        restart_button = ttk.Button(
            self._container,
            text="Nuevo diagnóstico",
            command=self._show_home,
        )
        restart_button.pack(pady=24)
