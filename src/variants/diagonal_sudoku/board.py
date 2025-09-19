from ..classic_sudoku.board import ClassicSudokuBoard
from .rules import DiagonalSudokuRules
from .generator import DiagonalSudokuGenerator

class DiagonalSudokuBoard(ClassicSudokuBoard):
    def __init__(self, difficulty: float, difficulty_label: str):
        super().__init__(difficulty, difficulty_label)
        self.rules = DiagonalSudokuRules()
        self.generator = DiagonalSudokuGenerator()
        self.puzzle, self.solution = self.generator.generate(difficulty)
