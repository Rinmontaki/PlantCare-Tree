
"""Reusable botanical symptom selection card."""

import tkinter as tk
from collections.abc import Callable
from pathlib import Path

import customtkinter as ctk
from PIL import Image

from plantcare.ui.plantcare_theme import PlantCareTheme as Theme


class SymptomOptionCard(ctk.CTkFrame):
    """Display a selectable option with botanical styling."""

    def __init__(
        self,
        parent: ctk.CTkBaseClass,
        option_id: str,
        label: str,
        icon: str,
        on_change: Callable[[str, bool], None] | None = None,
        image_path: str | Path | None = None,
    ) -> None:
        """Initialize a selectable botanical option card."""
        super().__init__(
            parent,
            fg_color=Theme.CARD,
            corner_radius=14,
            border_width=1,
            border_color=Theme.BORDER,
            height=86,
        )

        self.option_id = option_id
        self._on_change = on_change
        self._selected = tk.BooleanVar(value=False)

        # Keep a reference to the botanical image.
        self._botanical_image: ctk.CTkImage | None = None

        # Configure the internal layout.
        self.grid_columnconfigure(1, weight=1)
        self.grid_propagate(False)

        # Load the botanical illustration when available.
        if image_path is not None:
            path = Path(image_path)

            if not path.is_file():
                raise FileNotFoundError(
                    f"Botanical illustration not found: {path}"
                )

            with Image.open(path) as source_image:
                botanical_image = source_image.convert("RGBA")

            self._botanical_image = ctk.CTkImage(
                light_image=botanical_image,
                dark_image=botanical_image,
                size=(52, 52),
            )

        # Display an illustration or fall back to an emoji.
        self._icon_label = ctk.CTkLabel(
            self,
            text="" if self._botanical_image else icon,
            image=self._botanical_image,
            width=56,
            height=56,
            corner_radius=12,
            fg_color=Theme.SIDEBAR,
            text_color=Theme.PRIMARY,
            font=("Segoe UI Emoji", 23),
        )

        self._icon_label.grid(
            row=0,
            column=0,
            padx=(16, 12),
            pady=14,
        )

        # Display the selectable option.
        self._checkbox = ctk.CTkCheckBox(
            self,
            text=label,
            variable=self._selected,
            command=self._handle_selection,
            font=(Theme.FONT_FAMILY, 14, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            border_color=Theme.SECONDARY,
            checkbox_width=23,
            checkbox_height=23,
            corner_radius=7,
        )

        self._checkbox.grid(
            row=0,
            column=1,
            sticky="w",
            padx=(0, 18),
        )

    def _handle_selection(self) -> None:
        """Handle a user-triggered selection change."""
        self.set_selected(
            selected=self._selected.get(),
            notify=True,
        )

    def set_selected(
        self,
        selected: bool,
        notify: bool = False,
    ) -> None:
        """Update selection state and card appearance."""
        self._selected.set(selected)

        self.configure(
            fg_color=(
                Theme.OPTION_SELECTED
                if selected
                else Theme.CARD
            ),
            border_color=(
                Theme.PROGRESS_FILL
                if selected
                else Theme.BORDER
            ),
            border_width=2 if selected else 1,
        )

        # Avoid callback loops during programmatic changes.
        if notify and self._on_change is not None:
            self._on_change(
                self.option_id,
                selected,
            )

    @property
    def is_selected(self) -> bool:
        """Return whether this option is currently selected."""
        return self._selected.get()
