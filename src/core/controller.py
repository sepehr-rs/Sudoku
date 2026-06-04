# controller.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import threading
import logging
from gi.repository import GLib


class Controller:
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
