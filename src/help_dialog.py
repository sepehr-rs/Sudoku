# help_dialog.py
#
# Copyright 2025 sepehr-rs, Alexander Vanhee
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

from gi.repository import Gtk, Adw

class HowToPlayDialog(Adw.Dialog):
    def __init__(self, parent=None):
        super().__init__()
        self.set_title("How to Play Sudoku")
        self.set_content_width(500)
        self.set_content_height(400)

        toolbar_view = Adw.ToolbarView.new()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        label = Gtk.Label(margin_top=10, margin_bottom=10, margin_start=10,
            margin_end=10, wrap=True)

        instructions = (
            "Welcome to Sudoku!\n\n"
            "The goal is to fill the grid so that every row, column, "
            "and 3x3 box contains the numbers 1 through 9 without repeats.\n\n"
            "How to play:\n"
            "- Click on an empty cell to select it.\n"
            "- Use your keyboard or pencil tool to input a number.\n"
            "- Use the pencil tool to make notes.\n"
            "- Use the backspace key to clear a cell.\n"
            "- Try to solve the puzzle logically.\n\n"
            "Good luck and have fun!"
        )
        label.set_text(instructions)
        toolbar_view.set_content(label)
        self.set_child(toolbar_view)
