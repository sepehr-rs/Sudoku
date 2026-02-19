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
from typing import Any, Self
from .preferences_manager import PreferencesManager


class BoardBase(ABC):
    DEFAULT_SAVE_PATH = "saves/board.json"

    def __init__(
        self,
        rules: Any,
        generator: Any,
        difficulty: float,
        difficulty_label: str,
        variant: str,
        variant_preferences: dict[str, Any] | None = None,
        general_preferences: dict[str, Any] | None = None,
    ):
        self.rules = rules
        self.generator = generator
        self.difficulty = difficulty
        self.difficulty_label = difficulty_label
        self.variant = variant

        prefs = PreferencesManager.get_preferences()
        if prefs is None:
            raise RuntimeError("Preferences not initialized")
        self.variant_preferences = variant_preferences or prefs.variant_defaults
        self.general_preferences = general_preferences or prefs.general_defaults

        self.puzzle, self.solution = self.generator.generate(difficulty)
        self.user_inputs = [
            [None for _ in range(self.rules.size)] for _ in range(self.rules.size)
        ]
        self.notes = [
            [set() for _ in range(self.rules.size)] for _ in range(self.rules.size)
        ]

    @classmethod
    def _load_from_file_common(
        cls,
        *,
        filename: str | None,
        rules: Any,
        generator: Any,
    ) -> Self | None:
        filename = filename or cls.DEFAULT_SAVE_PATH
        if not os.path.exists(filename):
            return None

        with open(filename, "r", encoding="utf-8") as f:
            state = json.load(f)

        self = cls.__new__(cls)
        self.rules = rules
        self.generator = generator
        self.difficulty = state["difficulty"]
        self.difficulty_label = state.get("difficulty_label", "Unknown")

        prefs = PreferencesManager.get_preferences()
        if prefs is None:
            raise RuntimeError("Preferences not initialized")
        self.variant_preferences = state.get(
            "variant_preferences",
            prefs.variant_defaults,
        )
        self.general_preferences = state.get(
            "general_preferences",
            prefs.general_defaults,
        )
        self.variant = state.get("variant", "Unknown")
        self.puzzle = state["puzzle"]
        self.solution = state["solution"]
        self.user_inputs = state["user_inputs"]
        self.notes = [[set(n) for n in row] for row in state["notes"]]

        prefs.variant_defaults.update(self.variant_preferences)
        prefs.general_defaults.update(self.general_preferences)
        return self

    @classmethod
    def load_from_file(cls, filename: str | None = None) -> Self | None:
        raise NotImplementedError

    def save_to_file(self, filename: str | None = None):
        path = filename or self.DEFAULT_SAVE_PATH
        os.makedirs(os.path.dirname(path), exist_ok=True)
        prefs = PreferencesManager.get_preferences()
        if prefs is None:
            raise RuntimeError("Preferences not initialized")
        state = {
            "difficulty": self.difficulty,
            "difficulty_label": self.difficulty_label,
            "variant_preferences": prefs.variant_defaults,
            "general_preferences": prefs.general_defaults,
            "variant": self.variant,
            "puzzle": self.puzzle,
            "solution": self.solution,
            "user_inputs": self.user_inputs,
            "notes": [[list(n) for n in row] for row in self.notes],
        }
        with open(path, "w", encoding="utf-8") as f:
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

    def is_clue(self, row, col):
        return self.puzzle[row][col] is not None

    @abstractmethod
    def is_solved(self) -> bool:
        pass

    def get_notes(self, row: int, col: int) -> set:
        """Return the set of notes for a cell."""
        return self.notes[row][col]
