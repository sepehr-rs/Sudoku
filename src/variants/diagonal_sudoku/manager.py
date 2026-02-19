# manager.py
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

from ..classic_sudoku.manager import ClassicSudokuManager
from ...base.preferences_manager import PreferencesManager
from .board import DiagonalSudokuBoard
from .ui_helpers import DiagonalUIHelpers


class DiagonalSudokuManager(ClassicSudokuManager):
    def __init__(self, window):
        super().__init__(window)
        self.board_cls = DiagonalSudokuBoard
        self.key_map, self.remove_keys = DiagonalUIHelpers.setup_key_mappings()
        self.ui_helpers = DiagonalUIHelpers

    def on_cell_clicked(self, gesture, n_press, x, y, cell):
        """Handle mouse clicks on a cell (diagonal-aware)."""
        # Use diagonal-aware highlighting
        self.ui_helpers.highlight_related_cells(
            self.cell_inputs, cell.row, cell.col, self.board.rules.block_size
        )

        if cell.is_editable() and n_press == 1:
            self._show_popover(cell, gesture.get_current_button())
        else:
            cell.grab_focus()

    def _focus_cell(self, row: int, col: int):
        """Handle keyboard navigation focus (diagonal-aware)."""
        size = self.board.rules.size
        if 0 <= row < size and 0 <= col < size:
            cell = self.cell_inputs[row][col]
            if cell:
                cell.grab_focus()
                # Use diagonal-aware highlighting
                self.ui_helpers.highlight_related_cells(
                    self.cell_inputs,
                    row,
                    col,
                    self.board.rules.block_size,
                    cell.is_editable(),
                )

    def _handle_correct_input(self, cell):
        """Handle behavior when the user enters the correct number."""
        cell.set_editable(False)
        cell.highlight("correct")
        cell.set_tooltip_text("Correct")
        cell.start_feedback_timeout(lambda: self._clear_correct_feedback(cell))

    def _handle_wrong_input(self, cell, number: str, conflicts=None):
        """Handle behavior when the user enters a wrong number."""
        cell.highlight("wrong")
        cell.set_tooltip_text("Wrong")

        conflicts = conflicts or DiagonalUIHelpers.highlight_conflicts(
            self.cell_inputs, cell.row, cell.col, number, 3
        )
        self.conflict_cells.extend(conflicts)

        cell.start_feedback_timeout(self._clear_conflicts)

    def on_cell_filled(self, cell, number: str):
        """Called when a cell is filled with a number."""
        casual_mode = PreferencesManager.get_preferences().general("casual_mode")[1]
        correct_value = self.board.get_correct_value(cell.row, cell.col)
        # TODO: Add auto check for the board when casual_mdoe is turned off
        self._clear_feedback(cell)
        if casual_mode:
            if str(number) == str(correct_value):
                self._handle_correct_input(cell)
            else:
                self._handle_wrong_input(cell, number)
            return

        # non-casual mode: always check conflicts
        new_conflicts = DiagonalUIHelpers.highlight_conflicts(
            self.cell_inputs, cell.row, cell.col, number, 3
        )
        if new_conflicts:
            self._handle_wrong_input(cell, number, new_conflicts)

    def get_ui_helpers(self):
        return DiagonalUIHelpers
