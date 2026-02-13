# loading_screen.py
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
from abc import ABC, abstractmethod
from typing import Iterable, List, Optional, Set, Tuple
from .preferences_manager import PreferencesManager


class BoardBase(ABC):
    DEFAULT_SAVE_PATH = "saves/board.json"

    def __init__(
        self, rules, generator, difficulty: float, difficulty_label: str, variant: str
    ):
        self.rules = rules
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

    @classmethod
    @abstractmethod
    def load_from_file(cls, filename: Optional[str] = None):
        pass

    def save_to_file(self, filename: Optional[str] = None):
        filename = filename or self.DEFAULT_SAVE_PATH
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        prefs = PreferencesManager.get_preferences()
        variant_defaults = getattr(prefs, "variant_defaults", {}) if prefs else {}
        general_defaults = getattr(prefs, "general_defaults", {}) if prefs else {}
        state = {
            "difficulty": self.difficulty,
            "difficulty_label": self.difficulty_label,
            "variant_preferences": variant_defaults,
            "general_preferences": general_defaults,
            "variant": self.variant,
            "puzzle": self.puzzle,
            "solution": self.solution,
            "user_inputs": self.user_inputs,
            "notes": [[list(n) for n in row] for row in self.notes],
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(state, f)

    def set_input(self, row, col, value):
        self.user_inputs[row][col] = value

    def clear_input(self, row, col):
        self.user_inputs[row][col] = None

    def get_correct_value(self, row, col):
        return self.solution[row][col]

    def get_input(self, row, col):
        return self.user_inputs[row][col]

    def toggle_note(self, row: int, col: int, value: str):
        """Add the note if not present; remove it if already present."""
        if value in self.notes[row][col]:
            self.notes[row][col].remove(value)
        else:
            self.notes[row][col].add(value)

    def _iter_row_col_block_peers(
        self, row: int, col: int
    ) -> Iterable[Tuple[int, int]]:
        size = self.rules.size
        block_size = self.rules.block_size
        seen: Set[Tuple[int, int]] = set()

        for i in range(size):
            if i != col:
                coord = (row, i)
                if coord not in seen:
                    seen.add(coord)
                    yield coord
            if i != row:
                coord = (i, col)
                if coord not in seen:
                    seen.add(coord)
                    yield coord

        block_row_start = (row // block_size) * block_size
        block_col_start = (col // block_size) * block_size
        for r in range(block_row_start, block_row_start + block_size):
            for c in range(block_col_start, block_col_start + block_size):
                if r == row and c == col:
                    continue
                coord = (r, c)
                if coord not in seen:
                    seen.add(coord)
                    yield coord

    def iter_note_elimination_peers(
        self, row: int, col: int
    ) -> Iterable[Tuple[int, int]]:
        yield from self._iter_row_col_block_peers(row, col)

    def remove_note_from_peers(
        self, row: int, col: int, value: str
    ) -> List[Tuple[int, int]]:
        affected: List[Tuple[int, int]] = []
        for r, c in self.iter_note_elimination_peers(row, col):
            if value in self.notes[r][c]:
                self.notes[r][c].remove(value)
                affected.append((r, c))

        return affected

    def is_clue(self, row, col):
        return self.puzzle[row][col] is not None

    @abstractmethod
    def is_solved(self):
        pass

    def get_notes(self, row: int, col: int) -> Set[str]:
        """Return the set of notes for a cell."""
        return self.notes[row][col]
