"""CustomTkinter diagnostic questionnaire for PlantCare Tree."""

from pathlib import Path
from tkinter import messagebox

import customtkinter as ctk
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.diagnosis.questionnaire_session import QuestionnaireSession
from plantcare.ui.plantcare_theme import PlantCareTheme as Theme
from plantcare.ui.symptom_option_card import SymptomOptionCard


PROJECT_ROOT = Path(__file__).resolve().parents[3]
QUESTIONNAIRE_PATH = PROJECT_ROOT / "data" / "questionnaire.json"


SYMPTOM_IMAGES_PATH = (
    PROJECT_ROOT / "assets" / "images" / "symptoms"
)



class PlantCareQuestionnaireWindow(ctk.CTk):
    """Manage the botanical questionnaire interface."""

    def __init__(self) -> None:
        """Initialize the desktop questionnaire."""
        Theme.configure()
        super().__init__()
        self.title("PlantCare Tree | Diagnóstico botánico")
        self.geometry(
            f"{Theme.WINDOW_WIDTH}x{Theme.WINDOW_HEIGHT}"
        )
        self.minsize(
            Theme.MIN_WINDOW_WIDTH,
            Theme.MIN_WINDOW_HEIGHT,
        )
        self.configure(fg_color=Theme.BACKGROUND)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        # Load the questionnaire and create its session controller.
        self._questionnaire = load_questionnaire(
            QUESTIONNAIRE_PATH
        )
        self._session = QuestionnaireSession(
            self._questionnaire
        )
        self._option_cards: dict[str, SymptomOptionCard] = {}
        self._sidebar_steps: list[
            tuple[ctk.CTkFrame, ctk.CTkLabel, ctk.CTkLabel]
        ] = []
        self._build_sidebar()
        self._build_main_content()
        self._render_current_question()

    def _build_sidebar(self) -> None:
        """Create the botanical sidebar."""
        sidebar = ctk.CTkFrame(
            self,
            width=Theme.SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=Theme.SIDEBAR,
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        brand = ctk.CTkFrame(
            sidebar,
            fg_color="transparent",
        )
        brand.pack(
            fill="x",
            padx=25,
            pady=(35, 12),
        )
        ctk.CTkLabel(
            brand,
            text="✿ PlantCare",
            font=(Theme.FONT_FAMILY, 25, "bold"),
            text_color=Theme.PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="TREE  •  CUIDADO BOTÁNICO",
            font=(Theme.FONT_FAMILY, 10, "bold"),
            text_color=Theme.TEXT_SECONDARY,
        ).pack(
            anchor="w",
            pady=(2, 0),
        )
        ctk.CTkFrame(
            sidebar,
            height=2,
            fg_color=Theme.BORDER,
        ).pack(
            fill="x",
            padx=25,
            pady=(22, 28),
        )
        ctk.CTkLabel(
            sidebar,
            text="TU DIAGNÓSTICO",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.TEXT_SECONDARY,
        ).pack(
            anchor="w",
            padx=25,
            pady=(0, 15),
        )
        steps = (
            ("01", "Síntomas generales"),
            ("02", "Observaciones"),
            ("03", "Entorno de la planta"),
            ("04", "Resultados"),
        )
        for number, label in steps:
            self._add_sidebar_step(
                sidebar,
                number,
                label,
            )
        ctk.CTkLabel(
            sidebar,
            text="Cultiva plantas sanas,\nuna respuesta a la vez.",
            font=(Theme.FONT_FAMILY, 13),
            text_color=Theme.TEXT_SECONDARY,
            justify="left",
        ).pack(
            side="bottom",
            anchor="w",
            padx=25,
            pady=(0, 40),
        )

    def _add_sidebar_step(
        self,
        parent: ctk.CTkFrame,
        number: str,
        label: str,
    ) -> None:
        """Create a sidebar navigation indicator."""
        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent",
            corner_radius=12,
            height=52,
        )
        frame.pack(
            fill="x",
            padx=14,
            pady=5,
        )
        frame.pack_propagate(False)
        number_label = ctk.CTkLabel(
            frame,
            text=number,
            width=35,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color=Theme.TEXT_PRIMARY,
        )
        number_label.pack(
            side="left",
            padx=(12, 4),
        )
        text_label = ctk.CTkLabel(
            frame,
            text=label,
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color=Theme.TEXT_PRIMARY,
        )
        text_label.pack(side="left")
        self._sidebar_steps.append(
            (frame, number_label, text_label)
        )

    def _activate_sidebar_step(self, active_index: int) -> None:
        """Highlight the current questionnaire section."""
        for index, (frame, number_label, text_label) in enumerate(
            self._sidebar_steps
        ):
            active = index == active_index
            frame.configure(
                fg_color=(
                    Theme.PRIMARY
                    if active
                    else "transparent"
                )
            )
            text_color = (
                Theme.TEXT_LIGHT
                if active
                else Theme.TEXT_PRIMARY
            )
            number_label.configure(text_color=text_color)
            text_label.configure(text_color=text_color)

    def _build_main_content(self) -> None:
        """Create the main questionnaire area."""
        content = ctk.CTkScrollableFrame(
            self,
            fg_color=Theme.BACKGROUND,
            corner_radius=0,
        )
        content.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=32,
            pady=25,
        )
        self._content = content
        ctk.CTkLabel(
            content,
            text="DIAGNÓSTICO DE PLANTAS",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.PROGRESS_FILL,
        ).pack(
            anchor="w",
            pady=(5, 8),
        )
        ctk.CTkLabel(
            content,
            text="Conozcamos mejor tu planta",
            font=(Theme.FONT_FAMILY, 27, "bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).pack(anchor="w")
        ctk.CTkLabel(
            content,
            text=(
                "Cuéntanos qué observas. Cada respuesta "
                "nos ayudará a identificar posibles problemas."
            ),
            font=(Theme.FONT_FAMILY, 13),
            text_color=Theme.TEXT_SECONDARY,
            wraplength=650,
            justify="left",
        ).pack(
            anchor="w",
            pady=(8, 28),
        )
        progress_header = ctk.CTkFrame(
            content,
            fg_color="transparent",
        )
        progress_header.pack(
            fill="x",
            pady=(0, 9),
        )
        ctk.CTkLabel(
            progress_header,
            text="Progreso del cuestionario",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color=Theme.TEXT_PRIMARY,
        ).pack(side="left")
        self._progress_label = ctk.CTkLabel(
            progress_header,
            text="0%",
            font=(Theme.FONT_FAMILY, 12, "bold"),
            text_color=Theme.PRIMARY,
        )
        self._progress_label.pack(side="right")
        self._progress_bar = ctk.CTkProgressBar(
            content,
            height=9,
            corner_radius=8,
            progress_color=Theme.PROGRESS_FILL,
            fg_color=Theme.PROGRESS_BACKGROUND,
        )
        self._progress_bar.pack(
            fill="x",
            pady=(0, 28),
        )
        self._progress_bar.set(0)
        # Reusable container for questions and completion screens.
        self._question_host = ctk.CTkFrame(
            content,
            fg_color="transparent",
        )
        self._question_host.pack(
            fill="x",
            pady=(0, 24),
        )

    def _update_progress(self) -> None:
        """Calculate progress using currently applicable questions."""
        answers = self._session.context.get_answers()
        selected_options = {
            option_id
            for selections in answers.values()
            for option_id in selections
        }
        applicable_count = 0
        for question in self._questionnaire["questions"]:
            condition = question.get("show_if")
            if condition is None or (
                condition["selected_option"] in selected_options
            ):
                applicable_count += 1
        progress = len(answers) / max(applicable_count, 1)
        progress = min(progress, 1.0)
        self._progress_bar.set(progress)
        self._progress_label.configure(
            text=f"{round(progress * 100)}%"
        )

    def _render_current_question(self) -> None:
        """Display the current question or completion summary."""
        for widget in self._question_host.winfo_children():
            widget.destroy()
        self._option_cards.clear()
        self._update_progress()
        question = self._session.current_question
        if question is None:
            self._activate_sidebar_step(3)
            self._show_completion_preview()
            return
        question_id = question["id"]
        section_by_question = {
            "leaf_symptoms": 0,
            "insect_appearance": 1,
            "leaf_damage": 1,
            "soil_condition": 2,
        }
        self._activate_sidebar_step(
            section_by_question.get(question_id, 1)
        )
        card = ctk.CTkFrame(
            self._question_host,
            fg_color=Theme.CARD,
            corner_radius=Theme.CARD_RADIUS,
            border_width=1,
            border_color=Theme.BORDER,
        )
        card.pack(fill="x")
        # Use the visible question order, not the number of saved answers.
        selected_options = {
            option_id
            for selections in self._session.context.get_answers().values()
            for option_id in selections
        }
        applicable_questions = [
            candidate
            for candidate in self._questionnaire["questions"]
            if candidate.get("show_if") is None
            or candidate["show_if"]["selected_option"] in selected_options
        ]
        question_number = next(
            index
            for index, candidate in enumerate(applicable_questions, start=1)
            if candidate["id"] == question_id
        )
        ctk.CTkLabel(
            card,
            text=f"PREGUNTA {question_number:02d}  /  OBSERVACIÓN",
            font=(Theme.FONT_FAMILY, 11, "bold"),
            text_color=Theme.PROGRESS_FILL,
        ).pack(
            anchor="w",
            padx=30,
            pady=(30, 15),
        )
        ctk.CTkLabel(
            card,
            text=question["text"],
            font=(Theme.FONT_FAMILY, 22, "bold"),
            text_color=Theme.TEXT_PRIMARY,
            wraplength=600,
            justify="left",
        ).pack(
            anchor="w",
            padx=30,
        )
        multiple_selection = question["selection_mode"] == "multiple"
        instructions = (
            "Selecciona todas las opciones que describan "
            "el estado de tu planta."
            if multiple_selection
            else "Selecciona la opción que mejor describa "
            "lo que observas."
        )
        ctk.CTkLabel(
            card,
            text=instructions,
            font=(Theme.FONT_FAMILY, 13),
            text_color=Theme.TEXT_SECONDARY,
            wraplength=600,
            justify="left",
        ).pack(
            anchor="w",
            padx=30,
            pady=(10, 20),
        )
        option_icons = {
            "yellowing": "🍂",
            "leaf_holes": "🌿",
            "visible_insects": "🐛",
            "wilting": "🥀",
            "dark_spots": "🍃",
            "clustered_insects": "🐜",
            "cotton_like_insects": "🌼",
            "flying_insects": "🪰",
            "chewing_insects": "🐛",
            "wet_soil": "💧",
            "dry_soil": "☀️",
            "normal_soil": "🌱",
        }
        options_container = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )
        options_container.pack(
            fill="x",
            padx=30,
            pady=(0, 20),
        )
        
       
        for option in question["options"]:
            option_id = option["id"]

            # Find the botanical illustration for this option.
            image_path = (
                SYMPTOM_IMAGES_PATH / f"{option_id}.png"
            )

            # Use the original emoji if no illustration exists.
            if not image_path.is_file():
                image_path = None

            # Create the selectable symptom card.
            option_card = SymptomOptionCard(
                parent=options_container,
                option_id=option_id,
                label=option["label"],
                icon=option_icons.get(option_id, "🌱"),
                on_change=self._handle_option_change,
                image_path=image_path,
            )

            # Display the card inside the questionnaire.
            option_card.pack(
                fill="x",
                pady=5,
            )

            # Register the card for selection management.
            self._option_cards[option_id] = option_card



        # Restore previous selections without triggering change callbacks.
        saved_selections = self._session.context.get_answers().get(
            question_id, ()
        )
        for selected_id in saved_selections:
            saved_card = self._option_cards.get(selected_id)
            if saved_card is not None:
                saved_card.set_selected(True)

        button_area = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )
        button_area.pack(
            fill="x",
            padx=30,
            pady=(0, 30),
        )
        ctk.CTkButton(
            button_area,
            text="←  Anterior",
            command=self._go_to_previous_question,
            state="normal" if self._session.can_go_back else "disabled",
            fg_color=Theme.SIDEBAR,
            hover_color=Theme.BORDER,
            text_color=Theme.PRIMARY,
            corner_radius=Theme.BUTTON_RADIUS,
            height=45,
            font=(Theme.FONT_FAMILY, 13, "bold"),
        ).pack(side="left")

        ctk.CTkButton(
            button_area,
            text="Guardar y continuar  →",
            command=self._continue_questionnaire,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            text_color=Theme.TEXT_LIGHT,
            corner_radius=Theme.BUTTON_RADIUS,
            height=45,
            font=(Theme.FONT_FAMILY, 13, "bold"),
        ).pack(side="right")

    def _handle_option_change(
        self,
        option_id: str,
        selected: bool,
    ) -> None:
        """Apply single-choice and exclusive-option selection rules."""
        question = self._session.current_question
        if question is None or not selected:
            return
        # Single-choice questions allow only one selected option.
        if question["selection_mode"] == "single":
            for other_id, other_card in self._option_cards.items():
                if other_id != option_id:
                    other_card.set_selected(False)
            return
        # Define mutually exclusive options for multiple-choice questions.
        exclusive_options = {
            "insect_appearance": {"unknown_insects"},
        }
        exclusive_ids = exclusive_options.get(
            question["id"],
            set(),
        )
        # Selecting an exclusive option clears all other selections.
        if option_id in exclusive_ids:
            for other_id, other_card in self._option_cards.items():
                if other_id != option_id:
                    other_card.set_selected(False)
            return
        # Selecting a specific symptom clears any exclusive option.
        for exclusive_id in exclusive_ids:
            exclusive_card = self._option_cards.get(exclusive_id)
            if exclusive_card is not None:
                exclusive_card.set_selected(False)

    def _go_to_previous_question(self) -> None:
        """Return to the previous question without discarding answers."""
        if self._session.go_back():
            self._render_current_question()

    def _continue_questionnaire(self) -> None:
        """Save selected options and advance the session."""
        selected_options = tuple(
            option_id
            for option_id, card in self._option_cards.items()
            if card.is_selected
        )
        try:
            self._session.submit_answer(selected_options)
        except (ValueError, TypeError) as error:
            messagebox.showwarning(
                "Revisa tu respuesta",
                str(error),
            )
            return
        self._render_current_question()

    def _show_completion_preview(self) -> None:
        """Display a temporary summary of recorded observations."""
        card = ctk.CTkFrame(
            self._question_host,
            fg_color=Theme.CARD,
            corner_radius=Theme.CARD_RADIUS,
            border_width=1,
            border_color=Theme.BORDER,
        )
        card.pack(fill="x")
        ctk.CTkLabel(
            card,
            text="🌿 Cuestionario completado",
            font=(Theme.FONT_FAMILY, 24, "bold"),
            text_color=Theme.PRIMARY,
        ).pack(
            anchor="w",
            padx=30,
            pady=(30, 12),
        )
        ctk.CTkLabel(
            card,
            text=(
                "Tus observaciones quedaron registradas. "
                "Este es un resumen provisional mientras "
                "integramos los resultados del árbol binario."
            ),
            font=(Theme.FONT_FAMILY, 13),
            text_color=Theme.TEXT_SECONDARY,
            wraplength=620,
            justify="left",
        ).pack(
            anchor="w",
            padx=30,
            pady=(0, 20),
        )
        answers = self._session.context.get_answers()
        for question in self._questionnaire["questions"]:
            selected_ids = answers.get(question["id"])
            if selected_ids is None:
                continue
            option_labels = {
                option["id"]: option["label"]
                for option in question["options"]
            }
            selected_labels = [
                option_labels[option_id]
                for option_id in selected_ids
            ]
            ctk.CTkLabel(
                card,
                text=question["text"],
                font=(Theme.FONT_FAMILY, 13, "bold"),
                text_color=Theme.TEXT_PRIMARY,
                wraplength=620,
                justify="left",
            ).pack(
                anchor="w",
                padx=30,
                pady=(12, 3),
            )
            ctk.CTkLabel(
                card,
                text=", ".join(selected_labels),
                font=(Theme.FONT_FAMILY, 12),
                text_color=Theme.TEXT_SECONDARY,
                wraplength=620,
                justify="left",
            ).pack(
                anchor="w",
                padx=30,
            )
        completion_actions = ctk.CTkFrame(
            card,
            fg_color="transparent",
        )
        completion_actions.pack(
            fill="x",
            padx=30,
            pady=30,
        )

        ctk.CTkButton(
            completion_actions,
            text="←  Revisar respuestas",
            command=self._go_to_previous_question,
            fg_color=Theme.SIDEBAR,
            hover_color=Theme.BORDER,
            text_color=Theme.PRIMARY,
            corner_radius=Theme.BUTTON_RADIUS,
            height=45,
        ).pack(side="left")

        ctk.CTkButton(
            completion_actions,
            text="Iniciar nuevo cuestionario",
            command=self._restart_questionnaire,
            fg_color=Theme.PRIMARY,
            hover_color=Theme.PRIMARY_HOVER,
            corner_radius=Theme.BUTTON_RADIUS,
            height=45,
        ).pack(side="right")

    def _restart_questionnaire(self) -> None:
        """Start a new questionnaire session."""
        self._session = QuestionnaireSession(
            self._questionnaire
        )
        self._render_current_question()

if __name__ == "__main__":
    app = PlantCareQuestionnaireWindow()
    app.mainloop()
