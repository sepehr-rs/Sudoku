# controller.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import threading
import logging
from gi.repository import GLib


class CoreSudokuController:
    def __init__(self, window, board_cls, generator, block_size):
        self.window = window
        self.board_cls = board_cls
        self.generator = generator
        self.block_size = block_size

    def load_saved_game(self):
        self.board = self.board_cls.load(self.generator, self.block_size)
        if self.board:
            self.build_grid()
            self._restore_game_state()
            self.window.stack.set_visible_child(self.window.game_scrolled_window)
            logging.info(f"Loaded saved {self.board.variant.capitalize()} Sudoku game.")
            if self.board.is_solved():
                self._show_puzzle_finished_dialog()
        else:
            logging.error("No saved game found.")

    def _restore_game_state(self):
        raise NotImplementedError

    def build_grid(self):
        """Variant controllers override this to build the grid UI."""
        pass

    def start_game(self, difficulty: float, difficulty_label: str, variant: str):
        self.window.stack.set_visible_child(self.window.loading_screen)
        logging.info(
            f"Starting {variant.capitalize()} Sudoku game with difficulty: {difficulty}"
        )

        def worker():
            puzzle, solution = self.generator.generate(difficulty)
            GLib.idle_add(
                self._finish_start_game,
                puzzle,
                solution,
                difficulty,
                difficulty_label,
                variant,
            )

        threading.Thread(target=worker, daemon=True).start()

    def _finish_start_game(
        self, puzzle, solution, difficulty, difficulty_label, variant
    ):
        self.board = self.board_cls(
            generator=self.generator,
            puzzle=puzzle,
            solution=solution,
            difficulty=difficulty,
            difficulty_label=difficulty_label,
            variant=variant,
            block_size=self.block_size,
        )
        self.build_grid()
        self._restore_game_state()
        self.window.stack.set_visible_child(self.window.game_scrolled_window)

    def apply_compact_mode(compact, mode, parent_grid):
        parent_spacing, block_spacing = (8, 2) if compact else (10, 4)
        parent_grid.set_row_spacing(parent_spacing)
        parent_grid.set_column_spacing(parent_spacing)

        for row in self.blocks:
            for block in row:
                block.set_row_spacing(block_spacing)
                block.set_column_spacing(block_spacing)

        for row in self.cell_inputs:
            for cell in row:
                if cell:
                    cell.set_compact(compact)

        scrolled = self.game_scrolled_window
        if scrolled:
            scrolled.set_vexpand(True)
            scrolled.set_hexpand(True)
        grid_container = self.grid_container
        grid_container.set_hexpand(True)
        grid_container.set_vexpand(True)
        self.bp_bin.set_hexpand(True)
        self.bp_bin.set_vexpand(True)
        self.bp_bin.set_halign(Gtk.Align.FILL)
        self.bp_bin.set_valign(Gtk.Align.FILL)

        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.stack.set_halign(Gtk.Align.FILL)
        self.stack.set_valign(Gtk.Align.FILL)