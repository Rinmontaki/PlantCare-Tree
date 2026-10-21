
"""Validate observable evidence before plant diagnosis."""

from collections.abc import Collection, Mapping


def has_observed_symptoms(
    conditions: Mapping[str, bool],
    symptom_keys: Collection[str],
) -> bool:
    """Check whether at least one diagnostic symptom is present."""
    return any(
        conditions.get(symptom_key) is True
        for symptom_key in symptom_keys
    )
