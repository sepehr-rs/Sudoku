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
from .screens.game_setup_dialog import GameSetupDialog
from .screens.shortcuts_overlay import ShortcutsOverlay
from .screens.finished_page import FinishedPage  # noqa: F401
from .screens.loading_screen import LoadingScreen  # noqa: F401
from .screens.preferences_dialog import PreferencesDialog
from .variants.classic_sudoku.manager import ClassicSudokuManager
from .variants.classic_sudoku.preferences import ClassicSudokuPreferences
from .variants.diagonal_sudoku.manager import DiagonalSudokuManager
from .variants.diagonal_sudoku.preferences import DiagonalSudokuPreferences
from .base.preferences_manager import PreferencesManager
import os
import json


@Gtk.Template(resource_path="/io/github/sepehr_rs/Sudoku/blueprints/window.ui")
class SudokuWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SudokuWindow"

    stack = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()
    new_game_button = Gtk.Template.Child()
    main_menu_box = Gtk.Template.Child()  # Main screen
    finished_page = Gtk.Template.Child()
    loading_screen = Gtk.Template.Child()
    grid_container = Gtk.Template.Child()
    pencil_toggle_button = Gtk.Template.Child()
    primary_menu_button = Gtk.Template.Child()  # Hamburger menu
    sudoku_window_title = Gtk.Template.Child()
    home_button = Gtk.Template.Child()  # back arrow
    bp_bin = Gtk.Template.Child()
    game_scrolled_window = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.manager = None
        self.is_game_page = False
        actions = {
            "show-primary-menu": self.on_show_primary_menu,
            "show-shortcuts-overlay": self.on_show_shortcuts_overlay,
            "back-to-menu": self.on_back_to_menu,
            "pencil-toggled": self._on_pencil_toggled_action,
            "show-preferences": self.on_show_preferences,
        }
        for name, callback in actions.items():
            act = Gio.SimpleAction.new(name, None)
            act.connect("activate", callback)
            self.add_action(act)

        self._setup_stack_observer()
        self._setup_breakpoints()
        self._connect_buttons()
        self._build_primary_menu(show_preferences=False)

        gesture = Gtk.GestureClick.new()
        gesture.connect("pressed", self.on_window_clicked)
        self.add_controller(gesture)

    def _connect_buttons(self):
        self.continue_button.connect("clicked", self.on_continue_clicked)
        self.new_game_button.connect("clicked", self.on_new_game_clicked)
        self.pencil_toggle_button.connect("toggled", self._on_pencil_toggled_button)
        self.continue_button.set_tooltip_text(_("Continue Game"))
        self.new_game_button.set_tooltip_text(_("New Game"))
        self.continue_button.set_visible(os.path.exists("saves/board.json"))
        self.home_button.set_visible(False)

    def _update_preferences_visibility(self, visible: bool):
        self._build_primary_menu(show_preferences=visible)

    def _setup_ui(self):
        self.pencil_toggle_button.set_active(False)
        self.lookup_action("show-preferences").set_enabled(True)
        self._update_preferences_visibility(True)

    def _setup_stack_observer(self):
        self.stack.connect("notify::visible-child", self.on_stack_page_changed)
        self.on_stack_page_changed(self.stack, None)

    def on_stack_page_changed(self, stack, _):
        """Update UI elements based on the current visible page."""
        visible = stack.get_visible_child()

        # Reset pencil mode for non-game pages
        if visible in (self.main_menu_box, self.loading_screen, self.finished_page):
            self._force_disable_pencil_mode()
            self.sudoku_window_title.set_subtitle("")

        # Define state for each page type
        is_game_page = visible not in (
            self.main_menu_box,
            self.loading_screen,
            self.finished_page,
        )
        is_menu_or_loading = visible in (self.main_menu_box, self.loading_screen)

        # Update UI in a declarative way
        self._update_preferences_visibility(is_game_page)
        self.lookup_action("show-preferences").set_enabled(is_game_page)
        self.pencil_toggle_button.set_visible(is_game_page)
        self.lookup_action("show-primary-menu").set_enabled(is_game_page)
        self.lookup_action("back-to-menu").set_enabled(not is_menu_or_loading)
        self.home_button.set_visible(not is_menu_or_loading)
        self.primary_menu_button.set_visible(is_game_page)

        # Update subtitle for game pages
        if is_game_page:
            self.is_game_page = True
            self._change_subtitle_for_pencil_mode()
        else:
            self.is_game_page = False

    def _get_variant_and_prefs(self, variant):
        if variant in ("classic", "Unknown"):
            return ClassicSudokuManager(self), ClassicSudokuPreferences()
        if variant == "diagonal":
            return DiagonalSudokuManager(self), DiagonalSudokuPreferences()
        raise ValueError(f"Unknown Sudoku variant: {variant}")

    def get_manager_type(self, filename=None):
        path = filename or "saves/board.json"
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("variant", "Unknown")

    def on_continue_clicked(self, _):
        variant = self.get_manager_type()
        self.manager, prefs = self._get_variant_and_prefs(variant)
        PreferencesManager.set_preferences(prefs)
        self.manager.load_saved_game()
        self._setup_ui()

    def on_new_game_clicked(self, _):
        GameSetupDialog(on_select=self.on_game_setup_selected).present(self)

    def on_game_setup_selected(self, variant_name, difficulty):
        self.manager, prefs = self._get_variant_and_prefs(variant_name)
        PreferencesManager.set_preferences(prefs)

        label_map = {
            0.2: _("Easy"),
            0.5: _("Medium"),
            0.7: _("Hard"),
            0.9: _("Extreme"),
        }
        label = label_map.get(difficulty, str(difficulty))

        self.sudoku_window_title.set_subtitle(f"{variant_name.capitalize()} • {label}")
        self._setup_ui()
        self.manager.start_game(difficulty, label, variant_name)

    def on_show_primary_menu(self, *_):
        self.primary_menu_button.popup()

    def on_show_shortcuts_overlay(self, *_):
        shortcuts_overlay = ShortcutsOverlay(transient_for=self)
        shortcuts_overlay.present()

    def on_show_preferences(self, *_):
        PreferencesDialog(self).present()

    def on_window_clicked(self, _, __, x, y):
        frame = self.grid_container.get_first_child()
        if not frame:
            return
        grid = frame.get_child()
        alloc = grid.get_allocation()
        if not (
            alloc.x <= x < alloc.x + alloc.width
            and alloc.y <= y < alloc.y + alloc.height
        ):
            self.manager.on_grid_unfocus()

    def _setup_breakpoints(self):
        def bp(cond, apply_cb, unapply_cb):
            bp = Adw.Breakpoint.new(Adw.BreakpointCondition.parse(cond))
            bp.connect("apply", lambda *_: apply_cb(True))
            bp.connect("unapply", lambda *_: unapply_cb(False))
            self.add_breakpoint(bp)

        bp(
            "min-width: 800px and min-height: 800px",
            lambda large: self._apply_large(large),
            lambda large: self._apply_large(large),
        )
        bp(
            "max-width: 650px or max-height:700px",
            lambda c: self._apply_compact(c, "compact"),
            lambda c: self._apply_compact(c, "compact"),
        )
        bp(
            "max-width: 550px or max-height:550px",
            lambda c: self._apply_compact(c, "small"),
            lambda c: self._apply_compact(c, "small"),
        )

    def _apply_large(self, large):
        if large:
            self.bp_bin.add_css_class("large")
        else:
            self.bp_bin.remove_css_class("large")

    def _apply_compact(self, compact, mode):
        target = self.bp_bin or self
        css_class = f"{mode}-mode"
        if compact:
            target.add_css_class(css_class)
        else:
            target.remove_css_class(css_class)

        if not self.manager or not self.manager.parent_grid:
            return

        parent_spacing, block_spacing = (8, 2) if compact else (10, 4)
        self.manager.parent_grid.set_row_spacing(parent_spacing)
        self.manager.parent_grid.set_column_spacing(parent_spacing)

        for row in self.manager.blocks:
            for block in row:
                block.set_row_spacing(block_spacing)
                block.set_column_spacing(block_spacing)

        for row in self.manager.cell_inputs:
            for cell in row:
                if cell:
                    cell.set_compact(compact)

        scrolled = self.game_scrolled_window
        if scrolled:
            scrolled.set_vexpand(True)
            scrolled.set_hexpand(True)
        grid_container = self.grid_container
        grid_container.set_hexpand(True)
        grid_container.set_vexpand(True)
        self.bp_bin.set_hexpand(True)
        self.bp_bin.set_vexpand(True)
        self.bp_bin.set_halign(Gtk.Align.FILL)
        self.bp_bin.set_valign(Gtk.Align.FILL)

        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)
        self.stack.set_halign(Gtk.Align.FILL)
        self.stack.set_valign(Gtk.Align.FILL)

    def on_back_to_menu(self, *_):
        self.continue_button.set_visible(os.path.exists("saves/board.json"))
        self.sudoku_window_title.set_subtitle("")
        self.stack.set_visible_child(self.main_menu_box)
        self.pencil_toggle_button.set_visible(False)
        PreferencesManager.set_preferences(None)
        self._update_preferences_visibility(False)

    def _on_pencil_toggled_button(self, button):
        if self.manager:
            self._change_subtitle_for_pencil_mode()
            self.manager.on_pencil_toggled(button)

    def _on_pencil_toggled_action(self, *_):
        if not self.is_game_page:
            return
        self.pencil_toggle_button.set_active(not self.pencil_toggle_button.get_active())
        self._change_subtitle_for_pencil_mode()

    def _change_subtitle_for_pencil_mode(self):
        non_game_pages = {
            self.main_menu_box,
            self.finished_page,
            self.loading_screen,
        }

        visible = self.stack.get_visible_child()
        if (
            not self.sudoku_window_title
            or not self.manager
            or visible in non_game_pages
        ):
            return

        if self.pencil_toggle_button.get_active():
            self.sudoku_window_title.set_subtitle(
                _("Pencil Mode • Note possible numbers")
            )
        else:
            self.sudoku_window_title.set_subtitle(
                f"{self.manager.board.variant.capitalize()} • "
                f"{self.manager.board.difficulty_label}"
            )

    def _force_disable_pencil_mode(self):
        if self.pencil_toggle_button.get_active():
            self.pencil_toggle_button.set_active(False)

        if self.manager:
            self.manager.pencil_mode = False

    def _build_primary_menu(self, show_preferences=True):
        menu, section = Gio.Menu(), Gio.Menu()
        section.append(_("Keyboard Shortcuts"), "win.show-shortcuts-overlay")
        if show_preferences:
            section.append(_("Preferences"), "win.show-preferences")
        for label, action in [
            (_("How To Play"), "app.how_to_play"),
            (_("About Sudoku"), "app.about"),
        ]:
            section.append(label, action)
        menu.append_section(None, section)
        self.primary_menu_button.set_menu_model(menu)
