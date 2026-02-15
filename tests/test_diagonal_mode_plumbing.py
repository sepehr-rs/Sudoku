"""Tests for diagonal mode plumbing fixes (issue #273)."""

import json
import os
import sys
import tempfile
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock, patch

# Mock GTK modules before importing anything else
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()

import pytest


class _DummyPreferences:
    def __init__(self):
        self.variant_defaults = {}
        self.general_defaults = {}

    def general(self, _key, default=None):
        return default


@pytest.fixture(autouse=True)
def _prefs_guard():
    from src.base.preferences_manager import PreferencesManager

    old = PreferencesManager.get_preferences()
    PreferencesManager.set_preferences(_DummyPreferences())
    try:
        yield
    finally:
        PreferencesManager.set_preferences(old)


class TestDiagonalBoardLoadFromFile:
    """Tests for DiagonalSudokuBoard.load_from_file."""

    def test_load_from_file_uses_diagonal_rules(self, tmp_path):
        """Verify loaded board has DiagonalSudokuRules."""
        from src.variants.diagonal_sudoku.board import DiagonalSudokuBoard
        from src.variants.diagonal_sudoku.generator import DiagonalSudokuGenerator
        from src.variants.diagonal_sudoku.rules import DiagonalSudokuRules

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
        from src.variants.diagonal_sudoku.board import DiagonalSudokuBoard

        missing = os.path.join(tempfile.gettempdir(), "sudoku", "nope.json")
        board = DiagonalSudokuBoard.load_from_file(missing)
        assert board is None


