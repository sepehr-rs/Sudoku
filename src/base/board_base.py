# loading_screen.py
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import logging
import os
import time
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

        start_ts = time.time()
        logging.getLogger(__name__).info(
            "board_load_start path=%s variant=%s duration_ms=%s",
            filename,
            "unknown",
            0,
        )

        try:
            with open(filename, "r", encoding="utf-8") as f:
                state = json.load(f)
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            logging.getLogger(__name__).error(
                "board_load_error path=%s",
                filename,
                exc_info=True,
            )
            raise

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

        duration_ms = int((time.time() - start_ts) * 1000)
        logging.getLogger(__name__).info(
            "board_load_success path=%s variant=%s duration_ms=%s",
            filename,
            self.variant,
            duration_ms,
        )
        return self

    @classmethod
    def load_from_file(cls, filename: str | None = None) -> Self | None:
        del filename
        raise NotImplementedError

    def save_to_file(self, filename: str | None = None):
        path = filename or self.DEFAULT_SAVE_PATH
        start_ts = time.time()
        logging.getLogger(__name__).info(
            "board_save_start path=%s variant=%s duration_ms=%s",
            path,
            self.variant,
            0,
        )

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
        except (OSError, UnicodeDecodeError):
            logging.getLogger(__name__).error(
                "board_save_error path=%s",
                path,
                exc_info=True,
            )
            raise

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
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f)
        except (OSError, UnicodeDecodeError):
            logging.getLogger(__name__).error(
                "board_save_error path=%s",
                path,
                exc_info=True,
            )
            raise

        duration_ms = int((time.time() - start_ts) * 1000)
        logging.getLogger(__name__).info(
            "board_save_success path=%s variant=%s duration_ms=%s",
            path,
            self.variant,
            duration_ms,
        )

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
