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

from ...base.rules_base import RulesBase


class ClassicSudokuRules(RulesBase):
    block_size: int = 3

    @property
    def size(self) -> int:
        return self.block_size * self.block_size  # 9 for classic Sudoku

    def is_valid(self, grid, row, col, value) -> bool:
        # Row
        if value in grid[row]:
            return False
        # Column
        if value in [grid[r][col] for r in range(self.size)]:
            return False
        # Block
        br, bc = row // self.block_size, col // self.block_size
        for r in range(br * self.block_size, (br + 1) * self.block_size):
            for c in range(bc * self.block_size, (bc + 1) * self.block_size):
                if grid[r][c] == value:
                    return False
        return True

    def is_solved(self, user_inputs, solution) -> bool:
        return user_inputs == solution
