
"""Main desktop window for the PlantCare application."""

import tkinter as tk
from tkinter import ttk


class PlantCareApp(tk.Tk):
    """Manage the main application window and its widgets."""

    def __init__(self) -> None:
        """Initialize the application's main window."""
        super().__init__()

        # Configure the main window properties.
        self.title("PlantCare Tree")
        self.geometry("960x640")
        self.minsize(720, 480)

        # Build the initial user interface.
        self._build_layout()

    def _build_layout(self) -> None:
        """Create and organize the main interface components."""
        # Create the main container for all interface widgets.
        container = ttk.Frame(self, padding=24)
        container.pack(fill="both", expand=True)

        # Display the application's title.
        title_label = ttk.Label(
            container,
            text="PlantCare Tree",
            font=("Segoe UI", 22, "bold"),
        )
        title_label.pack(pady=(30, 12))

        # Display the application's introductory message.
        description_label = ttk.Label(
            container,
            text="Diagnóstico orientativo para tus plantas",
            font=("Segoe UI", 12),
        )
        description_label.pack()
