"""Verify that PlantCare passes per-case evidence to the AI, without mixing codes."""

from pathlib import Path
from unittest.mock import Mock

from plantcare.ai.explanation_service import generate_diagnostic_explanations
from plantcare.ai.ollama_client import OllamaClient, OllamaClientError
from plantcare.diagnosis.hierarchical_classifier import HierarchicalClassifier
from plantcare.diagnosis.problem_catalog import load_problem_catalog

ROOT = Path(__file__).resolve().parents[1]


def _setup():
    classifier = HierarchicalClassifier.from_data_directory(ROOT / "data")
    result = classifier.classify({"sign_022", "sign_024"})
    catalogue = load_problem_catalog(ROOT / "data" / "plant_problems.json")
    return result, catalogue


def test_model_receives_symptom_and_binary_trace_for_each_code():
    """Every prompt should contain only the observation for its own code."""
    result, catalogue = _setup()
    client = Mock(spec=OllamaClient)
    client.generate_explanation.side_effect = [
        f"{code} - {catalogue[code]['name']}"
        for code in result.diagnosis.problem_codes
    ]
    labels = {
        "sign_022": "Manchas amarillas angulares y vello bajo la hoja",
        "sign_024": "Manchas redondas o irregulares con humedad",
    }
    response = generate_diagnostic_explanations(
        result.diagnosis,
        catalogue,
        client,
        traces=result.traces,
        symptom_labels=labels,
    )
    assert len(response) == 2
    assert client.generate_explanation.call_count == 2
    prompts = [call.args[0] for call in client.generate_explanation.call_args_list]
    assert "sign_022: Manchas amarillas angulares" in prompts[0]
    assert "sign_024: Manchas redondas" not in prompts[0]
    assert "sign_024: Manchas redondas" in prompts[1]
    assert "sign_022: Manchas amarillas" not in prompts[1]
    assert "=SI" in prompts[0]
    assert "=SI" in prompts[1]
    assert "RECORRIDO BINARIO" in prompts[0]


def test_ollama_failure_cannot_remove_catalogue_diagnosis():
    """A failed response must return None while preserving the tree result."""
    result, catalogue = _setup()
    codes = result.diagnosis.problem_codes
    client = Mock(spec=OllamaClient)
    client.generate_explanation.side_effect = OllamaClientError("unavailable")
    explanations = generate_diagnostic_explanations(
        result.diagnosis, catalogue, client, traces=result.traces
    )
    assert all(explanations[code] is None for code in codes)
    assert result.diagnosis.problem_codes == codes
    assert all(code in catalogue for code in codes)
