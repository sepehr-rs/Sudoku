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


def load_game(cls, generator, block_size: int):
    filename = _get_save_path()
    if not os.path.exists(filename):
        return None

    with open(filename, "r", encoding="utf-8") as f:
        state = json.load(f)

    prefs = PreferencesManager.get_preferences()
    if prefs is None:
        raise RuntimeError("Preferences are not initialized. [id=0]")

    return cls(
        generator=generator,
        puzzle=state["puzzle"],
        solution=state["solution"],
        difficulty=state.get("difficulty", 0.2),
        difficulty_label=state.get("difficulty_label", "Unknown"),
        variant=state.get("variant", "Unknown"),
        block_size=block_size,
        variant_preferences=state.get("variant_preferences", prefs.variant_defaults),
        general_preferences=_migrate_general_preferences(
            state.get("general_preferences", prefs.general_defaults),
            prefs.general_defaults,
        ),
    )


def save_game(board):
    filename = _get_save_path()
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
