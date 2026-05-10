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
from gi.repository import GLib
from .preferences_manager import PreferencesManager


def _get_save_path():
    """Get the save file path following XDG spec."""
    data_dir = GLib.get_user_data_dir()
    save_dir = os.path.join(data_dir, "sudokugame")
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, "board.json")


class BoardBase(ABC):
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
        filename = filename or _get_save_path()
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
        self.puzzle = state["puzzle"]  # The default board shown to the user
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
        path = filename or _get_save_path()
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

    def get_input(self, row, col) -> str:
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


    def remove_note_from_related(self, row: int, col: int, value: str):
        """Remove `value` from notes of all cells in the same row, col, and block."""
        size = self.rules.size
        block_size = self.rules.block_size
        affected = set()
        diagonals = True if self.variant == "diagonal" else False

        # row and column
        for i in range(size):
            affected.add((row, i))
            affected.add((i, col))

        # block
        br, bc = (row // block_size) * block_size, (col // block_size) * block_size
        for r in range(br, br + block_size):
            for c in range(bc, bc + block_size):
                affected.add((r, c))

        # diagonals (diagonal variant)
        if diagonals:
            if row == col:
                for i in range(size):
                    affected.add((i, i))
            if row + col == size - 1:
                for i in range(size):
                    affected.add((i, size - 1 - i))

        for r, c in affected:
            self.notes[r][c].discard(value)

        return affected

    def get_remaining_valid_inputs(self) -> dict:
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
