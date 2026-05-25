from ..classic_sudoku.manager import ClassicSudokuManager
from .board import DiagonalSudokuBoard
from .ui_helpers import DiagonalUIHelpers


class DiagonalSudokuManager(ClassicSudokuManager):
    def __init__(self, window):
        super().__init__(window)
        self.board_cls = DiagonalSudokuBoard
        self.key_map, self.remove_keys = DiagonalUIHelpers.setup_key_mappings()
        self.ui_helpers = DiagonalUIHelpers

    def _focus_cell(self, row: int, col: int):
        board = self._require_board("Illegal state: cannot focus cell without a board")
        size = board.rules.size
        if 0 <= row < size and 0 <= col < size:
            cell = self.cell_inputs[row][col]
            if cell:
                cell.grab_focus()
                self.ui_helpers.highlight_related_cells(
                    self.cell_inputs,
                    row,
                    col,
                    board.rules.block_size,
                    cell.is_editable(),
                )

    def get_ui_helpers(self):
        return DiagonalUIHelpers
