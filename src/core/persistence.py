# persistence.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from .preferences import PreferencesManager, _migrate_general_preferences
from gi.repository import GLib
import os
import json


def _get_save_path():
    """Get the save file path following XDG spec."""
    data_dir = GLib.get_user_data_dir()
    save_dir = os.path.join(data_dir, "sudokugame")
    os.makedirs(save_dir, exist_ok=True)
    return os.path.join(save_dir, "board.json")


def load_game(cls, filename: str | None, *, generator, block_size: int):
    filename = filename or _get_save_path()
    if not os.path.exists(filename):
        return None

    with open(filename, "r", encoding="utf-8") as f:
        state = json.load(f)

    self = cls.__new__(cls)
    self.generator = generator
    self.block_size = block_size
    self.difficulty = state.get("difficulty", 0.2)  # default to easy
    self.difficulty_label = state.get("difficulty_label", "Unknown")
    self.mistakes = state.get("mistakes", 0)

    prefs = PreferencesManager.get_preferences()
    if prefs is None:
        # we shouldn't reach this state
        raise RuntimeError(
            "Preferences are not initialized. Please report as a bug. [id=0]"
        )
    self.variant_preferences = state.get(
        "variant_preferences",
        prefs.variant_defaults,
    )
    raw_general = state.get("general_preferences", prefs.general_defaults)
    self.general_preferences = _migrate_general_preferences(
        raw_general, prefs.general_defaults
    )
    self.variant = state.get("variant", "Unknown")
    try:
        self.puzzle = state["puzzle"]
        self.solution = state["solution"]
    except KeyError:
        # we shouldn't reach this state.
        raise KeyError("Puzzle or Solution not found. Please report as a bug.")

    self.sudoku_cells = self.initialize_sudoku_cells(self.puzzle, self.solution)
    prefs.variant_defaults.update(self.variant_preferences)
    prefs.general_defaults.update(self.general_preferences)

    return self


def save_game(board, filename: str | None = None):
    filename = filename or _get_save_path()
    state = {
        "difficulty": board.difficulty,
        "difficulty_label": board.difficulty_label,
        "mistakes": board.mistakes,
        "variant_preferences": board.variant_preferences,
        "general_preferences": board.general_preferences,
        "variant": board.variant,
        "puzzle": board.puzzle,
        "solution": board.solution,
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state, f)
