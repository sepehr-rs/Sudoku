# screens/general_page.py
from gi.repository import Gtk, Adw
from ..base.preferences_manager import PreferencesManager


class GeneralPreferencesPage(Adw.PreferencesGroup):
    def __init__(self):
        super().__init__(title="General")
        # TODO: Fix variant preferences being none on startup
        self.variant_preferences = PreferencesManager.get_preferences()
        if not self.variant_preferences:
            return
        self.controls = {}

        # Build toggles dynamically
        for key, default in self.variant_preferences.defaults.items():
            row = Adw.ActionRow(title=key.replace("_", " ").capitalize())

            switch = Gtk.Switch(valign=Gtk.Align.CENTER)
            switch.set_active(self.variant_preferences.defaults.get(key, default))
            switch.connect("notify::active", self.on_toggle_changed, key)

            row.add_suffix(switch)
            row.set_activatable_widget(switch)  # lets row click toggle the switch

            self.add(row)
            self.controls[key] = switch

    def on_toggle_changed(self, switch, gparam, key):
        self.variant_preferences.defaults[key] = switch.get_active()
        # self.get_toplevel().variant_preferences[key] = switch.get_active()
