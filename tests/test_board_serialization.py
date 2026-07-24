# tests/test_board_serialization.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import json
from unittest.mock import patch

import pytest

from src.core.persistence import (
    save_game,
    load_game,
    clear_save,
    has_saved_game,
    save_preferences,
    save_general_preferences,
    load_general_preferences,
    load_variant_preferences,
    migrate_preferences_from_board,
)
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
def prefs_path(tmp_path):
    path = tmp_path / "preferences.json"
    with patch(
        "src.core.persistence._get_preferences_path",
        return_value=str(path),
    ):
        yield path


@pytest.fixture
def prefs():
    p = ClassicSudokuPreferences()
    PreferencesManager.set_preferences(p)
    return p


@pytest.fixture
def diagonal_prefs():
    p = DiagonalSudokuPreferences()
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
def diagonal_board(diagonal_prefs):
    board = make_board_state(DiagonalSudokuBoard, puzzle=PUZZLE, solution=SOLUTION)
    board.set_input(1, 0, 4)
    board.toggle_note(2, 2, "9")
    board.mistakes = 1
    board.variant = "diagonal"
    board.variant_preferences = diagonal_prefs.variant_defaults.copy()
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
    def test_preserves_board_state(self, diagonal_board, save_path, prefs_path):
        save_game(diagonal_board)
        save_preferences()
        loaded = load_game(
            DiagonalSudokuBoard,
            generator=ClassicSudokuGenerator(),
            block_size=3,
        )

        assert loaded is not None
        assert loaded.puzzle == diagonal_board.puzzle
        assert loaded.variant == "diagonal"

    def test_notes_roundtrip(self, diagonal_board, save_path, prefs_path):
        save_game(diagonal_board)
        save_preferences()
        loaded = load_game(
            DiagonalSudokuBoard,
            generator=ClassicSudokuGenerator(),
            block_size=3,
        )

        assert loaded.notes[2][2] == {"9"}

    def test_variant_preferences_roundtrip(self, diagonal_board, save_path, prefs_path):
        save_game(diagonal_board)
        save_preferences()
        loaded = load_game(
            DiagonalSudokuBoard,
            generator=ClassicSudokuGenerator(),
            block_size=3,
        )

        assert loaded is not None
        assert loaded.variant_preferences.get("highlight_diagonals") is True


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

    def test_board_json_excludes_preferences(self, classic_board, save_path):
        save_game(classic_board)
        with open(save_path, "r") as f:
            raw = json.load(f)
        assert "general_preferences" not in raw
        assert "variant_preferences" not in raw


class TestClearSave:
    def test_clear_save_removes_file(self, classic_board, save_path):
        save_game(classic_board)
        assert save_path.exists()
        clear_save()
        assert not save_path.exists()

    def test_clear_save_noop_when_no_file(self, save_path):
        assert not save_path.exists()
        clear_save()

    def test_has_saved_game_true_after_save(self, classic_board, save_path):
        save_game(classic_board)
        assert has_saved_game() is True

    def test_has_saved_game_false_after_clear(self, classic_board, save_path):
        save_game(classic_board)
        clear_save()
        assert has_saved_game() is False

    def test_has_saved_game_false_when_no_file(self, save_path):
        assert has_saved_game() is False

    def test_clear_save_does_not_remove_preferences(
        self, classic_board, save_path, prefs_path, prefs
    ):
        save_game(classic_board)
        save_preferences()
        clear_save()
        assert not save_path.exists()
        assert prefs_path.exists()


class TestPreferencesFile:
    def test_save_and_load_general_roundtrip(self, prefs, prefs_path):
        save_preferences()
        loaded = load_general_preferences()
        assert loaded == {**prefs.general_toggles, **prefs.general_counted}

    def test_load_general_returns_defaults_when_no_file(self, prefs, prefs_path):
        loaded = load_general_preferences()
        assert loaded == {**prefs.general_toggles, **prefs.general_counted}

    def test_save_general_overwrites_existing(self, prefs, prefs_path):
        save_preferences()
        updated = {**prefs.general_toggles, **prefs.general_counted}
        updated["casual_mode"] = {"value": False, "tooltip": "test"}
        save_general_preferences(updated)
        loaded = load_general_preferences()
        assert loaded["casual_mode"]["value"] is False

    def test_save_preferences_from_manager(self, prefs, prefs_path):
        prefs.general_toggles["casual_mode"]["value"] = False
        save_preferences()
        with open(prefs_path, "r") as f:
            raw = json.load(f)
        assert raw["casual_mode"]["value"] is False

    def test_save_preferences_writes_variant_by_name(self, diagonal_prefs, prefs_path):
        save_preferences()
        loaded = load_variant_preferences("diagonal")
        assert loaded.get("highlight_diagonals") is True

    def test_load_variant_returns_defaults_for_unknown(self, prefs, prefs_path):
        loaded = load_variant_preferences("nonexistent")
        assert loaded == prefs.variant_defaults

    def test_load_variant_returns_saved_value(self, prefs, prefs_path):
        save_preferences()
        loaded = load_variant_preferences("classic")
        assert loaded == prefs.variant_defaults

    def test_general_preferences_survive_game_clear(
        self, classic_board, save_path, prefs_path, prefs
    ):
        save_preferences()
        clear_save()
        loaded = load_general_preferences()
        assert loaded == {**prefs.general_toggles, **prefs.general_counted}


