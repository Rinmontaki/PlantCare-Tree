"""Deterministic tests for the supplementary TXT-reference demonstration."""

from pathlib import Path

import pytest

from plantcare.ai.txt_knowledge import (
    load_txt_knowledge,
    reference_response,
    safe_response,
)

PATH = Path(__file__).resolve().parents[1] / "data" / "plantcare_respuestas_referencia.txt"


def test_txt_contains_50_complete_fiches():
    records = load_txt_knowledge(PATH)
    assert len(records) == 50
    assert set(records) == {f"PC-{i:03d}" for i in range(1, 51)}
    assert all(all(row[field] for field in ("NOMBRE", "SINTOMAS", "MANEJO"))
               for row in records.values())


def test_offline_uses_exact_reference():
    records = load_txt_knowledge(PATH)
    result, copied = safe_response("PC-022", records, None)
    assert result == reference_response("PC-022", records)
    assert copied is False


def test_incorrect_llm_output_does_not_replace_reference():
    records = load_txt_knowledge(PATH)
    result, copied = safe_response("PC-050", records, "Use una dosis inventada.")
    assert result == reference_response("PC-050", records)
    assert "dosis inventada" not in result
    assert copied is False


def test_exact_copy_accepted_and_unknown_code_rejected():
    records = load_txt_knowledge(PATH)
    expected = reference_response("PC-024", records)
    result, copied = safe_response("PC-024", records, expected)
    assert result == expected
    assert copied is True
    with pytest.raises(ValueError, match="Unknown reference code"):
        reference_response("PC-999", records)
