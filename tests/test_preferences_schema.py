"""Tests for typed preference schema (dict-format entries)."""

import sys
from unittest.mock import MagicMock

sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()
sys.modules["sudoku"] = MagicMock()
sys.modules["sudoku.base_sudoku"] = MagicMock()

import pytest  # noqa: E402

from src.base.preferences import Preferences  # noqa: E402


class _TestPrefs(Preferences):
    general_defaults = {
        "legacy_bool": True,
        "legacy_list": ["subtitle text", False],
        "typed_bool": {
            "type": "bool",
            "default": True,
            "subtitle": "Typed bool",
        },
        "typed_int": {
            "type": "int",
            "default": 3,
            "min": 1,
            "max": 99,
            "subtitle": "Typed int",
            "depends_on": "typed_bool",
        },
    }

    def __init__(self):
        super().__init__()
        self.name = "Test"


def test_typed_bool_returns_default_value():
    prefs = _TestPrefs()
    assert prefs.general("typed_bool") is True


def test_typed_int_returns_default_value():
    prefs = _TestPrefs()
    assert prefs.general("typed_int") == 3


def test_legacy_bool_unchanged():
    prefs = _TestPrefs()
    assert prefs.general("legacy_bool") is True


def test_legacy_list_unchanged():
    prefs = _TestPrefs()
    assert prefs.general("legacy_list") == ["subtitle text", False]


def test_missing_key_returns_default_argument():
    prefs = _TestPrefs()
    assert prefs.general("unknown", default="fallback") == "fallback"


def test_typed_value_is_mutable_per_instance():
    prefs_a = _TestPrefs()
    prefs_b = _TestPrefs()
    entry = prefs_a.general_defaults["typed_int"]
    entry["value"] = 7
    assert prefs_a.general("typed_int") == 7
    assert prefs_b.general("typed_int") == 3


def test_schema_metadata_preserved():
    prefs = _TestPrefs()
    entry = prefs.general_defaults["typed_int"]
    assert entry["schema"]["type"] == "int"
    assert entry["schema"]["min"] == 1
    assert entry["schema"]["max"] == 99
    assert entry["schema"]["depends_on"] == "typed_bool"
