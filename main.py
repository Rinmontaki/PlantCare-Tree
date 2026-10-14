"""Application entry point for PlantCare Tree."""

from plantcare.ui.main_window import PlantCareApp


def main() -> None:
    """Create and run the PlantCare desktop application."""
    # Create the main application instance.
    app = PlantCareApp()

    # Start the Tkinter event loop.
    app.mainloop()


if __name__ == "__main__":
    main()