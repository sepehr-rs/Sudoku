# src/shared/sudoku_cell.py
# Copyright 2026 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk, GLib  # pyright: ignore[reportAttributeAccessIssue]
from ..core import SUDOKU_CONSTANTS
from __future__ import annotations

class SudokuCellNotesManagement:
    """
    Handles SudokuCell pencil notes and their UI
    """

    def __init__(self, cell: SudokuCell):
        self.cell = cell
        self.notes_grid = self.create_notes_grid()
        self.note_labels = {}

    def create_notes_label(self, compact_mode, number):
        note_label = Gtk.Label(label=str(number))
        note_label.get_style_context().add_class("note-cell-label")
        size = max(8, 12 if not compact_mode else 8)
        note_label.set_size_request(size, size)
        note_label.set_halign(Gtk.Align.CENTER)
        note_label.set_valign(Gtk.Align.CENTER)
        
        return note_label

    def create_notes_grid(self):
        """Create and return a homogeneous GTK grid for pencil notes."""
        grid = Gtk.Grid(
            row_spacing=0,
            column_spacing=0,
            column_homogeneous=True,
            row_homogeneous=True,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
        )
        return grid

    def update_notes(
        self,
        notes: set[str],
        compact_mode: bool,
        main_label:str,
    ):
        """Update the notes display."""
        # Clear old labels
        for child in list(self.notes_grid):
            self.notes_grid.remove(child)
        self.note_labels.clear()
        if not notes or main_label.get_text():
            return
        sorted_notes = sorted(notes, key=int)
        for n in sorted_notes:
            note_label = self.create_notes_label(compact_mode, n)
            self.note_labels[n] = note_label
            index = int(n) - 1
            row = index // SUDOKU_CONSTANTS.block_size
            col = index % SUDOKU_CONSTANTS.block_size
            self.notes_grid.attach(note_label, col, row, 1, 1)

        self.notes_grid.show()


class SudokuCellUIManagement:
    """
    Handles SudokuCell instances' UI behavior.
    """

    def __init__(self, cell: SudokuCell):
        self.cell = cell
        self.notes_manager = SudokuCellNotesManagement(cell)
        self.compact_mode = False
        self.main_label = None

    def create_overlay(self, main_label, notes_grid):
        """Stack notes_grid on top of main_label inside a fill-aligned overlay."""
        overlay = Gtk.Overlay()
        overlay.set_child(main_label)
        overlay.add_overlay(notes_grid)
        overlay.set_halign(Gtk.Align.FILL)
        overlay.set_valign(Gtk.Align.FILL)
        return overlay

    def create_main_label(self):
        """Create and return a centered, expanding GTK label for the cell value."""
        return Gtk.Label(
            xalign=0.5,
            yalign=0.5,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            hexpand=True,
            vexpand=True,
        )

    def update_display(self):
        """Update the display state."""
        if self.main_label.get_text():
            for label in self.notes_manager.note_labels.values():
                label.set_text("")

    def set_value(self, value: str):
        """Set the main value of the cell."""
        self.main_label.set_text(value)
        self.update_display()

    def setup_ui_and_state(self):
        """Initialize the cell's label, notes grid, overlay, and GTK widget state."""
        self.main_label = self.create_main_label()
        notes_grid = self.notes_manager.notes_grid

        overlay = self.create_overlay(self.main_label, notes_grid)
        self.cell.set_child(overlay)
        self.cell.set_focus_on_click(False)
        self.cell.set_can_focus(True)
        self.cell.get_style_context().add_class("sudoku-cell-button")

        if self.cell.value is not None:
            self.set_value(str(self.cell.value))
            self.cell.get_style_context().add_class("clue-cell")
        else:
            self.set_value("")
            self.cell.get_style_context().add_class("entry-cell")

        self.update_display()

    def handle_compact(self, compact: bool):
        """
        Handles compact mode for Sudoku cells
        """
        self.compact_mode = compact
        size = 10 if compact else 40
        self.cell.set_size_request(size, size)
        current_notes = set(self.notes_manager.note_labels.keys())
        self.notes_manager.update_notes(current_notes, compact, self.main_label)

    def highlight(self, class_name: str):
        """Add a highlight class to the cell."""
        self.cell.get_style_context().add_class(class_name)

    def remove_highlight(self, class_name: str):
        """Remove a highlight class from the cell."""
        self.cell.get_style_context().remove_class(class_name)

    def clear(self):
        """Clear the main value and all notes."""
        self.set_value("")
        self.notes_manager.update_notes(set(), self.compact_mode, self.main_label)
        self.remove_highlight("wrong")

    def _cancel_feedback_timeout(self):
        """Cancel the active feedback timeout, if any."""
        if self._feedback_source_id is not None:
            GLib.source_remove(self._feedback_source_id)
            self._feedback_source_id = None

    def start_feedback_timeout(self, callback, delay=3000):
        """Start a feedback timeout, replacing any existing one.

        Args:
            callback: Called when the timeout fires.
            delay: Delay in milliseconds (default 3000).
        """
        self._cancel_feedback_timeout()

        def wrapped():
            self._feedback_source_id = None
            callback()
            return False

        self._feedback_source_id = GLib.timeout_add(delay, wrapped)

    def clear_feedback_timeout(self):
        """Cancel the active feedback timeout and reset state."""
        self._cancel_feedback_timeout()


class SudokuCell(Gtk.Button):
    """
    Represents a single cell in a Sudoku grid.
    Handles the cell's value, pencil notes, and associated widget behavior.
    """

    def __init__(self, row: int, column: int, value: int, editable: bool):
        super().__init__()
        self.row = row
        self.column = column
        self.editable = editable
        self.value = value
        self.ui = SudokuCellUIManagement(self)
        self.ui.setup_ui_and_state()