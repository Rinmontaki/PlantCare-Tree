
"""Main desktop window for the PlantCare application."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Any

from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.diagnostic_engine import DiagnosticEngine
from plantcare.diagnosis.diagnostic_engine_factory import (
    create_diagnostic_engine,
)
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.tree.tree_loader import load_tree
from plantcare.ui.diagnostic_form import DiagnosticForm


# Define configuration paths relative to the project directory.
PROJECT_ROOT = Path(__file__).resolve().parents[3]
QUESTIONNAIRE_PATH = PROJECT_ROOT / "data" / "questionnaire.json"
DEMO_TREE_PATH = PROJECT_ROOT / "data" / "demo_tree.json"


class PlantCareApp(tk.Tk):
    """Manage the PlantCare desktop application and its screens."""

    def __init__(self) -> None:
        """Initialize the main application window."""
        super().__init__()

        # Configure the main window.
        self.title("PlantCare Tree")
        self.geometry("960x640")
        self.minsize(720, 480)

        # Store the configuration and diagnostic engine.
        self._questionnaire: dict[str, Any] | None = None
        self._diagnostic_engine: DiagnosticEngine | None = None

        # Create the application's main container.
        self._container = ttk.Frame(self, padding=24)
        self._container.pack(fill="both", expand=True)

        # Display the welcome screen.
        self._show_home()

    def _clear_screen(self) -> None:
        """Remove all widgets from the current screen."""
        for widget in self._container.winfo_children():
            widget.destroy()

    def _show_home(self) -> None:
        """Display the application's welcome screen."""
        self._clear_screen()

        title = ttk.Label(
            self._container,
            text="PlantCare Tree",
            font=("Segoe UI", 26, "bold"),
        )
        title.pack(pady=(65, 16))

        description = ttk.Label(
            self._container,
            text="Sistema de orientación para el cuidado de plantas",
            font=("Segoe UI", 13),
        )
        description.pack(pady=(0, 24))

        start_button = ttk.Button(
            self._container,
            text="Iniciar diagnóstico",
            command=self._start_diagnosis,
        )
        start_button.pack(pady=12)

    def _start_diagnosis(self) -> None:
        """Load configurations and start a diagnostic session."""
        try:
            # Load and validate the questionnaire configuration.
            questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)

            # Build the binary tree from its demonstration JSON.
            root = load_tree(DEMO_TREE_PATH)

            # Connect the tree with the questionnaire conditions.
            diagnostic_engine = create_diagnostic_engine(
                questionnaire=questionnaire,
                root=root,
            )

        except (OSError, ValueError, TypeError, KeyError) as error:
            messagebox.showerror(
                "Error de configuración",
                f"No se pudo iniciar el diagnóstico:\n{error}",
            )
            return

        # Store the initialized components.
        self._questionnaire = questionnaire
        self._diagnostic_engine = diagnostic_engine

        self._clear_screen()

        # Create the diagnostic form with its completion callback.
        form = DiagnosticForm(
            parent=self._container,
            questionnaire=questionnaire,
            on_complete=self._show_summary,
        )
        form.pack(fill="both", expand=True)

    def _show_summary(self, context: DiagnosticContext) -> None:
        """Evaluate the binary tree and display recorded observations."""
        if self._diagnostic_engine is None:
            messagebox.showerror(
                "Error",
                "El motor diagnóstico no está disponible.",
            )
            return

        try:
            # Evaluate all recorded conditions through the binary tree.
            diagnosis = self._diagnostic_engine.evaluate(context)

        except (ValueError, TypeError) as error:
            messagebox.showerror(
                "Error de diagnóstico",
                f"No se pudo evaluar el árbol:\n{error}",
            )
            return

        self._clear_screen()

        title = ttk.Label(
            self._container,
            text="Resultado del diagnóstico",
            font=("Segoe UI", 22, "bold"),
        )
        title.pack(pady=(12, 18))

        # Clearly identify results produced by the sample tree.
        demo_notice = ttk.Label(
            self._container,
            text="RESULTADO DE DEMOSTRACIÓN - NO VALIDADO",
            font=("Segoe UI", 11, "bold"),
        )
        demo_notice.pack(pady=(0, 14))

        # Display the terminal node reached during traversal.
        diagnosis_label = ttk.Label(
            self._container,
            text=f"Hoja alcanzada: {diagnosis.node_id}",
            font=("Segoe UI", 12, "bold"),
        )
        diagnosis_label.pack(pady=(0, 8))

        problem_codes = ", ".join(diagnosis.problem_codes)

        codes_label = ttk.Label(
            self._container,
            text=f"Códigos de prueba: {problem_codes}",
            font=("Segoe UI", 11),
        )
        codes_label.pack(pady=(0, 16))

        summary_title = ttk.Label(
            self._container,
            text="Observaciones registradas",
            font=("Segoe UI", 15, "bold"),
        )
        summary_title.pack(anchor="w", pady=(8, 12))

        # Preserve and display every question answered by the user.
        if self._questionnaire is not None:
            answers = context.get_answers()

            for question in self._questionnaire["questions"]:
                selected_ids = answers.get(question["id"])

                if selected_ids is None:
                    continue

                # Convert internal option IDs into readable Spanish labels.
                option_labels = {
                    option["id"]: option["label"]
                    for option in question["options"]
                }

                selected_labels = [
                    option_labels[option_id]
                    for option_id in selected_ids
                ]

                question_label = ttk.Label(
                    self._container,
                    text=question["text"],
                    font=("Segoe UI", 11, "bold"),
                    wraplength=760,
                )
                question_label.pack(anchor="w", pady=(8, 3))

                answer_label = ttk.Label(
                    self._container,
                    text=", ".join(selected_labels),
                    wraplength=760,
                )
                answer_label.pack(anchor="w")

        # Allow the user to restart the diagnostic process.
        restart_button = ttk.Button(
            self._container,
            text="Nuevo diagnóstico",
            command=self._show_home,
        )
        restart_button.pack(pady=24)