class TestDiagonalBoardVariantIdentifier:
    """Tests for variant identifier storage."""

    def test_save_uses_diagonal_identifier(self, tmp_path):
        """Verify saved file has variant='diagonal'."""
        from src.variants.diagonal_sudoku.board import DiagonalSudokuBoard

        board = DiagonalSudokuBoard.__new__(DiagonalSudokuBoard)
        board.difficulty = 0.5
        board.difficulty_label = "Medium"
        board.variant = "diagonal"
        board.puzzle = [[None] * 9 for _ in range(9)]
        board.solution = [[None] * 9 for _ in range(9)]
        board.user_inputs = [[None] * 9 for _ in range(9)]
        board.notes = [[set() for _ in range(9)] for _ in range(9)]

        save_file = tmp_path / "test_save.json"
        board.save_to_file(str(save_file))

        with open(save_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["variant"] == "diagonal"


class TestManagerBoardClassUsage:
    """Tests for manager using self.board_cls."""

    def test_diagonal_manager_uses_diagonal_board_cls(self):
        """Verify DiagonalSudokuManager sets board_cls to DiagonalSudokuBoard."""
        from src.variants.diagonal_sudoku.board import DiagonalSudokuBoard
        from src.variants.diagonal_sudoku.manager import DiagonalSudokuManager

        mock_window = MagicMock()
        manager = DiagonalSudokuManager(mock_window)

        assert manager.board_cls == DiagonalSudokuBoard

    def test_start_game_instantiates_using_board_cls_not_classic(self):
        """Regression: start_game must instantiate self.board_cls."""
        from src.variants.diagonal_sudoku.manager import DiagonalSudokuManager

        class FakeBoard:
            def __init__(self, difficulty, difficulty_label, variant):
                self.difficulty = difficulty
                self.difficulty_label = difficulty_label
                self.variant = variant

        mock_window = MagicMock()
        mock_window.stack = MagicMock()
        mock_window.loading_screen = MagicMock()
        mock_window.game_scrolled_window = MagicMock()

        manager = DiagonalSudokuManager(mock_window)
        setattr(manager, "board_cls", FakeBoard)
        manager.build_grid = MagicMock()
        manager._finish_start_game = MagicMock(
            side_effect=lambda board: setattr(manager, "board", board) or False
        )

        class _InstantThread:
            def __init__(self, target, daemon=True):
                self._target = target

            def start(self):
                self._target()

        with patch(
            "src.variants.classic_sudoku.manager.threading.Thread",
            _InstantThread,
        ), patch(
            "src.variants.classic_sudoku.manager.GLib.idle_add",
            lambda cb, board: cb(board),
        ):
            manager.start_game(0.5, "Medium", "diagonal")

        assert isinstance(manager.board, FakeBoard)
        assert manager.board.variant == "diagonal"


class TestGetManagerTypeMigrationGuard:
    """Tests for migration guard in SudokuWindow.get_manager_type."""

    def _import_window_module_with_gtk_stubs(self):
        """Import src.window with minimal GTK stubs (no real GTK runtime)."""
        gtk_stub = ModuleType("gi.repository.Gtk")

        class Template:
            def __init__(self, *args, **kwargs):
                pass

            def __call__(self, cls):
                return cls

            class Child:
                def __init__(self, *args, **kwargs):
                    pass

        setattr(gtk_stub, "Template", Template)
        setattr(gtk_stub, "Align", SimpleNamespace(FILL=0))
        setattr(gtk_stub, "TextDirection", SimpleNamespace(RTL=0))
        setattr(gtk_stub, "GestureClick", MagicMock())

        adw_stub = ModuleType("gi.repository.Adw")
        setattr(adw_stub, "ApplicationWindow", type("ApplicationWindow", (), {}))

        gio_stub = ModuleType("gi.repository.Gio")
        setattr(
            gio_stub,
            "SimpleAction",
            type(
                "SimpleAction",
                (),
                {"new": staticmethod(lambda *_args, **_kwargs: MagicMock())},
            ),
        )

        repo_stub = ModuleType("gi.repository")
        setattr(repo_stub, "Gtk", gtk_stub)
        setattr(repo_stub, "Adw", adw_stub)
        setattr(repo_stub, "Gio", gio_stub)

        gi_stub = ModuleType("gi")
        setattr(gi_stub, "__path__", [])

        game_setup_stub = ModuleType("src.screens.game_setup_dialog")
        setattr(game_setup_stub, "GameSetupDialog", object)
        help_overlay_stub = ModuleType("src.screens.help_overlay")
        setattr(help_overlay_stub, "HelpOverlay", object)
        finished_page_stub = ModuleType("src.screens.finished_page")
        setattr(finished_page_stub, "FinishedPage", object)
        loading_screen_stub = ModuleType("src.screens.loading_screen")
        setattr(loading_screen_stub, "LoadingScreen", object)
        preferences_dialog_stub = ModuleType("src.screens.preferences_dialog")
        setattr(preferences_dialog_stub, "PreferencesDialog", object)

        with patch.dict(
            sys.modules,
            {
                "gi": gi_stub,
                "gi.repository": repo_stub,
                "gi.repository.Gtk": gtk_stub,
                "gi.repository.Adw": adw_stub,
                "gi.repository.Gio": gio_stub,
                "src.screens.game_setup_dialog": game_setup_stub,
                "src.screens.help_overlay": help_overlay_stub,
                "src.screens.finished_page": finished_page_stub,
                "src.screens.loading_screen": loading_screen_stub,
                "src.screens.preferences_dialog": preferences_dialog_stub,
            },
            clear=False,
        ):
            import importlib

            sys.modules.pop("src.window", None)
            return importlib.import_module("src.window")

    def test_get_manager_type_migrates_invalid_diagonal_save_to_classic(self, tmp_path):
        window_mod = self._import_window_module_with_gtk_stubs()
        SudokuWindow = window_mod.SudokuWindow

        solution = [["1" for _ in range(9)] for _ in range(9)]
        save_data = {"variant": "diagonal", "solution": solution}
        save_file = tmp_path / "board.json"
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(save_data, f)

        win = SudokuWindow.__new__(SudokuWindow)
        variant = win.get_manager_type(str(save_file))
        assert variant == "classic"

        with open(save_file, "r", encoding="utf-8") as f:
            migrated = json.load(f)
        assert migrated["variant"] == "classic"

    def test_get_manager_type_keeps_valid_diagonal_save(self, tmp_path):
        window_mod = self._import_window_module_with_gtk_stubs()
        SudokuWindow = window_mod.SudokuWindow

        solution = [["0" for _ in range(9)] for _ in range(9)]
        for i in range(9):
            solution[i][i] = str(i + 1)
            solution[i][8 - i] = str(9 - i)

        save_data = {"variant": "diagonal", "solution": solution}
        save_file = tmp_path / "board.json"
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(save_data, f)

        win = SudokuWindow.__new__(SudokuWindow)
        variant = win.get_manager_type(str(save_file))
        assert variant == "diagonal"
