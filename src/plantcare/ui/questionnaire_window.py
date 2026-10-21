"""CustomTkinter diagnostic questionnaire for PlantCare Tree."""

import logging
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from tkinter import messagebox

import customtkinter as ctk

from plantcare.ai.explanation_service import generate_diagnostic_explanations
from plantcare.ai.ollama_client import OllamaClient
from plantcare.diagnosis.hierarchical_classifier import (
    HierarchicalClassifier,
    HierarchicalResult,
)
from plantcare.diagnosis.problem_catalog import load_problem_catalog
from plantcare.diagnosis.questionnaire_loader import load_questionnaire
from plantcare.diagnosis.questionnaire_session import QuestionnaireSession
from plantcare.ui.plantcare_theme import PlantCareTheme as Theme
from plantcare.ui.symptom_option_card import SymptomOptionCard


PROJECT_ROOT = Path(__file__).resolve().parents[3]
QUESTIONNAIRE_PATH = (
    PROJECT_ROOT / "data" / "questionnaire_50_draft.json"
)


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

        # The hierarchical tree is the only active diagnostic classifier.
        self._hierarchical_classifier = (
            HierarchicalClassifier.from_data_directory(PROJECT_ROOT / "data")
        )
        self._problem_catalog = load_problem_catalog(
            PROJECT_ROOT / "data" / "plant_problems.json"
        )
        self._symptom_labels = {
            option["id"]: option["label"]
            for question in self._questionnaire["questions"]
            for option in question["options"]
        }

        # Store AI results without accessing Tkinter from worker threads.
        self._ai_results: Queue[
            tuple[int, dict[str, str | None]]
        ] = Queue()

        # Identify the currently active diagnostic request.
        self._ai_request_id = 0

        # Keep references to the labels displaying AI explanations.
        self._ai_result_labels: dict[str, ctk.CTkLabel] = {}


        self._option_cards: dict[str, SymptomOptionCard] = {}
        self._sidebar_steps: list[
            tuple[ctk.CTkFrame, ctk.CTkLabel, ctk.CTkLabel]
        ] = []
        self._build_sidebar()
        self._build_main_content()
        self._render_current_question()

        # Start polling for completed AI requests.
        self.after(150, self._poll_ai_results)

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
        # Invalidate pending AI responses when the screen changes.
        self._ai_request_id += 1
        self._ai_result_labels.clear()

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


        # Allow users to explicitly report no listed symptoms.
        if multiple_selection:
            ctk.CTkButton(
                card,
                text="Ninguno de estos síntomas",
                command=self._submit_no_symptoms,
                fg_color="transparent",
                hover_color=Theme.SIDEBAR,
                text_color=Theme.PRIMARY,
                border_width=1,
                border_color=Theme.BORDER,
                corner_radius=Theme.BUTTON_RADIUS,
                height=42,
                font=(Theme.FONT_FAMILY, 13, "bold"),
            ).pack(
                fill="x",
                padx=30,
                pady=(0, 15),
            )


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


    def _submit_no_symptoms(self) -> None:
        """Record no observed symptoms and advance the questionnaire."""
        try:
            self._session.submit_no_symptoms()
        except (ValueError, TypeError) as error:
            messagebox.showwarning(
                "Revisa tu respuesta",
                str(error),
            )
            return

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
                "Tus observaciones fueron analizadas mediante "
                "nuestro árbol binario de decisión. "
                "A continuación encontrarás el resultado "
                "orientativo del diagnóstico y un resumen "
                "de las respuestas registradas."
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

        # Classify the recorded observations using the new binary tree.
        assessment = self._hierarchical_classifier.classify_context(
            self._session.context
        )

        if assessment.status == "diagnosed":
            codes = ", ".join(
                assessment.diagnosis.problem_codes
            )
            result_text = (
                f"Posibles problemas identificados: {codes}"
            )
        elif assessment.status == "insufficient_evidence":
            result_text = (
                "Evidencia insuficiente: no se identificaron "
                "sintomas suficientes para un diagnostico."
            )
        else:
            result_text = (
                "Diagnostico pendiente: faltan respuestas "
                "para completar la evaluacion."
            )

        ctk.CTkLabel(
            card,
            text=result_text,
            font=(Theme.FONT_FAMILY, 15, "bold"),
            text_color=Theme.PRIMARY,
            wraplength=620,
            justify="left",
        ).pack(
            anchor="w",
            padx=30,
            pady=(0, 20),
        )


        # Display catalogue details for diagnosed plant problems.
        if assessment.status == "diagnosed" and assessment.diagnosis:
            # Clarify the meaning of multiple symptom-based results.
            if len(assessment.diagnosis.problem_codes) > 1:
                ctk.CTkLabel(
                    card,
                    text=(
                        "Se encontraron varios problemas posibles "
                        "asociados a los síntomas seleccionados. "
                        "Esto no confirma que todas las enfermedades "
                        "estén presentes simultáneamente."
                    ),
                    font=(Theme.FONT_FAMILY, 12),
                    text_color=Theme.TEXT_SECONDARY,
                    wraplength=620,
                    justify="left",
                ).pack(
                    anchor="w",
                    padx=30,
                    pady=(0, 15),
                )
            for problem_code in assessment.diagnosis.problem_codes:
                problem = self._problem_catalog.get(problem_code)

                if problem is None:
                    raise ValueError(
                        f"Problem not found in catalogue: {problem_code}"
                    )

                # Create a visual card for each possible problem.
                problem_card = ctk.CTkFrame(
                    card,
                    fg_color=Theme.BACKGROUND,
                    corner_radius=12,
                    border_width=1,
                    border_color=Theme.BORDER,
                )
                problem_card.pack(
                    fill="x",
                    padx=30,
                    pady=(0, 15),
                )

                # Problem name and identification code.
                ctk.CTkLabel(
                    problem_card,
                    text=f"{problem_code} | {problem['name']}",
                    font=(Theme.FONT_FAMILY, 17, "bold"),
                    text_color=Theme.PRIMARY,
                    wraplength=580,
                    justify="left",
                ).pack(
                    anchor="w",
                    padx=20,
                    pady=(20, 12),
                )

                # Reference symptoms.
                ctk.CTkLabel(
                    problem_card,
                    text="SÍNTOMAS DE REFERENCIA",
                    font=(Theme.FONT_FAMILY, 11, "bold"),
                    text_color=Theme.TEXT_PRIMARY,
                ).pack(
                    anchor="w",
                    padx=20,
                )

                ctk.CTkLabel(
                    problem_card,
                    text=problem["indicative_symptoms"],
                    font=(Theme.FONT_FAMILY, 13),
                    text_color=Theme.TEXT_SECONDARY,
                    wraplength=580,
                    justify="left",
                ).pack(
                    anchor="w",
                    padx=20,
                    pady=(5, 15),
                )

                # Organic and nonchemical management.
                ctk.CTkLabel(
                    problem_card,
                    text="MANEJO ORGÁNICO O NO QUÍMICO",
                    font=(Theme.FONT_FAMILY, 11, "bold"),
                    text_color=Theme.TEXT_PRIMARY,
                ).pack(
                    anchor="w",
                    padx=20,
                )

                # Always display the catalogue management BEFORE AI output.
                ctk.CTkLabel(
                    problem_card,
                    text=problem["organic_or_nonchemical_management"],
                    font=(Theme.FONT_FAMILY, 13),
                    text_color=Theme.TEXT_SECONDARY,
                    wraplength=580,
                    justify="left",
                ).pack(
                    anchor="w",
                    padx=20,
                    pady=(5, 20),
                )

                # AI output is optional and must never overwrite catalogue data.
                ctk.CTkLabel(
                    problem_card,
                    text="EXPLICACION ADICIONAL DE PLANTCARE AI",
                    font=(Theme.FONT_FAMILY, 11, "bold"),
                    text_color=Theme.PRIMARY,
                ).pack(
                    anchor="w",
                    padx=20,
                    pady=(0, 8),
                )
                ai_label = ctk.CTkLabel(
                    problem_card,
                    text="Generando comentario con PlantCare AI...",
                    font=(Theme.FONT_FAMILY, 13),
                    text_color=Theme.TEXT_SECONDARY,
                    wraplength=550,
                    justify="left",
                    anchor="w",
                )
                ai_label.pack(
                    fill="x",
                    padx=20,
                    pady=(0, 20),
                )
                self._ai_result_labels[problem_code] = ai_label

            # Clarify the limits of the diagnostic result.
            ctk.CTkLabel(
                card,
                text=(
                    "Diagnóstico orientativo basado en los síntomas "
                    "seleccionados. La identificación puede requerir "
                    "revisión adicional según la especie y el entorno."
                ),
                font=(Theme.FONT_FAMILY, 12),
                text_color=Theme.TEXT_SECONDARY,
                wraplength=620,
                justify="left",
            ).pack(
                anchor="w",
                padx=30,
                pady=(5, 20),
            )

            # Cap automatic local model requests while preserving all fichas.
            if len(assessment.diagnosis.problem_codes) <= 3:
                Thread(
                    target=self._run_ai_explanations,
                    args=(self._ai_request_id, assessment),
                    daemon=True,
                ).start()
            else:
                for label in self._ai_result_labels.values():
                    label.configure(
                        text=(
                            "Comentario automático omitido por haber más de tres "
                            "problemas candidatos. Consulta cada ficha del catálogo."
                        )
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

            # Display explicit negative answers clearly.
            answer_text = (
                ", ".join(selected_labels)
                if selected_labels
                else "Ninguno de estos síntomas"
            )

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
                text=answer_text,
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

    def _run_ai_explanations(
        self,
        request_id: int,
        assessment: HierarchicalResult,
    ) -> None:
        """Generate grounded explanations without touching Tkinter widgets."""
        diagnosis = assessment.diagnosis
        if diagnosis is None:
            return

        try:
            explanations = generate_diagnostic_explanations(
                diagnosis=diagnosis,
                catalogue=self._problem_catalog,
                client=OllamaClient(),
                traces=assessment.traces,
                symptom_labels=self._symptom_labels,
            )
        except Exception:
            logging.exception("PlantCare AI could not generate explanations.")
            explanations = {code: None for code in diagnosis.problem_codes}

        self._ai_results.put((request_id, explanations))

    def _poll_ai_results(self) -> None:
        """Display completed AI explanations on the Tkinter thread."""

        while True:
            try:
                request_id, explanations = (
                    self._ai_results.get_nowait()
                )
            except Empty:
                break

            # Ignore results from previous questionnaire sessions.
            if (
                request_id != self._ai_request_id
                or self._session.current_question is not None
            ):
                continue

            for code, explanation in explanations.items():
                label = self._ai_result_labels.get(code)

                if label is None or not label.winfo_exists():
                    continue

                if explanation is None:
                    label.configure(
                        text=(
                            "La explicación adicional de PlantCare AI "
                            "no está disponible. Puedes consultar "
                            "los cuidados indicados en la ficha."
                        )
                    )
                else:
                    label.configure(
                        text=explanation.replace("**", "")
                    )

        # Poll again without blocking the Tkinter event loop.
        self.after(150, self._poll_ai_results)



    def _restart_questionnaire(self) -> None:
        """Start a new questionnaire session."""
        self._session = QuestionnaireSession(
            self._questionnaire
        )
        self._render_current_question()

if __name__ == "__main__":
    app = PlantCareQuestionnaireWindow()
    app.mainloop()
