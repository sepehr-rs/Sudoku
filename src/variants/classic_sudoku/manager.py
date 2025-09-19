import logging
import threading
import unicodedata
from gi.repository import Gtk, Gdk, GLib
from ...base.manager_base import ManagerBase
from .board import ClassicSudokuBoard
from .ui_helpers import ClassicUIHelpers
from .sudoku_cell import SudokuCell


class ClassicSudokuManager(ManagerBase):
    def __init__(self, window):
        super().__init__(window, ClassicSudokuBoard)
        self.key_map, self.remove_keys = ClassicUIHelpers.setup_key_mappings()
        self.parent_grid = None
        self.blocks = []

    def start_game(self, difficulty: float, difficulty_label: str, variant: str):
        self.window.stack.set_visible_child(self.window.loading_screen)
        logging.info(f"Starting Classic Sudoku with difficulty: {difficulty}")

        def worker():
            self.board = ClassicSudokuBoard(difficulty, difficulty_label, variant)
            GLib.idle_add(self._on_game_ready)

        threading.Thread(target=worker, daemon=True).start()

    def _on_game_ready(self):
        self.build_grid()
        self.window.stack.set_visible_child(self.window.game_view_box)
        return False

    def load_saved_game(self):
        self.board = ClassicSudokuBoard.load_from_file()
        if self.board:
            self.window.sudoku_window_title.set_subtitle(
                f"{self.board.variant.capitalize()} - {self.board.difficulty_label}"
            )
            self.build_grid()
            self._restore_game_state()
            self.window.stack.set_visible_child(self.window.game_view_box)
            logging.info("Loaded saved Classic Sudoku game")
            if self.board.is_solved():
                self._show_puzzle_finished_dialog()
        else:
            logging.error("No saved game found")

    def _restore_game_state(self):
        size = self.board.rules.size
        for r in range(size):
            for c in range(size):
                value = self.board.user_inputs[r][c]
                notes = self.board.notes[r][c]
                cell = self.cell_inputs[r][c]
                if value:
                    cell.set_value(str(value))
                    correct_value = self.board.get_correct_value(r, c)
                    if str(value) != correct_value:
                        cell.highlight("wrong")
                if notes:
                    cell.update_notes(notes)

    def build_grid(self):
        # Clear previous children
        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)

        size = self.board.rules.size
        block_size = self.board.rules.block_size

        # Parent grid (NxN blocks)
        self.parent_grid = Gtk.Grid(
            row_spacing=10,
            column_spacing=10,
            column_homogeneous=True,
            row_homogeneous=True,
        )
        self.parent_grid.set_name("sudoku-parent-grid")

        # Prepare block grids
        self.blocks = []
        for br in range(block_size):
            row_blocks = []
            for bc in range(block_size):
                block = Gtk.Grid(
                    row_spacing=4,
                    column_spacing=4,
                    column_homogeneous=True,
                    row_homogeneous=True,
                )
                block.get_style_context().add_class("sudoku-block")
                row_blocks.append(block)
                self.parent_grid.attach(block, bc, br, 1, 1)
            self.blocks.append(row_blocks)

        # Initialize cell grid
        self.cell_inputs = [[None for _ in range(size)] for _ in range(size)]

        # Fill blocks with SudokuCell widgets
        for r in range(size):
            for c in range(size):
                value = self.board.puzzle[r][c]
                editable = not self.board.is_clue(r, c)
                cell = SudokuCell(r, c, value, editable)

                # Gesture click
                gesture = Gtk.GestureClick.new()
                gesture.set_button(0)
                gesture.connect("pressed", self.on_cell_clicked, cell)
                cell.add_controller(gesture)

                # Keyboard input
                key_controller = Gtk.EventControllerKey()
                key_controller.connect("key-pressed", self.on_key_pressed, r, c)
                cell.add_controller(key_controller)

                self.cell_inputs[r][c] = cell

                # Position inside its block
                br, bc = r // block_size, c // block_size
                inner_r, inner_c = r % block_size, c % block_size
                self.blocks[br][bc].attach(cell, inner_c, inner_r, 1, 1)

        # Wrap grid in AspectFrame to maintain square shape
        frame = Gtk.AspectFrame(ratio=1.0, obey_child=False)
        frame.set_hexpand(True)
        frame.set_vexpand(True)
        frame.set_halign(Gtk.Align.FILL)
        frame.set_valign(Gtk.Align.FILL)
        frame.set_child(self.parent_grid)

        self.board_frame = frame
        self.window.grid_container.append(frame)
        frame.show()

        # Reapply compact mode if needed
        width_mode_active, height_mode_active = False, False
        bp = getattr(self.window, "bp_bin", None)
        if bp and bp.get_style_context().has_class("width-compact"):
            width_mode_active = True
        if bp and bp.get_style_context().has_class("height-compact"):
            height_mode_active = True

        self.window._apply_compact(
            any([width_mode_active, height_mode_active]),
            "width" if width_mode_active else "height",
        )

        self.window.grid_container.queue_allocate()

    def _focus_cell(self, row: int, col: int):
        self.cell_inputs[row][col].grab_focus()
        ClassicUIHelpers.highlight_related_cells(
            self.cell_inputs, row, col, self.board.rules.block_size
        )

    def _fill_cell(self, cell: SudokuCell, number: str, ctrl_is_pressed=False):
        ClassicUIHelpers.clear_conflicts(self.conflict_cells)

        if not cell.is_editable():
            return

        r, c = cell.row, cell.col

        if self.pencil_mode or ctrl_is_pressed:
            self.board.toggle_note(r, c, number)
            cell.update_notes(self.board.get_notes(r, c))
            self.board.save_to_file()
            return

        cell.set_value(number)
        self.board.set_input(r, c, number)
        self.board.save_to_file()

        self.on_cell_filled(cell, number)

        if self.board.is_solved():
            self._show_puzzle_finished_dialog()

    def _clear_cell(self, cell: SudokuCell, clear_all=False):
        r, c = cell.row, cell.col
        if not cell.is_editable():
            return
        if clear_all:
            self.board.clear_input(r, c)
            cell.clear()
            self.board.notes[r][c].clear()
            cell.update_notes(set())

        elif self.pencil_mode:
            current_notes = self.board.get_notes(r, c)
            if current_notes:
                # remove the last note numerically
                last_note = sorted(current_notes, key=int)[-1]
                self.board.toggle_note(r, c, last_note)
                cell.update_notes(self.board.get_notes(r, c))

        else:
            self.board.clear_input(r, c)
            cell.clear()
            self.board.notes[r][c].clear()
            cell.update_notes(set())
        self.board.save_to_file()

    def _show_popover(self, cell: SudokuCell, mouse_button=None):
        ClassicUIHelpers.show_number_popover(
            cell, mouse_button, self.on_number_selected, self.on_clear_selected
        )

    def on_cell_clicked(self, gesture, n_press, x, y, cell: SudokuCell):
        ClassicUIHelpers.highlight_related_cells(
            self.cell_inputs, cell.row, cell.col, self.board.rules.block_size
        )
        if cell.is_editable() and n_press == 1:
            self._show_popover(cell, gesture.get_current_button())
        else:
            cell.grab_focus()

    def on_key_pressed(self, controller, keyval, keycode, state, row, col):
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)

        if self._handle_arrow_keys(keyval, ctrl, row, col):
            return True

        if self._handle_number_keys(keyval, ctrl, row, col):
            return True

        if self._handle_unicode_digit(keyval, ctrl, row, col):
            return True

        if self._handle_enter_key(keyval, row, col):
            return True

        if self._handle_remove_keys(keyval, row, col):
            return True

        return False

    def _handle_arrow_keys(self, keyval, ctrl, row, col):
        directions = {
            Gdk.KEY_Up: (-1, 0),
            Gdk.KEY_Down: (1, 0),
            Gdk.KEY_Left: (0, -1),
            Gdk.KEY_Right: (0, 1),
        }
        if keyval not in directions:
            return False

        dr, dc = directions[keyval]
        if ctrl:
            dr *= 3
            dc *= 3
        new_r, new_c = row + dr, col + dc
        if (
            0 <= new_r < self.board.rules.size
            and 0 <= new_c < self.board.rules.size
        ):
            self._focus_cell(new_r, new_c)
        return True

    def _handle_number_keys(self, keyval, ctrl, row, col):
        if keyval not in self.key_map:
            return False
        num = self.key_map[keyval]
        if num and num != 0:
            self._fill_cell(self.cell_inputs[row][col], num, ctrl_is_pressed=ctrl)
            return True
        return False

    def _handle_unicode_digit(self, keyval, ctrl, row, col):
        uni = Gdk.keyval_to_unicode(keyval)
        if uni == 0:
            return False
        try:
            digit = unicodedata.digit(chr(uni))
            if 1 <= digit <= 9:
                self._fill_cell(
                    self.cell_inputs[row][col], str(digit), ctrl_is_pressed=ctrl
                )
                return True
        except (ValueError, TypeError):
            return False
        return False

    def _handle_enter_key(self, keyval, row, col):
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self._show_popover(self.cell_inputs[row][col])
            return True
        return False

    def _handle_remove_keys(self, keyval, row, col):
        if keyval not in self.remove_keys:
            return False
        self._clear_cell(
            self.cell_inputs[row][col], clear_all=(keyval == Gdk.KEY_Delete)
        )
        return True

    def on_number_selected(
        self, num_button: Gtk.Button, cell: SudokuCell, popover, mouse_button
    ):
        number = num_button.get_label()
        self._fill_cell(cell, number, ctrl_is_pressed=(mouse_button == 3))
        popover.popdown()

    def on_clear_selected(self, clear_button, cell: SudokuCell, popover):
        self._clear_cell(cell)
        popover.popdown()

    def on_pencil_toggled(self, button: Gtk.ToggleButton):
        self.pencil_mode = button.get_active()
        logging.info(
            "Pencil Mode is now ON" if self.pencil_mode else "Pencil Mode is now OFF"
        )

    def _show_puzzle_finished_dialog(self):
        self.window.pencil_toggle_button.set_visible(False)
        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)
        self.window.stack.set_visible_child(self.window.finished_page)

    def on_cell_filled(self, cell, number: str):
        correct_value = self.board.get_correct_value(cell.row, cell.col)

        # Cancel any pending feedback timers
        tids = getattr(cell, "feedback_timeout_ids", [])
        for tid in tids:
            GLib.source_remove(tid)
        cell.feedback_timeout_ids = []

        # Clear previous highlights
        cell.remove_highlight("correct")
        cell.remove_highlight("wrong")
        cell.set_tooltip_text("")
        # Correct entry
        if str(number) == str(correct_value):
            cell.set_editable(False)
            cell.highlight("correct")
            cell.set_tooltip_text("Correct")

            # Remove highlight after delay
            tid1 = GLib.timeout_add(
                3000,
                lambda: (cell.remove_highlight("correct"), cell.set_tooltip_text("")),
            )
            cell.feedback_timeout_ids.append(tid1)

        else:
            cell.highlight("wrong")
            cell.set_tooltip_text("Wrong")

            # Highlight conflicts in related cells
            new_conflicts = ClassicUIHelpers.highlight_conflicts(
                self.cell_inputs, cell.row, cell.col, number, 3
            )
            self.conflict_cells.extend(new_conflicts)

            # Clear conflicts after delay
            tid2 = GLib.timeout_add(
                3000, lambda: ClassicUIHelpers.clear_conflicts(self.conflict_cells)
            )
            cell.feedback_timeout_ids.append(tid2)
