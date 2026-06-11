# classic_sudoku/controller.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from ...core.controller import CoreSudokuController


class ClassicSudokuController(CoreSudokuController):
    def __init__(self, window, board_cls, generator, block_size):
        super().__init__(window, board_cls, generator, block_size)
