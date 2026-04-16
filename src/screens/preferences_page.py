# screens/preferences_page.py
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk, Adw

from ..log_utils import log_preference_change


class VariantPreferencesPage(Adw.PreferencesGroup):
    # TODO: Consider changing the preferences types for variants to list too.
    # TODO: This would provide easier use for descriptions and subtitles.
    def __init__(self, variant_preferences, name, auto_save_function):
        super().__init__(
            title=name,
        )
        # TODO: Fix variant preferences being none on startup
        self.variant_preferences = variant_preferences
        self.controls = {}
        self.auto_save_function = auto_save_function

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

    def on_toggle_changed(self, switch, _gparam, key):
        self.variant_preferences[key] = switch.get_active()
        log_preference_change("variant", key, self.variant_preferences[key])
        # self.get_toplevel().variant_preferences[key] = switch.get_active()
        self.auto_save_function()


class GeneralPreferencesPage(Adw.PreferencesGroup):
    def __init__(self, general_preferences, name, auto_save_function):
        super().__init__(title=name)
        self.general_preferences = general_preferences
        self.controls = {}
        self.auto_save_function = auto_save_function

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

    def on_toggle_changed(self, switch, _gparam, key):
        value = self.general_preferences[key]
        if isinstance(value, list):
            value[1] = switch.get_active()
            new_value = value[1]
        else:
            self.general_preferences[key] = switch.get_active()
            new_value = self.general_preferences[key]
        log_preference_change("general", key, new_value)
        self.auto_save_function()
