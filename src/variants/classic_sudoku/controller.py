# classic_sudoku/controller.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from ...core.controller import CoreSudokuController
from .board import ClassicSudokuBoard
from .generator import ClassicSudokuGenerator


class ClassicSudokuController(CoreSudokuController):
    def __init__(self, window):
        super().__init__(
            window,
            board_cls=ClassicSudokuBoard,
            generator=ClassicSudokuGenerator(),
            board_size=9,
            block_size=3,
        )
