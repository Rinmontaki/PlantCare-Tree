
"""Integration tests for the PlantCare diagnostic form."""

import tkinter as tk
from collections.abc import Iterator
from pathlib import Path
from tkinter import ttk

import pytest

from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.ui.diagnostic_form import DiagnosticForm


# Locate the questionnaire used by the application.
QUESTIONNAIRE_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "questionnaire.json"
)


@pytest.fixture
def form_session() -> Iterator[
    tuple[DiagnosticForm, list[DiagnosticContext]]
]:
    """Create a Tkinter form and clean up its window after testing."""
    root = tk.Tk()

    # Keep the test window hidden while preserving widget behavior.
    root.withdraw()

    questionnaire = load_questionnaire(QUESTIONNAIRE_PATH)
    completed_contexts: list[DiagnosticContext] = []

    form = DiagnosticForm(
        parent=root,
        questionnaire=questionnaire,
        on_complete=completed_contexts.append,
    )
    form.pack()

    try:
        yield form, completed_contexts
    finally:
        # Release Tkinter resources after each test.
        root.destroy()


def select_option(
    form: DiagnosticForm,
    option_label: str,
) -> None:
    """Select a checkbox or radio button by its visible label."""
    for widget in form._options_frame.winfo_children():
        if isinstance(widget, (ttk.Checkbutton, ttk.Radiobutton)):
            if widget.cget("text") == option_label:
                widget.invoke()
                return

    raise AssertionError(f"Option not found: {option_label}")


def test_form_displays_first_question(
    form_session: tuple[DiagnosticForm, list[DiagnosticContext]],
) -> None:
    """Verify that the form initially displays the first question."""
    form, _ = form_session

    assert form._current_question is not None
    assert form._current_question["id"] == "leaf_symptoms"
    assert form._progress_label.cget("text") == "Pregunta 1 de hasta 10"


def test_form_processes_multiple_symptoms(
    form_session: tuple[DiagnosticForm, list[DiagnosticContext]],
) -> None:
    """Verify that multiple symptoms activate relevant follow-up questions."""
    form, completed_contexts = form_session

    # Select two symptoms in the first question.
    select_option(form, "Insectos visibles")
    select_option(form, "Agujeros o mordeduras")
    form._next_button.invoke()

    # Insect-related questions must appear first.
    assert form._current_question["id"] == "insect_appearance"

    select_option(form, "Orugas o insectos que comen hojas")
    form._next_button.invoke()

    # Leaf damage questions must also be activated.
    assert form._current_question["id"] == "leaf_damage"

    select_option(form, "Agujeros irregulares")
    form._next_button.invoke()

    # Finish the questionnaire by answering the soil question.
    assert form._current_question["id"] == "soil_condition"

    select_option(form, "Moderadamente húmedo")
    form._next_button.invoke()

    # The completion callback must receive all recorded answers.
    assert len(completed_contexts) == 1

    context = completed_contexts[0]
    answers = context.get_answers()

    assert context.question_count == 4
    assert answers["leaf_symptoms"] == (
        "leaf_holes",
        "visible_insects",
    )
    assert answers["insect_appearance"] == ("chewing_insects",)
    assert answers["leaf_damage"] == ("irregular_holes",)
    assert answers["soil_condition"] == ("normal_soil",)


def test_form_rejects_empty_selection(
    form_session: tuple[DiagnosticForm, list[DiagnosticContext]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prevent navigation when no answer is selected."""
    form, completed_contexts = form_session
    warnings: list[tuple[str, str]] = []

    # Replace the warning dialog to avoid blocking automated tests.
    monkeypatch.setattr(
        "plantcare.ui.diagnostic_form.messagebox.showwarning",
        lambda title, message: warnings.append((title, message)),
    )

    # Attempt to advance without selecting an option.
    form._next_button.invoke()

    assert form._current_question["id"] == "leaf_symptoms"
    assert len(warnings) == 1
    assert completed_contexts == []
