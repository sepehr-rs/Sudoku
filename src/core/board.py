# src/core/board.py
# Copyright 2026 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
from typing import Any
from ..shared import sudoku_cell
from .persistence import load_game, save_game
from .preferences import PreferencesManager


class BoardCore(ABC):
    """
    Manages the Sudoku board
    """

    def __init__(
        self,
        generator: Any,  # TODO: FIX THIS
        difficulty: float,
        difficulty_label: str,
        variant: str,
        block_size: int,
        variant_preferences: dict[str, Any] | None = None,
        general_preferences: dict[str, Any] | None = None,
    ):
        self.generator = generator
        self.difficulty = difficulty
        self.difficulty_label = difficulty_label
        self.variant = variant
        self.block_size = block_size
        self.mistakes = 0
        prefs = PreferencesManager.get_preferences()
        if prefs is None:
            raise RuntimeError(
                "Preferences are not initialized. Please report as a bug. [id=1]"
            )
        self.variant_preferences = variant_preferences or prefs.variant_defaults
        self.general_preferences = general_preferences or prefs.general_defaults
        self.puzzle, self.solution = self.generator.generate(self.difficulty)
        self.sudoku_cells = self.initialize_sudoku_cells(self.puzzle, self.solution)

    def initialize_sudoku_cells(self, puzzle, solution):
        return [
            [
                sudoku_cell.SudokuCell(
                    value=puzzle[r][c],
                    correct_value=solution[r][c],
                    editable=(puzzle[r][c] is None),
                    block_size=self.block_size,
                )
                for c in range(self.block_size)
            ]
            for r in range(self.block_size)
        ]

    def get_sudoku_cell(self, row: int, column: int) -> sudoku_cell.SudokuCell:
        return self.sudoku_cells[row][column]

    def get_correct_value(self, row: int, col: int) -> int:
        return self.solution[row][col]

    @classmethod
    def load(cls, filename, *, generator, block_size: int):
        return load_game(cls, filename, generator=generator, block_size=block_size)

    def save(self, filename):
        save_game(self, filename)
