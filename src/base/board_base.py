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
from abc import ABC, abstractclassmethod
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

    @abstractclassmethod
    def load_from_file(cls, filename: str = None):
        """Variant-specific boards must implement loading logic."""
        pass

    def save_to_file(self, filename: str = None):
        filename = filename or self.DEFAULT_SAVE_PATH
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        state = {
            "difficulty": self.difficulty,
            "difficulty_label": self.difficulty_label,
            "variant_preferences": PreferencesManager.get_preferences().variant_defaults,
            "general_preferences": PreferencesManager.get_preferences().general_defaults,
            "variant": self.variant,
            "puzzle": self.puzzle,
            "solution": self.solution,
            "user_inputs": self.user_inputs,
            "notes": [[list(n) for n in row] for row in self.notes],
        }
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(state, f)

    @classmethod
    def has_saved_game(cls, filename: str = None):
        filename = filename or cls.DEFAULT_SAVE_PATH
        return os.path.exists(filename)

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

    def is_clue(self, row, col):
        return self.puzzle[row][col] is not None

    @abstractclassmethod
    def is_solved(self):
        pass

    def get_notes(self, row: int, col: int) -> set:
        """Return the set of notes for a cell."""
        return self.notes[row][col]
