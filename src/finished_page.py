# finished_page.py
#
# Copyright 2025 sepehr-rs
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

import random
from gi.repository import Gtk
from gettext import gettext as _


@Gtk.Template(resource_path="/io/github/sepehr_rs/Sudoku/blueprints/finished-page.ui")
class FinishedPage(Gtk.Box):
    __gtype_name__ = "FinishedPage"

    finished_label = Gtk.Template.Child()
    back_button = Gtk.Template.Child()

    VICTORY_MESSAGES = [
        _("Sudoku Master! You've solved the puzzle with perfect logic!"),
        _("Incredible! Every number found its perfect place!"),
        _("Brilliant deduction! You've conquered this Sudoku challenge!"),
        _("Perfect solution! Your logical thinking is outstanding!"),
        _("Amazing work! You've mastered the art of Sudoku!"),
        _("Fantastic! Every row, column, and box is perfectly filled!"),
        _("Outstanding! Your puzzle-solving skills are remarkable!"),
        _("Excellent! You've completed the Sudoku with flying colors!"),
        _("Spectacular! Your mathematical reasoning is top-notch!"),
        _("Well done! You've proven yourself a Sudoku champion!"),
        _("Congratulations! You've solved the puzzle flawlessly!"),
        _("Victory! Your strategic thinking led to perfect completion!"),
        _("Genius! You've mastered the Sudoku grid with precision!"),
        _("Masterpiece! Every number placement was calculated perfectly!"),
        _("Phenomenal! You've conquered this Sudoku with style!"),
    ]

    def __init__(self):
        super().__init__()
        self.connect("map", self._on_map)

    def _on_map(self, widget):
        self._set_random_message()

    def _set_random_message(self):
        message = random.choice(self.VICTORY_MESSAGES)
        self.finished_label.set_label(message)
