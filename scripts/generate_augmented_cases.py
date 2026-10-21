"""Generate synthetic structural cases for PlantCare regression testing.

These are software test cases, not independently validated botanical diagnoses
or LLM fine-tuning data. Each mapping comes from the existing questionnaire.
"""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "augmented_test_cases.json"


def build_cases() -> list[dict]:
    """Create deterministic single, paired, and triple symptom examples."""
    cases = [{
        "case_id": "absence-000",
        "selected_symptoms": [],
        "expected_codes": [],
        "origin": "synthetic_structural",
    }]
    for index in range(50):
        number = index + 1
        for label, offsets in (
            ("single", (0,)),
            ("pair", (0, 17)),
            ("triple", (0, 13, 29)),
        ):
            numbers = sorted({(index + offset) % 50 + 1 for offset in offsets})
            cases.append({
                "case_id": f"{label}-{number:03d}",
                "selected_symptoms": [f"sign_{n:03d}" for n in numbers],
                "expected_codes": [f"PC-{n:03d}" for n in numbers],
                "origin": "synthetic_structural",
            })
    return cases


def main() -> None:
    """Save reproducible test observations."""
    payload = {
        "description": "Synthetic regression tests, NOT verified botanical cases",
        "cases": build_cases(),
    }
    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved {len(payload['cases'])} cases to {OUTPUT}")


if __name__ == "__main__":
    main()
