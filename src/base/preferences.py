# preferences.py
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC


class Preferences(ABC):
    general_defaults = {
        "casual_mode": [
            "Highlight when input does not match the correct solution",
            True,
        ],
        "prevent_conflicting_pencil_notes": False,
        "highlight_row": True,
        "highlight_column": True,
    }

    variant_defaults = {}

    def __init__(self):
        self.general_defaults = self.general_defaults.copy()
        self.variant_defaults = self.variant_defaults.copy()
        self.name = ""

    def general(self, key, default=False):
        return self.general_defaults.get(key, default)

    def variant(self, key, default=False):
        return self.variant_defaults.get(key, default)
