# classic_sudoku/generator.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import random
from sudoku import ClassicSudoku
from sudoku.base_sudoku import PuzzleGenerator
from ...core.generator import CoreSudokuGenerator


class ClassicSudokuGenerator(CoreSudokuGenerator):

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
