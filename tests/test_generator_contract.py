# tests/test_generator_contract.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest.mock import patch, MagicMock

from src.variants.classic_sudoku.generator import ClassicSudokuGenerator
from src.variants.diagonal_sudoku.generator import DiagonalSudokuGenerator


def _make_fake_sudoku(puzzle, solution):
    fake = MagicMock()
    fake.board = puzzle
    fake.solve.return_value.board = solution
    return fake


class TestClassicGenerator:
    @patch("src.variants.classic_sudoku.generator.PuzzleGenerator.make_puzzle")
    def test_returns_tuple_of_two_9x9_lists(self, mock_make):
        puzzle = [[(r * 9 + c) % 9 + 1 for c in range(9)] for r in range(9)]
        solution = [[(r * 9 + c) % 9 + 1 for c in range(9)] for r in range(9)]
        mock_make.return_value = _make_fake_sudoku(puzzle, solution)

        gen = ClassicSudokuGenerator()
        result_puzzle, result_solution = gen._generate_impl(0.5)

        assert isinstance(result_puzzle, list)
        assert isinstance(result_solution, list)
        assert len(result_puzzle) == 9
        assert all(len(row) == 9 for row in result_puzzle)
        assert len(result_solution) == 9
        assert all(len(row) == 9 for row in result_solution)

    @patch("src.variants.classic_sudoku.generator.PuzzleGenerator.make_puzzle")
    def test_passes_classic_sudoku_cls(self, mock_make):
        mock_make.return_value = _make_fake_sudoku(
            [[0] * 9 for _ in range(9)],
            [[1] * 9 for _ in range(9)],
        )
        ClassicSudokuGenerator()._generate_impl(0.7)
        _, kwargs = mock_make.call_args
        assert kwargs["sudoku_cls"].__name__ == "ClassicSudoku"


class TestDiagonalGenerator:
    @patch("src.variants.diagonal_sudoku.generator.PuzzleGenerator.make_puzzle")
    def test_returns_tuple_of_two_9x9_lists(self, mock_make):
        puzzle = [[(r * 9 + c) % 9 + 1 for c in range(9)] for r in range(9)]
        solution = [[(r * 9 + c) % 9 + 1 for c in range(9)] for r in range(9)]
        mock_make.return_value = _make_fake_sudoku(puzzle, solution)

        gen = DiagonalSudokuGenerator()
        result_puzzle, result_solution = gen._generate_impl(0.5)

        assert len(result_puzzle) == 9
        assert len(result_solution) == 9

    @patch("src.variants.diagonal_sudoku.generator.PuzzleGenerator.make_puzzle")
    def test_passes_diagonal_sudoku_cls(self, mock_make):
        mock_make.return_value = _make_fake_sudoku(
            [[0] * 9 for _ in range(9)],
            [[1] * 9 for _ in range(9)],
        )
        DiagonalSudokuGenerator()._generate_impl(0.7)
        _, kwargs = mock_make.call_args
        assert kwargs["sudoku_cls"].__name__ == "DiagonalSudoku"
