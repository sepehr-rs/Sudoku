# tests/test_board_conflicts.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from src.variants.classic_sudoku.board import ClassicSudokuBoard
from src.variants.diagonal_sudoku.board import DiagonalSudokuBoard
from tests.conftest import make_board_state


EMPTY = [[None] * 9 for _ in range(9)]
SOLUTION = [
    [1, 2, 3, 4, 5, 6, 7, 8, 9],
    [4, 5, 6, 7, 8, 9, 1, 2, 3],
    [7, 8, 9, 1, 2, 3, 4, 5, 6],
    [2, 3, 4, 5, 6, 7, 8, 9, 1],
    [5, 6, 7, 8, 9, 1, 2, 3, 4],
    [8, 9, 1, 2, 3, 4, 5, 6, 7],
    [3, 4, 5, 6, 7, 8, 9, 1, 2],
    [6, 7, 8, 9, 1, 2, 3, 4, 5],
    [9, 1, 2, 3, 4, 5, 6, 7, 8],
]


@pytest.fixture
def classic_board():
    return make_board_state(ClassicSudokuBoard, puzzle=EMPTY, solution=SOLUTION)


@pytest.fixture
def diagonal_board():
    return make_board_state(DiagonalSudokuBoard, puzzle=EMPTY, solution=SOLUTION)


class TestClassicConflict:
    def test_no_conflict_on_empty_board(self, classic_board):
        assert classic_board.has_conflict(0, 0, 5) == []

    def test_row_conflict(self, classic_board):
        classic_board.sudoku_cells[0][3].set_value(5)
        conflicts = classic_board.has_conflict(0, 7, 5)
        assert (0, 3) in conflicts

    def test_column_conflict(self, classic_board):
        classic_board.sudoku_cells[5][0].set_value(5)
        conflicts = classic_board.has_conflict(8, 0, 5)
        assert (5, 0) in conflicts

    def test_block_conflict(self, classic_board):
        classic_board.sudoku_cells[1][1].set_value(5)
        conflicts = classic_board.has_conflict(2, 2, 5)
        assert (1, 1) in conflicts

    def test_no_conflict_diagonal_on_classic(self, classic_board):
        classic_board.sudoku_cells[4][4].set_value(5)
        conflicts = classic_board.has_conflict(0, 0, 5)
        assert (4, 4) not in conflicts

    def test_multiple_conflicts(self, classic_board):
        classic_board.sudoku_cells[0][3].set_value(7)
        classic_board.sudoku_cells[7][7].set_value(7)
        classic_board.sudoku_cells[1][6].set_value(7)
        conflicts = classic_board.has_conflict(0, 7, 7)
        positions = set(conflicts)
        assert (0, 3) in positions
        assert (7, 7) in positions
        assert (1, 6) in positions

    def test_conflict_with_puzzle_clue(self):
        puzzle = [row[:] for row in EMPTY]
        puzzle[0][3] = 7
        board = make_board_state(
            ClassicSudokuBoard, puzzle=puzzle, solution=SOLUTION
        )
        conflicts = board.has_conflict(0, 7, 7)
        assert (0, 3) in conflicts


class TestDiagonalConflict:
    def test_main_diagonal_conflict(self, diagonal_board):
        diagonal_board.sudoku_cells[4][4].set_value(5)
        conflicts = diagonal_board.has_conflict(0, 0, 5)
        assert (4, 4) in conflicts

    def test_anti_diagonal_conflict(self, diagonal_board):
        diagonal_board.sudoku_cells[4][4].set_value(5)
        conflicts = diagonal_board.has_conflict(8, 0, 5)
        assert (4, 4) in conflicts

    def test_diagonal_does_not_conflict_off_diagonal(self, diagonal_board):
        diagonal_board.sudoku_cells[5][3].set_value(5)
        conflicts = diagonal_board.has_conflict(0, 0, 5)
        assert (5, 3) not in conflicts

    def test_classic_board_ignores_diagonal(self, classic_board):
        classic_board.sudoku_cells[4][4].set_value(5)
        conflicts = classic_board.has_conflict(0, 0, 5)
        assert conflicts == []
