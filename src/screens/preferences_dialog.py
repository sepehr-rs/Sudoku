from gi.repository import Adw
from .preferences_page import VariantPreferencesPage, GeneralPreferencesPage
from ..base.preferences_manager import PreferencesManager
from ..base.preferences import Preferences


class PreferencesDialog(Adw.PreferencesDialog):
    def __init__(self, auto_save_function):
        super().__init__(title="Preferences")
        self.auto_save_function = auto_save_function
        self.set_search_enabled(False)
        self.preferences = PreferencesManager.get_preferences()
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()
        page.add(group)
        group.add(
            GeneralPreferencesPage(
                self.preferences.general_defaults,
                "General Preferences",
                auto_save_function,
            )
        )

        group.add(
            VariantPreferencesPage(
                self.preferences.variant_defaults,
                self.preferences.name,
                auto_save_function,
            )
        )
        if not self.preferences:
            page = Adw.PreferencesPage()
            general_group = GeneralPreferencesPage(Preferences.general_defaults, "")
            page.add(general_group)
            self.add(page)
            return

        page = Adw.PreferencesPage()
        general_group = GeneralPreferencesPage(
            self.preferences.general_defaults, "", auto_save_function
        )
        variant_group = VariantPreferencesPage(
            self.preferences.variant_defaults, self.preferences.name, auto_save_function
        )

        page.add(general_group)
        page.add(variant_group)
        self.add(page)
