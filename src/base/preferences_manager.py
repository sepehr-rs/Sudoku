# preferences_manager.py
# SPDX-License-Identifier: GPL-3.0-or-later


from collections.abc import Callable


class PreferencesManager:
    _current_preferences = None
    _preferences_loaded_hook: Callable[[str], None] | None = None

    @classmethod
    def set_preferences_loaded_hook(cls, hook: Callable[[str], None] | None):
        cls._preferences_loaded_hook = hook

    @classmethod
    def set_preferences(cls, prefs):
        cls._current_preferences = prefs
        if prefs is not None and cls._preferences_loaded_hook is not None:
            cls._preferences_loaded_hook("preferences_loaded")

    @classmethod
    def get_preferences(cls):
        return cls._current_preferences
