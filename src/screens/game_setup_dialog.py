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
        self.set_content_height(610)

        self.on_select = on_select
        self.selected_variant = "classic"
        self.selected_difficulty = MEDIUM_DIFFICULTY
        self._radio_groups = {}

        toolbar_view = Adw.ToolbarView.new()
        toolbar_view.add_top_bar(Adw.HeaderBar())

        main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            margin_top=12,
            margin_start=12,
            margin_end=12,
            margin_bottom=12,
        )
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(main_box)
        toolbar_view.set_content(scroll)

        def add_section(label_text, items, group, default):
            label = Gtk.Label(label=label_text, xalign=0)
            label.add_css_class("title-3")
            main_box.append(label)
            lst = Gtk.ListBox()
            lst.add_css_class("boxed-list-separate")
            main_box.append(lst)
            self._create_radio_list(lst, items, group, default)

        add_section(
            _("Variant"),
            [(_("Classic Sudoku"), "classic"), (_("Diagonal Sudoku"), "diagonal")],
            "variant",
            "classic",
        )
        add_section(
            _("Difficulty"),
            [
                (_("Easy"), EASY_DIFFICULTY),
                (_("Medium"), MEDIUM_DIFFICULTY),
                (_("Hard"), HARD_DIFFICULTY),
                (_("Extreme"), EXTREME_DIFFICULTY),
            ],
            "difficulty",
            MEDIUM_DIFFICULTY,
        )

        btn = Gtk.Button(label=_("Start Game"))
        btn.add_css_class("pill")
        btn.add_css_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_hexpand(False)
        btn.connect("clicked", self._on_confirm_clicked)
        main_box.append(btn)
        self.set_child(toolbar_view)

    def _create_radio_list(self, listbox, items, group_name, default=None):
        self._radio_groups[group_name] = []
        group = None
        for label, value in items:
            btn = Gtk.CheckButton()
            btn.add_css_class("radio")
            if group:
                btn.set_group(group)
            else:
                group = btn
            if value == default:
                btn.set_active(True)
            btn.connect("toggled", self._on_radio_toggled, group_name, value)
            row = Adw.ActionRow(title=label)
            row.add_prefix(btn)
            row.connect("activated", lambda _r, b=btn: b.set_active(True))
            row.set_activatable_widget(btn)
            listbox.append(row)
            self._radio_groups[group_name].append(btn)

    def _on_radio_toggled(self, button, group_name, value):
        if button.get_active():
            setattr(self, f"selected_{group_name}", value)

    def _on_confirm_clicked(self, _):
        self.on_select(self.selected_variant, self.selected_difficulty)
        self.close()
