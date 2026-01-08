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
    # TODO: Consider changing the preferences types for variants to list too.
    # TODO: This would provide easier use for descriptions and subtitles.
    def __init__(self, variant_preferences, name):
        super().__init__(
            title=name,
        )
        # TODO: Fix variant preferences being none on startup
        self.variant_preferences = variant_preferences
        self.controls = {}

        # Build toggles dynamically
        for key, default in self.variant_preferences.items():
            row = Adw.ActionRow(title=key.replace("_", " ").title())

            switch = Gtk.Switch(valign=Gtk.Align.CENTER)
            switch.set_active(self.variant_preferences.get(key, default))
            switch.connect("notify::active", self.on_toggle_changed, key)

            row.add_suffix(switch)
            row.set_activatable_widget(switch)  # lets row click toggle the switch

            self.add(row)
            self.controls[key] = switch

    def on_toggle_changed(self, switch, gparam, key):
        self.variant_preferences[key] = switch.get_active()
        # self.get_toplevel().variant_preferences[key] = switch.get_active()


class GeneralPreferencesPage(Adw.PreferencesGroup):
    def __init__(self, general_preferences, name):
        super().__init__(title=name)
        self.general_preferences = general_preferences
        self.controls = {}

        for key, value in self.general_preferences.items():
            title = key.replace("_", " ").title()

            subtitle = None
            active = value

            if isinstance(value, list):
                subtitle = value[0]
                active = value[1]

            row = Adw.ActionRow(title=title)
            if subtitle:
                row.set_subtitle(subtitle)

            switch = Gtk.Switch(valign=Gtk.Align.CENTER)
            switch.set_active(active)
            switch.connect("notify::active", self.on_toggle_changed, key)

            row.add_suffix(switch)
            row.set_activatable_widget(switch)

            self.add(row)
            self.controls[key] = switch

    def on_toggle_changed(self, switch, gparam, key):
        value = self.general_preferences[key]
        if isinstance(value, list):
            value[1] = switch.get_active()
        else:
            self.general_preferences[key] = switch.get_active()
