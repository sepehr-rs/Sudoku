from unittest.mock import MagicMock, patch

import pytest


from src.variants.classic_sudoku.board import ClassicSudokuBoard
from src.variants.classic_sudoku.manager import ClassicSudokuManager


class _FakeStyleContext:
    def __init__(self, initial_classes=None):
        self.classes = set(initial_classes or [])

    def add_class(self, class_name):
        self.classes.add(class_name)

    def has_class(self, class_name):
        return class_name in self.classes


class _FakeGrid:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.attachments = []
        self.name = None
        self.style_context = _FakeStyleContext()

    def set_name(self, name):
        self.name = name

    def attach(self, child, left, top, width, height):
        self.attachments.append((child, left, top, width, height))

    def get_style_context(self):
        return self.style_context


class _FakeAspectFrame:
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.child = None
        self.visible = False

    def set_hexpand(self, value):
        self.hexpand = value

    def set_vexpand(self, value):
        self.vexpand = value

    def set_halign(self, value):
        self.halign = value

    def set_valign(self, value):
        self.valign = value

    def set_child(self, child):
        self.child = child

    def show(self):
        self.visible = True


class _FakeSudokuCell:
    def __init__(self, row, col, value, editable):
        self.row = row
        self.col = col
        self.initial_value = value
        self.editable = editable
        self.controllers = []
        self.feedback_timeouts_cleared = 0

    def add_controller(self, controller):
        self.controllers.append(controller)

    def clear_feedback_timeout(self):
        self.feedback_timeouts_cleared += 1


def _build_board():
    with patch(
        "src.base.generator_base.GeneratorBase.generate",
        return_value=(
            [[None for _ in range(9)] for _ in range(9)],
            [[None for _ in range(9)] for _ in range(9)],
        ),
    ):
        board = ClassicSudokuBoard(0.5, "Medium", "classic")

    board.puzzle[0][0] = "9"
    board.puzzle[4][4] = "5"
    return board


def _build_manager(board):
    manager = ClassicSudokuManager(MagicMock())
    manager.board = board

    grid_container = MagicMock()
    grid_container.get_first_child.return_value = None

    bp_bin = MagicMock()
    bp_bin.get_style_context.return_value = _FakeStyleContext()

    manager.window = MagicMock()
    manager.window.grid_container = grid_container
    manager.window.bp_bin = bp_bin
    manager.window._apply_compact = MagicMock()
    return manager


def test_build_grid_creates_expected_classic_structure():
    board = _build_board()
    manager = _build_manager(board)

    def fake_grid_factory(**kwargs):
        return _FakeGrid(**kwargs)

    with (
        patch(
            "src.variants.classic_sudoku.manager.Gtk.Grid",
            side_effect=fake_grid_factory,
        ),
        patch(
            "src.variants.classic_sudoku.manager.Gtk.AspectFrame",
            side_effect=lambda **kwargs: _FakeAspectFrame(**kwargs),
        ),
        patch(
            "src.variants.classic_sudoku.manager.SudokuCell",
            side_effect=lambda row, col, value, editable: _FakeSudokuCell(
                row, col, value, editable
            ),
        ),
    ):
        manager.build_grid()

    assert manager.parent_grid.name == "sudoku-parent-grid"
    assert len(manager.cell_inputs) == 9
    assert all(len(row) == 9 for row in manager.cell_inputs)
    assert sum(len(row) for row in manager.cell_inputs) == 81

    assert manager.cell_inputs[0][0].initial_value == "9"
    assert manager.cell_inputs[0][0].editable is False
    assert manager.cell_inputs[4][4].initial_value == "5"
    assert manager.cell_inputs[4][4].editable is False
    assert manager.cell_inputs[0][1].initial_value is None
    assert manager.cell_inputs[0][1].editable is True
    assert all(cell.controllers for row in manager.cell_inputs for cell in row)


def test_build_grid_wraps_appends_and_reapplies_layout():
    board = _build_board()
    manager = _build_manager(board)

    with (
        patch(
            "src.variants.classic_sudoku.manager.Gtk.Grid",
            side_effect=lambda **kwargs: _FakeGrid(**kwargs),
        ),
        patch(
            "src.variants.classic_sudoku.manager.Gtk.AspectFrame",
            side_effect=lambda **kwargs: _FakeAspectFrame(**kwargs),
        ),
        patch(
            "src.variants.classic_sudoku.manager.SudokuCell",
            side_effect=lambda row, col, value, editable: _FakeSudokuCell(
                row, col, value, editable
            ),
        ),
    ):
        manager.build_grid()

    assert manager.board_frame.child is manager.parent_grid
    manager.window.grid_container.append.assert_called_once_with(manager.board_frame)
    manager.window.grid_container.queue_allocate.assert_called_once()
    manager.window._apply_compact.assert_called_once_with(False, "small")


def test_create_blocks_requires_parent_grid():
    manager = ClassicSudokuManager(MagicMock())
    manager.parent_grid = None

    with pytest.raises(RuntimeError):
        manager._create_blocks(3)


def test_clear_previous_grid_clears_feedback_and_removes_children():
    board = _build_board()
    manager = _build_manager(board)
    existing_cells = [
        [_FakeSudokuCell(r, c, None, True) for c in range(2)] for r in range(2)
    ]
    manager.cell_inputs = existing_cells
    first_child = MagicMock()
    second_child = MagicMock()
    manager.window.grid_container.get_first_child.side_effect = [
        first_child,
        second_child,
        None,
    ]

    manager._clear_previous_grid()

    assert manager._active_popover is None
    assert manager._cell_popover is None
    manager.window.grid_container.remove.assert_any_call(first_child)
    manager.window.grid_container.remove.assert_any_call(second_child)
    assert manager.window.grid_container.remove.call_count == 2
    assert all(
        cell.feedback_timeouts_cleared == 1 for row in existing_cells for cell in row
    )
