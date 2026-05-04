from unittest.mock import MagicMock, patch

import pytest


from src.variants.classic_sudoku.board import ClassicSudokuBoard
from src.variants.classic_sudoku.manager import ClassicSudokuManager, Gdk
from src.variants.classic_sudoku.rules import ClassicSudokuRules


class MockCell:
    def __init__(self, row, col, value=None, editable=True):
        self.row = row
        self.col = col
        self.value = value
        self.editable_state = editable
        self.notes = set()
        self.cleared = False

    def is_editable(self):
        return self.editable_state

    def get_value(self):
        return self.value

    def set_value(self, value):
        self.value = value

    def update_notes(self, notes):
        self.notes = set(notes)

    def clear(self):
        self.value = None
        self.cleared = True

    def grab_focus(self):
        pass


@pytest.fixture
def classic_board():
    board = ClassicSudokuBoard.__new__(ClassicSudokuBoard)
    board.rules = ClassicSudokuRules()
    board.puzzle = [[None for _ in range(9)] for _ in range(9)]
    board.user_inputs = [[None for _ in range(9)] for _ in range(9)]
    board.solution = [
        [str((r * 3 + r // 3 + c) % 9 + 1) for c in range(9)] for r in range(9)
    ]
    board.notes = [[set() for _ in range(9)] for _ in range(9)]
    return board


@pytest.fixture
def manager(classic_board):
    test_manager = ClassicSudokuManager.__new__(ClassicSudokuManager)
    test_manager.board = classic_board
    test_manager.pencil_mode = False
    test_manager.conflict_cells = []
    test_manager.key_map = {Gdk.KEY_5: "5"}
    test_manager.remove_keys = (Gdk.KEY_BackSpace, Gdk.KEY_Delete)
    test_manager.cell_inputs = [[MockCell(r, c) for c in range(9)] for r in range(9)]
    return test_manager


def test_board_input_accessors(classic_board):
    classic_board.set_input(2, 3, "7")

    assert classic_board.get_input(2, 3) == "7"

    classic_board.clear_input(2, 3)

    assert classic_board.get_input(2, 3) is None


def test_board_notes_toggle_and_lookup(classic_board):
    classic_board.toggle_note(1, 1, "4")
    classic_board.toggle_note(1, 1, "7")

    assert classic_board.get_notes(1, 1) == {"4", "7"}

    classic_board.toggle_note(1, 1, "4")

    assert classic_board.get_notes(1, 1) == {"7"}


def test_board_is_clue_and_correct_value(classic_board):
    classic_board.puzzle[0][0] = "5"

    assert classic_board.is_clue(0, 0) is True
    assert classic_board.is_clue(0, 1) is False
    assert classic_board.get_correct_value(0, 0) == classic_board.solution[0][0]


def test_is_solved_requires_non_clue_matches(classic_board):
    classic_board.puzzle[0][0] = classic_board.solution[0][0]

    assert classic_board.is_solved() is False

    for row in range(9):
        for col in range(9):
            if not classic_board.is_clue(row, col):
                classic_board.user_inputs[row][col] = classic_board.solution[row][col]

    assert classic_board.is_solved() is True


def test_handle_number_keys_routes_to_fill_cell_with_ctrl(manager):
    with patch.object(manager, "_fill_cell") as fill_cell:
        handled = manager._handle_number_keys(Gdk.KEY_5, True, 2, 4)

    assert handled is True
    fill_cell.assert_called_once_with(
        manager.cell_inputs[2][4], "5", ctrl_is_pressed=True
    )


def test_handle_unicode_digit_routes_to_fill_cell(manager):
    with (
        patch(
            "src.variants.classic_sudoku.manager.Gdk.keyval_to_unicode",
            return_value=ord("7"),
        ),
        patch.object(manager, "_fill_cell") as fill_cell,
    ):
        handled = manager._handle_unicode_digit(object(), False, 3, 5)

    assert handled is True
    fill_cell.assert_called_once_with(
        manager.cell_inputs[3][5], "7", ctrl_is_pressed=False
    )


def test_handle_enter_key_opens_popover_for_editable_cell(manager):
    with patch.object(manager, "_show_popover") as show_popover:
        handled = manager._handle_enter_key(Gdk.KEY_Return, 1, 2)

    assert handled is True
    show_popover.assert_called_once_with(manager.cell_inputs[1][2])


def test_handle_remove_keys_uses_delete_as_clear_all(manager):
    with patch.object(manager, "_clear_cell") as clear_cell:
        handled = manager._handle_remove_keys(Gdk.KEY_Delete, 4, 6)

    assert handled is True
    clear_cell.assert_called_once_with(manager.cell_inputs[4][6], clear_all=True)


def test_on_number_selected_primary_click_closes_popover(manager):
    manager.pencil_mode = False
    manager._restore_focus_on_popover_close = True
    number_button = MagicMock()
    number_button.get_label.return_value = "8"
    popover = MagicMock()

    with patch.object(manager, "_fill_cell") as fill_cell:
        manager.on_number_selected(number_button, manager.cell_inputs[0][0], popover, 1)

    fill_cell.assert_called_once_with(
        manager.cell_inputs[0][0], "8", ctrl_is_pressed=False
    )
    assert manager._restore_focus_on_popover_close is False
    popover.popdown.assert_called_once()


def test_on_clear_selected_clears_cell_and_closes_popover(manager):
    manager._restore_focus_on_popover_close = True
    popover = MagicMock()

    with patch.object(manager, "_clear_cell") as clear_cell:
        manager.on_clear_selected(MagicMock(), manager.cell_inputs[2][2], popover)

    clear_cell.assert_called_once_with(manager.cell_inputs[2][2])
    assert manager._restore_focus_on_popover_close is False
    popover.popdown.assert_called_once()


def test_clear_cell_clear_all_removes_value_notes_and_saves(manager):
    manager.board.save_to_file = MagicMock()
    target_cell = manager.cell_inputs[1][1]
    target_cell.set_value("9")
    manager.board.user_inputs[1][1] = "9"
    manager.board.notes[1][1] = {"1", "3"}

    manager._clear_cell(target_cell, clear_all=True)

    assert manager.board.get_input(1, 1) is None
    assert manager.board.get_notes(1, 1) == set()
    assert target_cell.cleared is True
    assert target_cell.notes == set()
    manager.board.save_to_file.assert_called_once()


def test_clear_cell_in_pencil_mode_removes_highest_note_only(manager):
    manager.board.save_to_file = MagicMock()
    manager.pencil_mode = True
    target_cell = manager.cell_inputs[0][0]
    manager.board.notes[0][0] = {"1", "4", "9"}

    manager._clear_cell(target_cell)

    assert manager.board.get_notes(0, 0) == {"1", "4"}
    assert target_cell.notes == {"1", "4"}
    manager.board.save_to_file.assert_called_once()
