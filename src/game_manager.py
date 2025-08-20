# game_manager.py
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
import logging
from gi.repository import Gtk, Gdk, GLib, Gio
from gettext import gettext as _
from .game_board import GameBoard, GRID_SIZE
from .sudoku_cell import SudokuCell
from .ui_helpers import UIHelpers


class GameManager:
    def __init__(self, window):
        self.window = window
        self.game_board = None
        self.cell_inputs = None
        self.conflict_cells = []
        self.pencil_mode = False

        self.key_map, self.remove_cell_keybindings = UIHelpers.setup_key_mappings()

        self._setup_actions()

    def _setup_actions(self):
        back_action = Gio.SimpleAction.new("back-to-menu", None)
        back_action.connect("activate", self.on_back_to_menu)
        self.window.add_action(back_action)

        pencil_action = Gio.SimpleAction.new_stateful(
            "pencil-toggled", None, GLib.Variant.new_boolean(False)
        )
        pencil_action.connect("change-state", self.on_pencil_action_toggled)
        self.window.add_action(pencil_action)

    def start_game(self, difficulty: float, difficulty_label: str):
        logging.info(f"Starting game with difficulty: {difficulty}")
        self.game_board = GameBoard(difficulty, difficulty_label)
        self.build_grid()
        self.window.stack.set_visible_child(self.window.game_view_box)

    def load_saved_game(self):
        self.game_board = GameBoard.load_from_file()
        if self.game_board:
            difficulty_label = self.game_board.difficulty_label
            self.window.sudoku_window_title.set_subtitle(f"{difficulty_label}")
            self.build_grid()
            self._restore_game_state()
            self.window.stack.set_visible_child(self.window.game_view_box)
            logging.info("Game successfully loaded from save.")
            if self.game_board.is_solved():
                self._show_puzzle_finished_dialog()
        else:
            logging.error("Failed to load saved game")

    def _restore_game_state(self):
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                value = self.game_board.user_inputs[row][col]
                notes = self.game_board.get_notes(row, col)
                cell = self.cell_inputs[row][col]
                if value:
                    cell.set_value(str(value))
                    if str(value) != self.game_board.get_correct_value(row, col):
                        cell.highlight("wrong")
                        cell.set_tooltip_text(_("Wrong"))
                cell.update_notes(notes)

    def build_grid(self):
        # Clear previous children from the container
        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)

        # Parent grid (3x3) holding 9 blocks
        parent_grid = Gtk.Grid(
            row_spacing=10,
            column_spacing=10,
            column_homogeneous=True,
            row_homogeneous=True,
        )
        parent_grid.set_name("sudoku-parent-grid")

        # Prepare 9 block grids (3x3 each)
        blocks = [[None for _ in range(3)] for _ in range(3)]
        for block_row in range(3):
            for block_col in range(3):
                block = Gtk.Grid(
                    row_spacing=4,
                    column_spacing=4,
                    column_homogeneous=True,
                    row_homogeneous=True,
                )
                block.get_style_context().add_class("sudoku-block")
                blocks[block_row][block_col] = block
                parent_grid.attach(block, block_col, block_row, 1, 1)

        # Initialize the 9x9 cell grid
        self.cell_inputs = [[None for _ in range(9)] for _ in range(9)]

        # Fill blocks with SudokuCell widgets
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                value = self.game_board.puzzle[row][col]
                editable = not self.game_board.is_clue(row, col)
                cell = SudokuCell(row, col, value, editable)

                # Gesture click controller
                gesture = Gtk.GestureClick.new()
                gesture.connect("pressed", self.on_cell_clicked, cell)
                cell.add_controller(gesture)

                # Keyboard input controller
                key_controller = Gtk.EventControllerKey()
                key_controller.connect("key-pressed", self.on_key_pressed, row, col)
                cell.add_controller(key_controller)

                self.cell_inputs[row][col] = cell

                # Determine block and cell's position inside block
                block_row = row // 3
                block_col = col // 3
                inner_row = row % 3
                inner_col = col % 3

                block = blocks[block_row][block_col]
                block.attach(cell, inner_col, inner_row, 1, 1)

        # Wrap grid in an AspectFrame to maintain square shape
        frame = Gtk.AspectFrame(ratio=1.0, obey_child=False)
        frame.set_hexpand(True)
        frame.set_vexpand(True)
        frame.set_halign(Gtk.Align.FILL)  # ensure fills horizontal space
        frame.set_valign(Gtk.Align.FILL)  # ensure fills vertical space
        frame.set_child(parent_grid)

        self.window.grid_container.append(frame)
        frame.show()

    def _focus_cell(self, row: int, col: int):
        self.cell_inputs[row][col].grab_focus()
        UIHelpers.highlight_related_cells(self.cell_inputs, row, col)

    def _clear_cell(self, cell: SudokuCell, clear_all: bool = False):
        row, col = cell.row, cell.col
        if clear_all:
            self._clear_cell_notes(cell)
            self._clear_cell_value(cell)
        elif self.pencil_mode:
            if len(self.game_board.get_notes(row, col)) > 0:
                self.game_board.get_notes(row, col).pop()
                cell.update_notes(self.game_board.get_notes(row, col))
        else:
            self._clear_cell_notes(cell)
            self._clear_cell_value(cell)
        self.game_board.save_to_file()

    def _clear_cell_notes(self, cell: SudokuCell):
        row, col = cell.row, cell.col
        self.game_board.clear_notes(row, col)
        cell.update_notes(set())

    def _clear_cell_value(self, cell: SudokuCell):
        row, col = cell.row, cell.col
        cell.set_value("")
        cell.set_tooltip_text("")
        UIHelpers.clear_feedback_classes(cell.get_style_context())
        self.game_board.set_input(row, col, None)

    def _fill_cell(self, cell: SudokuCell, number: str):
        UIHelpers.clear_conflicts(self.conflict_cells)
        row, col = cell.row, cell.col

        if self.pencil_mode:
            if number in self.game_board.get_notes(row, col):
                self.game_board.remove_note(row, col, number)
            else:
                self.game_board.add_note(row, col, number)
            cell.update_notes(self.game_board.get_notes(row, col))
            return

        cell.set_value(number)
        self.game_board.set_input(row, col, number)
        self.game_board.save_to_file()

        correct = self.game_board.get_correct_value(row, col)
        context = cell.get_style_context()
        UIHelpers.clear_feedback_classes(context)
        UIHelpers.specify_cell_correctness(
            cell, number, correct, self.conflict_cells, self.cell_inputs
        )

        if self.game_board.is_solved():
            self._show_puzzle_finished_dialog()

    def _show_popover(self, cell: SudokuCell):
        popover = Gtk.Popover()
        popover.set_has_arrow(False)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_parent(cell)
        grid = Gtk.Grid(row_spacing=5, column_spacing=5)
        popover.set_child(grid)

        num_buttons = {}
        for i in range(1, 10):
            b = UIHelpers.create_number_button(
                str(i), self.on_number_selected, cell, popover
            )
            grid.attach(b, (i - 1) % 3, (i - 1) // 3, 1, 1)
            num_buttons[str(i)] = b

        clear_button = Gtk.Button(label=_("Clear Cell"))
        clear_button.set_size_request(40 * 3 + 10, 40)
        clear_button.connect("clicked", self.on_clear_selected, cell, popover)
        grid.attach(clear_button, 0, 3, 3, 1)

        def on_key_pressed(controller, keyval, keycode, state):
            if keyval in self.key_map and (num := self.key_map[keyval]) in num_buttons:
                num_buttons[num].emit("clicked")
                return True
            elif keyval in self.remove_cell_keybindings:
                clear_button.emit("clicked")
                return True
            return False

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", on_key_pressed)
        grid.add_controller(key_controller)

        grid.set_focus_on_click(True)
        grid.grab_focus()
        popover.show()

    def on_cell_clicked(self, gesture, n_press, x: int, y: int, cell: SudokuCell):
        UIHelpers.highlight_related_cells(self.cell_inputs, cell.row, cell.col)
        if cell.editable and n_press == 1:
            self._show_popover(cell)
        else:
            cell.grab_focus()

    def on_key_pressed(self, controller, keyval, keycode, state, row: int, col: int):
        # Left and right gets needs to be swapped in RTL as whole board is flipped
        direction = self.window.get_direction()
        is_rtl = direction == Gtk.TextDirection.RTL

        directions = {
            Gdk.KEY_Up: (-1, 0),
            Gdk.KEY_Down: (1, 0),
            Gdk.KEY_Left: (0, 1 if is_rtl else -1),
            Gdk.KEY_Right: (0, -1 if is_rtl else 1),
        }

        ctrl_pressed = state & Gdk.ModifierType.CONTROL_MASK

        if keyval in directions:
            d_row, d_col = directions[keyval]
            if ctrl_pressed:
                d_row *= 3
                d_col *= 3
            new_row, new_col = row + d_row, col + d_col
            if 0 <= new_row < 9 and 0 <= new_col < 9:
                self._focus_cell(new_row, new_col)
            else:
                return False
            return True

        cell = self.cell_inputs[row][col]
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and cell.editable:
            self._show_popover(cell)
            return True

        if keyval in self.key_map and cell.editable:
            self._fill_cell(cell, self.key_map[keyval])
            return True

        if keyval in self.remove_cell_keybindings and cell.editable:
            self._clear_cell(cell, clear_all=(keyval == Gdk.KEY_Delete))
            return True

        return False

    def on_number_selected(self, num_button: Gtk.Button, cell: SudokuCell, popover):
        number = num_button.get_label()
        self._fill_cell(cell, number)
        popover.popdown()

    def on_clear_selected(self, clear_button, cell: SudokuCell, popover):
        self._clear_cell(cell)
        popover.popdown()

    def on_pencil_toggled(self, button: Gtk.ToggleButton):
        self.pencil_mode = button.get_active()
        logging.info(
            "Pencil Mode is now ON" if self.pencil_mode else "Pencil mode is now OFF"
        )

    def on_pencil_action_toggled(self, action, value):
        new_state = not action.get_state().get_boolean()
        action.set_state(GLib.Variant.new_boolean(new_state))
        self.window.pencil_toggle_button.set_active(new_state)

    def on_back_to_menu(self, action, parameter):
        self.window.continue_button.set_sensitive(GameBoard.has_saved_game())
        self.window.stack.set_visible_child(self.window.main_menu_box)
        self.window.sudoku_window_title.set_subtitle("")

    def _show_puzzle_finished_dialog(self):
        self.window.pencil_toggle_button.set_visible(False)

        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)

        self.window.stack.set_visible_child(self.window.finished_page)

    def on_back_to_menu_clicked_after_finish(self, button):
        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)
        self.window.grid_container.append(self.window.game_view_box)
        self.window.sudoku_window_title.set_subtitle("")
        self.window.stack.set_visible_child(self.window.main_menu_box)
        self.window.continue_button.set_sensitive(GameBoard.has_saved_game())
