
"""Visual theme configuration for PlantCare Tree."""

import customtkinter as ctk


class PlantCareTheme:
    """Centralize colors and dimensions for the desktop interface."""

    # Primary brand colors.
    PRIMARY = "#285B3B"
    PRIMARY_HOVER = "#1E4930"
    SECONDARY = "#77A580"

    # Background surfaces.
    BACKGROUND = "#F7F7F0"
    SIDEBAR = "#EAF2E7"
    CARD = "#FFFFFF"
    OPTION_SELECTED = "#EDF5E9"

    # Typography colors.
    TEXT_PRIMARY = "#23392C"
    TEXT_SECONDARY = "#718174"
    TEXT_LIGHT = "#FFFFFF"

    # Borders and progress indicators.
    BORDER = "#DCE7D9"
    PROGRESS_BACKGROUND = "#DDE9DA"
    PROGRESS_FILL = "#44845B"

    # Window dimensions.
    WINDOW_WIDTH = 1120
    WINDOW_HEIGHT = 740
    MIN_WINDOW_WIDTH = 950
    MIN_WINDOW_HEIGHT = 650

    # Layout dimensions.
    SIDEBAR_WIDTH = 260
    CARD_RADIUS = 18
    BUTTON_RADIUS = 12

    # Font settings.
    FONT_FAMILY = "Segoe UI"

    @classmethod
    def configure(cls) -> None:
        """Configure the application appearance."""
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
