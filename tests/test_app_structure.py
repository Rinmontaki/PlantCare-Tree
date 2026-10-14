
"""Tests for the initial PlantCare application structure."""

import tkinter as tk

from plantcare.ui.main_window import PlantCareApp


def test_main_window_inherits_from_tk() -> None:
    """Verify that the application uses a Tkinter root window."""
    # Ensure the main application class extends Tkinter correctly.
    assert issubclass(PlantCareApp, tk.Tk)
