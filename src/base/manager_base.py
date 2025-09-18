from gi.repository import Gtk, Gdk, GLib
from .ui_helpers import UIHelpers


class ManagerBase:
    def __init__(self, window, board_cls):
        self.window = window
        self.board_cls = board_cls
        self.board = None
        self.cell_inputs = []
        self.conflict_cells = []
        self.pencil_mode = False

    def load_saved_game(self):
        self.board = self.board_cls.load_from_file()
        self.build_grid()

    def new_game(self, difficulty, difficulty_label):
        self.board = self.board_cls(difficulty, difficulty_label)
        self.build_grid()

    def build_grid(self):
        """Variant managers override this to build the grid UI."""
        pass

    def setup_key_mappings(self):
        self.key_map, self.remove_keys = UIHelpers.setup_key_mappings()

    def handle_key_press(self, event, cell):
        keyval = event.keyval
        if keyval in self.key_map:
            number = self.key_map[keyval]
            self._fill_cell(cell, number)
            return True
        if keyval in self.remove_keys:
            self._clear_cell(cell)
            return True
        return False


    def _fill_cell(self, cell, number: str, ctrl_is_pressed=False):
        pass

    def _clear_cell(self, cell):
        pass

    def on_cell_filled(self, cell, number: str):
        """
        Abstract correctness feedback.
        Subclasses can override, or rely on default behavior using specify_cell_correctness.
        """
        pass

    def _show_puzzle_finished_dialog(self):
        pass
        #TODO: FIX THIS

    def on_pencil_toggled(self, button: Gtk.ToggleButton):
        """Shared handler for pencil mode toggling."""
        self.pencil_mode = button.get_active()
        logging.info(
            "Pencil Mode is now ON" if self.pencil_mode else "Pencil mode is now OFF"
        )

    def on_grid_unfocus(self):
        """Clear highlights when clicking outside the grid."""
        if self.cell_inputs:
            UIHelpers.clear_highlights(self.cell_inputs, "highlight")
        if self.conflict_cells:
            UIHelpers.clear_highlights([self.conflict_cells], "conflict")
            self.conflict_cells.clear()