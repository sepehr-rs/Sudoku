# diagonal_sudoku/controller.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from ...core.controller import CoreSudokuController
from .board import DiagonalSudokuBoard
from .generator import DiagonalSudokuGenerator


class DiagonalSudokuController(CoreSudokuController):
    def __init__(self, window):
        super().__init__(
            window,
            board_cls=DiagonalSudokuBoard,
            generator=DiagonalSudokuGenerator(),
            board_size=9,
            block_size=3,
        )
