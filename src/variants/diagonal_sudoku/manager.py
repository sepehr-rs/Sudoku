from ..classic_sudoku.manager import ClassicSudokuManager
from .board import DiagonalSudokuBoard
from .ui_helpers import DiagonalUIHelpers


class DiagonalSudokuManager(ClassicSudokuManager):
    def __init__(self, window):
        super().__init__(window)
        self.board_cls = DiagonalSudokuBoard
        self.key_map, self.remove_keys = DiagonalUIHelpers.setup_key_mappings()
        self.ui_helpers = DiagonalUIHelpers

    def on_cell_clicked(self, gesture, n_press, x, y, cell):
        """Handle mouse clicks on a cell (diagonal-aware)."""
        # Use diagonal-aware highlighting
        self.ui_helpers.highlight_related_cells(
            self.cell_inputs, cell.row, cell.col, self.board.rules.block_size
        )

        if cell.is_editable() and n_press == 1:
            self._show_popover(cell, gesture.get_current_button())
        else:
            cell.grab_focus()

    def _focus_cell(self, row: int, col: int):
        """Handle keyboard navigation focus (diagonal-aware)."""
        size = self.board.rules.size
        if 0 <= row < size and 0 <= col < size:
            cell = self.cell_inputs[row][col]
            if cell:
                cell.grab_focus()
                # Use diagonal-aware highlighting
                self.ui_helpers.highlight_related_cells(
                    self.cell_inputs,
                    row,
                    col,
                    self.board.rules.block_size,
                    cell.is_editable(),
                )
