from abc import ABC, abstractmethod


class RulesBase(ABC):
    """Abstract base for Sudoku rules."""

    size: int = 9  # Default 9x9 Sudoku

    @abstractmethod
    def is_valid(self, grid, row, col, value) -> bool:
        """Check if placing value at (row, col) is valid."""
        pass

    @abstractmethod
    def is_solved(self, user_inputs, solution) -> bool:
        """Check if the puzzle is solved."""
        pass
