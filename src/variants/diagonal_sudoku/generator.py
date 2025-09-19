import random
from sudoku import DiagonalSudoku
from sudoku.base_sudoku import PuzzleGenerator
from ..classic_sudoku.generator import ClassicSudokuGenerator


class DiagonalSudokuGenerator(ClassicSudokuGenerator):
    """Puzzle generator for diagonal Sudoku, reusing Classic logic."""

    def _generate_impl(self, difficulty: float):
        random_seed = random.randint(1, 1_000_000)
        sudoku = PuzzleGenerator.make_puzzle(
            sudoku_cls=DiagonalSudoku,
            size=9,
            difficulty=difficulty,
            ensure_unique=True,
            seed=random_seed,
        )
        puzzle = sudoku.board
        solution = sudoku.solve().board
        return puzzle, solution
