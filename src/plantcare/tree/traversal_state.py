
"""Represent the current state of binary tree traversal."""

from dataclasses import dataclass

from plantcare.tree.node import DiagnosisNode


@dataclass(frozen=True, slots=True)
class TraversalState:
    """Represent a completed or pending binary tree traversal."""

    # Store the reached leaf, if the traversal has finished.
    diagnosis: DiagnosisNode | None

    # Identify the next required condition when traversal is pending.
    pending_condition_key: str | None

    # Preserve the identifiers of evaluated decision nodes.
    visited_node_ids: tuple[str, ...]

    @property
    def is_complete(self) -> bool:
        """Check whether the traversal reached a diagnostic leaf."""
        return self.diagnosis is not None

    def __post_init__(self) -> None:
        """Ensure that the traversal state is internally consistent."""
        # A result must contain either a diagnosis or a pending condition.
        has_diagnosis = self.diagnosis is not None
        has_pending_condition = self.pending_condition_key is not None

        if has_diagnosis == has_pending_condition:
            raise ValueError(
                "Traversal must have either a diagnosis "
                "or a pending condition."
            )
