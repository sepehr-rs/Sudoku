from gi.repository import Adw
from .preferences_page import VariantPreferencesPage, GeneralPreferencesPage
from ..base.preferences_manager import PreferencesManager
from ..base.preferences import Preferences


class PreferencesDialog(Adw.PreferencesWindow):
    def __init__(self, parent):
        super().__init__(title="Preferences")
        self.set_default_size(600, 550)
        self.set_search_enabled(False)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.preferences = PreferencesManager.get_preferences()
        if not self.preferences:
            page = Adw.PreferencesPage()
            general_group = GeneralPreferencesPage(Preferences.general_defaults, "")
            page.add(general_group)
            self.add(page)
            return

        page = Adw.PreferencesPage()
        general_group = GeneralPreferencesPage(self.preferences.general_defaults, "")
        variant_group = VariantPreferencesPage(
            self.preferences.variant_defaults, self.preferences.name
        )

        page.add(general_group)
        page.add(variant_group)
        self.add(page)
