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


class Preferences(ABC):
    general_defaults = {
        "casual_mode": [
            "Highlight when input does not match the correct solution",
            True,
        ],
        "prevent_conflicting_pencil_notes": [
            True,
        ],
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
