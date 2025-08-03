# window.py
#
# Copyright 2025 sepehr
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later
from gi.repository import Adw, Gtk, Gdk, GLib, Gio
from sudoku import Sudoku as PySudoku
from functools import partial
import json
import os
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

APP_ID = "io.github.sepehr_rs.LibreSudoku"

data_dir = os.path.expanduser(GLib.get_user_data_dir())
save_dir = os.path.join(data_dir, APP_ID)
os.makedirs(save_dir, exist_ok=True)

SAVE_PATH = os.path.join(save_dir, "save.json")

GRID_SIZE = 9
BLOCK_SIZE = 3
EASY_DIFFICULTY = 0.2
MEDIUM_DIFFICULTY = 0.5
HARD_DIFFICULTY = 0.7
EXTREME_DIFFICULTY = 0.9
DIALOG_DEFAULT_WIDTH = 340
DIALOG_DEFAULT_HEIGHT = 240


class GameBoard:
    def __init__(
        self,
        difficulty: float,
        puzzle=None,
        solution=None,
        user_inputs=None,
        notes=None,
    ):
        self.difficulty = difficulty

        if puzzle and solution:
            self.puzzle = puzzle
            self.solution = solution
        else:
            sudoku = PySudoku(3).difficulty(difficulty)
            self.puzzle = sudoku.board
            self.solution = sudoku.solve().board

        self.user_inputs = (
            user_inputs
            if user_inputs
            else [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        )
        self.notes = (
            notes
            if notes
            else [[set() for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        )

    def to_dict(self):
        return {
            "difficulty": self.difficulty,
            "puzzle": self.puzzle,
            "solution": self.solution,
            "user_inputs": self.user_inputs,
            "notes": [[list(n) for n in row] for row in self.notes],
        }

    def is_clue(self, row: int, col: int):
        return self.puzzle[row][col] is not None

    def set_input(self, row: int, col: int, value: str):
        self.user_inputs[row][col] = value

    def get_input(self, row: int, col: int):
        return self.user_inputs[row][col]

    def get_notes(self, row, col):
        return self.notes[row][col]

    def add_note(self, row, col, value):
        self.notes[row][col].add(value)

    def remove_note(self, row, col, value):
        self.notes[row][col].discard(value)

    def clear_notes(self, row, col):
        self.notes[row][col].clear()

    def save_to_file(self, path=SAVE_PATH):
        try:
            with open(SAVE_PATH, "w") as f:
                json.dump(self.to_dict(), f)
        except Exception as e:
            logging.error(f"Failed to save game: {e}")


class SudokuCell(Gtk.Button):
    def __init__(self, row: int, col: int, value: str, editable: bool):
        super().__init__()

        self.row = row
        self.col = col
        self.editable = editable

        self.main_label = Gtk.Label()
        self.notes_grid = Gtk.Grid(
            row_spacing=0,
            column_spacing=0,
            column_homogeneous=True,
            row_homogeneous=True,
        )
        self.notes_grid.get_style_context().add_class("notes-grid")

        self.note_labels = {}  # Store label widgets by number

        # Overlay both main and note labels
        overlay = Gtk.Overlay()
        overlay.set_child(self.main_label)
        overlay.add_overlay(self.notes_grid)

        self.set_child(overlay)

        self.set_hexpand(True)
        self.set_vexpand(True)
        self.set_halign(Gtk.Align.FILL)
        self.set_valign(Gtk.Align.FILL)
        self.set_can_focus(True)
        self.add_border_classes()

        if value is not None:
            self.set_value(str(value))
            self.get_style_context().add_class("clue-cell")
        else:
            self.set_value("")
            self.get_style_context().add_class("entry-cell")

        self.update_display()

    def set_value(self, value: str):
        self.main_label.set_text(value)
        self.update_display()

    def update_notes(self, notes):
        # Clear old labels
        for child in list(self.notes_grid):
            self.notes_grid.remove(child)

        self.note_labels.clear()

        if not notes or self.main_label.get_text():
            return

        sorted_notes = sorted(notes, key=int)

        for n in sorted_notes:
            note_label = Gtk.Label(label=n)
            note_label.get_style_context().add_class("note-cell-label")
            self.note_labels[n] = note_label

            index = int(n) - 1
            row = index // 3
            col = index % 3

            self.notes_grid.attach(note_label, col, row, 1, 1)

        self.notes_grid.show()

    def update_display(self):
        if self.main_label.get_text():
            for label in self.note_labels.values():
                label.set_text("")
        self.notes_grid.set_halign(Gtk.Align.FILL)
        self.notes_grid.set_valign(Gtk.Align.FILL)

    def highlight(self, class_name: str):
        self.get_style_context().add_class(class_name)

    def unhighlight(self, class_name: str):
        self.get_style_context().remove_class(class_name)

    def add_border_classes(self):
        context = self.get_style_context()
        if self.row % BLOCK_SIZE == 0:
            context.add_class("top-border")
        if self.col % BLOCK_SIZE == 0:
            context.add_class("left-border")
        if (self.col + 1) % BLOCK_SIZE == 0:
            context.add_class("right-border")
        if (self.row + 1) % BLOCK_SIZE == 0:
            context.add_class("bottom-border")


@Gtk.Template(resource_path="/io/github/sepehr_rs/LibreSudoku/window.ui")
class SudokuWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SudokuWindow"

    stack = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()
    new_game_button = Gtk.Template.Child()
    main_menu_box = Gtk.Template.Child()
    game_view_box = Gtk.Template.Child()
    grid_container = Gtk.Template.Child()
    pencil_toggle_button = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.light_css_path = "/io/github/sepehr_rs/LibreSudoku/light.css"
        self.dark_css_path = "/io/github/sepehr_rs/LibreSudoku/dark.css"
        self.css_provider = Gtk.CssProvider()
        settings = Gtk.Settings.get_default()
        dark_mode = settings.get_property("gtk-application-prefer-dark-theme")
        self._load_css(dark_mode)
        settings.connect(
            "notify::gtk-application-prefer-dark-theme", self._on_dark_mode_changed
        )
        self.conflict_cells = []

        self.key_map = {getattr(Gdk, f"KEY_{i}"): str(i) for i in range(1, 10)}
        self.key_map.update({getattr(Gdk, f"KEY_KP_{i}"): str(i) for i in range(1, 10)})

        self.remove_cell_keybindings = (
            Gdk.KEY_BackSpace,
            Gdk.KEY_Delete,
            Gdk.KEY_KP_Delete,
        )

        self.continue_button.set_sensitive(self._has_saved_game())
        self.continue_button.connect("clicked", self.on_continue_clicked)
        self.new_game_button.connect("clicked", self.on_new_game_clicked)

        back_action = Gio.SimpleAction.new("back-to-menu", None)
        back_action.connect("activate", self.on_back_to_menu)
        self.add_action(back_action)
        self.back_action = back_action

        self.pencil_mode = False
        self.pencil_toggle_button.set_active(False)
        self.pencil_toggle_button.connect("toggled", self.on_pencil_toggled)
        pencil_action = Gio.SimpleAction.new_stateful(
            "pencil-toggled", None, GLib.Variant.new_boolean(False)
        )
        pencil_action.connect("change-state", self.on_pencil_action_toggled)
        self.add_action(pencil_action)
        self.pencil_action = pencil_action

        self.stack.connect("notify::visible-child", self.on_stack_page_changed)
        self.on_stack_page_changed(self.stack, None)

    def _load_css(self, dark_mode: bool):
        css_path = self.dark_css_path if dark_mode else self.light_css_path
        self.css_provider.load_from_resource(css_path)

        # Remove previous provider if any and add the new one
        display = Gdk.Display.get_default()

        # Clear all previous providers with the same priority to avoid stacking
        # Unfortunately, GTK doesn't provide a direct way to remove all providers
        # by priority, so we just replace by re-adding with the same provider object.

        Gtk.StyleContext.add_provider_for_display(
            display, self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def _on_dark_mode_changed(self, settings, param):
        dark_mode = settings.get_property("gtk-application-prefer-dark-theme")
        self._load_css(dark_mode)

    def on_continue_clicked(self, button: Gtk.Button):
        self.load_saved_game()

    def on_stack_page_changed(self, stack, param):
        is_game_page = stack.get_visible_child() != self.main_menu_box
        self.lookup_action("back-to-menu").set_enabled(is_game_page)
        self.pencil_toggle_button.set_visible(is_game_page)

    def on_back_to_menu(self, action, parameter):
        self.continue_button.set_sensitive(self._has_saved_game())
        self.stack.set_visible_child(self.main_menu_box)

    def on_close_request(self, window):
        return False

    def on_new_game_clicked(self, action):
        dialog = Gtk.Dialog(
            title="Select Difficulty",
            transient_for=self,
            modal=True,
        )
        dialog.set_default_size(DIALOG_DEFAULT_WIDTH, DIALOG_DEFAULT_HEIGHT)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_top=24,
            margin_bottom=24,
            margin_start=24,
            margin_end=24,
        )
        dialog.get_content_area().append(box)
        dialog.get_style_context().add_class("sudoku-dialog")
        for label, difficulty in [
            ("Easy", EASY_DIFFICULTY),
            ("Medium", MEDIUM_DIFFICULTY),
            ("Hard", HARD_DIFFICULTY),
            ("Extreme", EXTREME_DIFFICULTY),
        ]:
            button = Gtk.Button(label=label)
            button.connect("clicked", partial(self.on_new_game, difficulty))
            box.append(button)

        dialog.show()

    def on_new_game(self, difficulty: float, button: Gtk.Button):
        self.start_game(difficulty)
        button.get_root().destroy()

    def on_pencil_toggled(self, button: Gtk.ToggleButton):
        self.pencil_mode = button.get_active()
        logging.info("Pencil Mode is now", "ON" if self.pencil_mode else "OFF")

    def on_pencil_action_toggled(self, action, value):
        # Flip the boolean state
        new_state = not action.get_state().get_boolean()
        action.set_state(GLib.Variant.new_boolean(new_state))
        self.pencil_toggle_button.set_active(new_state)

    def start_game(self, difficulty: float):
        logging.info(f"Starting game with difficulty: {difficulty}")
        self.game_board = GameBoard(difficulty)
        self.build_grid()
        self.stack.set_visible_child(self.game_view_box)

    def build_grid(self):
        # Clear old grid children
        while child := self.grid_container.get_first_child():
            self.grid_container.remove(child)

        grid = Gtk.Grid(
            row_spacing=0.4,
            column_spacing=0.4,
            column_homogeneous=True,
            row_homogeneous=True,
        )
        self.cell_inputs = [[None for _ in range(9)] for _ in range(9)]

        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                value = self.game_board.puzzle[row][col]
                editable = not self.game_board.is_clue(row, col)
                cell = SudokuCell(row, col, value, editable)
                # Connect cell events
                gesture = Gtk.GestureClick.new()
                gesture.connect("pressed", self.on_cell_clicked, cell)
                cell.add_controller(gesture)
                key_controller = Gtk.EventControllerKey()
                key_controller.connect("key-pressed", self.on_key_pressed, row, col)
                cell.add_controller(key_controller)

                self.cell_inputs[row][col] = cell
                grid.attach(cell, col, row, 1, 1)

        frame = Gtk.AspectFrame(ratio=1.0, obey_child=False)
        frame.set_hexpand(True)
        frame.set_vexpand(True)
        frame.set_child(grid)

        self.grid_container.append(frame)
        self._focus_cell(0, 0)
        frame.show()

    def _create_number_button(self, label: str, callback, *args):
        button = Gtk.Button(label=label)
        button.set_size_request(40, 40)
        button.connect("clicked", callback, *args)
        return button

    def _show_popover(self, button: Gtk.Button):
        popover = Gtk.Popover()
        popover.set_has_arrow(False)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_parent(button)
        grid = Gtk.Grid(row_spacing=5, column_spacing=5)
        popover.set_child(grid)

        num_buttons = {}
        for i in range(1, 10):
            b = self._create_number_button(
                str(i), self.on_number_selected, button, popover
            )
            grid.attach(b, (i - 1) % 3, (i - 1) // 3, 1, 1)
            num_buttons[str(i)] = b

        clear_button = Gtk.Button(label="Clear")
        clear_button.set_size_request(40 * 3 + 10, 40)
        clear_button.connect("clicked", self.on_clear_selected, button, popover)
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

    def on_clear_selected(self, clear_button, target_cell: SudokuCell, popover):
        row, col = target_cell.row, target_cell.col
        if self.pencil_mode:
            self.game_board.clear_notes(row, col)
            target_cell.update_notes(set())
        else:
            target_cell.set_value("")
            self._clear_feedback_classes(target_cell.get_style_context())
            self.game_board.set_input(row, col, None)
        self.game_board.save_to_file()
        popover.popdown()

    def on_number_selected(
        self, num_button: Gtk.Button, target_cell: SudokuCell, popover
    ):
        number = num_button.get_label()
        self._fill_cell(target_cell, number)
        popover.popdown()

    def _clear_highlights(self, class_name: str):
        for row in range(9):
            for col in range(9):
                self.cell_inputs[row][col].unhighlight(class_name)

    def _highlight_cell(self, row: int, col: int, class_name: str):
        self.cell_inputs[row][col].highlight(class_name)

    def highlight_related_cells(self, row: int, col: int):
        self._clear_highlights("highlight")
        for i in range(9):
            self._highlight_cell(row, i, "highlight")
            self._highlight_cell(i, col, "highlight")

        block_row_start = (row // BLOCK_SIZE) * BLOCK_SIZE
        block_col_start = (col // BLOCK_SIZE) * BLOCK_SIZE
        for r in range(block_row_start, block_row_start + BLOCK_SIZE):
            for c in range(block_col_start, block_col_start + BLOCK_SIZE):
                self._highlight_cell(r, c, "highlight")

    def on_cell_clicked(self, gesture, n_press, x: int, y: int, cell: SudokuCell):
        self.highlight_related_cells(cell.row, cell.col)
        if cell.editable and n_press == 1:
            self._show_popover(cell)
        else:
            cell.grab_focus()

    def _fill_cell(self, cell: SudokuCell, number: str):
        self._clear_conflicts()
        row, col = cell.row, cell.col

        if self.pencil_mode:
            if number in self.game_board.get_notes(row, col):
                self.game_board.remove_note(row, col, number)
            else:
                self.game_board.add_note(row, col, number)
            cell.update_notes(self.game_board.get_notes(row, col))
            return

        cell.set_value(number)
        self.game_board.set_input(row, col, number)
        self.game_board.save_to_file()

        correct = str(self.game_board.solution[row][col])
        context = cell.get_style_context()
        self._clear_feedback_classes(context)
        self._specify_cell_correctness(context, number, correct, cell)

    def _focus_cell(self, row: int, col: int):
        self.cell_inputs[row][col].grab_focus()
        self.highlight_related_cells(row, col)

    def _clear_feedback_classes(self, context):
        context.remove_class("correct")
        context.remove_class("wrong")

    def _highlight_conflicts(self, row: int, col: int, label: str):
        self.conflict_cells.clear()
        for c in range(GRID_SIZE):
            cell = self.cell_inputs[row][c]
            if (
                cell.main_label.get_text() == label
                and cell != self.cell_inputs[row][col]
            ):
                cell.highlight("conflict")
                self.conflict_cells.append(cell)
        for r in range(GRID_SIZE):
            cell = self.cell_inputs[r][col]
            if (
                cell.main_label.get_text() == label
                and cell != self.cell_inputs[row][col]
            ):
                cell.highlight("conflict")
                self.conflict_cells.append(cell)
        block_row_start = (row // BLOCK_SIZE) * BLOCK_SIZE
        block_col_start = (col // BLOCK_SIZE) * BLOCK_SIZE
        for r in range(block_row_start, block_row_start + BLOCK_SIZE):
            for c in range(block_col_start, block_col_start + BLOCK_SIZE):
                cell = self.cell_inputs[r][c]
                if (
                    cell.main_label.get_text() == label
                    and cell != self.cell_inputs[row][col]
                ):
                    cell.highlight("conflict")
                    self.conflict_cells.append(cell)

    def _clear_conflicts(self):
        for cell in self.conflict_cells:
            cell.unhighlight("conflict")
        self.conflict_cells.clear()
        return False

    def _specify_cell_correctness(
        self, context, number: int, correct: int, cell: SudokuCell
    ):
        if number == correct:
            cell.editable = False
            cell.highlight("correct")
            GLib.timeout_add(2000, lambda: cell.unhighlight("correct"))
        else:
            cell.highlight("wrong")
            self._highlight_conflicts(cell.row, cell.col, number)
            GLib.timeout_add(2000, self._clear_conflicts)

    def on_key_pressed(self, controller, keyval, keycode, state, row: int, col: int):
        directions = {
            Gdk.KEY_Up: (-1, 0),
            Gdk.KEY_Down: (1, 0),
            Gdk.KEY_Left: (0, -1),
            Gdk.KEY_Right: (0, 1),
        }

        if keyval in directions:
            d_row, d_col = directions[keyval]
            new_row, new_col = row + d_row, col + d_col
            # Buggy line later on ?
            if 0 <= new_row < 9 and 0 <= new_col < 9:
                self._focus_cell(new_row, new_col)
            return True

        cell = self.cell_inputs[row][col]
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and cell.editable:
            self._show_popover(cell)
            return True

        if keyval in self.key_map and cell.editable:
            self._fill_cell(cell, self.key_map[keyval])
            return True

        if keyval in self.remove_cell_keybindings and cell.editable:
            cell.set_value("")
            self._clear_feedback_classes(cell.get_style_context())
            self.game_board.clear_notes(row, col)
            self.game_board.set_input(row, col, None)
            cell.update_notes(set())
            return True

        return False

    def load_saved_game(self):
        try:
            with open(SAVE_PATH, "r") as f:
                data = json.load(f)

            notes = [[set(cell) for cell in row] for row in data["notes"]]
            self.game_board = GameBoard(
                difficulty=data["difficulty"],
                puzzle=data["puzzle"],
                solution=data["solution"],
                user_inputs=data["user_inputs"],
                notes=notes,
            )

            self.build_grid()

            for row in range(GRID_SIZE):
                for col in range(GRID_SIZE):
                    value = self.game_board.user_inputs[row][col]
                    notes = self.game_board.get_notes(row, col)
                    cell = self.cell_inputs[row][col]
                    if value:
                        cell.set_value(str(value))
                        if str(value) != str(self.game_board.solution[row][col]):
                            cell.highlight("wrong")  # Re-highlight wrong inputs
                    cell.update_notes(notes)

            self.stack.set_visible_child(self.game_view_box)
            logging.info("Game successfully loaded from save.")
        except Exception as e:
            logging.error(f"Error loading game: {e}")

    def _has_saved_game(self):
        try:
            with open(SAVE_PATH, "r"):
                return True
        except Exception:
            return False
