"""Classify observations by independent traversals of a real binary tree.

This is a rule-based candidate classifier, not clinical/plant pathology proof.
A diagnosis code is emitted only for an explicitly reported symptom pattern.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from plantcare.tree.binary_tree import BinaryDecisionTree
from plantcare.tree.node import DecisionNode, DiagnosisNode, TreeNode
from plantcare.tree.tree_loader import load_tree


@dataclass(frozen=True)
class DecisionStep:
    """Record one true binary decision used for an observed symptom."""

    node_id: str
    condition_key: str
    answer: bool


@dataclass(frozen=True)
class SymptomTrace:
    """Preserve the path for one positive observation."""

    symptom_id: str
    problem_code: str
    steps: tuple[DecisionStep, ...]


@dataclass(frozen=True)
class HierarchicalResult:
    """Represent the candidates and their reproducible tree evidence."""

    status: str
    diagnosis: DiagnosisNode | None
    traces: tuple[SymptomTrace, ...]
    warnings: tuple[str, ...]


class HierarchicalClassifier:
    """Traverse the same 50-leaf binary tree for each observed symptom."""

    def __init__(
        self,
        tree_root: TreeNode,
        group_definitions: dict[str, dict],
        valid_symptom_ids: Iterable[str],
    ) -> None:
        """Check predicate definitions and prepare the reusable tree."""
        self._root = tree_root
        self._tree = BinaryDecisionTree(tree_root)
        self._valid_symptoms = frozenset(valid_symptom_ids)
        self._groups = {
            key: frozenset(definition["any_of"])
            for key, definition in group_definitions.items()
        }
        if len(self._valid_symptoms) != 50:
            raise ValueError("Expected 50 distinct questionnaire symptom IDs.")
        for group_id, members in self._groups.items():
            if not members or not members.issubset(self._valid_symptoms):
                raise ValueError(f"Invalid group membership: {group_id}")
        self._validate_tree(self._root)

    @classmethod
    def from_data_directory(cls, directory: str | Path) -> "HierarchicalClassifier":
        """Load the new tree and metadata using existing project formats."""
        data_path = Path(directory)
        root = load_tree(data_path / "PlantCareTree_hierarchical.json")
        groups = json.loads(
            (data_path / "diagnostic_group_conditions.json").read_text(
                encoding="utf-8"
            )
        )
        questionnaire = json.loads(
            (data_path / "questionnaire_50_draft.json").read_text(
                encoding="utf-8"
            )
        )
        if len(questionnaire["questions"]) != 10:
            raise ValueError("Expected ten questionnaire questions.")
        symptom_ids = [
            option["id"]
            for question in questionnaire["questions"]
            for option in question["options"]
        ]
        if len(symptom_ids) != len(set(symptom_ids)):
            raise ValueError("Duplicate symptom IDs in questionnaire.")
        return cls(root, groups, symptom_ids)

    def _validate_tree(self, node: TreeNode, depth: int = 0) -> None:
        """Validate predicate coverage and the maximum path depth."""
        if depth > 10:
            raise ValueError("Binary decision depth exceeds ten.")
        if isinstance(node, DiagnosisNode):
            if len(node.problem_codes) != 1:
                raise ValueError("Each hierarchical leaf must have one code.")
            return
        if not isinstance(node, DecisionNode):
            raise TypeError("Unknown binary tree node.")
        if node.condition_key not in self._groups:
            raise ValueError(f"Missing group: {node.condition_key}")
        self._validate_tree(node.left, depth + 1)
        self._validate_tree(node.right, depth + 1)

    def classify(self, selected_symptoms: Iterable[str]) -> HierarchicalResult:
        """Classify all observed symptoms, retaining each binary route."""
        symptom_ids = set(selected_symptoms)
        invalid = symptom_ids.difference(self._valid_symptoms)
        if invalid:
            raise ValueError(f"Unknown questionnaire symptoms: {sorted(invalid)}")
        if not symptom_ids:
            return HierarchicalResult("insufficient_evidence", None, (), ())

        traces: list[SymptomTrace] = []
        for symptom in sorted(symptom_ids):
            # Evaluate group membership for THIS symptom alone.
            # Passing all symptoms together would mask later positive signs.
            answers = {
                key: symptom in members
                for key, members in self._groups.items()
            }
            diagnosis = self._tree.traverse(answers)
            steps: list[DecisionStep] = []
            node = self._root
            while isinstance(node, DecisionNode):
                yes = answers[node.condition_key]
                steps.append(
                    DecisionStep(node.node_id, node.condition_key, yes)
                )
                node = node.left if yes else node.right
            code = diagnosis.problem_codes[0]
            traces.append(SymptomTrace(symptom, code, tuple(steps)))

        problem_codes = tuple(sorted({trace.problem_code for trace in traces}))
        warnings = (
            ("Multiple candidates are symptom matches, not confirmed coexisting diseases.",)
            if len(problem_codes) > 1
            else ()
        )
        return HierarchicalResult(
            status="diagnosed",
            diagnosis=DiagnosisNode("hierarchical_combined", problem_codes),
            traces=tuple(traces),
            warnings=warnings,
        )

    def classify_context(self, context: object) -> HierarchicalResult:
        """Classify the positive answers recorded by DiagnosticContext."""
        answers = context.get_answers()
        return self.classify(
            symptom for selections in answers.values() for symptom in selections
        )
