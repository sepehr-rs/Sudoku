import pytest
import sys
from unittest.mock import MagicMock

# Mock gi.repository before importing manager to avoid GTK dependency
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()

from src.variants.classic_sudoku.board import ClassicSudokuBoard
from src.variants.diagonal_sudoku.board import DiagonalSudokuBoard
from src.variants.classic_sudoku.rules import ClassicSudokuRules
from src.variants.diagonal_sudoku.rules import DiagonalSudokuRules
from src.variants.classic_sudoku.manager import ClassicSudokuManager
from src.base.preferences_manager import PreferencesManager


class MockCell:
    def __init__(self, row, col, value=None, editable=True):
        self.row = row
        self.col = col
        self.value = value
        self.editable_state = editable
        self.notes = set()
        self.highlights = set()
        self.feedback_timeout_started = False

    def is_editable(self):
        return self.editable_state

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def update_notes(self, notes):
        self.notes = notes

    def highlight(self, type):
        self.highlights.add(type)

    def remove_highlight(self, type):
        if type in self.highlights:
            self.highlights.remove(type)

    def start_feedback_timeout(self, callback, delay=2000):
        self.feedback_timeout_started = True

    def grab_focus(self):
        pass


class MockPreferences:
    def __init__(self, prevent_conflicts=True):
        self.prevent_conflicts = prevent_conflicts

    def general(self, key, default=None):
        if key == "prevent_conflicting_pencil_notes":
            return self.prevent_conflicts
        return default

    def variant(self, key, default=None):
        return default


@pytest.fixture
def classic_board():
    board = ClassicSudokuBoard.__new__(ClassicSudokuBoard)
    board.rules = ClassicSudokuRules()
    board.puzzle = [[None for _ in range(9)] for _ in range(9)]
    board.user_inputs = [[None for _ in range(9)] for _ in range(9)]
    board.solution = [[None for _ in range(9)] for _ in range(9)]
    board.notes = [[set() for _ in range(9)] for _ in range(9)]
    return board


@pytest.fixture
def diagonal_board():
    board = DiagonalSudokuBoard.__new__(DiagonalSudokuBoard)
    board.rules = DiagonalSudokuRules()
    board.puzzle = [[None for _ in range(9)] for _ in range(9)]
    board.user_inputs = [[None for _ in range(9)] for _ in range(9)]
    board.solution = [[None for _ in range(9)] for _ in range(9)]
    board.notes = [[set() for _ in range(9)] for _ in range(9)]
    return board


def test_row_conflict(classic_board):
    classic_board.user_inputs[0][0] = "5"
    conflicts = classic_board.has_conflict(0, 5, "5")
    assert (0, 0) in conflicts


def test_column_conflict(classic_board):
    classic_board.user_inputs[0][0] = "5"
    conflicts = classic_board.has_conflict(5, 0, "5")
    assert (0, 0) in conflicts


def test_block_conflict(classic_board):
    classic_board.user_inputs[0][0] = "5"
    conflicts = classic_board.has_conflict(1, 1, "5")
    assert (0, 0) in conflicts


def test_diagonal_conflict(diagonal_board):
    diagonal_board.user_inputs[0][0] = "5"
    conflicts = diagonal_board.has_conflict(4, 4, "5")
    assert (0, 0) in conflicts

    diagonal_board.user_inputs[0][8] = "3"
    conflicts = diagonal_board.has_conflict(8, 0, "3")
    assert (0, 8) in conflicts


def test_no_conflict(classic_board):
    classic_board.user_inputs[0][0] = "5"
    conflicts = classic_board.has_conflict(1, 4, "5")
    assert len(conflicts) == 0


def test_pencil_pref_off(classic_board):
    manager = ClassicSudokuManager.__new__(ClassicSudokuManager)
    manager.board = classic_board
    manager.board.save_to_file = MagicMock()
    manager.pencil_mode = True
    manager.conflict_cells = []
    manager.cell_inputs = [[MockCell(r, c) for c in range(9)] for r in range(9)]

    PreferencesManager.set_preferences(MockPreferences(prevent_conflicts=False))

    # Conflict exists: "5" at (0,0)
    manager.board.user_inputs[0][0] = "5"

    # Toggle "5" at (0,1) - should succeed even with conflict because pref is OFF
    target_cell = manager.cell_inputs[0][1]
    manager._fill_cell(target_cell, "5")

    assert "5" in manager.board.get_notes(0, 1)
    assert target_cell.feedback_timeout_started is False


def test_pencil_pref_on_and_filled_guard(classic_board):
    manager = ClassicSudokuManager.__new__(ClassicSudokuManager)
    manager.board = classic_board
    manager.board.save_to_file = MagicMock()
    manager.pencil_mode = True
    manager.conflict_cells = []
    manager.cell_inputs = [[MockCell(r, c) for c in range(9)] for r in range(9)]

    PreferencesManager.set_preferences(MockPreferences(prevent_conflicts=True))

    # 1. Conflict test
    # Conflict exists: "5" at (0,0)
    manager.board.user_inputs[0][0] = "5"

    # Try to add "5" at (0,1) - should fail because pref is ON
    target_cell = manager.cell_inputs[0][1]
    manager._fill_cell(target_cell, "5")

    assert "5" not in manager.board.get_notes(0, 1)
    assert target_cell.feedback_timeout_started is True

    # 2. Filled cell guard test
    # Set cell (1,1) as filled
    manager.board.user_inputs[1][1] = "9"
    filled_cell = manager.cell_inputs[1][1]
    filled_cell.set_value("9")

    # Try to toggle note "1" - should be ignored
    manager._fill_cell(filled_cell, "1")
    assert "1" not in manager.board.get_notes(1, 1)
    assert filled_cell.feedback_timeout_started is False
