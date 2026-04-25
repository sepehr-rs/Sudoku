import json
import sys
from unittest.mock import MagicMock

import pytest


# Mock GTK modules before importing board code
sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Gdk"] = MagicMock()
sys.modules["gi.repository.GLib"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()

from src.base.preferences_manager import PreferencesManager
from src.variants.classic_sudoku.board import ClassicSudokuBoard
from src.variants.classic_sudoku.rules import ClassicSudokuRules
from src.variants.diagonal_sudoku.board import DiagonalSudokuBoard
from src.variants.diagonal_sudoku.rules import DiagonalSudokuRules


class _DummyPreferences:
    def __init__(self):
        self.variant_defaults = {
            "highlight_block": True,
            "highlight_related_cells": True,
            "highlight_diagonals": True,
        }
        self.general_defaults = {
            "highlight_row": True,
            "highlight_column": True,
            "casual_mode": [False, True],
            "prevent_conflicting_pencil_notes": True,
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


def _sample_solution():
    return [[str((r * 3 + r // 3 + c) % 9 + 1) for c in range(9)] for r in range(9)]


def _sample_puzzle(solution):
    return [
        [solution[r][c] if (r + c) % 4 == 0 else None for c in range(9)]
        for r in range(9)
    ]


def _sample_user_inputs(solution, puzzle):
    return [
        [
            solution[r][c] if puzzle[r][c] is None and (r + c) % 5 == 0 else None
            for c in range(9)
        ]
        for r in range(9)
    ]


def _sample_notes():
    return [
        [
            {"1", "3"} if (r, c) == (0, 1) else ({"7"} if (r, c) == (4, 4) else set())
            for c in range(9)
        ]
        for r in range(9)
    ]


def _build_board(board_cls, rules, variant):
    solution = _sample_solution()
    puzzle = _sample_puzzle(solution)
    user_inputs = _sample_user_inputs(solution, puzzle)
    notes = _sample_notes()

    board = board_cls.__new__(board_cls)
    board.rules = rules
    board.generator = MagicMock()
    board.difficulty = 0.5
    board.difficulty_label = "Medium"
    board.variant = variant
    board.puzzle = puzzle
    board.solution = solution
    board.user_inputs = user_inputs
    board.notes = notes
    return board


def test_classic_save_load_roundtrip_preserves_board_state(tmp_path):
    board = _build_board(ClassicSudokuBoard, ClassicSudokuRules(), "classic")
    save_path = tmp_path / "classic-save.json"

    board.save_to_file(str(save_path))

    loaded = ClassicSudokuBoard.load_from_file(str(save_path))

    assert loaded is not None
    assert loaded.variant == "classic"
    assert loaded.puzzle == board.puzzle
    assert loaded.solution == board.solution
    assert loaded.user_inputs == board.user_inputs
    assert loaded.notes == board.notes
    assert loaded.difficulty == board.difficulty
    assert loaded.difficulty_label == board.difficulty_label


def test_diagonal_save_load_roundtrip_preserves_board_state(tmp_path):
    board = _build_board(DiagonalSudokuBoard, DiagonalSudokuRules(), "diagonal")
    save_path = tmp_path / "diagonal-save.json"

    board.save_to_file(str(save_path))

    loaded = DiagonalSudokuBoard.load_from_file(str(save_path))

    assert loaded is not None
    assert loaded.variant == "diagonal"
    assert loaded.puzzle == board.puzzle
    assert loaded.solution == board.solution
    assert loaded.user_inputs == board.user_inputs
    assert loaded.notes == board.notes
    assert isinstance(loaded.rules, DiagonalSudokuRules)


def test_save_serializes_notes_as_lists(tmp_path):
    board = _build_board(ClassicSudokuBoard, ClassicSudokuRules(), "classic")
    save_path = tmp_path / "serialized-notes.json"

    board.save_to_file(str(save_path))

    with open(save_path, encoding="utf-8") as file_obj:
        state = json.load(file_obj)

    assert sorted(state["notes"][0][1]) == ["1", "3"]
    assert state["notes"][4][4] == ["7"]
    assert state["variant"] == "classic"


def test_classic_load_defaults_missing_optional_fields(tmp_path):
    save_data = {
        "difficulty": 0.25,
        "puzzle": [[None] * 9 for _ in range(9)],
        "solution": _sample_solution(),
        "user_inputs": [[None] * 9 for _ in range(9)],
        "notes": [[[] for _ in range(9)] for _ in range(9)],
    }
    save_path = tmp_path / "legacy-save.json"
    with open(save_path, "w", encoding="utf-8") as file_obj:
        json.dump(save_data, file_obj)

    loaded = ClassicSudokuBoard.load_from_file(str(save_path))

    assert loaded is not None
    assert loaded.difficulty_label == "Unknown"
    assert loaded.variant == "Unknown"
    assert (
        loaded.variant_preferences
        == PreferencesManager.get_preferences().variant_defaults
    )
    assert (
        loaded.general_preferences
        == PreferencesManager.get_preferences().general_defaults
    )
