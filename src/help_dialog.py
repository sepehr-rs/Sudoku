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


@Gtk.Template(
    resource_path="/io/github/sepehr_rs/Sudoku/blueprints/how-to-play-dialog.ui"
)
class HowToPlayDialog(Adw.Dialog):
    __gtype_name__ = "HowToPlayDialog"
    carousel = Gtk.Template.Child()
    prev = Gtk.Template.Child()
    next = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.prev.connect("clicked", self.on_prev_clicked)
        self.next.connect("clicked", self.on_next_clicked)
        self.carousel.connect("page-changed", self.on_page_changed)
        self.update_button_sensitivity()

    def on_prev_clicked(self, button):
        current_page = self.carousel.get_position()
        if current_page > 0:
            self.carousel.scroll_to(
                self.carousel.get_nth_page(int(current_page) - 1),
                True
            )

    def on_next_clicked(self, button):
        current_page = self.carousel.get_position()
        n_pages = self.carousel.get_n_pages()
        if current_page < n_pages - 1:
            self.carousel.scroll_to(
                self.carousel.get_nth_page(int(current_page) + 1),
                True
            )

    def on_page_changed(self, carousel, index):
        self.update_button_sensitivity()

    def update_button_sensitivity(self):
        current_page = self.carousel.get_position()
        n_pages = self.carousel.get_n_pages()
        self.prev.set_sensitive(current_page > 0)
        self.next.set_sensitive(current_page < n_pages - 1)
