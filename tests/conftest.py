import os
import sys
from unittest.mock import MagicMock

import pytest

from src.base.preferences_manager import PreferencesManager


if os.environ.get("SUDOKU_FD_TEST") != "1":
    sys.modules["gi"] = MagicMock()
    sys.modules["gi.repository"] = MagicMock()
    sys.modules["gi.repository.Gtk"] = MagicMock()
    sys.modules["gi.repository.Gdk"] = MagicMock()
    sys.modules["gi.repository.GLib"] = MagicMock()
    sys.modules["gi.repository.Adw"] = MagicMock()


class _DummyPreferences:
    def __init__(self, variant_defaults=None, general_defaults=None):
        self.variant_defaults = variant_defaults or {}
        self.general_defaults = general_defaults or {}

    def general(self, key, default=None):
        return self.general_defaults.get(key, default)

    def variant(self, key, default=None):
        return self.variant_defaults.get(key, default)


@pytest.fixture
def dummy_preferences_factory():
    def make_dummy_preferences(*, variant_defaults=None, general_defaults=None):
        return _DummyPreferences(
            variant_defaults=variant_defaults,
            general_defaults=general_defaults,
        )

    return make_dummy_preferences


@pytest.fixture(autouse=True)
def _prefs_guard(dummy_preferences_factory):
    PreferencesManager.set_preferences(dummy_preferences_factory())
    try:
        yield
    finally:
        PreferencesManager.set_preferences(None)
