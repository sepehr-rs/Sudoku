from gi.repository import Adw
from .preferences_page import GeneralPreferencesPage


class PreferencesDialog(Adw.PreferencesWindow):
    def __init__(self):
        super().__init__(title="Preferences")
        self.set_default_size(600, 550)
        self.set_search_enabled(False)
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()
        page.add(group)

        group.add(GeneralPreferencesPage())
        self.add(page)
