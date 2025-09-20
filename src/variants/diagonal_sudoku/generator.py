# generator.py
#
# Copyright 2025 sepehr-rs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

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
