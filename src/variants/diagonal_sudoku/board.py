# board.py
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

from ..classic_sudoku.board import ClassicSudokuBoard
from .rules import DiagonalSudokuRules
from .generator import DiagonalSudokuGenerator


class DiagonalSudokuBoard(ClassicSudokuBoard):
    def __init__(self, difficulty: float, difficulty_label: str):
        super().__init__(difficulty, difficulty_label)
        self.rules = DiagonalSudokuRules()
        self.generator = DiagonalSudokuGenerator()
        self.puzzle, self.solution = self.generator.generate(difficulty)
