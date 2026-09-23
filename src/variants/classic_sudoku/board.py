# classic_sudoku/board.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from ...core.board import CoreSudokuBoard


class ClassicSudokuBoard(CoreSudokuBoard):

    def is_solved(self) -> bool:
        for r, row in enumerate(self.sudoku_cells):
            for c, cell in enumerate(row):
                if self.puzzle[r][c] is None:
                    if cell.get_value() != self.solution[r][c]:
                        return False
        return True

    def has_conflict(self, row: int, col: int, value: int) -> list[tuple[int, int]]:
        conflicts = []
        size = len(self.puzzle)
        bs = self.block_size

        for i in range(size):
            for j in range(size):
                if i == row and j == col:
                    continue
                same_row = i == row
                same_col = j == col
                same_block = (i // bs == row // bs) and (j // bs == col // bs)

                if same_row or same_col or same_block:
                    existing = self.puzzle[i][j]
                    if existing is None:
                        cell = self.sudoku_cells[i][j]
                        existing = cell.get_value()

                    if existing is not None and existing == value:
                        conflicts.append((i, j))

        return conflicts
