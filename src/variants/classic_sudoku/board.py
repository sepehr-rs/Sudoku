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

from typing import List, Tuple
from ...base.board_base import BoardBase
from .rules import ClassicSudokuRules
from .generator import ClassicSudokuGenerator


class ClassicSudokuBoard(BoardBase):
    def __init__(self, difficulty: float, difficulty_label: str, variant: str):
        super().__init__(
            ClassicSudokuRules(),
            ClassicSudokuGenerator(),
            difficulty,
            difficulty_label,
            variant,
        )

    @classmethod
    def load_from_file(cls, filename: str | None = None):
        return cls._load_from_file_common(
            filename=filename,
            rules=ClassicSudokuRules(),
            generator=ClassicSudokuGenerator(),
        )

    def is_solved(self):
        for r in range(self.rules.size):
            for c in range(self.rules.size):
                if not self.is_clue(r, c):
                    if self.user_inputs[r][c] != str(self.solution[r][c]):
                        return False
        return True

    def has_conflict(self, row: int, col: int, value: str) -> List[Tuple[int, int]]:
        conflicts = []
        size = self.rules.size
        block_size = self.rules.block_size

        for r in range(size):
            for c in range(size):
                if r == row and c == col:
                    continue

                if (
                    r == row
                    or c == col
                    or (
                        r // block_size == row // block_size
                        and c // block_size == col // block_size
                    )
                ):
                    existing_value = self.puzzle[r][c]
                    if existing_value is None:
                        existing_value = self.user_inputs[r][c]

                    if existing_value is not None and str(existing_value) == value:
                        conflicts.append((r, c))

        return conflicts
