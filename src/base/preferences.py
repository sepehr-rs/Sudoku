# preferences.py
#
# Copyright 2025 sepehr-rs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC
from copy import deepcopy


def _is_schema_dict(value) -> bool:
    return isinstance(value, dict) and "type" in value and "default" in value


def _normalize_entry(value):
    """Convert a schema dict to {"schema": ..., "value": default}.

    Leaves bool, list, and already-normalized entries unchanged.
    """
    if _is_schema_dict(value):
        return {"schema": deepcopy(value), "value": deepcopy(value["default"])}
    return deepcopy(value)


def _unwrap(entry):
    if isinstance(entry, dict) and "schema" in entry and "value" in entry:
        return entry["value"]
    return entry


unwrap = _unwrap


class Preferences(ABC):
    general_defaults = {
        "casual_mode": [
            "Highlight when input does not match the correct solution",
            True,
        ],
        "prevent_conflicting_pencil_notes": False,
        "highlight_row": True,
        "highlight_column": True,
        "mistake_counter_enabled": {
            "type": "bool",
            "default": True,
            "subtitle": "Track mistakes and end the game at the limit",
        },
        "mistake_limit": {
            "type": "int",
            "default": 3,
            "min": 1,
            "max": 99,
            "subtitle": "Maximum mistakes before Game Over",
            "depends_on": "mistake_counter_enabled",
        },
    }

    variant_defaults = {}

    def __init__(self):
        cls = type(self)
        self.general_defaults = {
            key: _normalize_entry(value) for key, value in cls.general_defaults.items()
        }
        self.variant_defaults = deepcopy(cls.variant_defaults)
        self.name = ""

    def general(self, key, default=False):
        if key not in self.general_defaults:
            return default
        return _unwrap(self.general_defaults[key])

    def variant(self, key, default=False):
        return self.variant_defaults.get(key, default)
