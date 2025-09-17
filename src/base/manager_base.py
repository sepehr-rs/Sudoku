# src/base/manager_base.py
from abc import ABC, abstractmethod
from gi.repository import Gtk, GLib
from .board_base import BoardBase

class ManagerBase(ABC):
    """Base manager: connects Board + UI (Gtk)."""

    def __init__(self, window, board_class):
        self.window = window
        self.board_class = board_class
        self.board: BoardBase = None
        self.cell_inputs = None  # 2D list of SudokuCell
        self.blocks = []
        self.parent_grid = None
        self.conflict_cells = []
        self.pencil_mode = False

    @abstractmethod
    def build_grid(self):
        """Implement in variant: build Gtk Grid + attach SudokuCell widgets."""
        pass

    # --- Cell focus & highlighting ---
    def _focus_cell(self, row, col):
        self.cell_inputs[row][col].grab_focus()
        self.highlight_related_cells(row, col)

    def highlight_related_cells(self, row, col):
        """Highlight row, column, block, and same-value cells."""
        # Clear previous highlights
        for r in range(self.board.rules.size):
            for c in range(self.board.rules.size):
                self.cell_inputs[r][c].unhighlight("highlight")
        value = self.cell_inputs[row][col].get_value()
        size = self.board.rules.size
        block_size = self.board.rules.block_size

        # Highlight row/col/block
        for i in range(size):
            self.cell_inputs[row][i].highlight("highlight")
            self.cell_inputs[i][col].highlight("highlight")
        br, bc = row // block_size, col // block_size
        for r in range(br*block_size, (br+1)*block_size):
            for c in range(bc*block_size, (bc+1)*block_size):
                self.cell_inputs[r][c].highlight("highlight")

        # Highlight same-value cells
        if value:
            for r in range(size):
                for c in range(size):
                    if self.cell_inputs[r][c].get_value() == value:
                        self.cell_inputs[r][c].highlight("highlight")

    # --- Filling and clearing cells ---
    def _fill_cell(self, cell, number: str, ctrl_is_pressed=False):
        """Fill a cell with a number (handles pencil mode)."""
        self._clear_conflicts()
        row, col = cell.row, cell.col

        if self.pencil_mode or ctrl_is_pressed:
            notes = self.board.get_notes(row, col)
            if number in notes:
                self.board.remove_note(row, col, number)
            else:
                self.board.add_note(row, col, number)
            cell.update_notes(self.board.get_notes(row, col))
            self.board.save_to_file()
            return

        cell.set_value(number)
        self.board.set_input(row, col, number)
        self.board.save_to_file()

        correct = self.board.get_correct_value(row, col)
        if number == correct:
            cell.highlight("correct")
        else:
            cell.highlight("wrong")
            self._highlight_conflicts(row, col, number)

        if self.board.is_solved():
            self._show_puzzle_finished_dialog()

    def _clear_cell(self, cell):
        row, col = cell.row, cell.col
        cell.set_value("")
        cell.update_notes(set())
        self.board.set_input(row, col, None)
        cell.unhighlight("correct")
        cell.unhighlight("wrong")
        self._clear_conflicts()
        self.board.save_to_file()

    def _highlight_conflicts(self, row, col, number):
        """Highlight conflicting cells."""
        size = self.board.rules.size
        block_size = self.board.rules.block_size
        self._clear_conflicts()
        for r in range(size):
            for c in range(size):
                cell = self.cell_inputs[r][c]
                if cell.get_value() == number and (r != row or c != col):
                    if r == row or c == col or (r//block_size == row//block_size and c//block_size == col//block_size):
                        cell.highlight("conflict")
                        self.conflict_cells.append(cell)

    def _clear_conflicts(self):
        for cell in self.conflict_cells:
            cell.unhighlight("conflict")
        self.conflict_cells.clear()

    def _show_puzzle_finished_dialog(self):
        """Default behavior: can be overridden in variant."""
        self.window.stack.set_visible_child(self.window.finished_page)
