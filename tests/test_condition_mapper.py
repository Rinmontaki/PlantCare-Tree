
"""Unit tests for mapping diagnostic selections to binary conditions."""

from pathlib import Path

import pytest

from plantcare.diagnosis.condition_mapper import ConditionMapper
from plantcare.diagnosis.diagnostic_context import DiagnosticContext
from plantcare.tree.binary_tree import BinaryDecisionTree
from plantcare.tree.tree_loader import load_tree


# Locate the sample tree used for integration testing.
SAMPLE_TREE_PATH = (
    Path(__file__).parent / "fixtures" / "sample_tree.json"
)


@pytest.fixture
def condition_mapper() -> ConditionMapper:
    """Create a mapper containing two diagnostic questions."""
    return ConditionMapper(
        {
            "leaf_symptoms": (
                "yellowing",
                "visible_insects",
                "leaf_holes",
                "wilting",
                "dark_spots",
            ),
            "soil_condition": (
                "wet_soil",
                "dry_soil",
                "normal_soil",
            ),
        }
    )


def test_map_multiple_selected_symptoms(
    condition_mapper: ConditionMapper,
) -> None:
    """Convert multiple selections into Boolean conditions."""
    context = DiagnosticContext()

    # Record three selected symptoms in one question.
    context.record_answer(
        "leaf_symptoms",
        ("yellowing", "visible_insects", "leaf_holes"),
    )

    conditions = condition_mapper.build_conditions(context)

    assert conditions == {
        "yellowing": True,
        "visible_insects": True,
        "leaf_holes": True,
        "wilting": False,
        "dark_spots": False,
    }


def test_unanswered_questions_are_not_evaluated(
    condition_mapper: ConditionMapper,
) -> None:
    """Keep unanswered questions out of the condition mapping."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing",),
    )

    conditions = condition_mapper.build_conditions(context)

    # Soil conditions must remain unknown until answered.
    assert "wet_soil" not in conditions
    assert "dry_soil" not in conditions
    assert "normal_soil" not in conditions


def test_map_multiple_questions(
    condition_mapper: ConditionMapper,
) -> None:
    """Combine conditions from different answered questions."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("yellowing", "leaf_holes"),
    )

    context.record_answer(
        "soil_condition",
        ("wet_soil",),
    )

    conditions = condition_mapper.build_conditions(context)

    assert conditions["yellowing"] is True
    assert conditions["leaf_holes"] is True
    assert conditions["wet_soil"] is True
    assert conditions["dry_soil"] is False
    assert len(conditions) == 8


def test_reject_unknown_question(
    condition_mapper: ConditionMapper,
) -> None:
    """Reject questions missing from the registered configuration."""
    context = DiagnosticContext()

    context.record_answer(
        "unknown_question",
        ("yellowing",),
    )

    with pytest.raises(ValueError, match="Unknown question"):
        condition_mapper.build_conditions(context)


def test_reject_invalid_selection(
    condition_mapper: ConditionMapper,
) -> None:
    """Reject options that do not belong to the answered question."""
    context = DiagnosticContext()

    context.record_answer(
        "leaf_symptoms",
        ("wet_soil",),
    )

    with pytest.raises(ValueError, match="Invalid selection"):
        condition_mapper.build_conditions(context)


@pytest.mark.parametrize(
    "options",
    [
        ("option_1", "option_2"),
        (
            "option_1",
            "option_2",
            "option_3",
            "option_4",
            "option_5",
            "option_6",
        ),
    ],
)
def test_reject_invalid_number_of_options(
    options: tuple[str, ...],
) -> None:
    """Require between three and five options per question."""
    with pytest.raises(ValueError, match="3 to 5 options"):
        ConditionMapper({"test_question": options})


def test_reject_duplicate_options() -> None:
    """Prevent repeated option identifiers within one question."""
    with pytest.raises(ValueError, match="Duplicate options"):
        ConditionMapper(
            {
                "leaf_symptoms": (
                    "yellowing",
                    "yellowing",
                    "leaf_holes",
                ),
            }
        )


def test_reject_duplicate_options_across_questions() -> None:
    """Ensure that option identifiers are globally unique."""
    with pytest.raises(ValueError, match="unique across questions"):
        ConditionMapper(
            {
                "leaf_symptoms": (
                    "yellowing",
                    "visible_insects",
                    "leaf_holes",
                ),
                "other_symptoms": (
                    "visible_insects",
                    "wilting",
                    "dark_spots",
                ),
            }
        )


def test_mapper_integrates_with_binary_tree(
    condition_mapper: ConditionMapper,
) -> None:
    """Verify that mapped conditions can navigate the binary tree."""
    context = DiagnosticContext()

    # Simulate multiple symptoms selected in the interface.
    context.record_answer(
        "leaf_symptoms",
        ("yellowing", "visible_insects", "leaf_holes"),
    )

    # Convert selections into binary conditions.
    conditions = condition_mapper.build_conditions(context)

    # Build the tree directly from the JSON fixture.
    root = load_tree(SAMPLE_TREE_PATH)
    decision_tree = BinaryDecisionTree(root)

    # Navigate the tree using the converted conditions.
    result = decision_tree.traverse(conditions)

    assert result.node_id == "diagnosis_001"
    assert result.problem_codes == ("PC-031",)
