# game_over_page.py
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

    dark_picture = (
        "/io/github/sepehr_rs/Sudoku/illustrations/game-over-dark.svg"
    )
    light_picture = (
        "/io/github/sepehr_rs/Sudoku/illustrations/game-over-light.svg"
    )

    picture_contain = Gtk.Template.Child()
    title_label = Gtk.Template.Child()
    subtitle_label = Gtk.Template.Child()
    stats_mistakes_value = Gtk.Template.Child()
    stats_mistakes_label = Gtk.Template.Child()
    stats_progress_value = Gtk.Template.Child()
    stats_progress_label = Gtk.Template.Child()
    stats_difficulty_value = Gtk.Template.Child()
    stats_difficulty_label = Gtk.Template.Child()
    try_again_button = Gtk.Template.Child()
    new_game_button = Gtk.Template.Child()
    main_menu_button = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self._style_manager = Adw.StyleManager.get_default()
        self._style_manager.connect("notify::dark", self._update_picture)
        self.connect("map", self._on_map)

        self.title_label.set_label(_("Game Over"))
        self.stats_mistakes_label.set_label(_("Mistakes"))
        self.stats_progress_label.set_label(_("Complete"))
        self.stats_difficulty_label.set_label(_("Difficulty"))

    def populate(self, mistakes: int, percent: int, difficulty: str):
        self.subtitle_label.set_label(
            _("You reached {count} mistakes").format(count=mistakes)
        )
        self.stats_mistakes_value.set_label(str(mistakes))
        self.stats_progress_value.set_label(f"{percent}%")
        self.stats_difficulty_value.set_label(difficulty)

    def _on_map(self, _widget):
        self._update_picture()

    def _update_picture(self, *args):
        if self._style_manager.get_dark():
            self.picture_contain.set_resource(self.dark_picture)
        else:
            self.picture_contain.set_resource(self.light_picture)
