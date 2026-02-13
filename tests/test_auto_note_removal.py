import pytest

from src.variants.classic_sudoku.board import ClassicSudokuBoard
from src.variants.diagonal_sudoku.board import DiagonalSudokuBoard
from src.variants.classic_sudoku.rules import ClassicSudokuRules
from src.variants.diagonal_sudoku.rules import DiagonalSudokuRules


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


def test_remove_note_from_row_col_block_peers(classic_board):
    r, c, v = 4, 4, "5"
    classic_board.notes[r][c].add(v)

    row_peer = (4, 0)
    col_peer = (0, 4)
    block_peer = (3, 3)
    non_peer = (0, 0)

    classic_board.notes[row_peer[0]][row_peer[1]].add(v)
    classic_board.notes[col_peer[0]][col_peer[1]].add(v)
    classic_board.notes[block_peer[0]][block_peer[1]].add(v)
    classic_board.notes[non_peer[0]][non_peer[1]].add(v)

    affected = classic_board.remove_note_from_peers(r, c, v)

    assert v in classic_board.notes[r][c]
    assert v not in classic_board.notes[row_peer[0]][row_peer[1]]
    assert v not in classic_board.notes[col_peer[0]][col_peer[1]]
    assert v not in classic_board.notes[block_peer[0]][block_peer[1]]
    assert v in classic_board.notes[non_peer[0]][non_peer[1]]

    assert set(affected) == {row_peer, col_peer, block_peer}


def test_diagonal_variant_also_removes_diagonal_peers(diagonal_board):
    r, c, v = 0, 0, "7"
    diagonal_peer = (1, 1)
    non_peer = (4, 8)

    diagonal_board.notes[diagonal_peer[0]][diagonal_peer[1]].add(v)
    diagonal_board.notes[non_peer[0]][non_peer[1]].add(v)

    affected = diagonal_board.remove_note_from_peers(r, c, v)

    assert v not in diagonal_board.notes[diagonal_peer[0]][diagonal_peer[1]]
    assert v in diagonal_board.notes[non_peer[0]][non_peer[1]]
    assert diagonal_peer in set(affected)
