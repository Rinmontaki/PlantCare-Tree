
"""Coordinate diagnostic completion and evidence validation."""

from collections.abc import Collection
from dataclasses import dataclass
from typing import Literal

from plantcare.diagnosis.diagnostic_completion_policy import (
    DiagnosticCompletionPolicy,
)
from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.diagnosis.diagnostic_engine import DiagnosticEngine
from plantcare.diagnosis.diagnostic_evidence_policy import (
    has_observed_symptoms,
)
from plantcare.tree.node import DiagnosisNode


DiagnosticStatus = Literal[
    "pending",
    "insufficient_evidence",
    "diagnosed",
]


@dataclass(frozen=True)
class DiagnosticAssessment:
    """Represent the outcome of a diagnostic assessment."""

    status: DiagnosticStatus
    diagnosis: DiagnosisNode | None = None
    pending_questions: tuple[str, ...] = ()
    pending_condition_key: str | None = None


def assess_diagnosis(
    context: DiagnosticContext,
    engine: DiagnosticEngine,
    completion_policy: DiagnosticCompletionPolicy,
    symptom_keys: Collection[str],
) -> DiagnosticAssessment:
    """Evaluate questionnaire completion before returning a diagnosis."""

    # Evaluate questionnaire requirements and binary traversal.
    completion = engine.evaluate_completion(
        context=context,
        completion_policy=completion_policy,
    )

    # Do not diagnose while applicable questions remain unanswered.
    if completion.pending_required_questions:
        return DiagnosticAssessment(
            status="pending",
            pending_questions=completion.pending_required_questions,
        )

    # Detect conditions required by the tree but not yet answered.
    traversal = completion.traversal_state

    if not traversal.is_complete:
        return DiagnosticAssessment(
            status="pending",
            pending_condition_key=traversal.pending_condition_key,
        )

    # Collect the symptoms that the user explicitly selected.
    selected_conditions = {
        option_id: True
        for selections in context.get_answers().values()
        for option_id in selections
    }

    # A completed questionnaire without symptoms is not a diagnosis.
    if not has_observed_symptoms(
        selected_conditions,
        symptom_keys,
    ):
        return DiagnosticAssessment(
            status="insufficient_evidence",
        )

    # A complete tree traversal contains a diagnostic leaf.
    return DiagnosticAssessment(
        status="diagnosed",
        diagnosis=traversal.diagnosis,
    )
