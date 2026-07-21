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

from gi.repository import Gtk, Adw
from gettext import gettext as _


@Gtk.Template(resource_path="/io/github/sepehr_rs/Sudoku/blueprints/game-over-page.ui")
class GameOverPage(Gtk.Box):
    __gtype_name__ = "GameOverPage"

    # TODO: Take a look at the dark/light pictures for both states later.
    picture = "/io/github/sepehr_rs/Sudoku/illustrations/" "puzzle-game-over.svg"
    finished_label = Gtk.Template.Child()
    picture_contain = Gtk.Template.Child()

    GAMEOVER_MESSAGE = _("Game Over!")

    def __init__(self):
        super().__init__()
        self._style_manager = Adw.StyleManager.get_default()
        self.connect("map", self._on_map)

    def _on_map(self, widget):
        self._set_message()
        self._update_picture()

    def _set_message(self):
        message = self.GAMEOVER_MESSAGE
        self.finished_label.set_label(message)

    def _update_picture(self, *args):
        self.picture_contain.set_resource(self.picture)
