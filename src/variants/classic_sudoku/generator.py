import random
from sudoku.base_sudoku import PuzzleGenerator
from sudoku import ClassicSudoku
from ...base.generator_base import GeneratorBase


class ClassicSudokuGenerator(GeneratorBase):
    """Puzzle generator for classic Sudoku."""

    def _generate_impl(self, difficulty: float):
        random_seed = random.randint(1, 1_000_000)
        sudoku = PuzzleGenerator.make_puzzle(
            sudoku_cls=ClassicSudoku,
            size=9,
            difficulty=difficulty,
            ensure_unique=True,
            seed=random_seed,
        )
        puzzle = sudoku.board
        solution = sudoku.solve().board
        return puzzle, solution
