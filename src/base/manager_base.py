# src/base/manager_base.py
import logging
import threading
import unicodedata
from abc import ABC, abstractmethod
from gi.repository import Gtk, Gdk, GLib, Gio
from .ui_helpers import UIHelpers
from .board_base import BoardBase


class ManagerBase(ABC):
    """Abstract base manager: connects Board + UI (Gtk)."""

    def __init__(self, window, board_class):
        self.window = window
        self.board_class = board_class
        self.board: BoardBase = None
        self.cell_inputs = None
        self.blocks = []
        self.parent_grid = None
        self.conflict_cells = []
        self.pencil_mode = False
        self.key_map, self.remove_cell_keybindings = UIHelpers.setup_key_mappings()
        self._setup_actions()

    # -----------------------------
    # --- Actions & Game Control ---
    # -----------------------------
    def _setup_actions(self):
        back_action = Gio.SimpleAction.new("back-to-menu", None)
        back_action.connect("activate", self.on_back_to_menu)
        self.window.add_action(back_action)

        pencil_action = Gio.SimpleAction.new_stateful(
            "pencil-toggled", None, GLib.Variant.new_boolean(False)
        )
        pencil_action.connect("change-state", self.on_pencil_action_toggled)
        self.window.add_action(pencil_action)

    def start_game(self, difficulty: float, difficulty_label: str):
        self.window.stack.set_visible_child(self.window.loading_screen)
        logging.info(f"Starting game with difficulty: {difficulty}")

        def worker():
            board = self.board_class(difficulty, difficulty_label)
            GLib.idle_add(self._on_game_ready, board)

        threading.Thread(target=worker, daemon=True).start()

    def _on_game_ready(self, board):
        self.board = board
        self.build_grid()
        self.window.stack.set_visible_child(self.window.game_view_box)
        return False

    def load_saved_game(self):
        board = self.board_class.load_from_file()
        if board:
            self.board = board
            self.window.sudoku_window_title.set_subtitle(f"{self.board.difficulty_label}")
            self.build_grid()
            self._restore_game_state()
            self.window.stack.set_visible_child(self.window.game_view_box)
            logging.info("Game successfully loaded from save.")
            if self.board.is_solved():
                self._show_puzzle_finished_dialog()
        else:
            logging.error("Failed to load saved game")

    def _restore_game_state(self):
        size = self.board.rules.size
        for row in range(size):
            for col in range(size):
                value = self.board.user_inputs[row][col]
                notes = self.board.get_notes(row, col)
                cell = self.cell_inputs[row][col]
                if value:
                    cell.set_value(str(value))
                    if str(value) != self.board.get_correct_value(row, col):
                        cell.highlight("wrong")
                        cell.set_tooltip_text("Wrong")
                cell.update_notes(notes)

    # -----------------------------
    # --- Abstract Grid Builder ---
    # -----------------------------
    @abstractmethod
    def build_grid(self):
        """Implemented in variant: build Gtk Grid + attach SudokuCell widgets."""
        pass

    # -----------------------------
    # --- Pencil Mode & Menu ---
    # -----------------------------
    def on_pencil_toggled(self, button: Gtk.ToggleButton):
        self.pencil_mode = button.get_active()
        logging.info("Pencil Mode ON" if self.pencil_mode else "Pencil Mode OFF")

    def on_pencil_action_toggled(self, action, value):
        new_state = not action.get_state().get_boolean()
        action.set_state(GLib.Variant.new_boolean(new_state))
        self.window.pencil_toggle_button.set_active(new_state)

    def on_back_to_menu(self, action, parameter):
        self.window.continue_button.set_sensitive(self.board_class.has_saved_game())
        self.window.stack.set_visible_child(self.window.main_menu_box)
        self.window.sudoku_window_title.set_subtitle("")

    def on_back_to_menu_clicked_after_finish(self, button):
        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)
        self.window.grid_container.append(self.window.game_view_box)
        self.window.sudoku_window_title.set_subtitle("")
        self.window.stack.set_visible_child(self.window.main_menu_box)
        self.window.continue_button.set_sensitive(self.board_class.has_saved_game())

    # -----------------------------
    # --- Cell Highlighting & Focus ---
    # -----------------------------
    def _focus_cell(self, row, col):
        cell = self.cell_inputs[row][col]
        cell.grab_focus()
        self.highlight_related_cells(row, col)

    def highlight_related_cells(self, row, col):
        """Highlight based on cell type:
        - Editable cell: only same-number cells.
        - Clue cell: row, column, block.
        """
        cell = self.cell_inputs[row][col]
        UIHelpers.clear_highlights(self.cell_inputs, "highlight")

        value = cell.get_value()
        size = self.board.rules.size
        block_size = self.board.rules.block_size

        if getattr(cell, "editable", True):
            # Highlight all cells with the same value
            if value:
                for r in range(size):
                    for c in range(size):
                        if self.cell_inputs[r][c].get_value() == value:
                            self.cell_inputs[r][c].highlight("highlight")
        else:
            # Highlight row, column, block
            for i in range(size):
                self.cell_inputs[row][i].highlight("highlight")
                self.cell_inputs[i][col].highlight("highlight")
            br, bc = row // block_size, col // block_size
            for r in range(br * block_size, (br + 1) * block_size):
                for c in range(bc * block_size, (bc + 1) * block_size):
                    self.cell_inputs[r][c].highlight("highlight")


    # -----------------------------
    # --- Filling & Clearing Cells ---
    # -----------------------------
    def _fill_cell(self, cell, number: str, ctrl_is_pressed=False):
        UIHelpers.clear_conflicts(self.conflict_cells)
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
        UIHelpers.specify_cell_correctness(cell, number, correct, self.conflict_cells, self.cell_inputs)

        if self.board.is_solved():
            self._show_puzzle_finished_dialog()

    def _clear_cell(self, cell, clear_all=False):
        row, col = cell.row, cell.col
        if clear_all:
            self.board.clear_notes(row, col)
        cell.set_value("")
        cell.update_notes(set())
        self.board.set_input(row, col, None)
        UIHelpers.clear_feedback_classes(cell.get_style_context())
        UIHelpers.clear_conflicts(self.conflict_cells)
        self.board.save_to_file()

    # -----------------------------
    # --- Keyboard & Popover Handling ---
    # -----------------------------
    def on_key_pressed(self, controller, keyval, keycode, state, row, col):
        direction = self.window.get_direction()
        is_rtl = direction == Gtk.TextDirection.RTL
        directions = {
            Gdk.KEY_Up: (-1, 0),
            Gdk.KEY_Down: (1, 0),
            Gdk.KEY_Left: (0, 1 if is_rtl else -1),
            Gdk.KEY_Right: (0, -1 if is_rtl else 1),
        }

        ctrl_pressed = state & Gdk.ModifierType.CONTROL_MASK
        if keyval in directions:
            d_row, d_col = directions[keyval]
            if ctrl_pressed:
                d_row *= 3
                d_col *= 3
            new_row, new_col = row + d_row, col + d_col
            if 0 <= new_row < self.board.rules.size and 0 <= new_col < self.board.rules.size:
                self._focus_cell(new_row, new_col)
            return True

        cell = self.cell_inputs[row][col]
        number_str = None
        uni = Gdk.keyval_to_unicode(keyval)
        if uni != 0:
            char = chr(uni)
            try:
                number_str = str(unicodedata.digit(char))
            except (TypeError, ValueError):
                pass

        if number_str and getattr(cell, "editable", True):
            self._fill_cell(cell, number_str, ctrl_pressed)
            return True

        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and getattr(cell, "editable", True):
            self._show_popover(cell)
            return True

        if keyval in self.remove_cell_keybindings and getattr(cell, "editable", True):
            self._clear_cell(cell, clear_all=(keyval == Gdk.KEY_Delete))
            return True

        return False

    def _show_popover(self, cell, mouse_button=None):
        popover = Gtk.Popover()
        popover.set_has_arrow(False)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_parent(cell)

        grid = Gtk.Grid(row_spacing=5, column_spacing=5)
        popover.set_child(grid)
        num_buttons = {}
        for i in range(1, 10):
            b = UIHelpers.create_number_button(str(i), self.on_number_selected, cell, popover, mouse_button)
            grid.attach(b, (i - 1) % 3, (i - 1) // 3, 1, 1)
            num_buttons[str(i)] = b

        clear_button = Gtk.Button(label="Clear Cell")
        clear_button.set_size_request(40 * 3 + 10, 40)
        clear_button.connect("clicked", self.on_clear_selected, cell, popover)
        grid.attach(clear_button, 0, 3, 3, 1)

        def on_key_pressed(controller, keyval, keycode, state):
            if keyval in self.key_map and (num := self.key_map[keyval]) in num_buttons:
                num_buttons[num].emit("clicked")
                return True
            elif keyval in self.remove_cell_keybindings:
                clear_button.emit("clicked")
                return True
            return False

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", on_key_pressed)
        grid.add_controller(key_controller)

        grid.set_focus_on_click(True)
        grid.grab_focus()
        popover.show()

    def on_number_selected(self, num_button, cell, popover, mouse_button):
        number = num_button.get_label()
        if mouse_button == 1:
            self._fill_cell(cell, number)
        elif mouse_button == 3:
            self._fill_cell(cell, number, True)
        popover.popdown()

    def on_clear_selected(self, clear_button, cell, popover):
        self._clear_cell(cell)
        popover.popdown()

    def on_cell_clicked(self, gesture, n_press, x, y, cell):
        self.highlight_related_cells(cell.row, cell.col)
        if getattr(cell, "editable", True) and n_press == 1:
            self._show_popover(cell, gesture.get_current_button())
        else:
            cell.grab_focus()

    # -----------------------------
    # --- Puzzle Completion ---
    # -----------------------------
    def _show_puzzle_finished_dialog(self):
        self.window.pencil_toggle_button.set_visible(False)
        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)
        self.window.stack.set_visible_child(self.window.finished_page)

    def on_grid_unfocus(self):
        """Called when focus leaves the grid."""
        UIHelpers.clear_highlights(self.cell_inputs, "highlight")