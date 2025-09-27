from gi.repository import Adw
from .preferences_page import VariantPreferencesPage, GeneralPreferencesPage
from ..base.preferences_manager import PreferencesManager


class PreferencesDialog(Adw.PreferencesWindow):
    def __init__(self, auto_save_function):
        super().__init__(title="Preferences")
        self.auto_save_function = auto_save_function
        self.set_default_size(600, 550)
        self.set_search_enabled(False)
        self.preferences = PreferencesManager.get_preferences()
        if not self.preferences:
            return
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()
        group.set_margin_bottom(24)
        page.add(group)
        group.add(
            GeneralPreferencesPage(
                self.preferences.general_defaults, "General Preferences"
            )
        )
        group.add(
            VariantPreferencesPage(
                self.preferences.variant_defaults, self.preferences.name,
                auto_save_function
            )
        )
        self.add(page)
