# core/persistence.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from .preferences import PreferencesManager, _migrate_general_preferences
from gi.repository import GLib
import os
import json


def _get_data_dir():
    data_dir = GLib.get_user_data_dir()
    save_dir = os.path.join(data_dir, "sudokugame")
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


def _get_save_path():
    return os.path.join(_get_data_dir(), "board.json")


def _get_preferences_path():
    return os.path.join(_get_data_dir(), "preferences.json")


def get_variant():
    path = _get_save_path()
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("variant", "Unknown")


def _read_preferences_file():
    path = _get_preferences_path()
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_preferences_file(data):
    path = _get_preferences_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_general_preferences():
    prefs = PreferencesManager.get_preferences()
    defaults = {**prefs.general_toggles, **prefs.general_counted}
    saved = _read_preferences_file()
    if not saved:
        return defaults
    general = {k: v for k, v in saved.items() if k != "variant_preferences"}
    return _migrate_general_preferences(general, defaults)


def load_variant_preferences(variant):
    prefs = PreferencesManager.get_preferences()
    # variant_defaults is already hydrated by apply_variant_preferences()
    # before the board is constructed, so we just return a copy of it.
    return dict(prefs.variant_defaults)


def apply_variant_preferences(variant: str):
    """Load saved variant prefs into the active PreferencesManager instance."""
    prefs = PreferencesManager.get_preferences()
    if prefs is None:
        return
    saved = _read_preferences_file()
    variant_prefs = saved.get("variant_preferences", {})
    if variant in variant_prefs:
        prefs.variant_defaults.update(variant_prefs[variant])


def save_preferences():
    prefs = PreferencesManager.get_preferences()
    if prefs is None:
        return
    data = _read_preferences_file()
    data.update(
        {
            **prefs.general_toggles,
            **prefs.general_counted,
        }
    )
    if prefs.variant_defaults:
        data.setdefault("variant_preferences", {})
        data["variant_preferences"][prefs.variant_key] = prefs.variant_defaults
    _write_preferences_file(data)


def save_general_preferences(general_preferences=None):
    if general_preferences is None:
        prefs = PreferencesManager.get_preferences()
        general_preferences = {**prefs.general_toggles, **prefs.general_counted}
    data = _read_preferences_file()
    data.update(general_preferences)
    _write_preferences_file(data)


def load_game(cls, generator, block_size: int):
    filename = _get_save_path()
    if not os.path.exists(filename):
        return None

    with open(filename, "r", encoding="utf-8") as f:
        state = json.load(f)

    prefs = PreferencesManager.get_preferences()
    if prefs is None:
        raise RuntimeError("Preferences are not initialized. [id=0]")

    variant = state.get("variant", "Unknown")
    board = cls(
        generator=generator,
        puzzle=state["puzzle"],
        solution=state["solution"],
        difficulty=state.get("difficulty", 0.2),
        difficulty_label=state.get("difficulty_label", "Unknown"),
        variant=variant,
        block_size=block_size,
    )

    board.mistakes = state.get("mistakes", 0)

    saved_inputs = state.get("user_inputs")
    if saved_inputs:
        for r in range(len(saved_inputs)):
            for c in range(len(saved_inputs[r])):
                board.user_inputs[r][c] = saved_inputs[r][c]

    saved_notes = state.get("notes")
    if saved_notes:
        for r in range(len(saved_notes)):
            for c in range(len(saved_notes[r])):
                board.notes[r][c] = set(saved_notes[r][c])

    return board


def save_game(board):
    filename = _get_save_path()
    state = {
        "difficulty": board.difficulty,
        "difficulty_label": board.difficulty_label,
        "mistakes": board.mistakes,
        "variant": board.variant,
        "puzzle": board.puzzle,
        "solution": board.solution,
        "user_inputs": board.user_inputs,
        "notes": [[list(n) for n in row] for row in board.notes],
    }
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(state, f)


def clear_save():
    path = _get_save_path()
    if os.path.exists(path):
        os.remove(path)


def has_saved_game():
    return os.path.exists(_get_save_path())


def migrate_preferences_from_board():
    board_path = _get_save_path()
    prefs_path = _get_preferences_path()
    if not os.path.exists(board_path):
        return
    if os.path.exists(prefs_path):
        return
    with open(board_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    has_general = "general_preferences" in state
    has_variant = "variant_preferences" in state
    if not has_general and not has_variant:
        return
    prefs = PreferencesManager.get_preferences()
    if prefs is None:
        return
    migrated = {}
    if has_general:
        defaults = {**prefs.general_toggles, **prefs.general_counted}
        migrated.update(
            _migrate_general_preferences(state["general_preferences"], defaults),
        )
        del state["general_preferences"]
    if has_variant:
        variant = state.get("variant", "Unknown")
        migrated.setdefault("variant_preferences", {})
        migrated["variant_preferences"][variant] = state["variant_preferences"]
        del state["variant_preferences"]
    _write_preferences_file(migrated)
    with open(board_path, "w", encoding="utf-8") as f:
        json.dump(state, f)
