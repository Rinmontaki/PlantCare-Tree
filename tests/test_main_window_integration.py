
"""Integration tests for the complete PlantCare desktop workflow."""

import tkinter as tk
from tkinter import ttk

from plantcare.ui.diagnostic_form import DiagnosticForm
from plantcare.ui.main_window import PlantCareApp


def test_complete_diagnostic_workflow() -> None:
    """Verify the complete flow from symptom selection to tree result."""
    app = PlantCareApp()

    # Hide the application window during automated testing.
    app.withdraw()

    try:
        # Start a diagnostic session using the configured JSON files.
        app._start_diagnosis()

        # Retrieve the diagnostic form created by the main window.
        form = next(
            widget
            for widget in app._container.winfo_children()
            if isinstance(widget, DiagnosticForm)
        )

        # Select multiple symptoms in the first question.
        form._checkbox_variables["visible_insects"].set(True)
        form._checkbox_variables["leaf_holes"].set(True)
        form._save_and_continue()

        assert form._current_question is not None
        assert form._current_question["id"] == "insect_appearance"

        # Answer the question about insect appearance.
        form._radio_variable.set("chewing_insects")
        form._save_and_continue()

        assert form._current_question is not None
        assert form._current_question["id"] == "leaf_damage"

        # Record the observed leaf damage.
        form._checkbox_variables["irregular_holes"].set(True)
        form._save_and_continue()

        assert form._current_question is not None
        assert form._current_question["id"] == "soil_condition"

        # Complete the final applicable question.
        form._radio_variable.set("normal_soil")
        form._save_and_continue()

        # Collect all labels displayed on the result screen.
        result_labels = [
            widget.cget("text")
            for widget in app._container.winfo_children()
            if isinstance(widget, ttk.Label)
        ]

        # Verify that the binary tree reached the expected test leaf.
        assert "Hoja alcanzada: diagnosis_001" in result_labels
        assert "Códigos de prueba: PC-031" in result_labels

        # Verify that the result is clearly identified as a demo.
        assert (
            "RESULTADO DE DEMOSTRACIÓN - NO VALIDADO"
            in result_labels
        )

        # Ensure the original symptoms remain visible in the summary.
        assert any(
            "Insectos visibles" in label
            for label in result_labels
        )

        assert any(
            "Agujeros o mordeduras" in label
            for label in result_labels
        )

    finally:
        # Always release Tkinter resources after the test.
        app.destroy()
