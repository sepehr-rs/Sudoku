# ui_helpers.py
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

from ..classic_sudoku.ui_helpers import ClassicUIHelpers
from ...base.preferences_manager import PreferencesManager

class DiagonalUIHelpers(ClassicUIHelpers):
    @staticmethod
    def highlight_related_cells(
        cells, row, col, block_size: int, highlight_diagonal: bool = True
    ):
        prefs = PreferencesManager.get_preferences()
        ClassicUIHelpers.highlight_related_cells(cells, row, col, block_size)
        if highlight_diagonal and prefs.highlight_diagonal:
            size = len(cells)
            if row == col:
                for i in range(size):
                    ClassicUIHelpers.highlight_cell(cells, i, i, "highlight")
            if row + col == size - 1:
                for i in range(size):
                    ClassicUIHelpers.highlight_cell(cells, i, size - 1 - i, "highlight")
