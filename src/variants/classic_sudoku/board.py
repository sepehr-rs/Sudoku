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

import json
import os
from typing import List, Tuple
from ...base.board_base import BoardBase
from ...base.preferences_manager import PreferencesManager
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
    def load_from_file(cls, filename: str = None):
        filename = filename or cls.DEFAULT_SAVE_PATH
        if not os.path.exists(filename):
            return None

        with open(filename, "r", encoding="utf-8") as f:
            state = json.load(f)

        self = cls.__new__(cls)
        self.rules = ClassicSudokuRules()
        self.generator = ClassicSudokuGenerator()
        self.difficulty = state["difficulty"]
        self.difficulty_label = state.get("difficulty_label", "Unknown")
        self.variant_preferences = state.get(
            "variant_preferences", PreferencesManager.get_preferences().variant_defaults
        )
        self.general_preferences = state.get(
            "general_preferences", PreferencesManager.get_preferences().general_defaults
        )
        self.variant = state.get("variant", "Unknown")
        self.puzzle = state["puzzle"]
        self.solution = state["solution"]
        self.user_inputs = state["user_inputs"]
        self.notes = [[set(n) for n in row] for row in state["notes"]]
        PreferencesManager.get_preferences().variant_defaults.update(
            self.variant_preferences
        )
        PreferencesManager.get_preferences().general_defaults.update(
            self.general_preferences
        )
        return self

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
