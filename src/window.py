# window.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from gettext import gettext as _

from gi.repository import Adw, Gtk, Gio

from .core.persistence import (
    get_variant,
    has_saved_game,
    save_preferences,
    apply_variant_preferences,
    migrate_preferences_from_board,
)
from .core.preferences import PreferencesManager
from .screens.game_setup_dialog import GameSetupDialog
from .screens.preferences_dialog import PreferencesDialog
from .variants.classic_sudoku.controller import ClassicSudokuController
from .variants.diagonal_sudoku.controller import DiagonalSudokuController
from .variants.classic_sudoku.preferences import ClassicSudokuPreferences
from .variants.diagonal_sudoku.preferences import DiagonalSudokuPreferences
from .screens.finished_page import FinishedPage  # noqa: F401
from .screens.game_over_page import GameOverPage  # noqa: F401
from .screens.loading_screen import LoadingScreen  # noqa: F401

_TEMPLATE_WIDGET_TYPES = (FinishedPage, LoadingScreen, GameOverPage)


@Gtk.Template(resource_path="/io/github/sepehr_rs/Sudoku/blueprints/window.ui")
class SudokuWindow(Adw.ApplicationWindow):
    __gtype_name__ = "SudokuWindow"

    stack = Gtk.Template.Child()
    continue_button = Gtk.Template.Child()
    new_game_button = Gtk.Template.Child()
    main_menu_box = Gtk.Template.Child()  # Main screen
    finished_page = Gtk.Template.Child()
    game_over_page = Gtk.Template.Child()
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

        self.controller = None
        self.is_game_page = False

        actions = {
            "show-primary-menu": self.on_show_primary_menu,
            "back-to-menu": self.on_back_to_menu,
            "pencil-toggled": self._on_pencil_toggled_action,
            "show-preferences": self.on_show_preferences,
            "auto-pencil-marks": self.on_auto_pencil_marks,
        }
        for name, callback in actions.items():
            act = Gio.SimpleAction.new(name, None)
            act.connect("activate", callback)
            self.add_action(act)

        self._setup_stack_observer()
        self._setup_breakpoints()
        self._connect_buttons()
        self._build_primary_menu(show_game_actions=False)

        gesture = Gtk.GestureClick.new()
        gesture.set_button(0)
        gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        gesture.connect("pressed", self._on_window_pressed)
        self.add_controller(gesture)

    def on_show_primary_menu(self, *_):
        self.primary_menu_button.popup()

    def _update_preferences_visibility(self, visible: bool):
        self._build_primary_menu(show_game_actions=visible)

    def on_back_to_menu(self, *_):
        save_preferences()
        self.continue_button.set_visible(has_saved_game())
        self.update_sudoku_window_subtitle("")
        self.stack.set_visible_child(self.main_menu_box)
        self.pencil_toggle_button.set_visible(False)
        PreferencesManager.set_preferences(None)
        self._update_preferences_visibility(False)

    def on_auto_pencil_marks(self, *_):
        if self.controller and self.controller.board:
            self.controller.apply_auto_pencil_marks()

    def update_sudoku_window_subtitle(self, subtitle):
        self.sudoku_window_title.set_subtitle(subtitle)

    def _on_pencil_toggled_action(self, *_):
        if not self.is_game_page:
            return
        self.pencil_toggle_button.set_active(not self.pencil_toggle_button.get_active())
        self._change_subtitle_for_pencil_mode()

    def on_show_preferences(self, *_):
        if not self.controller:
            return

        def _on_prefs_changed():
            save_preferences()
            self.controller.board.save()
            self.controller._update_subtitle()

        PreferencesDialog(_on_prefs_changed).present(self)

    def _setup_stack_observer(self):
        self.stack.connect("notify::visible-child", self.on_stack_page_changed)
        self.on_stack_page_changed(self.stack, None)

    def _force_disable_pencil_mode(self):
        if self.pencil_toggle_button.get_active():
            self.pencil_toggle_button.set_active(False)
        if self.controller:
            self.controller.pencil_mode = False

    def on_stack_page_changed(self, stack, _):
        """Update UI elements based on the current visible page."""
        visible = stack.get_visible_child()

        # Reset pencil mode for non-game pages
        if visible in (
            self.main_menu_box,
            self.loading_screen,
            self.finished_page,
            self.game_over_page,
        ):
            self._force_disable_pencil_mode()
            self.update_sudoku_window_subtitle("")

        # Define state for each page type
        is_game_page = visible not in (
            self.main_menu_box,
            self.loading_screen,
            self.finished_page,
            self.game_over_page,
        )
        is_menu_or_loading = visible in (self.main_menu_box, self.loading_screen)

        # Update UI in a declarative way
        self._update_preferences_visibility(is_game_page)
        self.lookup_action("show-preferences").set_enabled(is_game_page)
        self.lookup_action("auto-pencil-marks").set_enabled(is_game_page)
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

    def _setup_breakpoints(self):
        def add_breakpoint(condition: str, mode: str):
            bp = Adw.Breakpoint.new(Adw.BreakpointCondition.parse(condition))

            bp.connect(
                "apply",
                lambda *_: self._apply_mode(True, mode),
            )
            bp.connect(
                "unapply",
                lambda *_: self._apply_mode(False, mode),
            )

            self.add_breakpoint(bp)

        add_breakpoint(
            "min-width: 800px and min-height: 800px",
            "large",
        )

        add_breakpoint(
            "max-width: 650px or max-height:700px",
            "compact",
        )

        add_breakpoint(
            "max-width: 550px or max-height:550px",
            "small",
        )

    def _connect_buttons(self):
        self.continue_button.connect("clicked", self.on_continue_clicked)
        self.new_game_button.connect("clicked", self.on_new_game_clicked)
        self.pencil_toggle_button.connect("toggled", self._on_pencil_toggled_button)
        self.continue_button.set_tooltip_text(_("Continue Saved Game"))
        self.new_game_button.set_tooltip_text(_("Start a New Game"))
        self.continue_button.set_visible(has_saved_game())
        self.home_button.set_visible(False)

    def get_controller_and_prefs(self, variant):
        if variant in ("classic", "Unknown"):
            return ClassicSudokuController(self), ClassicSudokuPreferences()
        if variant == "diagonal":
            return DiagonalSudokuController(self), DiagonalSudokuPreferences()
        raise ValueError(f"Unknown Sudoku variant: {variant}")

    def on_continue_clicked(self, _):
        variant = get_variant()
        if not variant:
            self.continue_button.set_visible(False)
            return
        self.controller, prefs = self.get_controller_and_prefs(variant)
        PreferencesManager.set_preferences(prefs)
        apply_variant_preferences(variant)
        migrate_preferences_from_board()
        self.controller.load_saved_game()
        self._setup_ui()

    def _setup_ui(self):
        self.pencil_toggle_button.set_active(False)
        self.lookup_action("show-preferences").set_enabled(True)
        self._update_preferences_visibility(True)

    def on_new_game_clicked(self, _):
        GameSetupDialog(on_select=self.on_game_setup_selected).present(self)

    def on_game_setup_selected(self, variant_name, difficulty):
        self.controller, prefs = self.get_controller_and_prefs(variant_name)
        PreferencesManager.set_preferences(prefs)
        apply_variant_preferences(variant_name)

        label_map = {
            0.2: _("Easy"),
            0.5: _("Medium"),
            0.7: _("Hard"),
            0.9: _("Extreme"),
        }
        label = label_map.get(difficulty, str(difficulty))

        self.update_sudoku_window_subtitle(f"{variant_name.capitalize()} • " f"{label}")
        self._setup_ui()
        self.controller.start_game(difficulty, label, variant_name)

    def _on_pencil_toggled_button(self, button):
        if self.controller:
            self._change_subtitle_for_pencil_mode()
            self.controller.on_pencil_toggled(button)

    def _change_subtitle_for_pencil_mode(self):
        non_game_pages = {
            self.main_menu_box,
            self.finished_page,
            self.game_over_page,
            self.loading_screen,
        }

        visible = self.stack.get_visible_child()
        if (
            not self.sudoku_window_title
            or not self.controller
            or visible in non_game_pages
        ):
            return

        prefs = PreferencesManager.get_preferences()
        if not prefs:
            return
        mistake_counter_on = prefs.general_counted_entry("mistake_limit")["enabled"]

        board = self.controller.board
        base = f"{board.variant.capitalize()} • {board.difficulty_label}"

        if self.pencil_toggle_button.get_active():
            self.update_sudoku_window_subtitle(_("Pencil Mode • Note possible numbers"))
        else:
            suffix = (
                f" • Mistakes: {self.controller.board.mistakes}"
                if mistake_counter_on
                else ""
            )
            self.update_sudoku_window_subtitle(base + suffix)

    def _build_primary_menu(self, show_game_actions=True):
        menu, section = Gio.Menu(), Gio.Menu()
        section.append(_("Keyboard Shortcuts"), "app.shortcuts")
        if show_game_actions:
            section.append(_("Preferences"), "win.show-preferences")
            section.append(_("Auto Pencil Marks"), "win.auto-pencil-marks")
        for label, action in [
            (_("How To Play"), "app.how_to_play"),
            (_("About Sudoku"), "app.about"),
        ]:
            section.append(label, action)
        menu.append_section(None, section)
        self.primary_menu_button.set_menu_model(menu)

    def _on_window_pressed(self, gesture, n_press, x, y):
        if gesture.get_current_button() != 1:
            return
        if not self.controller:
            return
        frame = self.grid_container.get_first_child()
        if not frame:
            return
        grid = frame.get_child()
        translated = grid.translate_coordinates(self, 0, 0)
        if translated is None:
            return
        gx, gy = translated[:2]
        alloc = grid.get_allocation()
        if not (gx <= x < gx + alloc.width and gy <= y < gy + alloc.height):
            self.controller.on_grid_unfocus()

    def _apply_mode(self, enabled: bool, mode: str):
        target = self.bp_bin or self

        css_class_map = {
            "large": "large",
            "compact": "compact-mode",
            "small": "small-mode",
        }

        css_class = css_class_map[mode]

        if enabled:
            target.add_css_class(css_class)
        else:
            target.remove_css_class(css_class)

        if mode in {"compact", "small"} and self.controller:
            self.controller.apply_compact_mode(enabled, mode)
