# src/shared/sudoku_cell.py
# Copyright 2026 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import annotations

from gi.repository import Gtk  # pyright: ignore[reportAttributeAccessIssue]


class SudokuCellNotesManagement:
    """Handles SudokuCell pencil notes and their UI."""

    def __init__(self, cell: SudokuCell):
        self.cell = cell
        self.notes_grid = self._create_notes_grid()
        self.note_labels: dict[str, Gtk.Label] = {}

    def _create_notes_grid(self) -> Gtk.Grid:
        """Create and return a homogeneous GTK grid for pencil notes."""
        return Gtk.Grid(
            row_spacing=0,
            column_spacing=0,
            column_homogeneous=True,
            row_homogeneous=True,
            halign=Gtk.Align.FILL,
            valign=Gtk.Align.FILL,
        )

    def _create_note_label(self, number: str) -> Gtk.Label:
        compact = self.cell.ui.compact_mode
        size = 8 if compact else 12
        label = Gtk.Label(label=number)
        label.get_style_context().add_class("note-cell-label")
        label.set_size_request(size, size)
        label.set_halign(Gtk.Align.FILL)
        label.set_valign(Gtk.Align.FILL)
        return label

    def update_notes(self, notes: set[str]):
        """Update the notes display."""
        for child in list(self.notes_grid):
            self.notes_grid.remove(child)
        self.note_labels.clear()

        main_text = (
            self.cell.ui.main_label.get_text() if self.cell.ui.main_label else ""
        )
        if not notes or main_text:
            return

        for n in sorted(notes, key=int):
            note_label = self._create_note_label(n)
            self.note_labels[n] = note_label
            index = int(n) - 1
            row = index // self.cell.block_size
            col = index % self.cell.block_size
            self.notes_grid.attach(note_label, col, row, 1, 1)

        self.notes_grid.show()


class SudokuCellUIManagement:
    """Handles SudokuCell UI behavior, layout, and feedback."""

    def __init__(self, cell: SudokuCell):
        self.cell = cell
        self.compact_mode = False
        self.main_label: Gtk.Label | None = None
        self.notes_manager = SudokuCellNotesManagement(cell)

    def _create_main_label(self) -> Gtk.Label:
        """Create and return a centered, expanding GTK label for the cell value."""
        return Gtk.Label(
            xalign=0.5,
            yalign=0.5,
            halign=Gtk.Align.CENTER,
            valign=Gtk.Align.CENTER,
            hexpand=True,
            vexpand=True,
        )

    def _create_overlay(
        self, main_label: Gtk.Label, notes_grid: Gtk.Grid
    ) -> Gtk.Overlay:
        """Stack notes_grid on top of main_label inside a fill-aligned overlay."""
        overlay = Gtk.Overlay()
        overlay.set_child(main_label)
        overlay.add_overlay(notes_grid)
        overlay.set_halign(Gtk.Align.FILL)
        overlay.set_valign(Gtk.Align.FILL)
        return overlay

    def setup_ui_and_state(self):
        """Initialize the cell's label, notes grid, overlay, and GTK widget state."""
        self.main_label = self._create_main_label()
        overlay = self._create_overlay(self.main_label, self.notes_manager.notes_grid)

        self.cell.set_child(overlay)
        self.cell.set_focus_on_click(False)
        self.cell.set_can_focus(True)
        self.cell.get_style_context().add_class("sudoku-cell-button")

        if self.cell.value is not None:
            self.cell.get_style_context().add_class("clue-cell")
        else:
            self.cell.get_style_context().add_class("entry-cell")

    def update_display(self):
        """Update the display based on the current main value.

        Shows the main label and hides the notes grid when a value is present,
        and shows the notes grid when no value is set.
        """
        has_value = self.cell.value is not None
        self.notes_manager.notes_grid.set_visible(not has_value)

    def set_value(self, value: int | None):
        """Set the main value label and refresh display."""
        self.main_label.set_text(str(value) if value is not None else "")
        self.update_display()

    def set_compact(self, compact: bool):
        """Switch compact mode, avoiding redundant redraws."""
        if self.compact_mode == compact:
            return
        self.compact_mode = compact
        size = 10 if compact else 40
        self.cell.set_size_request(size, size)
        current_notes = set(self.notes_manager.note_labels.keys())
        self.notes_manager.update_notes(current_notes)

    def highlight(self, class_name: str):
        """Add a CSS highlight class to the cell widget."""
        self.cell.get_style_context().add_class(class_name)

    def remove_highlight(self, class_name: str):
        """Remove a CSS highlight class from the cell widget."""
        self.cell.get_style_context().remove_class(class_name)

    def clear(self):
        """Clear the main value, all notes, and any highlights."""
        self.set_value(None)
        self.notes_manager.update_notes(set())
        # here we only remove the wrong css class because if a cell is correct
        # and gets the correct highlighting, it is no longer editable and therefore
        # cannot be cleared.
        self.remove_highlight("wrong")


class SudokuCell(Gtk.Button):
    """
    Represents a single cell in a Sudoku grid.
    Handles value, pencil notes, editability, and widget behavior.
    """

    def __init__(
        self,
        value: int | None,
        correct_value: int | None,
        editable: bool,
        block_size: int = 3,
    ):
        super().__init__()
        self._editable = editable
        self.value = value
        self.correct_value = correct_value
        self.block_size = block_size
        self.ui = SudokuCellUIManagement(self)
        self.ui.setup_ui_and_state()
        self.set_value(value)

    def set_editable(self, editable: bool):
        self._editable = editable

    def is_editable(self) -> bool:
        return self._editable

    def do_clicked(self, *args):
        """Block click propagation for non-editable cells."""
        if self._editable:
            super().do_clicked(*args)

    def set_value(self, value: int | None):
        self.value = value
        self.ui.set_value(value)

    def get_value(self) -> int | None:
        return self.value

    def update_notes(self, notes: set[str]):
        self.ui.notes_manager.update_notes(notes)

    def set_compact(self, compact: bool):
        self.ui.set_compact(compact)

    def highlight(self, class_name: str):
        self.ui.highlight(class_name)

    def remove_highlight(self, class_name: str):
        self.ui.remove_highlight(class_name)

    def clear(self):
        self.ui.clear()
