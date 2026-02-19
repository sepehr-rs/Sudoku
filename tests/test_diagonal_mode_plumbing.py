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


class _DummyPreferences:
    def __init__(self):
        self.variant_defaults = {}
        self.general_defaults = {}

    def general(self, _key, default=None):
        return default


@pytest.fixture(autouse=True)
def _prefs_guard():
    PreferencesManager.set_preferences(_DummyPreferences())
    try:
        yield
    finally:
        PreferencesManager.set_preferences(None)


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

        with patch(
            "src.base.manager_base.threading.Thread",
            _InstantThread,
        ), patch(
            "src.base.manager_base.GLib.idle_add",
            fake_idle_add,
        ), patch(
            "src.base.generator_base.GeneratorBase.generate",
            fake_generate,
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

        with patch(
            "src.base.manager_base.threading.Thread",
            _InstantThread,
        ), patch(
            "src.base.manager_base.GLib.idle_add",
            fake_idle_add,
        ), patch(
            "src.base.generator_base.GeneratorBase.generate",
            fake_generate,
        ):
            with patch.object(manager, "build_grid"):
                manager.start_game(0.5, "Medium", "classic")

        assert isinstance(manager.board, ClassicSudokuBoard)
        assert manager.board.variant == "classic"
