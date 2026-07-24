# shared/grid_manager.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk


class GridManager:
    """Builds and manages the Sudoku grid UI."""

    def __init__(self):
        self.board_size = 0
        self.block_size = 0
        self.window = None
        self.board = None
        self.input_handler = None
        self.popover_manager = None
        self.parent_grid = None
        self.blocks = []
        self.cells = []
        self.board_frame = None

    def setup(self, window, board, input_handler, popover_manager):
        self.window = window
        self.board = board
        self.input_handler = input_handler
        self.popover_manager = popover_manager
        self.board_size = board.size
        self.block_size = board.block_size

    def build_grid(self):
        self._clear_previous_grid()
        self.parent_grid = self._create_parent_grid()
        self.blocks = self._create_blocks()
        self.cells = self._create_cells()
        self.board_frame = self._wrap_in_aspect_frame(self.parent_grid)
        self.window.grid_container.append(self.board_frame)
        self.board_frame.show()
        self._reapply_compact_mode()
        self.window.grid_container.queue_allocate()

    def _clear_previous_grid(self):
        if self.popover_manager:
            self.popover_manager.invalidate()

        if self.cells:
            for row in self.cells:
                for cell in row:
                    if cell:
                        cell.clear_feedback_timeout()

        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)

    def _create_parent_grid(self):
        grid = Gtk.Grid(
            row_spacing=10,
            column_spacing=10,
            column_homogeneous=True,
            row_homogeneous=True,
        )
        grid.set_name("sudoku-parent-grid")
        return grid

    def _create_blocks(self):
        blocks = []
        n_blocks = self.board_size // self.block_size
        for br in range(n_blocks):
            row_blocks = []
            for bc in range(n_blocks):
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

    def _create_cells(self):
        cells = []
        for r in range(self.board_size):
            row_cells = []
            for c in range(self.board_size):
                cell = self.board.sudoku_cells[r][c]
                cell.row = r
                cell.col = c
                gesture = self.input_handler.make_cell_gesture(
                    lambda g, n, x, y, _r=r, _c=c: self.input_handler.on_cell_clicked(
                        g, n, x, y, _r, _c
                    )
                )
                cell.add_controller(gesture)

                key_ctrl = self.input_handler.make_cell_key_controller(r, c)
                cell.add_controller(key_ctrl)

                br = r // self.block_size
                bc = c // self.block_size
                inner_r = r % self.block_size
                inner_c = c % self.block_size
                self.blocks[br][bc].attach(cell, inner_c, inner_r, 1, 1)
                row_cells.append(cell)
            cells.append(row_cells)
        return cells

    def _wrap_in_aspect_frame(self, child):
        frame = Gtk.AspectFrame(ratio=1.0, obey_child=False)
        frame.set_hexpand(True)
        frame.set_vexpand(True)
        frame.set_halign(Gtk.Align.FILL)
        frame.set_valign(Gtk.Align.FILL)
        frame.set_child(child)
        return frame

    def _reapply_compact_mode(self):
        bp = getattr(self.window, "bp_bin", None)
        if not bp:
            return
        ctx = bp.get_style_context()
        for mode in ("compact-mode", "small-mode", "large"):
            if ctx.has_class(mode):
                canonical = mode.replace("-mode", "") if mode != "large" else "large"
                self.window._apply_mode(True, canonical)
                return
