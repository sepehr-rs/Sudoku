from gi.repository import Adw
from .preferences_page import VariantPreferencesPage, GeneralPreferencesPage
from ..core.preferences import PreferencesManager


class PreferencesDialog(Adw.PreferencesDialog):
    def __init__(self, auto_save_function):
        super().__init__(title="Preferences")
        self.set_search_enabled(False)
        preferences = PreferencesManager.get_preferences()

        page = Adw.PreferencesPage()

        general_group = GeneralPreferencesPage(
            preferences.general_defaults, "General", auto_save_function
        )
        variant_group = VariantPreferencesPage(
            preferences.variant_defaults, preferences.name, auto_save_function
        )

        page.add(general_group)
        page.add(variant_group)
        self.add(page)
