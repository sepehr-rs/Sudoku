# diagonal_sudoku/preferences.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from ..classic_sudoku.preferences import ClassicSudokuPreferences


class DiagonalSudokuPreferences(ClassicSudokuPreferences):
    def __init__(self):
        super().__init__()
        self.variant_defaults.update(
            {
                "highlight_diagonals": True,
            }
        )
        self.name = "Diagonal Sudoku"
        self.variant_key = "diagonal"