class TestMigration:
    def test_migrates_both_general_and_variant(
        self, save_path, prefs_path, diagonal_prefs
    ):
        old_state = {
            "puzzle": PUZZLE,
            "solution": SOLUTION,
            "variant": "diagonal",
            "general_preferences": {
                "casual_mode": {"value": False, "tooltip": "test"},
            },
            "variant_preferences": {"highlight_diagonals": True},
        }
        with open(save_path, "w") as f:
            json.dump(old_state, f)

        migrate_preferences_from_board()

        assert prefs_path.exists()
        with open(prefs_path, "r") as f:
            prefs_data = json.load(f)
        assert prefs_data["casual_mode"]["value"] is False
        assert prefs_data["variant_preferences"]["diagonal"] == {
            "highlight_diagonals": True,
        }

        with open(save_path, "r") as f:
            board_data = json.load(f)
        assert "general_preferences" not in board_data
        assert "variant_preferences" not in board_data

    def test_migrates_general_only(self, save_path, prefs_path, prefs):
        old_state = {
            "puzzle": PUZZLE,
            "solution": SOLUTION,
            "variant": "classic",
            "general_preferences": {
                "casual_mode": {"value": False, "tooltip": "test"},
            },
        }
        with open(save_path, "w") as f:
            json.dump(old_state, f)

        migrate_preferences_from_board()

        with open(prefs_path, "r") as f:
            prefs_data = json.load(f)
        assert prefs_data["casual_mode"]["value"] is False
        assert "variant_preferences" not in prefs_data

    def test_migrates_variant_only(self, save_path, prefs_path, prefs):
        old_state = {
            "puzzle": PUZZLE,
            "solution": SOLUTION,
            "variant": "diagonal",
            "variant_preferences": {"highlight_diagonals": True},
        }
        with open(save_path, "w") as f:
            json.dump(old_state, f)

        migrate_preferences_from_board()

        with open(prefs_path, "r") as f:
            prefs_data = json.load(f)
        assert prefs_data["variant_preferences"]["diagonal"] == {
            "highlight_diagonals": True,
        }
        assert "casual_mode" not in prefs_data

    def test_migration_noop_when_prefs_file_exists(self, save_path, prefs_path, prefs):
        old_state = {
            "puzzle": PUZZLE,
            "solution": SOLUTION,
            "general_preferences": {"casual_mode": {"value": True, "tooltip": ""}},
        }
        with open(save_path, "w") as f:
            json.dump(old_state, f)
        with open(prefs_path, "w") as f:
            json.dump({"casual_mode": {"value": False, "tooltip": "existing"}}, f)

        migrate_preferences_from_board()

        with open(prefs_path, "r") as f:
            prefs_data = json.load(f)
        assert prefs_data["casual_mode"]["value"] is False

    def test_migration_noop_when_no_board_file(self, save_path, prefs_path):
        migrate_preferences_from_board()
        assert not prefs_path.exists()

    def test_migration_noop_when_no_preferences_in_board(self, save_path, prefs_path):
        state = {"puzzle": PUZZLE, "solution": SOLUTION, "variant": "classic"}
        with open(save_path, "w") as f:
            json.dump(state, f)

        migrate_preferences_from_board()
        assert not prefs_path.exists()

    def test_migration_old_bool_format(self, save_path, prefs_path, prefs):
        old_state = {
            "puzzle": PUZZLE,
            "solution": SOLUTION,
            "general_preferences": {
                "casual_mode": True,
                "auto_remove_notes": False,
            },
        }
        with open(save_path, "w") as f:
            json.dump(old_state, f)

        migrate_preferences_from_board()

        with open(prefs_path, "r") as f:
            prefs_data = json.load(f)
        assert prefs_data["casual_mode"] == {
            "value": True,
            "tooltip": prefs.general_toggles["casual_mode"]["tooltip"],
        }
        assert prefs_data["auto_remove_notes"]["value"] is False
