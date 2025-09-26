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

from gi.repository import Gtk, Gdk
from abc import ABC


class UIHelpers(ABC):
    """Abstract base class for Sudoku UI helpers."""

    @staticmethod
    def create_button(label: str, callback, *args):
        button = Gtk.Button(label=label)
        button.connect("clicked", callback, *args)
        return button

    @staticmethod
    def setup_key_mappings():
        """
        Return (key_map, remove_keys). Variants may override with their own key maps.
        Default: only delete / backspace keys.
        """
        return {}, (Gdk.KEY_BackSpace, Gdk.KEY_Delete, Gdk.KEY_KP_Delete)

    @staticmethod
    def clear_highlights(cells, css_class: str):
        """Remove a CSS class from all cells in the grid."""
        for row in cells:
            for cell in row:
                cell.remove_highlight(css_class)

    @staticmethod
    def highlight_cell(cells, row: int, col: int, css_class: str):
        """Highlight a specific cell by adding a CSS class."""
        cells[row][col].highlight(css_class)

    @staticmethod
    def highlight_conflicts(cells, row: int, col: int, label: str, block_size: int):
        """
        Highlight conflicting cells and return list of conflicts.
        A conflict is any other cell in the same row, column,
        or block with the same label.
        """
        conflict_cells = []
        size = len(cells)
        for r in range(size):
            for c in range(size):
                cell = cells[r][c]
                if (
                    cell.get_value() == label
                    and (r != row or c != col)
                    and (
                        r == row
                        or c == col
                        or (
                            r // block_size == row // block_size
                            and c // block_size == col // block_size
                        )
                    )
                ):
                    cell.highlight("conflict")
                    conflict_cells.append(cell)
        return conflict_cells

    @staticmethod
    def clear_conflicts(conflict_cells):
        """Clear conflict highlights from the given list of cells."""
        for cell in conflict_cells:
            cell.remove_highlight("conflict")
        conflict_cells.clear()
