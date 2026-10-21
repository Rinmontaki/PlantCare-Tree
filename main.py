"""Launch the current PlantCare Tree CustomTkinter questionnaire."""

from plantcare.ui.questionnaire_window import PlantCareQuestionnaireWindow


def main() -> None:
    """Start the PlantCare desktop application."""
    app = PlantCareQuestionnaireWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
