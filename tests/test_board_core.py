# tests/test_board_core.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest

from src.variants.classic_sudoku.board import ClassicSudokuBoard
from tests.conftest import make_board_state


PUZZLE = [
    [1, None, 3, None, 5, None, 7, None, 9],
    [None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None],
    [None, None, None, None, None, None, None, None, None],
]

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
def board():
    return make_board_state(ClassicSudokuBoard, puzzle=PUZZLE, solution=SOLUTION)


class TestIsClue:
    def test_clue_returns_true(self, board):
        assert board.is_clue(0, 0) is True

    def test_empty_returns_false(self, board):
        assert board.is_clue(0, 1) is False

    def test_different_clue_positions(self, board):
        assert board.is_clue(0, 2) is True
        assert board.is_clue(0, 4) is True


class TestGetCorrectValue:
    def test_returns_solution_value(self, board):
        assert board.get_correct_value(0, 1) == 2
        assert board.get_correct_value(1, 0) == 4

    def test_clue_cell_matches_solution(self, board):
        assert board.get_correct_value(0, 0) == 1


class TestInputAccessors:
    def test_set_and_get(self, board):
        board.set_input(1, 0, 4)
        assert board.get_input(1, 0) == 4

    def test_get_returns_none_for_empty(self, board):
        assert board.get_input(1, 1) is None

    def test_clear_input(self, board):
        board.set_input(1, 0, 4)
        board.clear_input(1, 0)
        assert board.get_input(1, 0) is None


class TestNotes:
    def test_toggle_adds_note(self, board):
        board.toggle_note(1, 1, "5")
        assert "5" in board.get_notes(1, 1)

    def test_toggle_removes_note(self, board):
        board.toggle_note(1, 1, "5")
        board.toggle_note(1, 1, "5")
        assert "5" not in board.get_notes(1, 1)

    def test_get_notes_returns_set(self, board):
        assert isinstance(board.get_notes(1, 1), set)

    def test_multiple_notes(self, board):
        board.toggle_note(1, 1, "3")
        board.toggle_note(1, 1, "7")
        assert board.get_notes(1, 1) == {"3", "7"}


class TestRemoveNoteFromRelated:
    def test_removes_from_same_row(self, board):
        board.toggle_note(0, 3, "5")
        affected = board.remove_note_from_related(0, 0, 5)
        assert (0, 3) in affected
        assert "5" not in board.get_notes(0, 3)

    def test_removes_from_same_column(self, board):
        board.toggle_note(3, 0, "5")
        affected = board.remove_note_from_related(0, 0, 5)
        assert (3, 0) in affected

    def test_removes_from_same_block(self, board):
        board.toggle_note(1, 2, "5")
        affected = board.remove_note_from_related(0, 0, 5)
        assert (1, 2) in affected

    def test_does_not_remove_unrelated(self, board):
        board.toggle_note(5, 5, "5")
        affected = board.remove_note_from_related(0, 0, 5)
        assert (5, 5) not in affected
        assert "5" in board.get_notes(5, 5)

    def test_does_not_remove_from_self(self, board):
        board.toggle_note(0, 0, "5")
        board.remove_note_from_related(0, 0, 5)
        assert "5" in board.get_notes(0, 0)


class TestRemainingValidInputs:
    def test_clue_values_decremented(self, board):
        remaining = board.get_remaining_valid_inputs()
        assert remaining[1] == 8
        assert remaining[3] == 8
        assert remaining[5] == 8
        assert remaining[7] == 8
        assert remaining[9] == 8

    def test_non_clue_values_at_nine(self, board):
        remaining = board.get_remaining_valid_inputs()
        assert remaining[2] == 9
        assert remaining[4] == 9
        assert remaining[6] == 9
        assert remaining[8] == 9

    def test_decrements_for_correct_user_input(self, board):
        board.set_input(1, 0, 4)
        remaining = board.get_remaining_valid_inputs()
        assert remaining[4] == 8

    def test_does_not_decrement_for_wrong_user_input(self, board):
        board.set_input(1, 0, 9)
        remaining = board.get_remaining_valid_inputs()
        assert remaining[9] == 8


class TestIsSolved:
    def test_empty_board_not_solved(self, board):
        assert board.is_solved() is False

    def test_partially_filled_not_solved(self, board):
        for c in range(9):
            board.sudoku_cells[1][c].set_value(SOLUTION[1][c])
        assert board.is_solved() is False

    def test_fully_correct_solved(self, board):
        for r in range(9):
            for c in range(9):
                if PUZZLE[r][c] is None:
                    board.sudoku_cells[r][c].set_value(SOLUTION[r][c])
        assert board.is_solved() is True
