# core/preferences.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC


class CoreSudokuPreferences(ABC):
    general_toggles = {
        "casual_mode": {
            "value": True,
            "tooltip": "Highlight when input does not match the correct solution",
        },
        "prevent_conflicting_pencil_notes": {
            "value": False,
            "tooltip": "",
        },
        "highlight_row": {
            "value": True,
            "tooltip": "",
        },
        "highlight_column": {
            "value": True,
            "tooltip": "",
        },
        "auto_remove_notes": {
            "value": False,
            "tooltip": "Automatically remove pencil notes after a correct entry",
        },
        "show_remaining_valid_inputs": {
            "value": False,
            "tooltip": "View the possible places left for each number",
        },
        "show_popover": {
            "value": True,
            "tooltip": "Show popover when clicking on a cell",
        },
    }

    general_counted = {
        "mistake_limit": {
            "enabled": False,
            "count": 3,
            "tooltip": "End the game or warn after a set number of mistakes",
        },
    }

    variant_defaults = {}

    def __init__(self):
        self.general_toggles = self.general_toggles.copy()
        self.general_counted = self.general_counted.copy()
        self.variant_defaults = self.variant_defaults.copy()
        self.name = ""
        self.variant_key = ""

    def general(self, key, default=False):
        entry = self.general_toggles.get(key)
        if entry is not None:
            return entry.get("value", default)
        return default

    def general_counted_entry(self, key, default=None):
        return self.general_counted.get(key, default)

    def variant(self, key, default=False):
        return self.variant_defaults.get(key, default)


def _migrate_general_preferences(saved: dict, defaults: dict) -> dict:
    """Convert old-format general preferences to the current dict format."""
    migrated = {}
    for key, value in saved.items():
        if isinstance(value, dict):
            migrated[key] = value
        elif isinstance(value, list) and len(value) == 2:
            tooltip, val = value
            migrated[key] = {"value": val, "tooltip": tooltip}
        elif isinstance(value, bool):
            default_entry = defaults.get(key, {})
            tooltip = (
                default_entry.get("tooltip", "")
                if isinstance(default_entry, dict)
                else ""
            )
            migrated[key] = {"value": value, "tooltip": tooltip}
        else:
            migrated[key] = defaults.get(key, {"value": value, "tooltip": ""})
    return migrated


class PreferencesManager:
    _current_preferences: CoreSudokuPreferences | None = None

    @classmethod
    def set_preferences(cls, prefs: CoreSudokuPreferences) -> None:
        cls._current_preferences = prefs

    @classmethod
    def get_preferences(cls) -> CoreSudokuPreferences | None:
        return cls._current_preferences
