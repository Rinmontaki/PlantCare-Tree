
"""Node definitions for the PlantCare binary decision tree."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiagnosisNode:
    """Represent a terminal node containing candidate plant problems."""

    node_id: str
    problem_codes: tuple[str, ...]

    @property
    def is_leaf(self) -> bool:
        """Identify this node as a terminal diagnostic result."""
        return True


@dataclass(frozen=True, slots=True)
class DecisionNode:
    """Represent a binary decision based on an observed condition."""

    node_id: str
    condition_key: str

    # A positive condition follows the left child.
    left: TreeNode

    # A negative condition follows the right child.
    right: TreeNode

    @property
    def is_leaf(self) -> bool:
        """Identify this node as an internal decision node."""
        return False


# Both node types form the complete binary tree structure.
TreeNode = DecisionNode | DiagnosisNode
