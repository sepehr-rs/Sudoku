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

from gi.repository import Gtk, Adw, GObject


def _is_typed_entry(entry):
    return isinstance(entry, dict) and "schema" in entry and "value" in entry


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

        # Pass 1: create rows
        for key, value in self.general_preferences.items():
            row, control = self._build_row(key, value)
            if row is not None:
                self.add(row)
                self.controls[key] = control

        # Pass 2: wire depends_on bindings (requires controls to exist)
        for key, value in self.general_preferences.items():
            if not _is_typed_entry(value):
                continue
            depends_on = value["schema"].get("depends_on")
            if not depends_on:
                continue
            controller = self.controls.get(depends_on)
            dependent_row = self.controls.get(f"__row__{key}")
            if controller is None or dependent_row is None:
                continue
            controller.bind_property(
                "active",
                dependent_row,
                "sensitive",
                GObject.BindingFlags.SYNC_CREATE,
            )

    def _build_row(self, key, value):
        title = key.replace("_", " ").title()

        if _is_typed_entry(value):
            return self._build_typed_row(key, value, title)

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
        switch.connect("notify::active", self._on_legacy_switch_changed, key)

        row.add_suffix(switch)
        row.set_activatable_widget(switch)

        self.controls[f"__row__{key}"] = row
        return row, switch

    def _build_typed_row(self, key, entry, title):
        schema = entry["schema"]
        subtitle = schema.get("subtitle")

        if schema["type"] == "bool":
            row = Adw.SwitchRow(title=title)
            if subtitle:
                row.set_subtitle(subtitle)
            row.set_active(bool(entry["value"]))
            row.connect("notify::active", self._on_typed_bool_changed, key)
            self.controls[f"__row__{key}"] = row
            return row, row

        if schema["type"] == "int":
            lower = int(schema.get("min", 0))
            upper = int(schema.get("max", 100))
            adjustment = Gtk.Adjustment(
                lower=lower,
                upper=upper,
                step_increment=1,
                page_increment=1,
                value=int(entry["value"]),
            )
            row = Adw.SpinRow(title=title, adjustment=adjustment, digits=0)
            if subtitle:
                row.set_subtitle(subtitle)
            row.connect("notify::value", self._on_typed_int_changed, key)
            self.controls[f"__row__{key}"] = row
            return row, row

        return None, None

    def _on_legacy_switch_changed(self, switch, gparam, key):
        value = self.general_preferences[key]
        if isinstance(value, list):
            value[1] = switch.get_active()
        else:
            self.general_preferences[key] = switch.get_active()
        self.auto_save_function()

    def _on_typed_bool_changed(self, row, gparam, key):
        self.general_preferences[key]["value"] = row.get_active()
        self.auto_save_function()

    def _on_typed_int_changed(self, row, gparam, key):
        self.general_preferences[key]["value"] = int(row.get_value())
        self.auto_save_function()
