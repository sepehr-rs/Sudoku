# sudoku_cell.py
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


class SudokuCell(Gtk.Button):
    """Individual Sudoku cell widget with main value and notes display."""

    def __init__(self, row: int, col: int, value: str, editable: bool):
        super().__init__()

        self.row = row
        self.col = col
        self._editable = editable
        self.compact_mode = False
        self._feedback_source_id = None
        self._setup_ui()
        self._setup_initial_state(value)

    def set_editable(self, editable: bool):
        """Enable or disable user editing of this cell."""
        self._editable = editable

    def is_editable(self) -> bool:
        return self._editable

    def do_clicked(self, *args):
        """Only trigger clicked if editable."""
        if self._editable:
            try:
                super().do_clicked(*args)
            except Exception:
                # If there's an error in the parent's do_clicked, handle gracefully
                pass
        else:
            # swallow the click (make it a no-op)
            return

    def _setup_ui(self):
        """Set up the Sudoku cell UI."""
        self.main_label = self._create_main_label()
        self.notes_grid = self._create_notes_grid()
        self.note_labels = {}

        overlay = self._create_overlay(self.main_label, self.notes_grid)
        self.set_child(overlay)
        self.set_focus_on_click(False)
        self.set_can_focus(True)
        self.get_style_context().add_class("sudoku-cell-button")

    def _create_main_label(self):
        return Gtk.Label(
            xalign=0.5,
            yalign=0.5,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            hexpand=True,
            vexpand=True,
        )

    def _create_notes_grid(self):
        grid = Gtk.Grid(
            row_spacing=0,
            column_spacing=0,
            column_homogeneous=True,
            row_homogeneous=True,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
        )
        return grid

    def _create_overlay(self, main_label, notes_grid):
        overlay = Gtk.Overlay()
        overlay.set_child(main_label)
        overlay.add_overlay(notes_grid)
        overlay.set_halign(Gtk.Align.FILL)
        overlay.set_valign(Gtk.Align.FILL)
        return overlay

    def _setup_initial_state(self, value: str):
        """Setup initial cell state based on value."""
        if value is not None:
            self.set_value(str(value))
            self.get_style_context().add_class("clue-cell")
            self.set_editable(False)
        else:
            self.set_value("")
            self.get_style_context().add_class("entry-cell")
            self.set_editable(True)

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
            size = max(8, 12 if not self.compact_mode else 8)
            note_label.set_size_request(size, size)
            note_label.set_halign(Gtk.Align.CENTER)
            note_label.set_valign(Gtk.Align.CENTER)

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

    def set_compact(self, compact: bool):
        if self.compact_mode != compact:
            self.compact_mode = compact
            size = 10 if compact else 40
            self.set_size_request(size, size)
            current_notes = set(self.note_labels.keys())
            self.update_notes(current_notes)

    def highlight(self, class_name: str):
        """Add a highlight class to the cell."""
        self.get_style_context().add_class(class_name)

    def remove_highlight(self, class_name: str):
        """Remove a highlight class from the cell."""
        self.get_style_context().remove_class(class_name)

    def start_feedback_timeout(self, callback, delay=3000):
        """Start (or replace) a feedback timeout safely."""

        # If one already exists, remove it
        if self._feedback_source_id is not None:
            GLib.source_remove(self._feedback_source_id)
            self._feedback_source_id = None

        def wrapped():
            # Clear ID before running callback
            self._feedback_source_id = None
            callback()
            return False  # ensure timeout runs only once

        self._feedback_source_id = GLib.timeout_add(delay, wrapped)

    def clear_feedback_timeout(self):
        if self._feedback_source_id is not None:
            GLib.source_remove(self._feedback_source_id)
            self._feedback_source_id = None

    def clear(self):
        """Clear the main value and all notes."""
        self.set_value("")
        self.update_notes(set())
        self.remove_highlight("wrong")
