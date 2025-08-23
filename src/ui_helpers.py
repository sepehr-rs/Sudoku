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

from gi.repository import Gtk, Gdk, GLib
from gettext import gettext as _

from .game_board import GRID_SIZE, BLOCK_SIZE


class UIHelpers:
    """Static helper methods for UI operations."""

    @staticmethod
    def create_number_button(label: str, callback, *args):
        """Create a number button with consistent styling."""
        button = Gtk.Button(label=label)
        button.set_size_request(40, 40)
        button.connect("clicked", callback, *args)
        return button

    @staticmethod
    def setup_key_mappings():
        """Setup key mappings for number input."""
        key_map = {getattr(Gdk, f"KEY_{i}"): str(i) for i in range(1, 10)}
        key_map.update({getattr(Gdk, f"KEY_KP_{i}"): str(i) for i in range(1, 10)})

        remove_cell_keybindings = (
            Gdk.KEY_BackSpace,
            Gdk.KEY_Delete,
            Gdk.KEY_KP_Delete,
        )

        return key_map, remove_cell_keybindings

    @staticmethod
    def clear_highlights(cells: list, class_name: str):
        """Clear highlights from all cells."""
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                cells[row][col].unhighlight(class_name)

    @staticmethod
    def highlight_cell(cells: list, row: int, col: int, class_name: str):
        """Highlight a specific cell."""
        cells[row][col].highlight(class_name)

    @staticmethod
    def highlight_related_cells(cells: list, row: int, col: int):
        """Highlight all cells related to the given cell (row, column, block)."""
        UIHelpers.clear_highlights(cells, "highlight")

        # Highlight row and column
        for i in range(GRID_SIZE):
            UIHelpers.highlight_cell(cells, row, i, "highlight")
            UIHelpers.highlight_cell(cells, i, col, "highlight")

        # Highlight block only once per cell
        block_row_start = (row // BLOCK_SIZE) * BLOCK_SIZE
        block_col_start = (col // BLOCK_SIZE) * BLOCK_SIZE
        for r in range(block_row_start, block_row_start + BLOCK_SIZE):
            for c in range(block_col_start, block_col_start + BLOCK_SIZE):
                UIHelpers.highlight_cell(cells, r, c, "highlight")

    @staticmethod
    def highlight_conflicts(cells: list, row: int, col: int, label: str) -> list:
        """Highlight conflicting cells and return the list of highlighted cells."""
        conflict_cells = []

        # Check row, column, and block for conflicts
        for check_row in range(GRID_SIZE):
            for check_col in range(GRID_SIZE):
                cell = cells[check_row][check_col]
                if (
                    cell.get_value() == label
                    and cell != cells[row][col]
                    and (
                        check_row == row
                        or check_col == col
                        or (
                            check_row // BLOCK_SIZE == row // BLOCK_SIZE
                            and check_col // BLOCK_SIZE == col // BLOCK_SIZE
                        )
                    )
                ):
                    cell.highlight("conflict")
                    conflict_cells.append(cell)

        return conflict_cells

    @staticmethod
    def clear_conflicts(conflict_cells: list):
        """Clear conflict highlights from cells."""
        for cell in conflict_cells:
            cell.unhighlight("conflict")
        conflict_cells.clear()

    @staticmethod
    def clear_feedback_classes(context: Gtk.StyleContext):
        """Clear feedback classes from a style context."""
        context.remove_class("correct")
        context.remove_class("wrong")

    @staticmethod
    def specify_cell_correctness(
        cell, number: str, correct: str, conflict_cells: list, cell_inputs: list
    ):
        """Handle cell correctness feedback."""
        if number == correct:
            cell.editable = False
            cell.highlight("correct")
            cell.set_tooltip_text(_("Correct"))
            GLib.timeout_add(3000, lambda: cell.unhighlight("correct"))
            GLib.timeout_add(3000, lambda: cell.set_tooltip_text(""))
        else:
            cell.highlight("wrong")
            cell.set_tooltip_text(_("Wrong"))
            new_conflicts = UIHelpers.highlight_conflicts(
                cell_inputs, cell.row, cell.col, number
            )
            conflict_cells.extend(new_conflicts)
            GLib.timeout_add(3000, lambda: UIHelpers.clear_conflicts(conflict_cells))

    @staticmethod
    def create_difficulty_dialog(parent_window: Gtk.Window, difficulties: list):
        """Create a difficulty selection dialog."""
        dialog = Gtk.Dialog(
            title="Select Difficulty",
            transient_for=parent_window,
            modal=True,
        )

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_top=24,
            margin_bottom=24,
            margin_start=24,
            margin_end=24,
        )
        dialog.get_content_area().append(box)
        dialog.get_style_context().add_class("sudoku-dialog")

        return dialog, box
