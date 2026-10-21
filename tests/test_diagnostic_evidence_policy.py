
"""Unit tests for diagnostic evidence validation."""

from plantcare.diagnosis.diagnostic_evidence_policy import (
    has_observed_symptoms,
)


SYMPTOM_KEYS = frozenset(
    f"sign_{index:03d}"
    for index in range(1, 51)
)


def test_no_symptoms_means_no_evidence() -> None:
    """Reject diagnosis when no plant symptoms are present."""
    conditions = {
        symptom_key: False
        for symptom_key in SYMPTOM_KEYS
    }

    assert has_observed_symptoms(
        conditions,
        SYMPTOM_KEYS,
    ) is False


def test_one_symptom_provides_evidence() -> None:
    """Detect evidence when one plant symptom is present."""
    conditions = {
        symptom_key: False
        for symptom_key in SYMPTOM_KEYS
    }

    conditions["sign_022"] = True

    assert has_observed_symptoms(
        conditions,
        SYMPTOM_KEYS,
    ) is True


def test_multiple_symptoms_provide_evidence() -> None:
    """Detect evidence when several symptoms are present."""
    conditions = {
        symptom_key: False
        for symptom_key in SYMPTOM_KEYS
    }

    conditions["sign_022"] = True
    conditions["sign_024"] = True

    assert has_observed_symptoms(
        conditions,
        SYMPTOM_KEYS,
    ) is True


def test_unrelated_condition_is_not_evidence() -> None:
    """Ignore positive conditions outside the symptom catalog."""
    conditions = {
        symptom_key: False
        for symptom_key in SYMPTOM_KEYS
    }

    conditions["normal_soil"] = True

    assert has_observed_symptoms(
        conditions,
        SYMPTOM_KEYS,
    ) is False


def test_missing_symptom_answers_are_not_positive() -> None:
    """Do not interpret missing symptom answers as evidence."""
    conditions = {}

    assert has_observed_symptoms(
        conditions,
        SYMPTOM_KEYS,
    ) is False
