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

from gi.repository import Adw, Gtk, Gdk, GLib
from sudoku import Sudoku as PySudoku
from functools import partial

SAVE_PATH = "/home/sepehr/gnome-project/saves/save.json"


@Gtk.Template(resource_path="/io/github/sepehr_rs/GSudoku/window.ui")
class SudokuWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SudokuWindow"

    stack = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()
    new_game_button = Gtk.Template.Child()
    main_menu_box = Gtk.Template.Child()
    game_view_box = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._load_css()

        self.continue_button.set_sensitive(self._has_saved_game())
        self.continue_button.connect("clicked", self.on_continue_clicked)
        self.new_game_button.connect("clicked", self.on_new_game_clicked)
        self.key_map = {
            Gdk.KEY_1: "1",
            Gdk.KEY_2: "2",
            Gdk.KEY_3: "3",
            Gdk.KEY_4: "4",
            Gdk.KEY_5: "5",
            Gdk.KEY_6: "6",
            Gdk.KEY_7: "7",
            Gdk.KEY_8: "8",
            Gdk.KEY_9: "9",
            Gdk.KEY_KP_1: "1",
            Gdk.KEY_KP_2: "2",
            Gdk.KEY_KP_3: "3",
            Gdk.KEY_KP_4: "4",
            Gdk.KEY_KP_5: "5",
            Gdk.KEY_KP_6: "6",
            Gdk.KEY_KP_7: "7",
            Gdk.KEY_KP_8: "8",
            Gdk.KEY_KP_9: "9",
        }
        self.remove_cell_keybindings = (
            Gdk.KEY_BackSpace,
            Gdk.KEY_Delete,
            Gdk.KEY_KP_Delete,
        )

    def _load_css(self):
        css_provider = Gtk.CssProvider()
        css_provider.load_from_resource("/io/github/sepehr_rs/GSudoku/styles.css")
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(), css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER
        )

    def on_continue_clicked(self, button):
        print("Continue Game clicked")

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

        difficulties = [
            ("Easy", 0.2),
            ("Medium", 0.4),
            ("Hard", 0.6),
            ("Extreme", 0.8),
        ]

        for label, difficulty in difficulties:
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

        # Clear previous game content
        while child := self.game_view_box.get_first_child():
            self.game_view_box.remove(child)

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

        self.game_view_box.append(frame)
        self.highlight_related_cells(0, 0)
        frame.show()

    def _clear_highlights(self):
        for row in range(9):
            for col in range(9):
                cell = self.cell_buttons[row][col]
                cell.get_style_context().remove_class("highlight")

    def highlight_related_cells(self, row, col):
        self._clear_highlights()

        for i in range(9):
            self.cell_buttons[row][i].get_style_context().add_class("highlight")
            self.cell_buttons[i][col].get_style_context().add_class("highlight")

        block_row_start = (row // 3) * 3
        block_col_start = (col // 3) * 3
        for r in range(block_row_start, block_row_start + 3):
            for c in range(block_col_start, block_col_start + 3):
                self.cell_buttons[r][c].get_style_context().add_class("highlight")

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

        # Use 'button-press-event' to get event info (mouse button, modifiers)
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

    def _clear_feedback_classes(self, context):
        context.remove_class("correct")
        context.remove_class("wrong")

    def on_clear_selected(self, clear_button, target_cell, popover):
        target_cell.set_label("")
        context = target_cell.get_style_context()
        self._clear_feedback_classes(context)
        popover.popdown()

    def _show_popover(self, button):
        popover = Gtk.Popover()
        popover.set_has_arrow(False)
        popover.set_position(Gtk.PositionType.BOTTOM)
        popover.set_parent(button)

        grid = Gtk.Grid(row_spacing=5, column_spacing=5)
        popover.set_child(grid)

        num_buttons = {}

        for i in range(1, 10):
            num_button = Gtk.Button(label=str(i))
            num_button.set_size_request(40, 40)
            num_button.connect(
                "clicked",
                self.on_number_selected,
                button,
                popover,
            )
            grid.attach(num_button, (i - 1) % 3, (i - 1) // 3, 1, 1)
            num_buttons[str(i)] = num_button

        clear_button = Gtk.Button(label="Clear")
        clear_button.set_size_request(40 * 3 + 10, 40)
        clear_button.connect("clicked", self.on_clear_selected, button, popover)
        grid.attach(clear_button, 0, 3, 3, 1)

        key_controller = Gtk.EventControllerKey()
        grid.add_controller(key_controller)

        def on_key_pressed(controller, keyval, keycode, state):

            if keyval in self.key_map:
                num_str = self.key_map[keyval]
                if num_str in num_buttons:
                    num_buttons[num_str].emit("clicked")
                    return True
            elif keyval in self.remove_cell_keybindings:
                clear_button.emit("clicked")
                return True

            return False

        key_controller.connect("key-pressed", on_key_pressed)

        grid.set_focus_on_click(True)
        grid.grab_focus()

        popover.show()

    def on_cell_clicked(self, gesture, n_press, x, y, cell):
        self.highlight_related_cells(cell.row, cell.col)

        if not getattr(cell, "editable", False):
            return

        # Only respond to single left-clicks (n_press == 1)
        if n_press == 1:
            self._show_popover(cell)
        else:
            cell.grab_focus()

    def _specify_cell_correctness(self, context, number, correct, cell):
        def remove_class(name):
            context.remove_class(name)
            return False  # Don't repeat the timeout

        if number == correct:
            setattr(cell, "editable", False)
            context.add_class("correct")
            GLib.timeout_add(2000, lambda: remove_class("correct"))
        else:
            context.add_class("wrong")

    def on_number_selected(self, num_button, target_cell, popover):
        number = num_button.get_label()
        target_cell.set_label(number)
        popover.popdown()

        row, col = target_cell.row, target_cell.col
        correct = str(self.solution[row][col])

        context = target_cell.get_style_context()
        self._clear_feedback_classes(context)
        self._specify_cell_correctness(context, number, correct, target_cell)

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
                next_cell = self.cell_buttons[new_row][new_col]
                next_cell.grab_focus()
                self.highlight_related_cells(new_row, new_col)
            return True

        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            cell = self.cell_buttons[row][col]
            if getattr(cell, "editable", False):
                self._show_popover(cell)
                return True

        if keyval in self.key_map:
            num = self.key_map[keyval]
            cell = self.cell_buttons[row][col]
            if getattr(cell, "editable", False):
                cell.set_label(num)
                correct = str(self.solution[row][col])
                context = cell.get_style_context()
                self._clear_feedback_classes(context)
                self._specify_cell_correctness(context, num, correct, cell)

        if keyval in self.remove_cell_keybindings:
            cell = self.cell_buttons[row][col]
            if getattr(cell, "editable", False):
                cell.set_label("")
                context = cell.get_style_context()
                self._clear_feedback_classes(context)
        return True

    def _has_saved_game(self):
        try:
            with open(SAVE_PATH, "r"):
                return True
        except Exception:
            return False
