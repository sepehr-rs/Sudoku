"""Tests for diagonal mode plumbing fixes (issue #273)."""

import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch

# Mock GTK modules before importing anything else
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()

import pytest

from src.base.preferences_manager import PreferencesManager
from src.variants.classic_sudoku.board import ClassicSudokuBoard
from src.variants.classic_sudoku.manager import ClassicSudokuManager
from src.variants.diagonal_sudoku.board import DiagonalSudokuBoard
from src.variants.diagonal_sudoku.generator import DiagonalSudokuGenerator
from src.variants.diagonal_sudoku.manager import DiagonalSudokuManager
from src.variants.diagonal_sudoku.rules import DiagonalSudokuRules
from src.variants.diagonal_sudoku.ui_helpers import DiagonalUIHelpers


class _DummyPreferences:
    def __init__(self):
        self.variant_defaults = {}
        self.general_defaults = {}

    def general(self, _key, default=None):
        return default

    def variant(self, _key, default=None):
        return default


class _HighlightPreferences(_DummyPreferences):
    def __init__(self):
        self.variant_defaults = {
            "highlight_block": False,
            "highlight_related_cells": False,
            "highlight_diagonals": True,
        }
        self.general_defaults = {
            "highlight_row": False,
            "highlight_column": False,
        }

    def general(self, key, default=None):
        return self.general_defaults.get(key, default)

    def variant(self, key, default=None):
        return self.variant_defaults.get(key, default)


@pytest.fixture(autouse=True)
def _prefs_guard():
    PreferencesManager.set_preferences(_DummyPreferences())
    try:
        yield
    finally:
        PreferencesManager.set_preferences(None)


class _MockCell:
    def __init__(self, row, col, value=None):
        self.row = row
        self.col = col
        self.value = value
        self.highlights = set()

    def get_value(self):
        return self.value

    def highlight(self, highlight_type):
        self.highlights.add(highlight_type)

    def remove_highlight(self, highlight_type):
        self.highlights.discard(highlight_type)


@pytest.fixture
def diagonal_board():
    board = DiagonalSudokuBoard.__new__(DiagonalSudokuBoard)
    board.rules = DiagonalSudokuRules()
    board.puzzle = [[None for _ in range(9)] for _ in range(9)]
    board.user_inputs = [[None for _ in range(9)] for _ in range(9)]
    board.solution = [[None for _ in range(9)] for _ in range(9)]
    board.notes = [[set() for _ in range(9)] for _ in range(9)]
    return board


def _make_cells():
    return [[_MockCell(r, c) for c in range(9)] for r in range(9)]


class TestDiagonalBoardLoadFromFile:
    """Tests for DiagonalSudokuBoard.load_from_file."""

    def test_load_from_file_uses_diagonal_rules(self, tmp_path):
        """Verify loaded board has DiagonalSudokuRules."""
        save_data = {
            "difficulty": 0.5,
            "difficulty_label": "Medium",
            "variant": "diagonal",
            "variant_preferences": {},
            "general_preferences": {},
            "puzzle": [[None] * 9 for _ in range(9)],
            "solution": [
                [str((i * 9 + j + 1) % 9 + 1) for j in range(9)] for i in range(9)
            ],
            "user_inputs": [[None] * 9 for _ in range(9)],
            "notes": [[[] for _ in range(9)] for _ in range(9)],
        }

        save_file = tmp_path / "test_save.json"
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(save_data, f)

        board = DiagonalSudokuBoard.load_from_file(str(save_file))

        assert board is not None
        assert isinstance(board.rules, DiagonalSudokuRules)
        assert isinstance(board.generator, DiagonalSudokuGenerator)
        assert board.variant == "diagonal"

    def test_load_from_file_returns_none_for_missing_file(self):
        """Verify returns None when file doesn't exist."""
        missing = os.path.join(tempfile.gettempdir(), "sudoku", "nope.json")
        board = DiagonalSudokuBoard.load_from_file(missing)
        assert board is None


