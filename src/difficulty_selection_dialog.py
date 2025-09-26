# difficulty_selection_dialog.py
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
from functools import partial

from .game_board import (
    EASY_DIFFICULTY,
    MEDIUM_DIFFICULTY,
    HARD_DIFFICULTY,
    EXTREME_DIFFICULTY,
)


class DifficultySelectionDialog(Adw.Dialog):
    def __init__(self, on_select, **kwargs):
        super().__init__()
        self.set_title(_("Select Difficulty"))
        self.set_content_width(250)
        self.set_content_height(290)

        toolbar_view = Adw.ToolbarView.new()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        box = Gtk.ListBox(margin_start=12, margin_end=12, margin_top=12)
        box.add_css_class("boxed-list-separate")
        toolbar_view.set_content(box)

        # Create difficulty buttons
        difficulties = [
            (_("Easy"), EASY_DIFFICULTY),
            (_("Medium"), MEDIUM_DIFFICULTY),
            (_("Hard"), HARD_DIFFICULTY),
            (_("Extreme"), EXTREME_DIFFICULTY),
        ]

        for label_text, difficulty_value in difficulties:
            button = Adw.ButtonRow(title=label_text)
            button.add_css_class("text-button")
            button.set_tooltip_text(
                _("Start new game with {} difficulty").format(label_text.lower())
            )
            button.connect(
                "activated",
                partial(
                    self._on_button_clicked, on_select, difficulty_value, label_text
                ),
            )
            box.append(button)

        self.set_child(toolbar_view)

    def _on_button_clicked(self, callback, difficulty, label, *args):
        callback(difficulty, label)
        self.close()
