# core/board.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC
from typing import Any
from ..shared import sudoku_cell
from .persistence import load_game, save_game, load_variant_preferences


class CoreSudokuBoard(ABC):

    def __init__(
        self,
        generator: Any,
        puzzle: list[list[int | None]],
        solution: list[list[int]],
        difficulty: float,
        difficulty_label: str,
        variant: str,
        block_size: int,
    ):
        self.generator = generator
        self.difficulty = difficulty
        self.difficulty_label = difficulty_label
        self.variant = variant
        self.block_size = block_size
        self.puzzle = puzzle
        self.solution = solution
        self.mistakes = 0

        self.variant_preferences = load_variant_preferences(variant)

        self.size = len(puzzle)
        self.user_inputs: list[list[int | None]] = [
            [None] * self.size for _ in range(self.size)
        ]
        self.notes: list[list[set[str]]] = [
            [set() for _ in range(self.size)] for _ in range(self.size)
        ]
        self.sudoku_cells = self.initialize_sudoku_cells()

    def initialize_sudoku_cells(self) -> list[list[sudoku_cell.SudokuCell]]:
        return [
            [
                sudoku_cell.SudokuCell(
                    value=self.puzzle[r][c],
                    correct_value=self.solution[r][c],
                    editable=(self.puzzle[r][c] is None),
                    block_size=self.block_size,
                )
                for c in range(self.size)
            ]
            for r in range(self.size)
        ]

    def is_clue(self, row: int, col: int) -> bool:
        return self.puzzle[row][col] is not None

    def get_correct_value(self, row: int, col: int) -> int:
        return self.solution[row][col]

    def set_input(self, row: int, col: int, value: int):
        self.user_inputs[row][col] = value

    def get_input(self, row: int, col: int) -> int | None:
        return self.user_inputs[row][col]

    def clear_input(self, row: int, col: int):
        self.user_inputs[row][col] = None

    def toggle_note(self, row: int, col: int, value: str):
        if value in self.notes[row][col]:
            self.notes[row][col].discard(value)
        else:
            self.notes[row][col].add(value)

    def get_notes(self, row: int, col: int) -> set[str]:
        return self.notes[row][col]

    def get_auto_pencil_marks(self) -> dict[tuple[int, int], set[str]]:
        """Return valid candidates for every empty, unfilled cell."""
        marks = {}
        for r in range(self.size):
            for c in range(self.size):
                if self.puzzle[r][c] is not None:
                    continue
                if self.user_inputs[r][c] is not None:
                    continue
                candidates = set()
                for v in range(1, self.size + 1):
                    if not self.has_conflict(r, c, v):
                        candidates.add(str(v))
                marks[(r, c)] = candidates
        return marks

    def remove_note_from_related(
        self, row: int, col: int, value: int
    ) -> list[tuple[int, int]]:
        affected = []
        value_str = str(value)
        for r in range(self.size):
            for c in range(self.size):
                if r == row and c == col:
                    continue
                same_row = r == row
                same_col = c == col
                same_block = (
                    r // self.block_size == row // self.block_size
                    and c // self.block_size == col // self.block_size
                )
                if same_row or same_col or same_block:
                    if value_str in self.notes[r][c]:
                        self.notes[r][c].discard(value_str)
                        affected.append((r, c))
        return affected

    def get_remaining_valid_inputs(self) -> dict[int, int]:
        remaining = {i: 9 for i in range(1, 10)}
        for r in range(self.size):
            for c in range(self.size):
                if self.puzzle[r][c] is not None:
                    remaining[self.puzzle[r][c]] -= 1
                val = self.user_inputs[r][c]
                if val is not None and val == self.solution[r][c]:
                    remaining[val] -= 1
        return remaining

    @classmethod
    def load(cls, generator, block_size: int = 3):
        return load_game(cls, generator=generator, block_size=block_size)

    def save(self):
        save_game(self)
