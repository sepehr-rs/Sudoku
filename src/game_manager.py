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
"""Game Manager module to control game logic."""
import threading
from gettext import gettext as _

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, GLib, Gtk

from . import GameBoard, SudokuCell
from .finished_page import FinishedPage
from .ui_helpers import UIHelpers


class GameManager:
    """Main game manager to control game logic."""

    def __init__(self, window):
        self.window = window
        self.game_board = None
        self.cell_inputs = [[None for _ in range(9)] for _ in range(9)]
        self.blocks = [[None for _ in range(3)] for _ in range(3)]
        self.parent_grid = None
        self.game_running = False
        self.pencil_mode = False
        self.conflict_cells = []

        # Key bindings
        self.key_map = {
            Gdk.KEY_1: "1",
            Gdk.KEY_2: "2",
            Gdk.KEY_3: "3",
            Gdk.KEY_4: "4",
            Gdk.KEY_5: "5",
            Gdk.KEY_6: "6",
            Gdk.KEY_7: "7",
            Gdk.KEY_8: "8",
            Gdk.KEY_9: "9",
            Gdk.KEY_KP_1: "1",
            Gdk.KEY_KP_2: "2",
            Gdk.KEY_KP_3: "3",
            Gdk.KEY_KP_4: "4",
            Gdk.KEY_KP_5: "5",
            Gdk.KEY_KP_6: "6",
            Gdk.KEY_KP_7: "7",
            Gdk.KEY_KP_8: "8",
            Gdk.KEY_KP_9: "9",
        }

        self.remove_cell_keybindings = [
            Gdk.KEY_Delete,
            Gdk.KEY_KP_Delete,
            Gdk.KEY_BackSpace,
            Gdk.KEY_0,
            Gdk.KEY_KP_0,
        ]

    def new_game(self, difficulty):
        """Start a new game with the given difficulty."""

        def generate_and_display():
            try:
                self.game_board = GameBoard(difficulty)
                GLib.idle_add(self._setup_grid)
            except Exception as e:
                print(f"Error generating game: {e}")
                GLib.idle_add(self.window.set_visible_child_name, "start")

        # Show loading screen
        self.window.set_visible_child_name("loading")
        # Generate game in a separate thread
        threading.Thread(target=generate_and_display, daemon=True).start()

    def continue_game(self):
        """Continue a saved game."""
        try:
            self.game_board = GameBoard.load_from_file()
            self._setup_grid()
        except Exception as e:
            print(f"Error loading game: {e}")
            self.window.set_visible_child_name("start")

    def _setup_grid(self):
        """Setup the Sudoku grid."""
        if self.parent_grid:
            self.window.grid_container.remove(self.parent_grid)

        self.parent_grid = Gtk.Grid(
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            row_spacing=10,
            column_spacing=10,
        )

        frame = Gtk.Frame(css_classes=["sudoku-grid"])
        frame.set_child(self.parent_grid)
        self.window.grid_container.set_child(frame)

        # Create 3x3 blocks
        for block_row in range(3):
            for block_col in range(3):
                block_grid = Gtk.Grid(row_spacing=4, column_spacing=4)
                block_grid.add_css_class("sudoku-block")
                self.blocks[block_row][block_col] = block_grid
                self.parent_grid.attach(block_grid, block_col, block_row, 1, 1)

                # Create cells within each block
                for cell_row in range(3):
                    for cell_col in range(3):
                        row = block_row * 3 + cell_row
                        col = block_col * 3 + cell_col

                        value = self.game_board.get_current_value(row, col)
                        correct_value = self.game_board.get_correct_value(row, col)
                        editable = self.game_board.is_editable(row, col)
                        notes = self.game_board.get_notes(row, col)

                        cell = SudokuCell(
                            row,
                            col,
                            value,
                            correct_value,
                            editable,
                            self.on_cell_clicked,
                            self.on_key_pressed,
                            notes,
                        )
                        self.cell_inputs[row][col] = cell
                        block_grid.attach(cell, cell_col, cell_row, 1, 1)

        self.game_running = True
        self.window.set_visible_child_name("game")

        # Clear any previous highlights and set focus
        UIHelpers.clear_highlights(self.cell_inputs, "highlight")
        if self.cell_inputs[0][0].editable:
            self.cell_inputs[0][0].grab_focus()
        else:
            for row in range(9):
                for col in range(9):
                    if self.cell_inputs[row][col].editable:
                        self.cell_inputs[row][col].grab_focus()
                        return

    def _show_puzzle_finished_dialog(self):
        """Show puzzle finished dialog."""
        self.game_running = False
        self.game_board.delete_saved_game()

        self.window.set_visible_child_name("finished")
        finished_page = self.window.get_visible_child()
        if isinstance(finished_page, FinishedPage):
            time_taken = self.game_board.get_time_taken()
            finished_page.set_time_taken(time_taken)

    def on_pencil_toggled(self, button):
        """Handle pencil mode toggle."""
        self.pencil_mode = button.get_active()

    def on_number_selected(self, button, cell: SudokuCell, popover, mouse_button):
        """Handle number selection from popover."""
        popover.hide()
        number = int(button.get_label())
        row, col = cell.row, cell.col

        if not cell.editable:
            return

        # Determine if we're in note mode
        ctrl_is_pressed = mouse_button == 3  # Right click
        in_note_mode = self.pencil_mode or ctrl_is_pressed

        if in_note_mode:
            if number in self.game_board.get_notes(row, col):
                self.game_board.remove_note(row, col, number)
            else:
                self.game_board.add_note(row, col, number)
            cell.update_notes(self.game_board.get_notes(row, col))
            self.game_board.save_to_file()
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

    def on_clear_selected(self, button, cell: SudokuCell, popover):
        """Handle clear cell selection."""
        popover.hide()
        if not cell.editable:
            return

        row, col = cell.row, cell.col
        self.game_board.clear_cell(row, col)
        cell.set_value(0)
        cell.update_notes([])
        self.game_board.save_to_file()

    def on_number_input(self, cell: SudokuCell, number: int):
        """Handle number input."""
        row, col = cell.row, cell.col

        if not cell.editable:
            return

        # Check if Ctrl is pressed for note mode
        # This is a fallback for direct keyboard input
        ctrl_is_pressed = False  # You might need to track this separately

        if self.pencil_mode or ctrl_is_pressed:
            if number in self.game_board.get_notes(row, col):
                self.game_board.remove_note(row, col, number)
            else:
                self.game_board.add_note(row, col, number)
            cell.update_notes(self.game_board.get_notes(row, col))
            self.game_board.save_to_file()
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

    def _show_popover(self, cell: SudokuCell, mouse_button=None):
        popover = Gtk.Popover()
        popover.set_has_arrow(False)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_parent(cell)
        
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.set_margin_top(8)
        main_box.set_margin_bottom(8)
        main_box.set_margin_start(8)
        main_box.set_margin_end(8)
        popover.set_child(main_box)

        # Determine mode
        ctrl_is_pressed = mouse_button == 3  # Right click
        in_note_mode = self.pencil_mode or ctrl_is_pressed

        # Add header with mode indication
        if in_note_mode:
            header_label = Gtk.Label(label=_("Add Note:"))
            header_label.add_css_class("caption-heading")
            header_label.add_css_class("note-mode-header")
            header_label.set_halign(Gtk.Align.START)
            main_box.append(header_label)
            
            # Add CSS class to popover for styling
            popover.add_css_class("note-mode-popover")
        else:
            header_label = Gtk.Label(label=_("Add Number:"))
            header_label.add_css_class("caption-heading")
            header_label.add_css_class("number-mode-header")
            header_label.set_halign(Gtk.Align.START)
            main_box.append(header_label)
            
            # Add CSS class to popover for styling
            popover.add_css_class("number-mode-popover")

        # Number grid
        grid = Gtk.Grid(row_spacing=5, column_spacing=5)
        main_box.append(grid)

        num_buttons = {}
        for i in range(1, 10):
            b = UIHelpers.create_number_button(
                str(i), self.on_number_selected, cell, popover, mouse_button
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
        main_box.add_controller(key_controller)

        main_box.set_focus_on_click(True)
        main_box.grab_focus()
        popover.show()

    def on_cell_clicked(self, gesture, n_press, x: int, y: int, cell: SudokuCell):
        UIHelpers.highlight_related_cells(self.cell_inputs, cell.row, cell.col)
        if cell.editable and n_press == 1:
            self._show_popover(cell, gesture.get_current_button())
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
                # Jump to edge of 3x3 block
                block_row, block_col = row // 3, col // 3
                if d_row != 0:
                    new_row = (
                        block_row * 3 + (2 if d_row > 0 else 0)
                        if d_row > 0
                        else block_row * 3
                    )
                    new_row = max(0, min(8, new_row))
                else:
                    new_row = row

                if d_col != 0:
                    new_col = (
                        block_col * 3 + (2 if d_col > 0 else 0)
                        if d_col > 0
                        else block_col * 3
                    )
                    new_col = max(0, min(8, new_col))
                else:
                    new_col = col
            else:
                new_row = max(0, min(8, row + d_row))
                new_col = max(0, min(8, col + d_col))

            self.cell_inputs[new_row][new_col].grab_focus()
            UIHelpers.highlight_related_cells(self.cell_inputs, new_row, new_col)
            return True

        if keyval in self.key_map:
            number = int(self.key_map[keyval])
            cell = self.cell_inputs[row][col]
            self.on_number_input(cell, number)
            return True
        elif keyval in self.remove_cell_keybindings:
            cell = self.cell_inputs[row][col]
            if cell.editable:
                self.game_board.clear_cell(row, col)
                cell.set_value(0)
                cell.update_notes([])
                self.game_board.save_to_file()
            return True

        return False