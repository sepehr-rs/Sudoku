# tests/conftest.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import sys
from unittest.mock import MagicMock

import pytest

from src.core.preferences import PreferencesManager

# Mock GTK before any src imports (unless running the FD leak integration test)
if os.environ.get("SUDOKU_FD_TEST") != "1":
    sys.modules["gi"] = MagicMock()
    sys.modules["gi.repository"] = MagicMock()
    sys.modules["gi.repository.Gtk"] = MagicMock()
    sys.modules["gi.repository.Gdk"] = MagicMock()
    sys.modules["gi.repository.GLib"] = MagicMock()
    sys.modules["gi.repository.Adw"] = MagicMock()


class FakeCell:
    """Lightweight stand-in for SudokuCell in board logic tests."""

    def __init__(self, value=None, correct_value=None, editable=True, block_size=3):
        self._value = value
        self._editable = editable

    def get_value(self):
        return self._value

    def set_value(self, v):
        self._value = v

    def is_editable(self):
        return self._editable

    def set_editable(self, e):
        self._editable = e


@pytest.fixture(autouse=True)
def _patch_sudoku_cell():
    """Replace SudokuCell with FakeCell so board __init__ works without GTK."""
    import src.core.board as board_mod

    original = board_mod.sudoku_cell.SudokuCell
    board_mod.sudoku_cell.SudokuCell = FakeCell
    yield
    board_mod.sudoku_cell.SudokuCell = original


def make_board_state(board_cls, *, puzzle, solution, block_size=3):
    """Construct a board instance with FakeCells, bypassing GTK __init__."""
    board = object.__new__(board_cls)
    board.puzzle = puzzle
    board.solution = solution
    board.block_size = block_size
    board.size = len(puzzle)
    board.user_inputs = [[None] * board.size for _ in range(board.size)]
    board.notes = [[set() for _ in range(board.size)] for _ in range(board.size)]
    board.mistakes = 0
    board.difficulty = 0.5
    board.difficulty_label = "Medium"
    board.variant = "classic"
    board.variant_preferences = {}
    board.general_preferences = {}
    board.sudoku_cells = [
        [
            FakeCell(value=puzzle[r][c], editable=(puzzle[r][c] is None))
            for c in range(board.size)
        ]
        for r in range(board.size)
    ]
    return board


@pytest.fixture(autouse=True)
def _prefs_guard():
    PreferencesManager.set_preferences(
        type("_P", (), {"general_defaults": {}, "variant_defaults": {}})()
    )
    yield
    PreferencesManager.set_preferences(None)
