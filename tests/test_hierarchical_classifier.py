"""Auditable coverage and branch-depth tests for all 50 candidate codes."""

from itertools import combinations
from pathlib import Path

import pytest

from plantcare.diagnosis.hierarchical_classifier import HierarchicalClassifier


DATA = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture(scope="module")
def classifier():
    """Reuse one validated hierarchical decision tree."""
    return HierarchicalClassifier.from_data_directory(DATA)


def test_all_50_individual_symptoms(classifier):
    """Every individual observation must reach its designated leaf."""
    for number in range(1, 51):
        sign = f"sign_{number:03d}"
        code = f"PC-{number:03d}"
        result = classifier.classify({sign})
        assert result.diagnosis.problem_codes == (code,)
        assert result.traces[0].problem_code == code
        assert 1 <= len(result.traces[0].steps) <= 10


def test_all_1225_symptom_pairs_preserved(classifier):
    """No selected symptom should be lost to early leaf termination."""
    for first, second in combinations(range(1, 51), 2):
        result = classifier.classify(
            {f"sign_{first:03d}", f"sign_{second:03d}"}
        )
        assert set(result.diagnosis.problem_codes) == {
            f"PC-{first:03d}",
            f"PC-{second:03d}",
        }
        assert len(result.traces) == 2


def test_no_symptoms_means_no_diagnosis(classifier):
    """A completely negative questionnaire is not a plant disease."""
    result = classifier.classify(set())
    assert result.status == "insufficient_evidence"
    assert result.diagnosis is None


def test_unknown_symptoms_rejected(classifier):
    """Only real questionnaire IDs may drive the tree."""
    with pytest.raises(ValueError, match="Unknown questionnaire symptoms"):
        classifier.classify({"sign_999"})


def test_multiple_distant_symptoms_produce_traces(classifier):
    """An early positive branch must not conceal a later observation."""
    result = classifier.classify({"sign_001", "sign_050"})
    assert set(result.diagnosis.problem_codes) == {"PC-001", "PC-050"}
    assert all(trace.steps for trace in result.traces)
    assert result.warnings


def test_three_distant_symptoms_produce_three_results(classifier):
    """Multiple classifications must be reproducible from input routes."""
    result = classifier.classify({"sign_003", "sign_022", "sign_024"})
    assert set(result.diagnosis.problem_codes) == {
        "PC-003", "PC-022", "PC-024"
    }
