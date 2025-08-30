# loading_screen.py
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


@Gtk.Template(resource_path="/io/github/sepehr_rs/Sudoku/blueprints/loading-screen.ui")
class LoadingScreen(Gtk.Box):
    __gtype_name__ = "LoadingScreen"

    loading_message_label = Gtk.Template.Child()

    LOADING_MESSAGES = [
        _("Sharpening pencils…"),
        _("Because one solution is all you need…"),
        _("Trying not to make this impossible…"),
        _("Mathing really hard right now…"),
        _("If this takes long, blame the number 8."),
        _("One does not simply guess in Sudoku…"),
        _("Untangling a very stubborn grid…"),
        _("Filling in some blanks… and then erasing them again."),
        _("Yes, the computer is also sweating a little."),
        _("Solving it first, so you don’t have to…"),
        _("Erasing mistakes before you even see them…"),
        _("Making sure every 3x3 box feels special."),
        _("Convincing zero to stay out of Sudoku."),
        _("Giving each number its forever home."),
        _("Letting the algorithm have a snack break."),
    ]

    def __init__(self):
        super().__init__()
        self.connect("map", self._on_map)

    def _on_map(self, widget):
        self._set_random_message()

    def _set_random_message(self):
        message = random.choice(self.LOADING_MESSAGES)
        self.loading_message_label.set_label(message)
