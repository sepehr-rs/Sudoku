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
from gettext import gettext as _

class HowToPlayDialog(Adw.Dialog):
    def __init__(self, parent=None):
        super().__init__()
        self.set_title(_("How to Play Sudoku"))
        self.set_content_width(500)
        self.set_content_height(400)

        toolbar_view = Adw.ToolbarView.new()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        label = Gtk.Label(
            margin_top=10,
            margin_bottom=10,
            margin_start=10,
            margin_end=10,
            wrap=True
        )

        instructions_parts = [
            _("Welcome to Sudoku!"),
            "",
            _("The goal is to fill the grid so that every row, column, "
              "and 3x3 box contains the numbers 1 through 9 without repeats."),
            "",
            _("How to play:"),
            _("– Click on an empty cell to select it."),
            _("– Use your keyboard or pencil tool to input a number."),
            _("– Use the pencil tool to make notes."),
            _("– Use the backspace key to clear a cell."),
            _("– Try to solve the puzzle logically."),
            "",
            _("Good luck and have fun!"),
        ]

        label.set_text("\n".join(instructions_parts))
        toolbar_view.set_content(label)
        self.set_child(toolbar_view)
