# diagonal_sudoku/board.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from ..classic_sudoku.board import ClassicSudokuBoard


class DiagonalSudokuBoard(ClassicSudokuBoard):

    def has_conflict(self, row: int, col: int, value: int) -> list[tuple[int, int]]:
        conflicts = super().has_conflict(row, col, value)
        existing = set(conflicts)
        size = len(self.puzzle)

        for i in range(size):
            for j in range(size):
                if (i, j) in existing or (i == row and j == col):
                    continue
                on_main = i == j and row == col
                on_anti = i + j == size - 1 and row + col == size - 1

                if on_main or on_anti:
                    cell_value = self.puzzle[i][j]
                    if cell_value is None:
                        cell_value = self.sudoku_cells[i][j].get_value()
                    if cell_value is not None and cell_value == value:
                        conflicts.append((i, j))

        return conflicts
