# game_setup_dialog.py
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

EASY_DIFFICULTY = 0.2
MEDIUM_DIFFICULTY = 0.5
HARD_DIFFICULTY = 0.7
EXTREME_DIFFICULTY = 0.9


class GameSetupDialog(Adw.Dialog):
    def __init__(self, on_select, **kwargs):
        super().__init__(**kwargs)
        self.set_title(_("New Game"))
        self.set_content_width(380)
        self.set_content_height(600)

        self.on_select = on_select
        self.selected_variant = "classic"
        self.selected_difficulty = MEDIUM_DIFFICULTY
        self._radio_groups = {}

        toolbar_view = Adw.ToolbarView.new()
        header = Adw.HeaderBar()
        toolbar_view.add_top_bar(header)

        main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            margin_top=12,
            margin_start=12,
            margin_end=12,
            margin_bottom=12
        )
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_child(main_box)
        toolbar_view.set_content(scrolled_window)

        variant_label = Gtk.Label(label=_("Select Variant"), xalign=0)
        variant_label.add_css_class("title-4")
        main_box.append(variant_label)

        variant_group_box = Gtk.ListBox()
        variant_group_box.add_css_class("boxed-list-separate")
        main_box.append(variant_group_box)

        self._create_radio_group(
            variant_group_box,
            items=[(_("Classic Sudoku"), "classic"), (_("Diagonal Sudoku"), "diagonal")],
            group_name="variant",
            default="classic"
        )

        difficulty_label = Gtk.Label(label=_("Select Difficulty"), xalign=0)
        difficulty_label.add_css_class("title-4")
        main_box.append(difficulty_label)

        difficulty_group_box = Gtk.ListBox()
        difficulty_group_box.add_css_class("boxed-list-separate")
        main_box.append(difficulty_group_box)

        self._create_radio_group(
            difficulty_group_box,
            items=[
                (_("Easy"), EASY_DIFFICULTY),
                (_("Medium"), MEDIUM_DIFFICULTY),
                (_("Hard"), HARD_DIFFICULTY),
                (_("Extreme"), EXTREME_DIFFICULTY)
            ],
            group_name="difficulty",
            default=MEDIUM_DIFFICULTY
        )

        confirm_button = Gtk.Button(label=_("Start Game"))
        confirm_button.add_css_class("suggested-action")
        confirm_button.connect("clicked", self._on_confirm_clicked)
        main_box.append(confirm_button)

        self.set_child(toolbar_view)

    def _create_radio_group(self, listbox, items, group_name, default=None):
        self._radio_groups[group_name] = []

        for label, value in items:
            btn = Gtk.CheckButton()
            if value == default:
                btn.set_active(True)
            btn.connect("toggled", self._on_radio_toggled, group_name, value)
            row = Adw.ActionRow(title=label)
            row.add_suffix(btn)
            row.set_activatable_widget(btn)
            listbox.append(row)
            self._radio_groups[group_name].append(btn)

    def _on_radio_toggled(self, button, group_name, value):
        if button.get_active():
            for b in self._radio_groups[group_name]:
                if b != button:
                    b.set_active(False)

            if group_name == "variant":
                self.selected_variant = value
            else:
                self.selected_difficulty = value

    def _on_confirm_clicked(self, button):
        self.on_select(self.selected_variant, self.selected_difficulty)
        self.close()
