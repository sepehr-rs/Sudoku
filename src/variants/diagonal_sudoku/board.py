# board.py
#
# Copyright 2025 sepehr-rs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from typing import List, Tuple, Iterable, Set
from ..classic_sudoku.board import ClassicSudokuBoard
from .rules import DiagonalSudokuRules
from .generator import DiagonalSudokuGenerator


class DiagonalSudokuBoard(ClassicSudokuBoard):
    def __init__(self, difficulty: float, difficulty_label: str):
        super().__init__(difficulty, difficulty_label, "Diagonal Sudoku")
        self.rules = DiagonalSudokuRules()
        self.generator = DiagonalSudokuGenerator()
        self.puzzle, self.solution = self.generator.generate(difficulty)

    def _iter_diagonal_cells(self, row: int, col: int) -> Iterable[Tuple[int, int]]:
        size = self.rules.size
        if row == col:
            for i in range(size):
                if i != row:
                    yield (i, i)
        if row + col == size - 1:
            for i in range(size):
                r, c = i, size - 1 - i
                if r != row or c != col:
                    yield (r, c)

    def _get_existing_value(self, row: int, col: int):
        val = self.puzzle[row][col]
        return val if val is not None else self.user_inputs[row][col]

    def has_conflict(self, row: int, col: int, value: str) -> List[Tuple[int, int]]:
        conflicts = super().has_conflict(row, col, value)
        diagonal_conflicts: List[Tuple[int, int]] = []
        seen_conflicts: Set[Tuple[int, int]] = set(conflicts)

        for r, c in self._iter_diagonal_cells(row, col):
            if (r, c) in seen_conflicts:
                continue

            existing_value = self._get_existing_value(r, c)
            if existing_value is not None and str(existing_value) == value:
                diagonal_conflicts.append((r, c))
                seen_conflicts.add((r, c))

        return conflicts + diagonal_conflicts