class TestManagerBoardClassUsage:
    """Tests for manager using self.board_cls."""

    def test_diagonal_manager_start_game_creates_diagonal_board(self):
        """Verify DiagonalSudokuManager.start_game() creates DiagonalSudokuBoard."""

        class _InstantThread:
            def __init__(self, *args, target=None, daemon=True, **kwargs):
                del args, daemon, kwargs
                self._target = target or (lambda: None)

            def start(self):
                self._target()

        def fake_idle_add(func, *args, **kwargs):
            return func(*args, **kwargs) or True

        def fake_generate(_self, _difficulty, timeout=5):
            del timeout
            puzzle = [[None] * 9 for _ in range(9)]
            solution = [
                [str((i * 9 + j + 1) % 9 + 1) for j in range(9)] for i in range(9)
            ]
            return puzzle, solution

        mock_window = MagicMock()
        mock_window.stack = MagicMock()
        mock_window.loading_screen = MagicMock()
        mock_window.game_scrolled_window = MagicMock()
        manager = DiagonalSudokuManager(mock_window)

        with (
            patch(
                "src.base.manager_base.threading.Thread",
                _InstantThread,
            ),
            patch(
                "src.base.manager_base.GLib.idle_add",
                fake_idle_add,
            ),
            patch(
                "src.base.generator_base.GeneratorBase.generate",
                fake_generate,
            ),
        ):
            with patch.object(manager, "build_grid"):
                manager.start_game(0.5, "Medium", "diagonal")

        assert isinstance(manager.board, DiagonalSudokuBoard)
        assert manager.board.variant == "diagonal"

    def test_classic_manager_start_game_creates_classic_board(self):
        """Verify ClassicSudokuManager.start_game() creates ClassicSudokuBoard."""

        class _InstantThread:
            def __init__(self, *args, target=None, daemon=True, **kwargs):
                del args, daemon, kwargs
                self._target = target or (lambda: None)

            def start(self):
                self._target()

        def fake_idle_add(func, *args, **kwargs):
            return func(*args, **kwargs) or True

        def fake_generate(_self, _difficulty, timeout=5):
            del timeout
            puzzle = [[None] * 9 for _ in range(9)]
            solution = [
                [str((i * 9 + j + 1) % 9 + 1) for j in range(9)] for i in range(9)
            ]
            return puzzle, solution

        mock_window = MagicMock()
        mock_window.stack = MagicMock()
        mock_window.loading_screen = MagicMock()
        mock_window.game_scrolled_window = MagicMock()
        manager = ClassicSudokuManager(mock_window)

        with (
            patch(
                "src.base.manager_base.threading.Thread",
                _InstantThread,
            ),
            patch(
                "src.base.manager_base.GLib.idle_add",
                fake_idle_add,
            ),
            patch(
                "src.base.generator_base.GeneratorBase.generate",
                fake_generate,
            ),
        ):
            with patch.object(manager, "build_grid"):
                manager.start_game(0.5, "Medium", "classic")

        assert isinstance(manager.board, ClassicSudokuBoard)
        assert manager.board.variant == "classic"


class TestDiagonalConflictBehavior:
    def test_center_cell_checks_both_diagonals(self, diagonal_board):
        diagonal_board.user_inputs[0][0] = "5"
        diagonal_board.user_inputs[0][8] = "5"

        conflicts = diagonal_board.has_conflict(4, 4, "5")

        assert (0, 0) in conflicts
        assert (0, 8) in conflicts

    def test_main_diagonal_conflict_uses_puzzle_value(self, diagonal_board):
        diagonal_board.puzzle[0][0] = "7"

        conflicts = diagonal_board.has_conflict(8, 8, "7")

        assert (0, 0) in conflicts

    def test_get_existing_value_prefers_puzzle_over_user_input(self, diagonal_board):
        diagonal_board.puzzle[2][2] = "4"
        diagonal_board.user_inputs[2][2] = "9"

        assert diagonal_board._get_existing_value(2, 2) == "4"

    def test_iter_diagonal_cells_for_center_includes_both_diagonals(
        self, diagonal_board
    ):
        cells = set(diagonal_board._iter_diagonal_cells(4, 4))

        assert len(cells) == 16
        assert (0, 0) in cells
        assert (0, 8) in cells
        assert (4, 4) not in cells


class TestDiagonalHighlightBehavior:
    def test_highlight_conflicts_marks_diagonal_matches(self):
        cells = _make_cells()
        cells[0][0].value = "5"
        cells[0][1].value = "5"

        conflicts = DiagonalUIHelpers.highlight_conflicts(cells, 4, 4, "5", 3)

        assert cells[0][0] in conflicts
        assert "conflict" in cells[0][0].highlights
        assert cells[0][1] not in conflicts

    def test_highlight_related_cells_marks_diagonals_when_enabled(self):
        PreferencesManager.set_preferences(_HighlightPreferences())
        cells = _make_cells()

        DiagonalUIHelpers.highlight_related_cells(cells, 4, 4, 3)

        assert "highlight" in cells[0][0].highlights
        assert "highlight" in cells[0][8].highlights
        assert "highlight" not in cells[0][1].highlights
