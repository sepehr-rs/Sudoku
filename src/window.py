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

from gi.repository import Adw, Gtk
from gettext import gettext as _
from .screens.difficulty_selection_dialog import DifficultySelectionDialog
from .screens.finished_page import FinishedPage  # noqa: F401 Used in Blueprint
from .screens.loading_screen import LoadingScreen  # noqa: F401 Used in Blueprint
from .screens.variant_selection_dialog import VariantSelectionDialog
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

    # Template children
    stack = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()
    new_game_button = Gtk.Template.Child()
    main_menu_box = Gtk.Template.Child()
    game_view_box = Gtk.Template.Child()
    finished_page = Gtk.Template.Child()
    loading_screen = Gtk.Template.Child()
    grid_container = Gtk.Template.Child()
    pencil_toggle_button = Gtk.Template.Child()
    primary_menu_button = Gtk.Template.Child()
    sudoku_window_title = Gtk.Template.Child()
    bp_bin = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Initialize the manager (replaces GameManager/GameBoard)
        self.manager = None
        self.selected_variant = None

        # Primary menu actions
        self.add_action_entries(
            (
                ("show-primary-menu", lambda *_: self.on_show_primary_menu()),
                ("back-to-menu", lambda *_: self.on_back_to_menu()),
                ("pencil-toggled", lambda *_: self._on_pencil_toggled_action()),
                ("show-preferences", lambda *_: self.on_show_preferences()),
            )
        )

        # Setup UI
        self._setup_stack_observer()
        self._setup_breakpoints()

        self.continue_button.connect("clicked", self.on_continue_clicked)
        self.continue_button.set_tooltip_text(_("Continue Game"))
        self.continue_button.set_sensitive(os.path.exists("saves/board.json"))
        self.new_game_button.connect("clicked", self.on_new_game_clicked)
        self.new_game_button.set_tooltip_text(_("New Game"))
        self.pencil_toggle_button.connect("toggled", self._on_pencil_toggled_button)

        # Add click gesture for unfocus
        gesture = Gtk.GestureClick.new()
        gesture.connect("pressed", self.on_window_clicked)
        self.add_controller(gesture)

    def _setup_ui(self):
        self.pencil_toggle_button.set_active(False)

    def _setup_stack_observer(self):
        self.stack.connect("notify::visible-child", self.on_stack_page_changed)
        self.on_stack_page_changed(self.stack, None)

    def on_stack_page_changed(self, stack, param):
        is_game_page = stack.get_visible_child() != self.main_menu_box
        self.lookup_action("back-to-menu").set_enabled(is_game_page)
        self.pencil_toggle_button.set_visible(is_game_page)

    def get_manager_type(self, filename: str = None):
        filename = filename or "saves/board.json"
        if not os.path.exists(filename):
            return None

        with open(filename, "r", encoding="utf-8") as f:
            state = json.load(f)

        return state.get("variant", "Unknown")

    def on_continue_clicked(self, button):
        variant = self.get_manager_type()
        if variant in ("classic", "Unknown"):
            self.manager = ClassicSudokuManager(self)
            PreferencesManager.set_preferences(ClassicSudokuPreferences())
        elif variant == "diagonal":
            self.manager = DiagonalSudokuManager(self)
            PreferencesManager.set_preferences(DiagonalSudokuPreferences())
        self.manager.load_saved_game()
        self._setup_ui()

    def on_new_game_clicked(self, button):
        self._show_variant_dialog()

    def _show_variant_dialog(self):
        dialog = VariantSelectionDialog(on_select=self.on_variant_selected)
        dialog.present(self)

    def on_variant_selected(self, variant_name: str):
        self.selected_variant = variant_name
        self._show_difficulty_dialog()

    def _show_difficulty_dialog(self):
        dialog = DifficultySelectionDialog(on_select=self.on_difficulty_selected)
        dialog.present(self)

    def on_difficulty_selected(self, difficulty: float, difficulty_label: str):
        """Initialize the manager based on variant and start game."""

        if self.selected_variant == "classic":
            self.manager = ClassicSudokuManager(self)
            PreferencesManager.set_preferences(ClassicSudokuPreferences())
        elif self.selected_variant == "diagonal":
            self.manager = DiagonalSudokuManager(self)
            PreferencesManager.set_preferences(DiagonalSudokuPreferences())
        else:
            raise ValueError(f"Unknown Sudoku variant: {self.selected_variant}")

        self.sudoku_window_title.set_subtitle(
            f"{self.selected_variant.capitalize()} - {difficulty_label}"
        )

        self._setup_ui()
        self.manager.start_game(difficulty, difficulty_label, self.selected_variant)

    def on_show_primary_menu(self):
        self.primary_menu_button.popup()

    def on_show_help_overlay(self, action, param):
        help_overlay = HelpOverlay()
        help_overlay.set_transient_for(self)
        help_overlay.present()

    def on_show_preferences(self, action, param):
        dialog = PreferencesDialog(
            self.manager.board.save_to_file
        )
        dialog.set_transient_for(self)
        dialog.present()

    def on_window_clicked(self, gesture, n_press, x, y):
        frame = self.grid_container.get_first_child()
        if frame is None:
            return
        grid = frame.get_child()
        alloc = grid.get_allocation()
        if not (
            alloc.x <= x < alloc.x + alloc.width
            and alloc.y <= y < alloc.y + alloc.height
        ):
            self.manager.on_grid_unfocus()

    def _setup_breakpoints(self):
        large_condition = Adw.BreakpointCondition.parse(
            "min-width: 750px and min-height: 750px"
        )
        large_condition = Adw.Breakpoint.new(large_condition)
        large_condition.connect("apply", lambda bp, *_: self._apply_large(True))
        large_condition.connect("unapply", lambda bp, *_: self._apply_large(False))
        self.add_breakpoint(large_condition)

        compact_condition = Adw.BreakpointCondition.parse(
            "max-width: 650px or max-height:700px"
        )
        compact_bp = Adw.Breakpoint.new(compact_condition)
        compact_bp.name = "compact-width"
        compact_bp.connect("apply", lambda bp, *_: self._apply_compact(True, "width"))
        compact_bp.connect(
            "unapply", lambda bp, *_: self._apply_compact(False, "width")
        )
        self.add_breakpoint(compact_bp)

        small_condition = Adw.BreakpointCondition.parse(
            "max-width: 400px or max-height:400px"
        )
        small_bp = Adw.Breakpoint.new(small_condition)
        small_bp.name = "compact-height"
        small_bp.connect("apply", lambda bp, *_: self._apply_compact(True, "height"))
        small_bp.connect("unapply", lambda bp, *_: self._apply_compact(False, "height"))
        self.add_breakpoint(small_bp)

    def _apply_large(self, large: bool):
        css_class = "large"
        target = self.bp_bin or self
        if large:
            target.add_css_class(css_class)
        else:
            target.remove_css_class(css_class)

    def _apply_compact(self, compact: bool, mode):
        css_class = f"{mode}-compact"
        target = self.bp_bin or self
        if compact:
            target.add_css_class(css_class)
        else:
            target.remove_css_class(css_class)

        parent_spacing = 8 if compact else 10
        block_spacing = 2 if compact else 4
        if not self.manager or not self.manager.parent_grid:
            return

        self.manager.parent_grid.set_row_spacing(parent_spacing)
        self.manager.parent_grid.set_column_spacing(parent_spacing)

        for row in self.manager.blocks:
            for block in row:
                block.set_row_spacing(block_spacing)
                block.set_column_spacing(block_spacing)

        for r in range(9):
            for c in range(9):
                cell = self.manager.cell_inputs[r][c]
                if cell:
                    cell.set_compact(compact)

    def on_back_to_menu(self):
        self.sudoku_window_title.set_subtitle("")
        self.stack.set_visible_child(self.main_menu_box)
        self.pencil_toggle_button.set_visible(False)
        PreferencesManager.set_preferences(None)

    def _on_pencil_toggled_button(self, button):
        if self.manager:
            self.manager.on_pencil_toggled(button)

    def _on_pencil_toggled_action(self):
        current = self.pencil_toggle_button.get_active()
        self.pencil_toggle_button.set_active(not current)
