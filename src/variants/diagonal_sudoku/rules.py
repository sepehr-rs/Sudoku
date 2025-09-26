# rules.py
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

from ..classic_sudoku.rules import ClassicSudokuRules


class DiagonalSudokuRules(ClassicSudokuRules):
    def is_valid(self, grid, row, col, value) -> bool:
        if not super().is_valid(grid, row, col, value):
            return False

        size = self.size
        # Main diagonal
        if row == col:
            if value in [grid[i][i] for i in range(size) if i != row]:
                return False
        # Anti-diagonal
        if row + col == size - 1:
            if value in [grid[i][size - 1 - i] for i in range(size) if i != row]:
                return False
        return True
