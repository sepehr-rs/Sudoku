from gi.repository import Adw
from .preferences_page import VariantPreferencesPage, GeneralPreferencesPage
from ..base.preferences_manager import PreferencesManager
from ..base.preferences import Preferences


class PreferencesDialog(Adw.PreferencesWindow):
    def __init__(self, parent, auto_save_function):
        super().__init__(title="Preferences")
        self.auto_save_function = auto_save_function
        self.set_default_size(600, 550)
        self.set_search_enabled(False)
        self.set_transient_for(parent)
        self.set_modal(True)
        self.preferences = PreferencesManager.get_preferences()
        page = Adw.PreferencesPage()
        group = Adw.PreferencesGroup()
        group.set_margin_bottom(24)
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
