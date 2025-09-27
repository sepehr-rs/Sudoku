# screens/general_page.py
from gi.repository import Gtk, Adw


class VariantPreferencesPage(Adw.PreferencesGroup):
    def __init__(self, variant_preferences, name, auto_save_function):
        super().__init__(title=name)
        # TODO: Fix variant preferences being none on startup
        self.variant_preferences = variant_preferences
        self.controls = {}
        self.auto_save_function = auto_save_function

        # Build toggles dynamically
        for key, default in self.variant_preferences.items():
            row = Adw.ActionRow(title=key.replace("_", " ").capitalize())

            switch = Gtk.Switch(valign=Gtk.Align.CENTER)
            switch.set_active(self.variant_preferences.get(key, default))
            switch.connect("notify::active", self.on_toggle_changed, key)

            row.add_suffix(switch)
            row.set_activatable_widget(switch)  # lets row click toggle the switch

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

        for key, default in self.general_preferences.items():
            row = Adw.ActionRow(title=key.replace("_", " ").capitalize())
            switch = Gtk.Switch(valign=Gtk.Align.CENTER)
            switch.set_active(self.general_preferences.get(key, default))
            switch.connect("notify::active", self.on_toggle_changed, key)
            row.add_suffix(switch)
            row.set_activatable_widget(switch)
            self.add(row)
            self.controls[key] = switch

    def on_toggle_changed(self, switch, gparam, key):
        self.general_preferences[key] = switch.get_active()
        self.auto_save_function()
