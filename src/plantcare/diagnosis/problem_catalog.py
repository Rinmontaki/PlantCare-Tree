
"""Load and validate the PlantCare problem catalogue."""

import json
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = (
    "code",
    "name",
    "indicative_symptoms",
    "organic_or_nonchemical_management",
)


def load_problem_catalog(
    path: str | Path,
) -> dict[str, dict[str, Any]]:
    """Load plant problems indexed by their unique codes."""

    catalogue_path = Path(path)

    with catalogue_path.open(encoding="utf-8") as file:
        data = json.load(file)

    problems = data.get("problems")

    if not isinstance(problems, list):
        raise ValueError("The catalogue must contain a problems list.")

    catalogue: dict[str, dict[str, Any]] = {}

    for problem in problems:
        if not isinstance(problem, dict):
            raise ValueError("Each problem must be an object.")

        for field in REQUIRED_FIELDS:
            value = problem.get(field)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    f"Invalid or missing problem field: {field}"
                )

        code = problem["code"]

        if code in catalogue:
            raise ValueError(f"Duplicate problem code: {code}")

        catalogue[code] = problem

    return catalogue
