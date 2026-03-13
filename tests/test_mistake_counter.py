"""Tests for mistake counter behavior."""

import sys
from unittest.mock import MagicMock

# Mock GTK modules before importing anything else
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()
sys.modules["sudoku"] = MagicMock()
sys.modules["sudoku.base_sudoku"] = MagicMock()

import pytest

from src.base.preferences_manager import PreferencesManager
from src.variants.classic_sudoku.board import ClassicSudokuBoard
from src.variants.classic_sudoku.manager import ClassicSudokuManager


class _DummyPreferences:
    def __init__(self):
        self.variant_defaults = {}
        self.general_defaults = {}

    def general(self, key, default=None):
        if key == "casual_mode":
            return ["desc", True]
        if key == "prevent_conflicting_pencil_notes":
            return False
        return default


class _MockCell:
    def __init__(self, row, col, value=None, editable=True):
        self.row = row
        self.col = col
        self.value = value
        self._editable = editable
        self.notes = set()

    def is_editable(self):
        return self._editable

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def clear(self):
        self.value = None

    def update_notes(self, notes):
        self.notes = set(notes)

    def clear_feedback_timeout(self):
        pass

    def remove_highlight(self, _name):
        pass

    def set_tooltip_text(self, _text):
        pass

    def start_feedback_timeout(self, callback, delay=2000):
        del callback, delay


@pytest.fixture(autouse=True)
def _prefs_guard():
    PreferencesManager.set_preferences(_DummyPreferences())
    try:
        yield
    finally:
        PreferencesManager.set_preferences(None)


@pytest.fixture
def manager_with_board():
    board = ClassicSudokuBoard.__new__(ClassicSudokuBoard)
    board.rules = MagicMock(size=9, block_size=3)
    board.puzzle = [[None for _ in range(9)] for _ in range(9)]
    board.user_inputs = [[None for _ in range(9)] for _ in range(9)]
    board.solution = [["1" for _ in range(9)] for _ in range(9)]
    board.notes = [[set() for _ in range(9)] for _ in range(9)]
    board.mistake_count = 0
    board.save_to_file = MagicMock()
    board.is_solved = MagicMock(return_value=False)

    manager = ClassicSudokuManager.__new__(ClassicSudokuManager)
    manager.window = MagicMock()
    manager.board = board
    manager.pencil_mode = False
    manager.conflict_cells = []
    manager.cell_inputs = [[_MockCell(r, c) for c in range(9)] for r in range(9)]
    manager._handle_wrong_input = MagicMock()
    manager._handle_correct_input = MagicMock()
    manager._clear_feedback = MagicMock()

    return manager


def test_wrong_committed_input_increments_mistake_counter(manager_with_board):
    manager = manager_with_board
    target_cell = manager.cell_inputs[0][0]

    manager._fill_cell(target_cell, "2")

    assert manager.board.mistake_count == 1


def test_pencil_note_does_not_increment_mistake_counter(manager_with_board):
    manager = manager_with_board
    manager.pencil_mode = True
    target_cell = manager.cell_inputs[0][0]

    manager._fill_cell(target_cell, "2")

    assert manager.board.mistake_count == 0
