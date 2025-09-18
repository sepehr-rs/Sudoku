# src/variants/classic_sudoku/manager.py
from gi.repository import Gtk
from ...base.manager_base import ManagerBase
from .board import ClassicSudokuBoard
from .sudoku_cell import SudokuCell


class ClassicSudokuManager(ManagerBase):
    def __init__(self, window):
        super().__init__(window, ClassicSudokuBoard)
        # Load saved game if available
        if ClassicSudokuBoard.has_saved_game():
            self.load_saved_game()

    def build_grid(self):
        """Builds a 9×9 Sudoku grid and attaches SudokuCell widgets."""
        size = self.board.rules.size
        block_size = self.board.rules.block_size

        # Clear previous grid
        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)

        # Parent grid (3x3 blocks)
        parent_grid = Gtk.Grid(
            row_spacing=10,
            column_spacing=10,
            row_homogeneous=True,
            column_homogeneous=True,
        )
        parent_grid.set_name("sudoku-parent-grid")
        self.parent_grid = parent_grid

        # Create 3x3 block grids
        self.blocks = []
        for br in range(3):
            row_blocks = []
            for bc in range(3):
                block = Gtk.Grid(
                    row_spacing=4,
                    column_spacing=4,
                    row_homogeneous=True,
                    column_homogeneous=True,
                )
                block.get_style_context().add_class("sudoku-block")
                row_blocks.append(block)
                parent_grid.attach(block, bc, br, 1, 1)
            self.blocks.append(row_blocks)

        # Initialize 9x9 cell grid
        self.cell_inputs = [[None for _ in range(size)] for _ in range(size)]
        for r in range(size):
            for c in range(size):
                value = self.board.puzzle[r][c]
                editable = not self.board.is_clue(r, c)
                cell = SudokuCell(r, c, value, editable)
                self.cell_inputs[r][c] = cell

                # Mouse gesture for popover
                gesture = Gtk.GestureClick.new()
                gesture.set_button(0)  # Accept any button
                gesture.connect("pressed", self.on_cell_clicked, cell)
                cell.add_controller(gesture)

                # Keyboard controller
                key_controller = Gtk.EventControllerKey()
                key_controller.connect("key-pressed", self.on_key_pressed, r, c)
                cell.add_controller(key_controller)

                # Place cell in correct block
                br, bc = r // block_size, c // block_size
                inner_r, inner_c = r % block_size, c % block_size
                self.blocks[br][bc].attach(cell, inner_c, inner_r, 1, 1)

        # Wrap parent grid in AspectFrame to maintain square shape
        frame = Gtk.AspectFrame(ratio=1.0, obey_child=False)
        frame.set_hexpand(True)
        frame.set_vexpand(True)
        frame.set_halign(Gtk.Align.FILL)
        frame.set_valign(Gtk.Align.FILL)
        frame.set_child(parent_grid)

        self.window.grid_container.append(frame)
        frame.show()
