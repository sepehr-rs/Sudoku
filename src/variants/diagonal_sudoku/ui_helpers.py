from ..classic_sudoku.ui_helpers import ClassicUIHelpers

class DiagonalUIHelpers(ClassicUIHelpers):
    @staticmethod
    def highlight_related_cells(cells, row, col, block_size: int, highlight_diagonal:bool = True):
        ClassicUIHelpers.highlight_related_cells(cells, row, col, block_size)
        if highlight_diagonal:
            size = len(cells)
            if row == col:
                for i in range(size):
                    ClassicUIHelpers.highlight_cell(cells, i, i, "highlight")
            if row + col == size - 1:
                for i in range(size):
                    ClassicUIHelpers.highlight_cell(cells, i, size - 1 - i, "highlight")
