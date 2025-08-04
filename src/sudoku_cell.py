# sudoku_cell.py
#
# Copyright 2025 sepehr
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

from gi.repository import Gtk

from .game_board import BLOCK_SIZE


class SudokuCell(Gtk.Button):
    """Individual Sudoku cell widget with main value and notes display."""

    def __init__(self, row: int, col: int, value: str, editable: bool):
        super().__init__()

        self.row = row
        self.col = col
        self.editable = editable

        self._setup_ui()
        self._setup_initial_state(value)
        self._add_border_classes()

    def _setup_ui(self):
        """Setup the UI components."""
        self.main_label = Gtk.Label()
        self.notes_grid = Gtk.Grid(
            row_spacing=0,
            column_spacing=0,
            column_homogeneous=True,
            row_homogeneous=True,
        )
        self.notes_grid.get_style_context().add_class("notes-grid")

        self.note_labels = {}  # Store label widgets by number

        # Overlay both main and note labels
        overlay = Gtk.Overlay()
        overlay.set_child(self.main_label)
        overlay.add_overlay(self.notes_grid)

        self.set_child(overlay)

        # Configure button properties
        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.FILL)
        self.set_can_focus(True)
        self.get_style_context().add_class("sudoku-cell-button")

    def _setup_initial_state(self, value: str):
        """Setup initial cell state based on value."""
        if value is not None:
            self.set_value(str(value))
            self.get_style_context().add_class("clue-cell")
        else:
            self.set_value("")
            self.get_style_context().add_class("entry-cell")

        self.update_display()

    def set_value(self, value: str):
        """Set the main value of the cell."""
        self.main_label.set_text(value)
        self.update_display()

    def get_value(self) -> str:
        """Get the main value of the cell."""
        return self.main_label.get_text()

    def update_notes(self, notes: set):
        """Update the notes display."""
        # Clear old labels
        for child in list(self.notes_grid):
            self.notes_grid.remove(child)

        self.note_labels.clear()

        if not notes or self.main_label.get_text():
            return

        sorted_notes = sorted(notes, key=int)

        for n in sorted_notes:
            note_label = Gtk.Label(label=n)
            note_label.get_style_context().add_class("note-cell-label")
            self.note_labels[n] = note_label

            index = int(n) - 1
            row = index // 3
            col = index % 3

            self.notes_grid.attach(note_label, col, row, 1, 1)

        self.notes_grid.show()

    def update_display(self):
        """Update the display state."""
        if self.main_label.get_text():
            for label in self.note_labels.values():
                label.set_text("")
        self.notes_grid.set_halign(Gtk.Align.FILL)
        self.notes_grid.set_valign(Gtk.Align.FILL)

    def highlight(self, class_name: str):
        """Add a highlight class to the cell."""
        self.get_style_context().add_class(class_name)

    def unhighlight(self, class_name: str):
        """Remove a highlight class from the cell."""
        self.get_style_context().remove_class(class_name)

    def _add_border_classes(self):
        """Add border classes based on cell position."""
        context = self.get_style_context()
        if self.row % BLOCK_SIZE == 0:
            context.add_class("top-border")
        if self.col % BLOCK_SIZE == 0:
            context.add_class("left-border")
        if (self.col + 1) % BLOCK_SIZE == 0:
            context.add_class("right-border")
        if (self.row + 1) % BLOCK_SIZE == 0:
            context.add_class("bottom-border")
