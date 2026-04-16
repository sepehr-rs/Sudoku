# about_dialog.py
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _
import logging

from gi.repository import Adw, Gtk

from ..base.debug_settings import save_debug_logging_preference
from .. import log_utils


class SudokuAboutDialog(Adw.PreferencesWindow):
    def __init__(self, parent, version: str):
        super().__init__(title=_("About Sudoku"))
        self.set_default_size(580, 520)
        self.set_transient_for(parent)
        self.set_modal(True)

        page = Adw.PreferencesPage()

        about_group = Adw.PreferencesGroup(title=_("About"))
        about_group.add(self._info_row(_("Application"), _("Sudoku")))
        about_group.add(self._info_row(_("Version"), version))
        about_group.add(self._info_row(_("Developers"), "Sepehr, Revisto"))
        page.add(about_group)

        troubleshooting_group = Adw.PreferencesGroup(title=_("Troubleshooting"))
        troubleshooting_group.set_description(
            _("Diagnostic controls and data useful for issue reports")
        )
        troubleshooting_group.add(self._debug_logging_row())
        page.add(troubleshooting_group)

        self.add(page)

    def _info_row(self, title: str, subtitle: str) -> Adw.ActionRow:
        row = Adw.ActionRow(title=title)
        row.set_subtitle(subtitle)
        row.set_activatable(False)
        return row

    def _debug_logging_row(self) -> Adw.ActionRow:
        row = Adw.ActionRow(title=_("Enable debug logging"))
        row.set_subtitle(_("Capture verbose logs and exception tracebacks"))

        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.set_active(log_utils.is_debug_logging_enabled())
        switch.connect("notify::active", self._on_debug_logging_toggled)

        row.add_suffix(switch)
        row.set_activatable_widget(switch)
        return row

    def _on_debug_logging_toggled(self, switch, _gparam) -> None:
        enabled = switch.get_active()
        try:
            save_debug_logging_preference(enabled)
        except OSError:
            logging.warning(
                (
                    "Unable to persist debug logging preference; "
                    "applying runtime setting only"
                ),
                exc_info=True,
            )
        log_utils.set_debug_logging(enabled)
