from ....base.manager_base import ManagerBase
from .board import ClassicSudokuBoard
from .sudoku_cell import SudokuCell
from gi.repository import Gtk


class ClassicSudokuManager(ManagerBase):
    def __init__(self, window):
        super().__init__(window, ClassicSudokuBoard)
        self.blocks = []  # keep blocks for subgrid access

    def build_grid(self):
        grid_size = 9
        block_size = 3
        self.cell_inputs = [[None for _ in range(grid_size)] for _ in range(grid_size)]
        self.blocks = [[[] for _ in range(block_size)] for _ in range(block_size)]

        for row in range(grid_size):
            for col in range(grid_size):
                cell_value = self.board.puzzle[row][col]
                cell = SudokuCell(row, col, cell_value, self.board)
                self.cell_inputs[row][col] = cell

                # put into Gtk grid
                self.window.grid_container.attach(cell, col, row, 1, 1)

                # also store in block structure
                br, bc = row // block_size, col // block_size
                self.blocks[br][bc].append(cell)

        self.window.grid_container.show_all()

    def highlight_rules(self, row: int, col: int):
        # Row + column highlight (from ManagerBase)
        super().highlight_rules(row, col)

        # Block highlight using stored structure
        br, bc = row // 3, col // 3
        for cell in self.blocks[br][bc]:
            cell.highlight()
