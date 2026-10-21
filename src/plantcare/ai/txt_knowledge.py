"""Load exact plant-care reference responses from a local TXT catalogue."""

import re
from pathlib import Path

HEADER_RE = re.compile(r"^===== (PC-\d{3}) =====$", re.MULTILINE)
FIELDS = ("NOMBRE", "SINTOMAS", "MANEJO")


def load_txt_knowledge(path: str | Path) -> dict[str, dict[str, str]]:
    """Read one reference record for each unique diagnosis code."""
    contents = Path(path).read_text(encoding="utf-8-sig")
    sections = HEADER_RE.split(contents)
    if len(sections) < 3 or (len(sections) - 1) % 2:
        raise ValueError("TXT catalogue has no valid problem sections.")

    records: dict[str, dict[str, str]] = {}
    for index in range(1, len(sections), 2):
        code, text = sections[index], sections[index + 1]
        if code in records:
            raise ValueError(f"Duplicate TXT problem code: {code}")
        data: dict[str, str] = {}
        for line in text.splitlines():
            key, sep, value = line.partition(": ")
            if sep and key in FIELDS:
                if key in data or not value.strip():
                    raise ValueError(f"Invalid {key} for {code}")
                data[key] = value.strip()
        if any(key not in data for key in FIELDS):
            raise ValueError(f"Missing required TXT fields for {code}")
        records[code] = data
    return records


def reference_response(code: str, records: dict[str, dict[str, str]]) -> str:
    """Construct the final answer only from the selected TXT record."""
    try:
        data = records[code]
    except KeyError as exc:
        raise ValueError(f"Unknown reference code: {code}") from exc
    return (
        f"{code} | {data['NOMBRE']}\n"
        f"Síntomas orientativos: {data['SINTOMAS']}\n"
        f"Manejo no químico: {data['MANEJO']}\n"
        "Resultado orientativo; puede requerir revisión según especie y contexto."
    )


def safe_response(code: str, records: dict[str, dict[str, str]],
                  llm_response: str | None) -> tuple[str, bool]:
    """Use the model response only when it exactly matches the TXT answer.

    Return (answer, copied_verbatim). Otherwise return the authoritative
    local reference text. No model-generated treatments are ever substituted.
    """
    expected = reference_response(code, records)
    if llm_response is not None and llm_response.strip() == expected:
        return expected, True
    return expected, False
