# popover_manager.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
from gi.repository import Gtk, GLib, Gdk
from ..core.preferences import PreferencesManager


class PopoverManager:
    def __init__(self, parent_grid, pencil_mode: bool, input_handler):
        self.parent_grid = parent_grid
        self.pencil_mode = pencil_mode
        self._input_handler = input_handler
        self._active_popover = None
        self._cell_popover = None
        self._last_popover_cell = None
        self._restore_focus_on_popover_close = False

    def get_or_create_popover(self) -> Gtk.Popover:
        if self._cell_popover is not None:
            return self._cell_popover
        return self._create_popover()

    def _create_popover(self) -> Gtk.Popover:
        popover = Gtk.Popover(position=Gtk.PositionType.BOTTOM)
        popover.set_has_arrow(False)
        popover.set_name("sudoku-popover")
        popover.set_parent(self.parent_grid)
        popover.connect("closed", self._on_popover_closed)
        self._cell_popover = popover
        return popover

    def invalidate(self):
        """Discard the current popover — call when the grid is rebuilt."""
        self._popdown_active_popover()
        self._cell_popover = None
        self._active_popover = None

    def _on_popover_closed(self, _popover):
        """Signal handler — fires after GTK has already closed the popover."""
        cell = self._last_popover_cell
        restore_focus = self._restore_focus_on_popover_close

        # Reset state unconditionally before any early return.
        self._active_popover = None
        self._restore_focus_on_popover_close = False
        self._last_popover_cell = None

        if not restore_focus or cell is None:
            return

        def _restore():
            cell.grab_focus()
            return False

        GLib.idle_add(_restore)

    def _popdown_active_popover(self):
        """Proactively dismiss the current popover (if any).

        Setting _restore_focus_on_popover_close to False first tells
        _on_popover_closed not to restore focus when we're the ones
        initiating the dismissal.
        """
        popover = self._active_popover
        if popover is None:
            return

        self._restore_focus_on_popover_close = False
        try:
            if popover.get_visible():
                popover.popdown()
        except AttributeError:
            logging.debug("Popover popdown skipped (attribute missing)", exc_info=True)

    def show_popover(self, cell, remaining_valid_inputs, button):
        """Defer popover display to the next GTK idle cycle.

        This avoids showing the popover mid-gesture, before GTK has
        finished processing the click event.
        """

        def _deferred():
            self._show_popover(cell, remaining_valid_inputs, mouse_button=button)
            return False

        GLib.idle_add(_deferred)

    def _show_popover(self, cell, remaining_valid_inputs, mouse_button=None):
        # Clearing the flag before _popdown_active_popover ensures
        # _on_popover_closed won't restore focus for the *old* popover.
        self._restore_focus_on_popover_close = False
        self._popdown_active_popover()

        if self.parent_grid is None:
            return

        popover = self.get_or_create_popover()
        self._point_popover_at_cell(popover, cell)
        self._build_and_show_popover_contents(
            cell,
            mouse_button,
            remaining_valid_inputs=remaining_valid_inputs,
        )

        self._last_popover_cell = cell
        self._restore_focus_on_popover_close = True
        self._active_popover = popover

    def _point_popover_at_cell(self, popover, cell):
        x, y, w, h = self._get_cell_geometry(cell)
        rect = self._create_rectangle(x, y, w, h)
        self._set_popover_position(popover, rect)

    def _build_and_show_popover_contents(
        self,
        cell,
        mouse_button,
        remaining_valid_inputs,
    ):
        popover = self.get_or_create_popover()
        grid = Gtk.Grid(row_spacing=5, column_spacing=5)
        popover.set_child(grid)

        num_buttons = self._add_number_buttons(
            grid, cell, popover, mouse_button, remaining_valid_inputs
        )
        clear_button = self._add_action_buttons(grid, cell, popover, mouse_button)

        controller = self._input_handler.make_popover_key_controller(
            num_buttons, clear_button
        )
        grid.add_controller(controller)

        grid.set_focus_on_click(True)
        grid.grab_focus()
        popover.popup()

    def _get_cell_geometry(self, cell):
        try:
            coords = cell.translate_coordinates(self.parent_grid, 0, 0)
        except (AttributeError, TypeError):
            coords = None

        alloc = cell.get_allocation()

        if coords is None:
            return alloc.x, alloc.y, alloc.width, alloc.height

        x, y = coords
        return x, y, alloc.width, alloc.height

    @staticmethod
    def _create_rectangle(x, y, w, h) -> Gdk.Rectangle:
        try:
            rect = Gdk.Rectangle()
            rect.x, rect.y, rect.width, rect.height = int(x), int(y), int(w), int(h)
        except TypeError:
            rect = Gdk.Rectangle(int(x), int(y), int(w), int(h))
        return rect

    def _set_popover_position(self, popover, rect):
        try:
            popover.set_pointing_to(rect)
        except (AttributeError, TypeError):
            logging.debug("Failed to set popover pointing rect", exc_info=True)

    def on_number_selected(self, num_button: Gtk.Button, cell, popover, mouse_button):
        # FIXME: Delegate to input handler:
        # number = num_button.get_label()
        # self._fill_cell(cell, number, ctrl_is_pressed=(mouse_button == 3))
        if not self.pencil_mode and mouse_button != 3:
            self._restore_focus_on_popover_close = False
            popover.popdown()

    def on_clear_selected(self, _button, cell, popover):
        cell.clear()
        self._restore_focus_on_popover_close = False
        popover.popdown()

    @staticmethod
    def create_number_button(label: str, callback, *args) -> Gtk.Button:
        """Create a consistently-styled number button."""
        button = Gtk.Button(label=label)
        button.set_size_request(40, 40)
        button.connect("clicked", callback, *args)
        return button

    @staticmethod
    def _make_counter_overlay(button, count) -> Gtk.Overlay:
        overlay = Gtk.Overlay()
        overlay.set_child(button)

        corner_label = Gtk.Label(label=count)
        corner_label.set_halign(Gtk.Align.END)
        corner_label.set_valign(Gtk.Align.START)
        corner_label.set_margin_start(2)
        corner_label.set_margin_end(3)
        corner_label.set_margin_top(2)
        corner_label.set_margin_bottom(2)
        corner_label.get_style_context().add_class("corner-label")

        overlay.add_overlay(corner_label)
        return overlay

    def _add_number_buttons(
        self, grid, cell, popover, mouse_button, remaining_valid_inputs
    ):
        prefs = PreferencesManager.get_preferences()
        show_remaining = prefs.general("show_remaining_valid_inputs")
        num_buttons = {}

        for i in range(1, 10):
            button = self.create_number_button(
                str(i), self.on_number_selected, cell, popover, mouse_button
            )
            count = remaining_valid_inputs[i] if show_remaining else None

            if count is not None and count > 0:
                widget = self._make_counter_overlay(button, count)
            elif count == 0:
                button.set_sensitive(False)
                widget = button
            else:
                widget = button

            grid.attach(widget, (i - 1) % 3, (i - 1) // 3, 1, 1)
            num_buttons[str(i)] = button

        return num_buttons

    def _add_action_buttons(self, grid, cell, popover, mouse_button) -> Gtk.Button:
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=5)
        grid.attach(button_box, 0, 3, 3, 1)

        clear_button = Gtk.Button(label=_("Clear"))
        clear_button.set_size_request(-1, 40)
        clear_button.set_hexpand(True)
        clear_button.set_tooltip_text(_("Clear Cell (Del/Backspace)"))
        clear_button.connect("clicked", self.on_clear_selected, cell, popover)
        button_box.append(clear_button)

        if self.pencil_mode or mouse_button == 3:
            done_button = Gtk.Button(label=_("Done"))
            done_button.set_size_request(-1, 40)
            done_button.set_hexpand(True)
            done_button.set_tooltip_text(_("Finish Editing Cell"))
            done_button.connect("clicked", lambda *_: popover.popdown())
            button_box.append(done_button)

        return clear_button
