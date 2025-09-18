from ...base.rules_base import RulesBase


class ClassicSudokuRules(RulesBase):
    block_size: int = 3

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
