
"""Tests for the PlantCare AI explanation service."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from plantcare.ai.explanation_service import (
    generate_diagnostic_explanations,
)
from plantcare.ai.ollama_client import OllamaClient, OllamaClientError
from plantcare.diagnosis.problem_catalog import load_problem_catalog
from plantcare.tree.node import DiagnosisNode


CATALOG_PATH = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "plant_problems.json"
)


@pytest.fixture
def catalogue():
    """Load the actual PlantCare problem catalogue."""
    return load_problem_catalog(CATALOG_PATH)


@pytest.fixture
def diagnosis():
    """Build a diagnosis containing two plant problems."""
    return DiagnosisNode(
        node_id="test_diagnosis",
        problem_codes=("PC-022", "PC-024"),
    )


def valid_response(code, catalogue):
    """Create a structurally valid model response."""
    return f"{code} - {catalogue[code]['name']}"


def test_generates_one_explanation_per_problem(
    catalogue,
    diagnosis,
):
    """Keep multiple diagnoses in separate model requests."""
    client = Mock(spec=OllamaClient)

    client.generate_explanation.side_effect = [
        valid_response("PC-022", catalogue),
        valid_response("PC-024", catalogue),
    ]

    result = generate_diagnostic_explanations(
        diagnosis,
        catalogue,
        client,
    )

    assert result["PC-022"] is not None
    assert result["PC-024"] is not None
    assert client.generate_explanation.call_count == 2

    first_prompt = client.generate_explanation.call_args_list[0].args[0]
    second_prompt = client.generate_explanation.call_args_list[1].args[0]

    assert "PC-022" in first_prompt
    assert "PC-024" not in first_prompt

    assert "PC-024" in second_prompt
    assert "PC-022" not in second_prompt


def test_rejects_incorrect_problem_name(catalogue):
    """Reject a response that changes the problem name."""
    client = Mock(spec=OllamaClient)
    client.generate_explanation.return_value = (
        "PC-022 - Unknown plant disease"
    )

    diagnosis = DiagnosisNode(
        node_id="test",
        problem_codes=("PC-022",),
    )

    result = generate_diagnostic_explanations(
        diagnosis,
        catalogue,
        client,
    )

    assert result["PC-022"] is None


def test_rejects_unexpected_problem_code(catalogue):
    """Reject a response mentioning another diagnosis code."""
    client = Mock(spec=OllamaClient)

    client.generate_explanation.return_value = (
        f"PC-022 - {catalogue['PC-022']['name']}. "
        "Additional problem: PC-024."
    )

    diagnosis = DiagnosisNode(
        node_id="test",
        problem_codes=("PC-022",),
    )

    result = generate_diagnostic_explanations(
        diagnosis,
        catalogue,
        client,
    )

    assert result["PC-022"] is None


def test_continues_after_ollama_connection_error(
    catalogue,
    diagnosis,
):
    """Keep processing other problems when one request fails."""
    client = Mock(spec=OllamaClient)

    client.generate_explanation.side_effect = [
        OllamaClientError("Connection unavailable"),
        valid_response("PC-024", catalogue),
    ]

    result = generate_diagnostic_explanations(
        diagnosis,
        catalogue,
        client,
    )

    assert result["PC-022"] is None
    assert result["PC-024"] is not None
    assert client.generate_explanation.call_count == 2


def test_rejects_problem_missing_from_catalogue(catalogue):
    """Prevent explanations for unknown problem codes."""
    client = Mock(spec=OllamaClient)

    diagnosis = DiagnosisNode(
        node_id="test",
        problem_codes=("PC-999",),
    )

    with pytest.raises(
        ValueError,
        match="Problem not found in catalogue",
    ):
        generate_diagnostic_explanations(
            diagnosis,
            catalogue,
            client,
        )

    client.generate_explanation.assert_not_called()
