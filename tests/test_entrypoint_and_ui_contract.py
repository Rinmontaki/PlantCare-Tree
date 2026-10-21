"""Check the currently shipped UI wiring without starting a desktop session."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_launcher_targets_customtkinter_questionnaire():
    """Prevent accidental launch of the obsolete demonstration window."""
    source = (ROOT / "main.py").read_text(encoding="utf-8")
    module = ast.parse(source)
    assert "PlantCareQuestionnaireWindow" in source
    assert "PlantCareApp" not in source
    assert "app.mainloop()" in source


def test_ai_output_is_registered_and_appears_after_catalogue_care():
    """Prevent the prior missing-label and presentation-order regressions."""
    source = (
        ROOT / "src" / "plantcare" / "ui" / "questionnaire_window.py"
    ).read_text(encoding="utf-8")
    ast.parse(source)
    assert "self._ai_result_labels[problem_code] = ai_label" in source
    assert (
    source.index('text=problem["organic_or_nonchemical_management"]')
    < source.index("ai_label = ctk.CTkLabel(")
)
    assert "assessment.traces" in source
    assert 'from plantcare.tree.tree_loader import load_tree' not in source
