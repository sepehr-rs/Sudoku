# manager_base.py
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

from gi.repository import Gtk, GLib
from .ui_helpers import UIHelpers
import logging
import threading


class ManagerBase:
    def __init__(self, window, board_cls):
        self.window = window
        self.board_cls = board_cls
        self.board = None
        self.cell_inputs = []
        self.conflict_cells = []
        self.pencil_mode = False

    def load_saved_game(self):
        self.board = self.board_cls.load_from_file()
        if self.board:
            self.window.sudoku_window_title.set_subtitle(
                f"{self.board.variant.capitalize()} • {self.board.difficulty_label}"
            )
            self.build_grid()
            self._restore_game_state()
            self.window.stack.set_visible_child(self.window.game_scrolled_window)
            logging.info(
                f"Loaded saved {self.board.variant.capitalize()} Sudoku game"
            )
            if self.board.is_solved():
                self._show_puzzle_finished_dialog()
        else:
            logging.error("No saved game found")

    def _restore_game_state(self):
        raise NotImplementedError

    def new_game(self, difficulty, difficulty_label):
        self.board = self.board_cls(difficulty, difficulty_label)

    def start_game(self, difficulty: float, difficulty_label: str, variant: str):
        self.window.stack.set_visible_child(self.window.loading_screen)
        logging.info(
            f"Starting {variant.capitalize()} Sudoku with difficulty: {difficulty}"
        )

        def worker():
            self.board = self.board_cls(difficulty, difficulty_label, variant)
            GLib.idle_add(self._finish_start_game, self.board)

        threading.Thread(target=worker, daemon=True).start()

    def _finish_start_game(self, board):
        raise NotImplementedError

    def build_grid(self):
        """Variant managers override this to build the grid UI."""
        pass

    def setup_key_mappings(self):
        self.key_map, self.remove_keys = UIHelpers.setup_key_mappings()

    def handle_key_press(self, event, cell):
        keyval = event.keyval
        if keyval in self.key_map:
            number = self.key_map[keyval]
            self._fill_cell(cell, number)
            return True
        if keyval in self.remove_keys:
            self._clear_cell(cell)
            return True
        return False

    def _fill_cell(self, cell, number: str, ctrl_is_pressed=False):
        pass

    def _clear_cell(self, cell):
        pass

    def on_cell_filled(self, cell, number: str):
        """
        Abstract correctness feedback.
        Subclasses can override, or rely on default
        behavior using specify_cell_correctness.
        """
        pass

    def _show_puzzle_finished_dialog(self):
        pass

    def on_pencil_toggled(self, button: Gtk.ToggleButton):
        """Shared handler for pencil mode toggling."""
        self.pencil_mode = button.get_active()
        logging.info(
            "Pencil Mode is now ON" if self.pencil_mode else "Pencil mode is now OFF"
        )

    def on_grid_unfocus(self):
        """Clear highlights when clicking outside the grid."""
        if self.cell_inputs:
            UIHelpers.clear_highlights(self.cell_inputs, "highlight")
        if self.conflict_cells:
            UIHelpers.clear_highlights([self.conflict_cells], "conflict")
            self.conflict_cells.clear()
