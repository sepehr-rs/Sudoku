# src/core/board.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod

class BoardBase(ABC):
    """
    Manages the Sudoku board
    """
    def __init__(
        self,
        generator: Any,
        difficulty: float,
        difficulty_label: str,
        variant: str,
        variant_preferences: dict[str, Any] | None = None,
        general_preferences: dict[str, Any] | None = None,
    ):
        self.generator = generator
        self.difficulty = difficulty
        self.difficulty_label = difficulty_label
        self.variant = variant
        self.puzzle, self.solution = self.generator.generate(difficulty)
        self.user_inputs = [
            [None for _ in range(self.rules.size)] for _ in range(self.rules.size)
        ]
        self.notes = [
            [set() for _ in range(self.rules.size)] for _ in range(self.rules.size)
        ]

    @abstractmethod
    def is_solved(self) -> bool:
        pass
    
    def get_remaining_valid_inputs(self) -> dict:
        """
        Return how many times each value (1–9) can still be correctly placed.

        Starts from 9 for each value and subtracts once for every correct
        user input and once for every pre-filled puzzle cell containing that value.

        Returns:
            A dict mapping each value 1–9 to its remaining placement count,
            or an empty dict if the puzzle or user inputs are not set.
        """

        if not self.puzzle or not self.user_inputs:
            return {}

        # Count numbers in solution
        remaining_valid_inputs = {i: 9 for i in range(1, 10)}

        # Count numbers in the user input
        for row in range(0, 9):
            for column in range(0, 9):
                if not self.get_input(row, column):
                    continue
                if not int(self.get_input(row, column)) == self.get_correct_value(
                    row, column
                ):
                    continue
                else:
                    remaining_valid_inputs[int(self.get_input(row, column))] -= 1

        # Substitute remaining_valid_inputs from pre-set values in the puzzle
        for row in range(0, 9):
            for column in range(0, 9):
                if not self.puzzle[row][column]:
                    continue
                remaining_valid_inputs[self.puzzle[row][column]] -= 1

        return remaining_valid_inputs

    @abstractmethod
    def is_conflicting(self, value: int, row: set[int], col: set[int], **regions: set[int]) -> bool:
        """
        Check whether `value` conflicts with any of the given regions.

        Each region is a set of values already present in that area of the board.
        Subclasses define which regions are relevant (e.g. block, diagonal, color).

        Args:
            value: The candidate value to check.
            row: Values already in the cell's row.
            col: Values already in the cell's column.
            **regions: Additional variant-specific regions (e.g. block, diagonal).

        Returns:
            True if `value` is already present in any region, False otherwise.
        """
        pass
