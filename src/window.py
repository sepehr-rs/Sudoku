# window.py
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

from gi.repository import Adw, Gtk, Gio
from gettext import gettext as _

from .game_board import GameBoard
from .game_manager import GameManager
from .ui_helpers import UIHelpers
from .difficulty_selection_dialog import DifficultySelectionDialog
from .help_overlay import HelpOverlay
from .finished_page import FinishedPage  # noqa: F401 Used in Blueprint


@Gtk.Template(resource_path="/io/github/sepehr_rs/Sudoku/blueprints/window.ui")
class SudokuWindow(Adw.ApplicationWindow):
    """Main application window."""

    __gtype_name__ = "SudokuWindow"

    # Template children
    stack = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()
    new_game_button = Gtk.Template.Child()
    main_menu_box = Gtk.Template.Child()
    game_view_box = Gtk.Template.Child()
    finished_page = Gtk.Template.Child()
    grid_container = Gtk.Template.Child()
    pencil_toggle_button = Gtk.Template.Child()
    primary_menu_button = Gtk.Template.Child()
    sudoku_window_title = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize game manager
        self.game_manager = GameManager(self)
        # Setup UI
        self._setup_ui()
        self._setup_stack_observer()

        # Add a click gesture to detect clicks anywhere in the window
        gesture = Gtk.GestureClick.new()
        gesture.connect("pressed", self.on_window_clicked)
        self.add_controller(gesture)
        action = Gio.SimpleAction.new("show-primary-menu", None)
        action.connect("activate", self.on_show_primary_menu)
        action = Gio.SimpleAction.new("show-help-overlay", None)
        action.connect("activate", self.on_show_help_overlay)
        self.add_action(action)

    def on_show_primary_menu(self, action, param):
        """Open the hamburger menu popover."""
        self.primary_menu_button.popup()

    def on_show_help_overlay(self, action, param):
        help_overlay = HelpOverlay()
        help_overlay.set_transient_for(self)
        help_overlay.present()

    def _get_grid_widget(self):
        frame = self.grid_container.get_first_child()
        if frame is None:
            return None
        return frame.get_child()

    def on_window_clicked(self, gesture, n_press, x, y):
        grid = self._get_grid_widget()
        if grid is None:
            return

        alloc = grid.get_allocation()

        if not (
            alloc.x <= x < alloc.x + alloc.width
            and alloc.y <= y < alloc.y + alloc.height
        ):
            self.on_grid_unfocus()

    def on_grid_unfocus(self):
        if self.game_manager and self.game_manager.cell_inputs:
            UIHelpers.clear_highlights(self.game_manager.cell_inputs, "highlight")
        # self.set_focus(None)

    def _setup_ui(self):
        """Setup the user interface."""
        # Setup buttons
        self.continue_button.set_sensitive(GameBoard.has_saved_game())
        self.continue_button.connect("clicked", self.on_continue_clicked)
        self.continue_button.set_tooltip_text(_("Continue Game"))
        self.new_game_button.connect("clicked", self.on_new_game_clicked)
        self.new_game_button.set_tooltip_text(_("New Game"))
        # Setup pencil button
        self.pencil_toggle_button.set_active(False)
        self.pencil_toggle_button.connect(
            "toggled", self.game_manager.on_pencil_toggled
        )

    def _setup_stack_observer(self):
        """Setup stack page change observer."""
        self.stack.connect("notify::visible-child", self.on_stack_page_changed)
        self.on_stack_page_changed(self.stack, None)

    def on_stack_page_changed(self, stack, param):
        """Handle stack page changes."""
        is_game_page = stack.get_visible_child() != self.main_menu_box
        self.lookup_action("back-to-menu").set_enabled(is_game_page)
        self.pencil_toggle_button.set_visible(is_game_page)

    def on_continue_clicked(self, button):
        """Handle continue button click."""
        self.game_manager.load_saved_game()

    def on_new_game_clicked(self, button):
        """Handle new game button click."""
        self._show_difficulty_dialog()

    def _show_difficulty_dialog(self):
        dialog = DifficultySelectionDialog(on_select=self.on_difficulty_selected)
        dialog.present(self)

    def on_difficulty_selected(self, difficulty: float, difficulty_label: str):
        """Handle difficulty selection."""
        self.sudoku_window_title.set_subtitle(f"{difficulty_label}")
        self.game_manager.start_game(difficulty, difficulty_label)
