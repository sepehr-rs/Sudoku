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
