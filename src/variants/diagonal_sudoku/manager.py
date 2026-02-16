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
from ..classic_sudoku.sudoku_cell import SudokuCell
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

    def _fill_cell(self, cell: SudokuCell, number: str, ctrl_is_pressed=False):
        DiagonalUIHelpers.clear_conflicts(self.conflict_cells)

        if not cell.is_editable():
            return

        r, c = cell.row, cell.col

        if self.pencil_mode or ctrl_is_pressed:
            if cell.get_value():
                return

            prefs = PreferencesManager.get_preferences()
            if prefs is None:
                pref_enabled = True
            else:
                pref_value = prefs.general(
                    "prevent_conflicting_pencil_notes",
                    default=True,
                )
                pref_enabled = pref_value

            if pref_enabled and self.board.has_conflict(r, c, number):
                new_conflicts = DiagonalUIHelpers.highlight_conflicts(
                    self.cell_inputs, r, c, number, self.board.rules.block_size
                )
                self.conflict_cells.extend(new_conflicts)
                cell.start_feedback_timeout(self._clear_conflicts, delay=2000)
                return

            self.board.toggle_note(r, c, number)
            cell.update_notes(self.board.get_notes(r, c))
            self.board.save_to_file()
            return

        cell.set_value(number)
        self.board.set_input(r, c, number)
        self.board.save_to_file()

        self.on_cell_filled(cell, number)

        if self.board.is_solved():
            self._show_puzzle_finished_dialog()
