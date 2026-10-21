"""Generate a semantic binary decision tree for all 50 PlantCare signs.

Each of the 50 signs is routed through a hierarchy of group-membership
YES/NO predicates. Group predicates are derived from questionnaire answers;
they are not additional questions asked to the user.
"""

import json
from pathlib import Path


CATEGORIES = {
    "water_roots": tuple(range(1, 6)),
    "light_environment": tuple(range(6, 11)),
    "heat_nutrition": tuple(range(11, 16)),
    "minerals_ph": tuple(range(16, 21)),
    "foliar_disease": tuple(range(21, 26)),
    "deep_disease": tuple(range(26, 31)),
    "aerial_pests": tuple(range(31, 36)),
    "leaf_soil_pests": tuple(range(36, 41)),
    "special_pests": tuple(range(41, 46)),
    "stem_root_pests": tuple(range(46, 51)),
}

SIGNIFICANCE = {
    "domain_abiotic": "Care, environment, or nutrition evidence versus biological agents",
    "abiotic_environment": "Water, roots, or environment versus nutrition",
    "abiotic_water_roots": "Water or substrate evidence versus light and environment",
    "abiotic_nutrition": "Heat or general nutrition versus mineral or pH signs",
    "biotic_diseases": "Disease-associated signs versus visible pests",
    "diseases_foliar": "Foliar disease signs versus other disease signs",
    "pests_aerial_or_leaf": "Aerial or leaf/soil pests versus other pests",
    "pests_aerial": "Common aerial pests versus leaf or soil pests",
    "pests_special": "Specialized insect evidence versus stem or root pests",
}


def sign(number: int) -> str:
    """Return a stable option identifier."""
    return f"sign_{number:03d}"


def category(name: str) -> tuple[int, ...]:
    """Return the option numbers in one botanical category."""
    return CATEGORIES[name]


def leaf(number: int) -> dict:
    """Construct a diagnosis leaf for one observation pattern."""
    return {
        "type": "diagnosis",
        "node_id": f"leaf_pc_{number:03d}",
        "problem_codes": [f"PC-{number:03d}"],
    }


predicate_definitions: dict[str, dict] = {}


def subtree_signs(node: dict) -> set[str]:
    """Return all possible signs reaching a subtree."""
    if node["type"] == "diagnosis":
        return {"sign_" + node["problem_codes"][0][-3:]}
    return subtree_signs(node["left"]) | subtree_signs(node["right"])


def decision(name: str, left: dict, right: dict) -> dict:
    """Add a binary decision that checks membership in the left subtree."""
    key = f"has_{name}"
    if key in predicate_definitions:
        raise ValueError(f"Repeated predicate: {key}")
    predicate_definitions[key] = {
        "any_of": sorted(subtree_signs(left)),
        "meaning": SIGNIFICANCE.get(
            name,
            "Does the observation match this group of symptoms?",
        ),
    }
    return {
        "type": "decision",
        "node_id": f"decision_{name}",
        "condition_key": key,
        "left": left,
        "right": right,
    }


def category_subtree(name: str) -> dict:
    """Recursively balance the five characteristic signs of a category."""
    numbers = category(name)

    def build(values: tuple[int, ...]) -> dict:
        if len(values) == 1:
            return leaf(values[0])
        midpoint = len(values) // 2
        left = build(values[:midpoint])
        right = build(values[midpoint:])
        suffix = "_".join(str(value).zfill(3) for value in values)
        return decision(f"{name}_{suffix}", left, right)

    return build(numbers)


def build() -> dict:
    """Build domain, category, and characteristic levels."""
    roots = {
        name: category_subtree(name)
        for name in CATEGORIES
    }

    environment = decision(
        "abiotic_water_roots", roots["water_roots"], roots["light_environment"]
    )
    nutrition = decision(
        "abiotic_nutrition", roots["heat_nutrition"], roots["minerals_ph"]
    )
    abiotic = decision("abiotic_environment", environment, nutrition)

    diseases = decision(
        "diseases_foliar", roots["foliar_disease"], roots["deep_disease"]
    )
    common_pests = decision(
        "pests_aerial", roots["aerial_pests"], roots["leaf_soil_pests"]
    )
    other_pests = decision(
        "pests_special", roots["special_pests"], roots["stem_root_pests"]
    )
    pests = decision("pests_aerial_or_leaf", common_pests, other_pests)
    biotic = decision("biotic_diseases", diseases, pests)
    return decision("domain_abiotic", abiotic, biotic)


def inspect(node: dict, depth: int = 0) -> tuple[int, int, int, set[str]]:
    """Return decision count, leaves, max depth, and included codes."""
    if node["type"] == "diagnosis":
        return 0, 1, depth, set(node["problem_codes"])
    left = inspect(node["left"], depth + 1)
    right = inspect(node["right"], depth + 1)
    return (
        1 + left[0] + right[0],
        left[1] + right[1],
        max(left[2], right[2]),
        left[3] | right[3],
    )


def main() -> None:
    """Generate the two files without overwriting the original tree."""
    root = Path(__file__).resolve().parents[1]
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)
    tree = build()
    decisions, leaves, depth, codes = inspect(tree)
    assert decisions == 49
    assert leaves == 50
    assert depth <= 10
    assert codes == {f"PC-{n:03d}" for n in range(1, 51)}

    (data_dir / "PlantCareTree_hierarchical.json").write_text(
        json.dumps(tree, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    (data_dir / "diagnostic_group_conditions.json").write_text(
        json.dumps(predicate_definitions, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"Tree generated: {decisions} binary nodes, {leaves} leaves")
    print(f"Maximum depth: {depth} decisions")
    print(f"Problem codes covered: {len(codes)}/50")


if __name__ == "__main__":
    main()
