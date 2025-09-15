# application.py
#
# Copyright 2025 sepehr-rs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import gi
import platform

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gio, Adw, Gtk
from .window import SudokuWindow
from .help_dialog import HowToPlayDialog
from .log_utils import setup_logging


class SudokuApplication(Adw.Application):
    def __init__(self, version):
        super().__init__(
            application_id="io.github.sepehr_rs.Sudoku",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.version = version
        self._setup_actions()
        self._setup_accelerators()
        self.log_handler = setup_logging()

    def _setup_actions(self):
        """Set up application actions."""
        self.create_action("quit", self._on_close_request, ["<primary>q", "<primary>w"])
        self.create_action("about", self.on_about_action)
        self.create_action("how_to_play", self.on_how_to_play, ["F1"])

    def _setup_accelerators(self):
        """Set up keyboard accelerators for window actions."""
        self.set_accels_for_action("win.pencil-toggled", ["p"])
        self.set_accels_for_action("win.back-to-menu", ["<Ctrl>m"])
        self.set_accels_for_action("win.show-primary-menu", ["F10"])
        self.set_accels_for_action("win.show-help-overlay", ["<Ctrl>question"])

    def do_activate(self):
        """Called when the application is activated.

        We raise the application's main window, creating it if
        necessary.
        """
        win = self.props.active_window
        if not win:
            win = SudokuWindow(application=self)
        win.present()

    def generate_debug_info(self):
        debug_info = f"Sudoku {self.version}\n"
        debug_info += f"System: {platform.system()}\n"
        if platform.system() == "Linux":
            debug_info += f"Dist: {platform.freedesktop_os_release()['PRETTY_NAME']}\n"
        debug_info += f"Python {platform.python_version()}\n"
        debug_info += (
            f"GTK {Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}\n"
        )
        debug_info += (
            f"Adwaita {Adw.MAJOR_VERSION}.{Adw.MINOR_VERSION}.{Adw.MICRO_VERSION}"
        )
        debug_info += "PyGObject {}.{}.{}\n".format(*gi.version_info)
        debug_info += "\n--- Logs ---\n"
        debug_info += self.log_handler.get_logs()
        return debug_info

    def on_about_action(self, widget, _):
        """Callback for the app.about action."""
        debug_info = self.generate_debug_info()
        about = Adw.AboutDialog(
            application_name="Sudoku",
            application_icon="io.github.sepehr_rs.Sudoku",
            developer_name="Sepehr",
            version=self.version,
            developers=["Sepehr", "Revisto"],
            copyright="© 2025 sepehr-rs",
            license_type=Gtk.License.GPL_3_0,
            debug_info=debug_info,
            issue_url="https://github.com/sepehr-rs/sudoku/issues",
        )
        about.present(self.props.active_window)

    def on_how_to_play(self, action, param):
        """Show how to play dialog."""
        dialog = HowToPlayDialog()
        dialog.present(self.props.active_window)

    def _on_close_request(self, *args):
        self.quit()

    def create_action(self, name, callback, shortcuts=None):
        """Add an application action.

        Args:
            name: the name of the action
            callback: the function to be called when the action is
              activated
            shortcuts: an optional list of accelerators
        """
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)
