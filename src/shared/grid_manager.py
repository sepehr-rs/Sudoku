# grid_manager.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk


class GridManager:
    def __init__(
        self, board_size: int, block_size: int, window, board
    ):
        self.board_size = board_size  # row * column
        self.block_size = block_size
        self.window = window
        self.board = board

    def build_grid(self, window):
        self._clear_previous_grid()
        self.parent_grid = self._create_parent_grid()
        self.blocks = self._create_blocks()
        self.board_frame = self._wrap_in_aspect_frame(self.parent_grid)
        self.window.grid_container.append(self.board_frame)
        self.board_frame.show()
        self._reapply_compact_mode()
        self.window.grid_container.queue_allocate()

    def _clear_previous_grid(self):
        self._popover_manager.invalidate()

        for row in self.board.sudoku_cells:
            for cell in row:
                cell.clear_feedback_timeout()  # TODO: implement

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

    def _create_blocks(self):
        """Create and attach the NxN block grids to the parent grid."""
        blocks = []
        for br in range(self.block_size):
            row_blocks = []
            for bc in range(self.block_size):
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
        """Reapply layout modes after UI rebuild."""
        bp = getattr(self.window, "bp_bin", None)
        if not bp:
            return

        ctx = bp.get_style_context()

        if ctx.has_class("large"):
            self.window._apply_mode(True, "large")
            return

        if ctx.has_class("compact-mode"):
            self.window._apply_mode(True, "compact")
            return

        if ctx.has_class("small-mode"):
            self.window._apply_mode(True, "small")
            return
