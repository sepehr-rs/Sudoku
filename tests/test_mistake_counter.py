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


def _load_sudoku_window():
    """Import SudokuWindow with mocks that preserve the class under @Gtk.Template."""
    import sys
    from unittest.mock import MagicMock

    # Remove stale cache so the module is re-imported with the right mock.
    for key in list(sys.modules.keys()):
        if key == "src.window" or key.startswith("src.window."):
            del sys.modules[key]

    # Make Gtk.Template an identity decorator so SudokuWindow stays a real class.
    def _template(**_kwargs):
        def _decorator(cls):
            return cls
        return _decorator

    # Patch both the sys.modules entry AND the gi.repository attribute, because
    # `from gi.repository import Gtk` resolves via the gi.repository MagicMock's
    # attribute (not sys.modules['gi.repository.Gtk']).
    gtk_mock = MagicMock()
    gtk_mock.Template = _template
    gtk_mock.Template.Child = MagicMock
    sys.modules["gi.repository.Gtk"] = gtk_mock
    sys.modules["gi.repository"].Gtk = gtk_mock

    # Adw.ApplicationWindow must be a real class so SudokuWindow can inherit from it.
    class _FakeAdwWindow:
        pass

    adw_mock = sys.modules["gi.repository.Adw"]
    adw_mock.ApplicationWindow = _FakeAdwWindow
    sys.modules["gi.repository"].Adw = adw_mock

    from src.window import SudokuWindow
    return SudokuWindow


def test_subtitle_includes_mistakes_when_counter_enabled(manager_with_board):
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return True
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())
    SudokuWindow = _load_sudoku_window()

    manager = manager_with_board
    manager.board.variant = "classic"
    manager.board.difficulty_label = "Easy"
    manager.board.mistake_count = 2

    window = SudokuWindow.__new__(SudokuWindow)
    window.manager = manager
    window.sudoku_window_title = MagicMock()
    window.main_menu_box = object()
    window.finished_page = object()
    window.loading_screen = object()
    window.pencil_toggle_button = MagicMock()
    window.pencil_toggle_button.get_active = MagicMock(return_value=False)
    window.stack = MagicMock()
    window.stack.get_visible_child = MagicMock(return_value=object())

    SudokuWindow.refresh_game_subtitle(window)

    args, _kwargs = window.sudoku_window_title.set_subtitle.call_args
    assert "Mistakes: 2" in args[0]


def test_subtitle_omits_mistakes_when_counter_disabled(manager_with_board):
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return False
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())
    SudokuWindow = _load_sudoku_window()

    manager = manager_with_board
    manager.board.variant = "classic"
    manager.board.difficulty_label = "Easy"
    manager.board.mistake_count = 2

    window = SudokuWindow.__new__(SudokuWindow)
    window.manager = manager
    window.sudoku_window_title = MagicMock()
    window.main_menu_box = object()
    window.finished_page = object()
    window.loading_screen = object()
    window.pencil_toggle_button = MagicMock()
    window.pencil_toggle_button.get_active = MagicMock(return_value=False)
    window.stack = MagicMock()
    window.stack.get_visible_child = MagicMock(return_value=object())

    SudokuWindow.refresh_game_subtitle(window)

    args, _kwargs = window.sudoku_window_title.set_subtitle.call_args
    assert "Mistakes" not in args[0]
    assert "Classic" in args[0]
    assert "Easy" in args[0]


def test_increment_triggers_game_over_at_limit(manager_with_board):
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return True
            if key == "mistake_limit":
                return 2
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())
    manager = manager_with_board
    manager._trigger_game_over = MagicMock()

    manager._increment_mistake_count()
    assert not manager._trigger_game_over.called

    manager._increment_mistake_count()
    assert manager._trigger_game_over.called


def test_increment_does_not_trigger_when_counter_disabled(manager_with_board):
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return False
            if key == "mistake_limit":
                return 1
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())
    manager = manager_with_board
    manager._trigger_game_over = MagicMock()

    for _ in range(5):
        manager._increment_mistake_count()

    assert not manager._trigger_game_over.called


def test_increment_does_not_trigger_below_limit(manager_with_board):
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return True
            if key == "mistake_limit":
                return 5
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())
    manager = manager_with_board
    manager._trigger_game_over = MagicMock()

    for _ in range(4):
        manager._increment_mistake_count()

    assert not manager._trigger_game_over.called
    assert manager.board.mistake_count == 4


def test_classic_cleanup_active_grid_clears_feedback(manager_with_board):
    manager = manager_with_board
    manager._popdown_active_popover = lambda: setattr(manager, "_popdown_called", True)

    calls = {"cells_cleared": 0}

    class _FeedbackCell:
        def clear_feedback_timeout(self):
            calls["cells_cleared"] += 1

    manager.cell_inputs = [[_FeedbackCell() for _ in range(3)] for _ in range(3)]

    manager._cleanup_active_grid()

    assert getattr(manager, "_popdown_called", False) is True
    assert calls["cells_cleared"] == 9
    assert manager._active_popover is None
    assert manager._cell_popover is None


def test_game_over_page_populate_sets_stats():
    import sys
    from unittest.mock import MagicMock

    # Remove stale cache so the module is re-imported with the right mock.
    for key in list(sys.modules.keys()):
        if key == "src.screens.game_over_page" or key.startswith("src.screens.game_over_page."):
            del sys.modules[key]

    # Make Gtk.Template an identity decorator so GameOverPage stays a real class.
    def _template(**_kwargs):
        def _decorator(cls):
            return cls
        return _decorator

    # Create real fake base classes
    class _FakeGtkBox:
        def connect(self, *args, **kwargs):
            pass

    gtk_mock = MagicMock()
    gtk_mock.Template = _template
    gtk_mock.Template.Child = MagicMock
    gtk_mock.Box = _FakeGtkBox
    sys.modules["gi.repository.Gtk"] = gtk_mock
    sys.modules["gi.repository"].Gtk = gtk_mock

    # Adw.StyleManager must exist for __init__ to work.
    class _FakeStyleManager:
        @staticmethod
        def get_default():
            return MagicMock(connect=MagicMock())

    adw_mock = sys.modules["gi.repository.Adw"]
    adw_mock.StyleManager = _FakeStyleManager
    sys.modules["gi.repository"].Adw = adw_mock

    from src.screens.game_over_page import GameOverPage

    page = GameOverPage.__new__(GameOverPage)
    page.subtitle_label = MagicMock()
    page.stats_mistakes_value = MagicMock()
    page.stats_progress_value = MagicMock()
    page.stats_difficulty_value = MagicMock()

    page.populate(mistakes=3, percent=47, difficulty="Medium")

    page.subtitle_label.set_label.assert_called_once()
    subtitle_arg = page.subtitle_label.set_label.call_args[0][0]
    assert "3" in subtitle_arg

    page.stats_mistakes_value.set_label.assert_called_once_with("3")
    page.stats_progress_value.set_label.assert_called_once_with("47%")
    page.stats_difficulty_value.set_label.assert_called_once_with("Medium")
