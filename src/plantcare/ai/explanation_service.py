
"""Generate individual AI explanations for plant diagnoses."""

import re
from collections.abc import Iterable, Mapping
from typing import Any

from plantcare.ai.ollama_client import (
    OllamaClient,
    OllamaClientError,
)
from plantcare.ai.prompt_builder import build_diagnostic_prompt
from plantcare.diagnosis.hierarchical_classifier import SymptomTrace
from plantcare.tree.node import DiagnosisNode


def generate_diagnostic_explanations(
    diagnosis: DiagnosisNode,
    catalogue: Mapping[str, Mapping[str, Any]],
    client: OllamaClient,
    *,
    traces: Iterable[SymptomTrace] = (),
    symptom_labels: Mapping[str, str] | None = None,
) -> dict[str, str | None]:
    """Generate and structurally validate one explanation per problem."""

    explanations: dict[str, str | None] = {}
    traces_by_code: dict[str, list[SymptomTrace]] = {}
    for trace in traces:
        traces_by_code.setdefault(trace.problem_code, []).append(trace)
    labels = symptom_labels or {}

    for code in diagnosis.problem_codes:
        problem = catalogue.get(code)

        if problem is None:
            raise ValueError(
                f"Problem not found in catalogue: {code}"
            )

        # Isolate each diagnosis to prevent mixing problem records.
        individual_diagnosis = DiagnosisNode(
            node_id=f"ai_{code}",
            problem_codes=(code,),
        )

        code_traces = traces_by_code.get(code, [])
        observations = [
            f"{trace.symptom_id}: {labels.get(trace.symptom_id, trace.symptom_id)}"
            for trace in code_traces
        ]
        decision_paths = [
            " -> ".join(
                f"{step.condition_key}={'SI' if step.answer else 'NO'}"
                for step in trace.steps
            )
            for trace in code_traces
        ]
        prompt = build_diagnostic_prompt(
            diagnosis=individual_diagnosis,
            catalogue=catalogue,
            case_observations=observations,
            decision_paths=decision_paths,
        )

        try:
            response = client.generate_explanation(prompt)
        except OllamaClientError:
            explanations[code] = None
            continue

        # Validate that the model uses only the expected problem code.
        mentioned_codes = set(
            re.findall(r"\bPC-\d{3}\b", response)
        )

        expected_name = problem["name"]

        valid_response = (
            mentioned_codes == {code}
            and expected_name.casefold() in response.casefold()
        )

        explanations[code] = (
            response if valid_response else None
        )

    return explanations
