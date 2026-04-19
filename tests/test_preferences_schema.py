"""Tests for typed preference schema (dict-format entries)."""

import sys
from unittest.mock import MagicMock

sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()
sys.modules["sudoku"] = MagicMock()
sys.modules["sudoku.base_sudoku"] = MagicMock()

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


def test_typed_entry_save_and_load_roundtrip_preserves_values():
    """A wrapped entry serializes as its unwrapped value and re-loads via merge."""
    import json
    from src.base.preferences import unwrap

    prefs = _TestPrefs()
    # Mutate a typed value
    prefs.general_defaults["typed_int"]["value"] = 7
    prefs.general_defaults["typed_bool"]["value"] = False

    # Simulate what board_base.save_to_file now does
    serialized = {
        key: unwrap(entry) for key, entry in prefs.general_defaults.items()
    }
    payload = json.dumps(serialized)

    # Legacy pass-through: bool/list stay as-is
    assert json.loads(payload)["legacy_bool"] is True
    assert json.loads(payload)["legacy_list"] == ["subtitle text", False]
    # Typed values are flat in the save file
    assert json.loads(payload)["typed_int"] == 7
    assert json.loads(payload)["typed_bool"] is False

    # Simulate what board_base.load_from_file merges
    fresh = _TestPrefs()
    for key, saved_value in json.loads(payload).items():
        current = fresh.general_defaults.get(key)
        if isinstance(current, dict) and "schema" in current and "value" in current:
            current["value"] = saved_value
        else:
            fresh.general_defaults[key] = saved_value

    # Values restored, schema preserved
    assert fresh.general("typed_int") == 7
    assert fresh.general("typed_bool") is False
    assert fresh.general_defaults["typed_int"]["schema"]["min"] == 1
    assert fresh.general("legacy_bool") is True
    assert fresh.general("legacy_list") == ["subtitle text", False]


class _RealBasePrefs(Preferences):
    """Uses the real Preferences.general_defaults (no override)."""

    def __init__(self):
        super().__init__()
        self.name = "Real"


def test_mistake_counter_enabled_default_is_true():
    prefs = _RealBasePrefs()
    assert prefs.general("mistake_counter_enabled") is True


def test_mistake_limit_default_is_three():
    prefs = _RealBasePrefs()
    assert prefs.general("mistake_limit") == 3


def test_mistake_limit_has_bounds_metadata():
    prefs = _RealBasePrefs()
    entry = prefs.general_defaults["mistake_limit"]
    assert entry["schema"]["min"] == 1
    assert entry["schema"]["max"] == 99
    assert entry["schema"]["depends_on"] == "mistake_counter_enabled"


def test_mutating_typed_int_value_is_visible_through_general():
    prefs = _RealBasePrefs()
    prefs.general_defaults["mistake_limit"]["value"] = 5
    assert prefs.general("mistake_limit") == 5


def test_mutating_typed_bool_value_is_visible_through_general():
    prefs = _RealBasePrefs()
    prefs.general_defaults["mistake_counter_enabled"]["value"] = False
    assert prefs.general("mistake_counter_enabled") is False
