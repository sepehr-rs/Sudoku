"""Test for generator contract and type safety."""

import sys
from unittest.mock import MagicMock, patch

# Mock GTK modules before importing anything else
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()

from src.variants.classic_sudoku.generator import ClassicSudokuGenerator


class TestGeneratorContract:
    """Tests for GeneratorBase contract."""

    def test_generate_impl_returns_tuple(self):
        """Verify _generate_impl returns (puzzle, solution) tuple."""
        generator = ClassicSudokuGenerator()

        with patch(
            "src.variants.classic_sudoku.generator.PuzzleGenerator"
        ) as mock_puzzle:
            mock_sudoku = MagicMock()
            mock_sudoku.board = [[0] * 9 for _ in range(9)]
            mock_sudoku.solve.return_value = mock_sudoku
            mock_puzzle.make_puzzle.return_value = mock_sudoku

            puzzle, solution = generator._generate_impl(0.5)

            # Verify it returns a tuple of two elements
            assert isinstance(puzzle, list)
            assert isinstance(solution, list)
            assert isinstance(puzzle[0], list)
            assert isinstance(solution[0], list)
            assert len(puzzle) == 9
            assert len(solution) == 9
            assert len(puzzle[0]) == 9
            assert len(solution[0]) == 9
