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
from gettext import gettext as _

from ...base.ui_helpers import UIHelpers
from ...base.preferences_manager import PreferencesManager


class ClassicUIHelpers(UIHelpers):
    """UI helpers specifically for Classic Sudoku."""

    @staticmethod
    def create_number_button(label: str, callback, *args):
        """Create a Sudoku number button with consistent styling."""
        button = Gtk.Button(label=label)
        button.set_size_request(40, 40)
        button.connect("clicked", callback, *args)
        return button

    @staticmethod
    def setup_key_mappings():
        """Map keyboard keys to Sudoku numbers 1–9."""
        key_map = {getattr(Gdk, f"KEY_{i}"): str(i) for i in range(1, 10)}
        key_map.update({getattr(Gdk, f"KEY_KP_{i}"): str(i) for i in range(1, 10)})
        remove_keys = (Gdk.KEY_BackSpace, Gdk.KEY_Delete, Gdk.KEY_KP_Delete)
        return key_map, remove_keys

    @staticmethod
    def highlight_related_cells(cells, row: int, col: int, block_size: int):
        """Highlight row, column, block, or same-value cells."""
        ClassicUIHelpers.clear_highlights(cells, "highlight")
        prefs = PreferencesManager.get_preferences()

        selected_value = cells[row][col].get_value()

        if not selected_value:
            ClassicUIHelpers._highlight_empty_cell_related(
                cells, row, col, block_size, prefs
            )
        else:
            ClassicUIHelpers._highlight_same_value(cells, selected_value, prefs)

    @staticmethod
    def _highlight_empty_cell_related(
        cells, row: int, col: int, block_size: int, prefs
    ):
        """Highlight row, column, and block when the cell is empty."""
        size = len(cells)

        if prefs.general("highlight_row"):
            for i in range(size):
                ClassicUIHelpers.highlight_cell(cells, row, i, "highlight")

        if prefs.general("highlight_column"):
            for i in range(size):
                ClassicUIHelpers.highlight_cell(cells, i, col, "highlight")

        if prefs.variant("highlight_block"):
            block_row_start = (row // block_size) * block_size
            block_col_start = (col // block_size) * block_size
            for r in range(block_row_start, block_row_start + block_size):
                for c in range(block_col_start, block_col_start + block_size):
                    ClassicUIHelpers.highlight_cell(cells, r, c, "highlight")

    @staticmethod
    def _highlight_same_value(cells, selected_value: int, prefs):
        """Highlight all cells containing the same value."""
        if not prefs.variant("highlight_related_cells"):
            return

        size = len(cells)
        for r in range(size):
            for c in range(size):
                if cells[r][c].get_value() == selected_value:
                    ClassicUIHelpers.highlight_cell(cells, r, c, "highlight")

    @staticmethod
    def clear_feedback_classes(context: Gtk.StyleContext):
        """Remove correctness classes from a style context."""
        context.remove_class("correct")
        context.remove_class("wrong")

    @staticmethod
    def show_number_popover(
        cell,
        mouse_button,
        on_number_selected,
        on_clear_selected,
        pencil_mode=False,
        key_map=None,
        remove_keys=None,
    ):
        """Show the number selection popover for a Sudoku cell."""
        popover = Gtk.Popover(has_arrow=False, position=Gtk.PositionType.BOTTOM)
        popover.set_parent(cell)

        grid = Gtk.Grid(row_spacing=5, column_spacing=5)
        popover.set_child(grid)
        num_buttons = ClassicUIHelpers._add_number_buttons(
            grid, on_number_selected, cell, popover, mouse_button
        )
        clear_button = ClassicUIHelpers._add_action_buttons(
            grid, cell, popover, on_clear_selected, pencil_mode, mouse_button
        )
        key_map, remove_keys = (
            ClassicUIHelpers.setup_key_mappings()
            if key_map is None or remove_keys is None
            else (key_map, remove_keys)
        )
        ClassicUIHelpers._attach_key_controller(
            grid, num_buttons, clear_button, key_map, remove_keys
        )
        grid.set_focus_on_click(True)
        grid.grab_focus()
        popover.set_name("sudoku-popover")
        popover.show()

        getattr(cell, "set_popover", lambda p: None)(popover)

        return popover

    @staticmethod
    def _add_number_buttons(grid, on_number_selected, cell, popover, mouse_button):
        """Create 1–9 number buttons inside the popover grid."""
        num_buttons = {}
        for i in range(1, 10):
            b = ClassicUIHelpers.create_number_button(
                str(i), on_number_selected, cell, popover, mouse_button
            )
            grid.attach(b, (i - 1) % 3, (i - 1) // 3, 1, 1)
            num_buttons[str(i)] = b
        return num_buttons

    @staticmethod
    def _add_action_buttons(
        grid, cell, popover, on_clear_selected, pencil_mode, mouse_button
    ):
        """Create Clear (and optionally Done) buttons."""
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        grid.attach(button_box, 0, 3, 3, 1)

        clear_button = Gtk.Button(label=_("Clear"))
        clear_button.set_size_request(-1, 40)
        clear_button.set_hexpand(True)
        clear_button.set_tooltip_text(_("Clear Cell (Del/Backspace)"))
        clear_button.connect("clicked", on_clear_selected, cell, popover)
        button_box.append(clear_button)

        if pencil_mode or mouse_button == 3:
            done_button = Gtk.Button(label=_("Done"))
            done_button.set_size_request(-1, 40)
            done_button.set_hexpand(True)
            done_button.set_tooltip_text(_("Finish Editing Cell"))
            done_button.connect("clicked", lambda _: popover.popdown())
            button_box.append(done_button)

        return clear_button

    @staticmethod
    def _attach_key_controller(grid, num_buttons, clear_button, key_map, remove_keys):
        """Wire up keyboard input for numbers and clearing."""

        def on_key_pressed(controller, keyval, keycode, state):
            if keyval in key_map and (num := key_map[keyval]) in num_buttons:
                num_buttons[num].emit("clicked")
                return True
            elif keyval in remove_keys:
                clear_button.emit("clicked")
                return True
            return False

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", on_key_pressed)
        grid.add_controller(key_controller)
