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

import logging
import unicodedata
from typing import Any

from gi.repository import Gtk, Gdk, GLib  # pyright: ignore[reportAttributeAccessIssue]
from ...base.manager_base import ManagerBase
from ...base.preferences_manager import PreferencesManager
from .board import ClassicSudokuBoard
from .ui_helpers import ClassicUIHelpers
from .sudoku_cell import SudokuCell


class ClassicSudokuManager(ManagerBase):
    def __init__(self, window):
        super().__init__(window, ClassicSudokuBoard)
        self.key_map, self.remove_keys = ClassicUIHelpers.setup_key_mappings()
        self.ui_helpers = ClassicUIHelpers
        self.parent_grid = None
        self.blocks = []
        self._active_popover = None
        self._cell_popover = None
        self._last_popover_cell = None
        self._restore_focus_on_popover_close = False
        self.board_frame = None

    def _require_board(self, message: str):
        board = self.board
        if board is None:
            raise RuntimeError(message)
        return board

    def _get_cell_popover(self):
        if self._cell_popover is not None:
            return self._cell_popover

        if self.parent_grid is None:
            return None

        popover = Gtk.Popover(position=Gtk.PositionType.BOTTOM)
        popover.set_has_arrow(False)
        popover.set_name("sudoku-popover")
        popover.set_parent(self.parent_grid)
        popover.connect("closed", self._on_cell_popover_closed)
        self._cell_popover = popover
        return popover

    def _on_cell_popover_closed(self, popover):
        cell = getattr(self, "_last_popover_cell", None)
        restore = bool(getattr(self, "_restore_focus_on_popover_close", False))

        self._restore_focus_on_popover_close = False
        self._last_popover_cell = None
        if popover is getattr(self, "_active_popover", None):
            self._active_popover = None

        if not restore or cell is None:
            return

        def _restore_focus():
            cell.grab_focus()
            return False

        GLib.idle_add(_restore_focus)

    def _finish_start_game(self, board):
        self.board = board
        self.build_grid()
        self.window.stack.set_visible_child(self.window.game_scrolled_window)
        return False

    def _restore_game_state(self):
        board = self._require_board("Illegal state: no board for restore_game_state")
        size = board.rules.size
        for r in range(size):
            for c in range(size):
                value = board.user_inputs[r][c]
                notes = board.notes[r][c]
                cell = self.cell_inputs[r][c]
                if value:
                    cell.set_value(str(value))
                    correct_value = board.get_correct_value(r, c)
                    if str(value) != str(correct_value):
                        cell.highlight("wrong")
                if notes:
                    cell.update_notes(notes)

    def build_grid(self):
        """Build or rebuild the Sudoku grid in the UI."""
        board = self._require_board("Illegal state: cannot build grid without a board")
        self._clear_previous_grid()

        size = board.rules.size
        block_size = board.rules.block_size

        self.parent_grid = self._create_parent_grid()
        self.blocks = self._create_blocks(block_size)

        self.cell_inputs = self._create_cells(size, block_size)

        self.board_frame = self._wrap_in_aspect_frame(self.parent_grid)
        self.window.grid_container.append(self.board_frame)
        self.board_frame.show()

        self._reapply_compact_mode()
        self.window.grid_container.queue_allocate()

    def _clear_previous_grid(self):
        """Remove all children from the grid container."""
        self._popdown_active_popover()
        self._active_popover = None
        self._cell_popover = None

        if hasattr(self, "cell_inputs") and self.cell_inputs:
            for row in self.cell_inputs:
                for cell in row:
                    if cell:
                        cell.clear_feedback_timeout()

        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)

    def _create_parent_grid(self):
        """Create the top-level grid containing Sudoku blocks."""
        grid = Gtk.Grid(
            row_spacing=10,
            column_spacing=10,
            column_homogeneous=True,
            row_homogeneous=True,
        )
        grid.set_name("sudoku-parent-grid")
        return grid

    def _create_blocks(self, block_size):
        """Create and attach the NxN block grids to the parent grid."""
        if self.parent_grid is None:
            raise RuntimeError("Illegal state: no parent_grid for create_blocks")
        blocks = []
        for br in range(block_size):
            row_blocks = []
            for bc in range(block_size):
                block = Gtk.Grid(
                    row_spacing=4,
                    column_spacing=4,
                    column_homogeneous=True,
                    row_homogeneous=True,
                )
                block.get_style_context().add_class("sudoku-block")
                row_blocks.append(block)
                self.parent_grid.attach(block, bc, br, 1, 1)
            blocks.append(row_blocks)
        return blocks

    def _create_cells(self, size, block_size):
        """Create SudokuCell widgets, add controllers, and place into blocks."""
        board = self._require_board(
            "Illegal state: cannot create cells without a board"
        )
        cells: list[list[SudokuCell]] = []

        for r in range(size):
            row_cells: list[SudokuCell] = []
            for c in range(size):
                value = board.puzzle[r][c]
                editable = not board.is_clue(r, c)
                cell = SudokuCell(r, c, value, editable)

                self._attach_controllers(cell, r, c)
                row_cells.append(cell)

                br, bc = r // block_size, c // block_size
                inner_r, inner_c = r % block_size, c % block_size
                self.blocks[br][bc].attach(cell, inner_c, inner_r, 1, 1)

            cells.append(row_cells)

        return cells

    def _attach_controllers(self, cell, r, c):
        """Attach click and keyboard controllers to a cell."""
        gesture = Gtk.GestureClick.new()
        gesture.set_button(0)
        try:
            gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        except AttributeError:
            gesture.set_exclusive(True)
        gesture.connect("released", self.on_cell_clicked, cell)
        cell.add_controller(gesture)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed, r, c)
        cell.add_controller(key_controller)

    def _wrap_in_aspect_frame(self, child):
        """Wrap grid in an AspectFrame to maintain square shape."""
        frame = Gtk.AspectFrame(ratio=1.0, obey_child=False)
        frame.set_hexpand(True)
        frame.set_vexpand(True)
        frame.set_halign(Gtk.Align.FILL)
        frame.set_valign(Gtk.Align.FILL)
        frame.set_child(child)
        return frame

    def _reapply_compact_mode(self):
        """Reapply compact layout mode if needed."""
        compact_mode_active, small_mode_active = False, False
        bp = getattr(self.window, "bp_bin", None)

        if bp and bp.get_style_context().has_class("compact-mode"):
            compact_mode_active = True
        if bp and bp.get_style_context().has_class("small-mode"):
            small_mode_active = True

        self.window._apply_compact(
            any([compact_mode_active, small_mode_active]),
            "compact" if compact_mode_active else "small",
        )

    def _focus_cell(self, row: int, col: int):
        board = self._require_board("Illegal state: cannot focus cell without a board")
        self.cell_inputs[row][col].grab_focus()
        ClassicUIHelpers.highlight_related_cells(
            self.cell_inputs, row, col, board.rules.block_size
        )

    def get_ui_helpers(self):
        return ClassicUIHelpers

    def _fill_cell(self, cell: SudokuCell, number: str, ctrl_is_pressed=False):
        board = self._require_board("Illegal state: cannot fill cell without a board")
        ClassicUIHelpers.clear_conflicts(self.conflict_cells)

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

            if pref_enabled and board.has_conflict(r, c, number):
                new_conflicts = ClassicUIHelpers.highlight_conflicts(
                    self.cell_inputs, r, c, number, board.rules.block_size
                )
                self.conflict_cells.extend(new_conflicts)
                cell.start_feedback_timeout(self._clear_conflicts, delay=2000)
                return

            board.toggle_note(r, c, number)
            cell.update_notes(board.get_notes(r, c))
            board.save_to_file()
            return

        cell.set_value(number)
        board.set_input(r, c, number)
        board.save_to_file()

        self.on_cell_filled(cell, number)

        if board.is_solved():
            self._show_puzzle_finished_dialog()

    def _clear_cell(self, cell: SudokuCell, clear_all=False):
        board = self._require_board("Illegal state: cannot clear cell without a board")
        r, c = cell.row, cell.col
        if not cell.is_editable():
            return
        if clear_all:
            board.clear_input(r, c)
            cell.clear()
            board.notes[r][c].clear()
            cell.update_notes(set())

        elif self.pencil_mode:
            current_notes = board.get_notes(r, c)
            if current_notes:
                # remove the last note numerically
                last_note = sorted(current_notes, key=int)[-1]
                board.toggle_note(r, c, last_note)
                cell.update_notes(board.get_notes(r, c))

        else:
            board.clear_input(r, c)
            cell.clear()
            board.notes[r][c].clear()
            cell.update_notes(set())
        board.save_to_file()

    def _popdown_active_popover(self):
        popover: Any = getattr(self, "_active_popover", None)
        if popover is None:
            return

        self._restore_focus_on_popover_close = False
        try:
            if popover.get_visible():
                popover.popdown()
        except AttributeError:
            logging.debug("Popover popdown skipped (attribute missing)", exc_info=True)

    def _gesture_get_button(self, gesture):
        try:
            return gesture.get_current_button()
        except AttributeError:
            return None

    def _gesture_get_state(self, gesture):
        try:
            return gesture.get_current_event_state()
        except AttributeError:
            return 0

    def _ignore_click_due_to_modifiers(self, button, state):
        if button == 1 and (state & Gdk.ModifierType.BUTTON3_MASK):
            return True
        if button == 3 and (state & Gdk.ModifierType.BUTTON1_MASK):
            return True
        return False

    def _show_popover_for_editable_cell(self, cell, button, n_press):
        def _deferred_show():
            self._show_popover(cell, mouse_button=button)
            return False

        GLib.idle_add(_deferred_show)

    def _show_popover(self, cell: SudokuCell, mouse_button=None):
        self._restore_focus_on_popover_close = False
        self._popdown_active_popover()

        popover = self._get_cell_popover()
        if popover is None or self.parent_grid is None:
            return None

        try:
            coords = cell.translate_coordinates(self.parent_grid, 0, 0)
        except (AttributeError, TypeError):
            coords = None
        if coords is None:
            alloc = cell.get_allocation()
            x, y = alloc.x, alloc.y
            w, h = alloc.width, alloc.height
        else:
            x, y = coords
            alloc = cell.get_allocation()
            w, h = alloc.width, alloc.height

        try:
            rect = Gdk.Rectangle()
            rect.x = int(x)
            rect.y = int(y)
            rect.width = int(w)
            rect.height = int(h)
        except TypeError:
            rect = Gdk.Rectangle(int(x), int(y), int(w), int(h))

        try:
            popover.set_pointing_to(rect)
        except (AttributeError, TypeError):
            logging.debug("Failed to set popover pointing rect", exc_info=True)

        popover = ClassicUIHelpers.show_number_popover(
            cell,
            mouse_button,
            self.on_number_selected,
            self.on_clear_selected,
            popover=popover,
            pencil_mode=self.pencil_mode,
            key_map=self.key_map,
            remove_keys=self.remove_keys,
        )

        self._last_popover_cell = cell
        self._restore_focus_on_popover_close = True
        self._active_popover = popover
        return popover

    def on_cell_clicked(self, gesture, n_press, x, y, cell: SudokuCell):
        board = self._require_board(
            "Illegal state: received cell click without a board"
        )

        button = self._gesture_get_button(gesture)
        if button not in (1, 3):
            return

        state = self._gesture_get_state(gesture)
        if self._ignore_click_due_to_modifiers(button, state):
            return

        self.ui_helpers.highlight_related_cells(
            self.cell_inputs, cell.row, cell.col, board.rules.block_size
        )

        if cell.is_editable() and n_press == 1:
            self._show_popover_for_editable_cell(cell, button, n_press)
        else:
            cell.grab_focus()

    def on_key_pressed(self, controller, keyval, keycode, state, row, col):
        self._require_board("Illegal state: received key press without a board")
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)

        if self._handle_arrow_keys(keyval, ctrl, row, col):
            return True

        if self._handle_number_keys(keyval, ctrl, row, col):
            return True

        if self._handle_unicode_digit(keyval, ctrl, row, col):
            return True

        if self._handle_enter_key(keyval, row, col):
            return True

        if self._handle_remove_keys(keyval, row, col):
            return True

        return False

    def _handle_arrow_keys(self, keyval, ctrl, row, col):
        board = self._require_board("Illegal state: no board for arrow key handling")
        direction = self.window.get_direction()
        is_rtl = direction == Gtk.TextDirection.RTL
        directions = {
            Gdk.KEY_Up: (-1, 0),
            Gdk.KEY_Down: (1, 0),
            Gdk.KEY_Left: (0, -1) if not is_rtl else (0, 1),
            Gdk.KEY_Right: (0, 1) if not is_rtl else (0, -1),
        }
        if keyval not in directions:
            return False

        dr, dc = directions[keyval]
        if ctrl:
            dr *= 3
            dc *= 3
        new_r, new_c = row + dr, col + dc
        if 0 <= new_r < board.rules.size and 0 <= new_c < board.rules.size:
            self._focus_cell(new_r, new_c)
        return True

    def _handle_number_keys(self, keyval, ctrl, row, col):
        if keyval not in self.key_map:
            return False
        num = self.key_map[keyval]
        if num and num != 0:
            self._fill_cell(self.cell_inputs[row][col], num, ctrl_is_pressed=ctrl)
            return True
        return False

    def _handle_unicode_digit(self, keyval, ctrl, row, col):
        uni = Gdk.keyval_to_unicode(keyval)
        if uni == 0:
            return False
        try:
            digit = unicodedata.digit(chr(uni))
            if 1 <= digit <= 9:
                self._fill_cell(
                    self.cell_inputs[row][col], str(digit), ctrl_is_pressed=ctrl
                )
                return True
        except (ValueError, TypeError):
            return False
        return False

    def _handle_enter_key(self, keyval, row, col):
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self._show_popover(self.cell_inputs[row][col])
            return True
        return False

    def _handle_remove_keys(self, keyval, row, col):
        if keyval not in self.remove_keys:
            return False
        self._clear_cell(
            self.cell_inputs[row][col], clear_all=(keyval == Gdk.KEY_Delete)
        )
        return True

    def on_number_selected(
        self, num_button: Gtk.Button, cell: SudokuCell, popover, mouse_button
    ):
        number = num_button.get_label()
        self._fill_cell(cell, number, ctrl_is_pressed=(mouse_button == 3))
        if not self.pencil_mode and mouse_button != 3:
            self._restore_focus_on_popover_close = False
            popover.popdown()

    def on_clear_selected(self, clear_button, cell: SudokuCell, popover):
        self._clear_cell(cell)
        self._restore_focus_on_popover_close = False
        popover.popdown()

    def on_pencil_toggled(self, button: Gtk.ToggleButton):
        self.pencil_mode = button.get_active()
        logging.info(
            "Pencil Mode is now ON" if self.pencil_mode else "Pencil Mode is now OFF"
        )

    def _show_puzzle_finished_dialog(self):
        self._popdown_active_popover()
        self._active_popover = None
        self._cell_popover = None

        self.window.pencil_toggle_button.set_visible(False)
        if hasattr(self, "cell_inputs") and self.cell_inputs:
            for row in self.cell_inputs:
                for cell in row:
                    if cell:
                        cell.clear_feedback_timeout()
        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)
        self.window.stack.set_visible_child(self.window.finished_page)

    def on_cell_filled(self, cell, number: str):
        """Called when a cell is filled with a number."""
        board = self._require_board("Illegal state: no board for on_cell_filled")
        prefs = PreferencesManager.get_preferences()
        if prefs is None:
            raise RuntimeError("Illegal state: preferences unavailable")
        casual_mode = prefs.general("casual_mode")[1]
        correct_value = board.get_correct_value(cell.row, cell.col)
        # TODO: Add auto check for the board when casual_mdoe is turned off
        self._clear_feedback(cell)
        if casual_mode:
            if str(number) == str(correct_value):
                self._handle_correct_input(cell)
            else:
                self._handle_wrong_input(cell, number)
            return

        # non-casual mode: always check conflicts
        new_conflicts = ClassicUIHelpers.highlight_conflicts(
            self.cell_inputs, cell.row, cell.col, number, 3
        )
        if new_conflicts:
            self._handle_wrong_input(cell, number, new_conflicts)

    def _clear_feedback(self, cell):
        """Remove existing highlights, tooltips, and timeouts for a cell."""
        cell.clear_feedback_timeout()
        cell.remove_highlight("correct")
        cell.remove_highlight("wrong")
        cell.set_tooltip_text("")

    def _handle_correct_input(self, cell):
        """Handle behavior when the user enters the correct number."""
        cell.set_editable(False)
        cell.highlight("correct")
        cell.set_tooltip_text("Correct")
        cell.start_feedback_timeout(lambda: self._clear_correct_feedback(cell))

    def _clear_correct_feedback(self, cell):
        """Remove correct highlight and tooltip."""
        cell.remove_highlight("correct")
        cell.set_tooltip_text("")
        return False

    def _handle_wrong_input(self, cell, number: str, conflicts=None):
        """Handle behavior when the user enters a wrong number."""
        cell.highlight("wrong")
        cell.set_tooltip_text("Wrong")

        conflicts = conflicts or ClassicUIHelpers.highlight_conflicts(
            self.cell_inputs, cell.row, cell.col, number, 3
        )
        self.conflict_cells.extend(conflicts)

        cell.start_feedback_timeout(self._clear_conflicts)

    def _clear_conflicts(self):
        """Clear conflicts highlight after timeout."""
        ClassicUIHelpers.clear_conflicts(self.conflict_cells)
        return False
