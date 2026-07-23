# tests/test_preferences.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from src.core.preferences import (
    PreferencesManager,
    _migrate_general_preferences,
)
from src.variants.classic_sudoku.preferences import ClassicSudokuPreferences
from src.variants.diagonal_sudoku.preferences import DiagonalSudokuPreferences


class TestCoreSudokuPreferences:
    def test_general_returns_value_for_known_key(self):
        prefs = ClassicSudokuPreferences()
        assert prefs.general("highlight_row") is True

    def test_general_returns_default_for_unknown_key(self):
        prefs = ClassicSudokuPreferences()
        assert prefs.general("nonexistent_key") is False

    def test_general_returns_custom_default_for_unknown_key(self):
        prefs = ClassicSudokuPreferences()
        assert prefs.general("nonexistent_key", default=42) == 42

    def test_general_returns_full_entry_for_counted_toggle(self):
        prefs = ClassicSudokuPreferences()
        entry = prefs.general("mistake_limit")
        assert isinstance(entry, dict)
        assert "enabled" in entry
        assert "count" in entry

    def test_variant_returns_value_for_known_key(self):
        prefs = ClassicSudokuPreferences()
        assert prefs.variant("highlight_block") is True

    def test_variant_returns_default_for_unknown_key(self):
        prefs = ClassicSudokuPreferences()
        assert prefs.variant("nonexistent_key") is False

    def test_diagonal_preferences_include_highlight_diagonals(self):
        prefs = DiagonalSudokuPreferences()
        assert prefs.variant("highlight_diagonals") is True
        assert prefs.variant("highlight_block") is True

    def test_diagonal_preferences_name(self):
        prefs = DiagonalSudokuPreferences()
        assert prefs.name == "Diagonal Sudoku"

    def test_diagonal_inherits_general_defaults(self):
        prefs = DiagonalSudokuPreferences()
        assert prefs.general("highlight_row") is True
        assert prefs.general("highlight_column") is True

    def test_diagonal_instances_are_independent(self):
        a = DiagonalSudokuPreferences()
        b = DiagonalSudokuPreferences()
        a.variant_defaults["custom"] = True
        assert "custom" not in b.variant_defaults

    def test_diagonal_vs_classic_variant_defaults(self):
        classic = ClassicSudokuPreferences()
        diagonal = DiagonalSudokuPreferences()
        assert classic.variant("highlight_diagonals") is False
        assert diagonal.variant("highlight_diagonals") is True

    def test_preferences_instances_are_independent(self):
        a = ClassicSudokuPreferences()
        b = ClassicSudokuPreferences()
        a.variant_defaults["custom"] = True
        assert "custom" not in b.variant_defaults


class TestMigrateGeneralPreferences:
    def test_new_format_dict_passthrough(self):
        saved = {"highlight_row": {"value": True, "tooltip": "test"}}
        result = _migrate_general_preferences(saved, {})
        assert result["highlight_row"] == {"value": True, "tooltip": "test"}

    def test_old_format_list_converted(self):
        saved = {"highlight_row": ["Toggle row", True]}
        result = _migrate_general_preferences(saved, {})
        assert result["highlight_row"] == {"value": True, "tooltip": "Toggle row"}

    def test_old_format_bool_converted(self):
        saved = {"highlight_row": True}
        defaults = {"highlight_row": {"value": False, "tooltip": "Row tooltip"}}
        result = _migrate_general_preferences(saved, defaults)
        assert result["highlight_row"] == {"value": True, "tooltip": "Row tooltip"}

    def test_unknown_format_falls_back_to_default(self):
        saved = {"weird_key": [1, 2, 3]}
        defaults = {"weird_key": {"value": False, "tooltip": ""}}
        result = _migrate_general_preferences(saved, defaults)
        assert result["weird_key"] == {"value": False, "tooltip": ""}

    def test_counted_toggle_dict_passthrough(self):
        saved = {"mistake_limit": {"enabled": True, "count": 5}}
        result = _migrate_general_preferences(saved, {})
        assert result["mistake_limit"] == {"enabled": True, "count": 5}

    def test_empty_saved_returns_empty(self):
        assert _migrate_general_preferences({}, {}) == {}


class TestPreferencesManager:
    def test_set_and_get(self):
        prefs = ClassicSudokuPreferences()
        PreferencesManager.set_preferences(prefs)
        assert PreferencesManager.get_preferences() is prefs

    def test_get_returns_none_initially(self):
        PreferencesManager.set_preferences(None)
        assert PreferencesManager.get_preferences() is None

    def test_set_replaces_previous(self):
        a = ClassicSudokuPreferences()
        b = DiagonalSudokuPreferences()
        PreferencesManager.set_preferences(a)
        PreferencesManager.set_preferences(b)
        assert PreferencesManager.get_preferences() is b
