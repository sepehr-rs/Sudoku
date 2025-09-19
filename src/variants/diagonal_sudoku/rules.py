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
