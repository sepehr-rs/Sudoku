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

# TODO: Remove local path
SAVE_PATH = "/home/sepehr/gnome-project/saves/save.json"


@Gtk.Template(resource_path="/io/github/sepehr_rs/LibreSudoku/window.ui")
class SudokuWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SudokuWindow"

    stack = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()
    new_game_button = Gtk.Template.Child()
    main_menu_box = Gtk.Template.Child()
    game_view_box = Gtk.Template.Child()
    grid_container = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._load_css()
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

        self.stack.connect("notify::visible-child", self.on_stack_page_changed)
        self.on_stack_page_changed(self.stack, None)

    def _load_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource("/io/github/sepehr_rs/LibreSudoku/styles.css")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def on_continue_clicked(self, button):
        print("Continue Game clicked")

    def on_stack_page_changed(self, stack, param):
        is_game_page = stack.get_visible_child() != self.main_menu_box
        self.lookup_action("back-to-menu").set_enabled(is_game_page)

    def on_back_to_menu(self, action, parameter):
        self.stack.set_visible_child(self.main_menu_box)

    def on_close_request(self, window):
        print("Close request signal received")
        return False

    def on_new_game_clicked(self, action):
        dialog = Gtk.Dialog(
            title="Select Difficulty",
            transient_for=self,
            modal=True,
        )
        dialog.set_default_size(400, 170)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=12,
            margin_top=24,
            margin_bottom=24,
            margin_start=24,
            margin_end=24,
        )
        dialog.get_content_area().append(box)

        for label, difficulty in [
            ("Easy", 0.2),
            ("Medium", 0.4),
            ("Hard", 0.6),
            ("Extreme", 0.8),
        ]:
            button = Gtk.Button(label=label)
            button.connect("clicked", partial(self.on_new_game, difficulty))
            box.append(button)

        dialog.show()

    def on_new_game(self, difficulty, button):
        self.start_game(difficulty)
        button.get_root().destroy()

    def start_game(self, difficulty: float):
        print("Starting game with difficulty:", difficulty)
        self.build_grid(difficulty)
        self.stack.set_visible_child(self.game_view_box)

    def build_grid(self, difficulty):
        sudoku = PySudoku(3).difficulty(difficulty)
        self.solution = sudoku.solve().board
        puzzle = sudoku.board

        while child := self.grid_container.get_first_child():
            self.grid_container.remove(child)

        grid = Gtk.Grid(
            row_spacing=0.4,
            column_spacing=0.4,
            column_homogeneous=True,
            row_homogeneous=True,
        )
        self.cell_buttons = [[None for _ in range(9)] for _ in range(9)]

        for row in range(9):
            for col in range(9):
                value = puzzle[row][col]
                cell = self._create_cell(row, col, value)
                self._add_border_classes(cell, row, col)
                self.cell_buttons[row][col] = cell
                grid.attach(cell, col, row, 1, 1)

        frame = Gtk.AspectFrame(ratio=1.0, obey_child=False)
        frame.set_hexpand(True)
        frame.set_vexpand(True)
        frame.set_child(grid)

        self.grid_container.append(frame)
        self._focus_cell(0, 0)
        frame.show()

    def _create_cell(self, row, col, value):
        cell = Gtk.Button()
        cell.set_hexpand(True)
        cell.set_vexpand(True)
        cell.set_halign(Gtk.Align.FILL)
        cell.set_valign(Gtk.Align.FILL)
        cell.set_can_focus(True)

        cell.row = row
        cell.col = col

        if value is None:
            cell.set_label("")
            cell.get_style_context().add_class("entry-cell")
            cell.editable = True
        else:
            cell.set_label(str(value))
            cell.get_style_context().add_class("clue-cell")
            cell.editable = False

        gesture = Gtk.GestureClick.new()
        gesture.connect("pressed", self.on_cell_clicked, cell)
        cell.add_controller(gesture)

        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed, row, col)
        cell.add_controller(key_controller)

        return cell

    def _add_border_classes(self, cell, row, col):
        context = cell.get_style_context()
        if row % 3 == 0:
            context.add_class("top-border")
        if col % 3 == 0:
            context.add_class("left-border")
        if (col + 1) % 3 == 0:
            context.add_class("right-border")
        if (row + 1) % 3 == 0:
            context.add_class("bottom-border")

    def _clear_highlights(self):
        for row in range(9):
            for col in range(9):
                self.cell_buttons[row][col].get_style_context().remove_class(
                    "highlight"
                )

    def _highlight_cell(self, row, col):
        self.cell_buttons[row][col].get_style_context().add_class("highlight")

    def highlight_related_cells(self, row, col):
        self._clear_highlights()
        for i in range(9):
            self._highlight_cell(row, i)
            self._highlight_cell(i, col)

        block_row_start = (row // 3) * 3
        block_col_start = (col // 3) * 3
        for r in range(block_row_start, block_row_start + 3):
            for c in range(block_col_start, block_col_start + 3):
                self._highlight_cell(r, c)

    def on_cell_clicked(self, gesture, n_press, x, y, cell):
        self.highlight_related_cells(cell.row, cell.col)
        if getattr(cell, "editable", False) and n_press == 1:
            self._show_popover(cell)
        else:
            cell.grab_focus()

    def _create_number_button(self, label, callback, *args):
        button = Gtk.Button(label=label)
        button.set_size_request(40, 40)
        button.connect("clicked", callback, *args)
        return button

    def _show_popover(self, button):
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

    def on_clear_selected(self, clear_button, target_cell, popover):
        target_cell.set_label("")
        self._clear_feedback_classes(target_cell.get_style_context())
        popover.popdown()

    def on_number_selected(self, num_button, target_cell, popover):
        number = num_button.get_label()
        self._fill_cell(target_cell, number)
        popover.popdown()

    def _fill_cell(self, cell, number):
        self._clear_conflicts()
        cell.set_label(number)
        row, col = cell.row, cell.col
        correct = str(self.solution[row][col])
        context = cell.get_style_context()
        self._clear_feedback_classes(context)
        self._specify_cell_correctness(context, number, correct, cell)

    def _focus_cell(self, row, col):
        self.cell_buttons[row][col].grab_focus()
        self.highlight_related_cells(row, col)

    def _clear_feedback_classes(self, context):
        context.remove_class("correct")
        context.remove_class("wrong")

    def _highlight_conflicts(self, row, col, number_str):
        self.conflict_cells.clear()
        for c in range(9):
            cell = self.cell_buttons[row][c]
            if cell.get_label() == number_str and cell != self.cell_buttons[row][col]:
                cell.get_style_context().add_class("conflict")
                self.conflict_cells.append(cell)
        for r in range(9):
            cell = self.cell_buttons[r][col]
            if cell.get_label() == number_str and cell != self.cell_buttons[row][col]:
                cell.get_style_context().add_class("conflict")
                self.conflict_cells.append(cell)
        block_row_start = (row // 3) * 3
        block_col_start = (col // 3) * 3
        for r in range(block_row_start, block_row_start + 3):
            for c in range(block_col_start, block_col_start + 3):
                cell = self.cell_buttons[r][c]
                if (
                    cell.get_label() == number_str
                    and cell != self.cell_buttons[row][col]
                ):
                    cell.get_style_context().add_class("conflict")
                    self.conflict_cells.append(cell)

    def _clear_conflicts(self):
        for cell in self.conflict_cells:
            cell.get_style_context().remove_class("conflict")
        self.conflict_cells.clear()
        return False

    def _specify_cell_correctness(self, context, number, correct, cell):
        def remove_class(name):
            context.remove_class(name)
            return False

        if number == correct:
            cell.editable = False
            context.add_class("correct")
            GLib.timeout_add(2000, lambda: remove_class("correct"))
        else:
            context.add_class("wrong")
            self._highlight_conflicts(cell.row, cell.col, number)
            GLib.timeout_add(2000, self._clear_conflicts)

    def on_key_pressed(self, controller, keyval, keycode, state, row, col):
        directions = {
            Gdk.KEY_Up: (-1, 0),
            Gdk.KEY_Down: (1, 0),
            Gdk.KEY_Left: (0, -1),
            Gdk.KEY_Right: (0, 1),
        }

        if keyval in directions:
            d_row, d_col = directions[keyval]
            new_row, new_col = row + d_row, col + d_col
            if 0 <= new_row < 9 and 0 <= new_col < 9:
                self._focus_cell(new_row, new_col)
            return True

        cell = self.cell_buttons[row][col]
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter) and getattr(
            cell, "editable", False
        ):
            self._show_popover(cell)
            return True

        if keyval in self.key_map and getattr(cell, "editable", False):
            self._fill_cell(cell, self.key_map[keyval])
            return True

        if keyval in self.remove_cell_keybindings and getattr(cell, "editable", False):
            cell.set_label("")
            self._clear_feedback_classes(cell.get_style_context())
            return True

        return False

    def _has_saved_game(self):
        try:
            with open(SAVE_PATH, "r"):
                return True
        except Exception:
            return False
