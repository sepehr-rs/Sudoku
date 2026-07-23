# tests/test_board_serialization.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import os
import tempfile
from unittest.mock import patch

import pytest

from src.core.persistence import save_game, load_game
from src.core.preferences import PreferencesManager
from src.variants.classic_sudoku.board import ClassicSudokuBoard
from src.variants.classic_sudoku.generator import ClassicSudokuGenerator
from src.variants.classic_sudoku.preferences import ClassicSudokuPreferences
from src.variants.diagonal_sudoku.board import DiagonalSudokuBoard
from src.variants.diagonal_sudoku.preferences import DiagonalSudokuPreferences
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
def save_path(tmp_path):
    path = tmp_path / "board.json"
    with patch("src.core.persistence._get_save_path", return_value=str(path)):
        yield path


@pytest.fixture
def prefs():
    p = ClassicSudokuPreferences()
    PreferencesManager.set_preferences(p)
    return p


@pytest.fixture
def classic_board(prefs):
    board = make_board_state(ClassicSudokuBoard, puzzle=PUZZLE, solution=SOLUTION)
    board.set_input(1, 0, 4)
    board.toggle_note(1, 1, "5")
    board.toggle_note(1, 1, "8")
    board.mistakes = 2
    return board


@pytest.fixture
def diagonal_board(prefs):
    board = make_board_state(DiagonalSudokuBoard, puzzle=PUZZLE, solution=SOLUTION)
    board.set_input(1, 0, 4)
    board.toggle_note(2, 2, "9")
    board.mistakes = 1
    return board


class TestClassicRoundtrip:
    def test_preserves_board_state(self, classic_board, save_path):
        save_game(classic_board)
        loaded = load_game(
            ClassicSudokuBoard,
            generator=ClassicSudokuGenerator(),
            block_size=3,
        )

        assert loaded is not None
        assert loaded.puzzle == classic_board.puzzle
        assert loaded.solution == classic_board.solution
        assert loaded.user_inputs == classic_board.user_inputs
        assert loaded.mistakes == classic_board.mistakes
        assert loaded.variant == "classic"

    def test_notes_roundtrip(self, classic_board, save_path):
        save_game(classic_board)
        loaded = load_game(
            ClassicSudokuBoard,
            generator=ClassicSudokuGenerator(),
            block_size=3,
        )

        assert loaded.notes[1][1] == {"5", "8"}


class TestDiagonalRoundtrip:
    def test_preserves_board_state(self, diagonal_board, save_path):
        save_game(diagonal_board)
        loaded = load_game(
            DiagonalSudokuBoard,
            generator=ClassicSudokuGenerator(),
            block_size=3,
        )

        assert loaded is not None
        assert loaded.puzzle == diagonal_board.puzzle
        assert loaded.variant == "classic"

    def test_notes_roundtrip(self, diagonal_board, save_path):
        save_game(diagonal_board)
        loaded = load_game(
            DiagonalSudokuBoard,
            generator=ClassicSudokuGenerator(),
            block_size=3,
        )

        assert loaded.notes[2][2] == {"9"}


class TestSerializationFormat:
    def test_notes_serialized_as_lists(self, classic_board, save_path):
        save_game(classic_board)
        with open(save_path, "r") as f:
            raw = json.load(f)
        notes_row = raw["notes"][1]
        assert isinstance(notes_row[1], list)
        assert sorted(notes_row[1]) == ["5", "8"]

    def test_load_returns_none_for_missing_file(self):
        result = load_game(
            ClassicSudokuBoard,
            generator=ClassicSudokuGenerator(),
            block_size=3,
        )
        assert result is None

    def test_load_defaults_missing_optional_fields(self, save_path, prefs):
        minimal_state = {
            "puzzle": PUZZLE,
            "solution": SOLUTION,
            "user_inputs": [[None] * 9 for _ in range(9)],
            "notes": [[[] for _ in range(9)] for _ in range(9)],
        }
        with open(save_path, "w") as f:
            json.dump(minimal_state, f)

        loaded = load_game(
            ClassicSudokuBoard,
            generator=ClassicSudokuGenerator(),
            block_size=3,
        )
        assert loaded is not None
        assert loaded.difficulty == 0.2
        assert loaded.difficulty_label == "Unknown"
        assert loaded.variant == "Unknown"
        assert loaded.mistakes == 0
