# screens/preferences_page.py
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


class VariantPreferencesPage(Adw.PreferencesGroup):
    def __init__(self, variant_preferences, name, auto_save_function):
        super().__init__(title=name)
        self.variant_preferences = variant_preferences
        self.controls = {}
        self.auto_save_function = auto_save_function

        for key, default in self.variant_preferences.items():
            row = Adw.ActionRow(title=key.replace("_", " ").title())

            switch = Gtk.Switch(valign=Gtk.Align.CENTER)
            switch.set_active(self.variant_preferences.get(key, default))
            switch.connect("notify::active", self.on_toggle_changed, key)

            row.add_suffix(switch)
            row.set_activatable_widget(switch)

            self.add(row)
            self.controls[key] = switch

    def on_toggle_changed(self, switch, gparam, key):
        self.variant_preferences[key] = switch.get_active()
        self.auto_save_function()


class GeneralPreferencesPage(Adw.PreferencesGroup):
    def __init__(self, general_preferences, name, auto_save_function):
        super().__init__(title=name)
        self.general_preferences = general_preferences
        self.controls = {}
        self.auto_save_function = auto_save_function

        for key, value in self.general_preferences.items():
            if "enabled" in value and "count" in value:
                self._add_counted_toggle_row(key, value)
            else:
                self._add_bool_row(key, value)

    def _add_bool_row(self, key, value):
        title = key.replace("_", " ").title()
        tooltip = value.get("tooltip", "")
        active = value.get("value", False)

        row = Adw.ActionRow(title=title)
        if tooltip:
            row.set_subtitle(tooltip)

        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.set_active(active)
        switch.connect("notify::active", self._on_bool_changed, key)

        row.add_suffix(switch)
        row.set_activatable_widget(switch)

        self.add(row)
        self.controls[key] = switch

    def _add_counted_toggle_row(self, key, value):
        title = key.replace("_", " ").title()
        tooltip = value.get("tooltip", "")

        toggle_row = Adw.ActionRow(title=title)
        if tooltip:
            toggle_row.set_subtitle(tooltip)

        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.set_active(value["enabled"])

        toggle_row.add_suffix(switch)
        toggle_row.set_activatable_widget(switch)
        self.add(toggle_row)

        spin_row = Adw.SpinRow.new_with_range(1, 20, 1)
        spin_row.set_title("Mistake limit")
        spin_row.set_value(value["count"])
        spin_row.set_sensitive(value["enabled"])
        self.add(spin_row)

        switch.connect("notify::active", self._on_counted_toggle_changed, key, spin_row)
        spin_row.connect("notify::value", self._on_count_changed, key)

        self.controls[key] = (switch, spin_row)

    def _on_bool_changed(self, switch, gparam, key):
        self.general_preferences[key]["value"] = switch.get_active()
        self.auto_save_function()

    def _on_counted_toggle_changed(self, switch, gparam, key, spin_row):
        self.general_preferences[key]["enabled"] = switch.get_active()
        spin_row.set_sensitive(switch.get_active())
        self.auto_save_function()

    def _on_count_changed(self, spin_row, gparam, key):
        self.general_preferences[key]["count"] = int(spin_row.get_value())
        self.auto_save_function()
