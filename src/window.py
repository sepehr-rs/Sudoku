from gi.repository import Adw, Gtk, Gio
from gettext import gettext as _

from .variants.classic_sudoku.manager import ClassicSudokuManager
from .base.ui_helpers import UIHelpers
from .difficulty_selection_dialog import DifficultySelectionDialog
from .help_overlay import HelpOverlay
from .finished_page import FinishedPage  # noqa: F401 Used in Blueprint
from .loading_screen import LoadingScreen  # noqa: F401 Used in Blueprint


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
        self.manager = ClassicSudokuManager(self)

        # Primary menu and help actions
        for name, callback in [
            ("show-primary-menu", self.on_show_primary_menu),
            ("show-help-overlay", self.on_show_help_overlay),
            ("back-to-menu", self.on_back_to_menu),
        ]:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", callback)
            self.add_action(action)

        # Setup UI
        self._setup_ui()
        self._setup_stack_observer()
        self._setup_breakpoints()

        # Add click gesture for unfocus
        gesture = Gtk.GestureClick.new()
        gesture.connect("pressed", self.on_window_clicked)
        self.add_controller(gesture)

    def _setup_ui(self):
        self.continue_button.set_sensitive(self.manager.board_cls.has_saved_game())
        self.continue_button.connect("clicked", self.on_continue_clicked)
        self.continue_button.set_tooltip_text(_("Continue Game"))

        self.new_game_button.connect("clicked", self.on_new_game_clicked)
        self.new_game_button.set_tooltip_text(_("New Game"))

        self.pencil_toggle_button.set_active(False)
        self.pencil_toggle_button.connect("toggled", self.manager.on_pencil_toggled)

    def _setup_stack_observer(self):
        self.stack.connect("notify::visible-child", self.on_stack_page_changed)
        self.on_stack_page_changed(self.stack, None)

    def on_stack_page_changed(self, stack, param):
        is_game_page = stack.get_visible_child() != self.main_menu_box
        self.lookup_action("back-to-menu").set_enabled(is_game_page)
        self.pencil_toggle_button.set_visible(is_game_page)

    def on_continue_clicked(self, button):
        self.manager.load_saved_game()

    def on_new_game_clicked(self, button):
        self._show_difficulty_dialog()

    def _show_difficulty_dialog(self):
        dialog = DifficultySelectionDialog(on_select=self.on_difficulty_selected)
        dialog.present(self)

    def on_difficulty_selected(self, difficulty: float, difficulty_label: str):
        self.sudoku_window_title.set_subtitle(f"{difficulty_label}")
        self.manager.start_game(difficulty, difficulty_label)

    def on_show_primary_menu(self, action, param):
        self.primary_menu_button.popup()

    def on_show_help_overlay(self, action, param):
        help_overlay = HelpOverlay()
        help_overlay.set_transient_for(self)
        help_overlay.present()

    def on_window_clicked(self, gesture, n_press, x, y):
        frame = self.grid_container.get_first_child()
        if frame is None:
            return
        grid = frame.get_child()
        alloc = grid.get_allocation()
        if not (alloc.x <= x < alloc.x + alloc.width and alloc.y <= y < alloc.y + alloc.height):
            self.manager.on_grid_unfocus()

    def _setup_breakpoints(self):
        compact_condition = Adw.BreakpointCondition.parse("max-width: 550px or max-height:600px")
        compact_bp = Adw.Breakpoint.new(compact_condition)
        compact_bp.name = "compact-width"
        compact_bp.connect("apply", lambda bp, *_: self._apply_compact(True, "width"))
        compact_bp.connect("unapply", lambda bp, *_: self._apply_compact(False, "width"))
        self.add_breakpoint(compact_bp)

        small_condition = Adw.BreakpointCondition.parse("max-width: 400px or max-height:400px")
        small_bp = Adw.Breakpoint.new(small_condition)
        small_bp.name = "compact-height"
        small_bp.connect("apply", lambda bp, *_: self._apply_compact(True, "height"))
        small_bp.connect("unapply", lambda bp, *_: self._apply_compact(False, "height"))
        self.add_breakpoint(small_bp)

    def _apply_compact(self, compact: bool, mode):
        css_class = f"{mode}-compact"
        target = self.bp_bin or self
        if compact:
            target.add_css_class(css_class)
        else:
            target.remove_css_class(css_class)

        parent_spacing = 8 if compact else 10
        block_spacing = 2 if compact else 4

        if self.manager.parent_grid:
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

    def on_back_to_menu(self, action, param):
        self.stack.set_visible_child(self.main_menu_box)
        self.pencil_toggle_button.set_visible(False)