# input_handler.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import unicodedata
from gi.repository import Gtk, Gdk


class InputHandler:
    """Translates raw GTK key and gesture events into game actions.

    All action callbacks are injected at construction time so this class
    has no dependency on the board, manager, or UI layer.
    """

    def __init__(
        self,
        *,
        on_move,  # (from_r, from_c, to_r, to_c) -> None
        on_fill,  # (row, col, value, ctrl) -> None
        on_clear,  # (row, col, clear_all) -> None
        on_show_popover,  # (row, col, button) -> None
        on_cell_click,  # (row, col, button) -> None
        get_board_size,  # () -> int
        get_direction,  # () -> Gtk.TextDirection
    ):
        self._on_move = on_move
        self._on_fill = on_fill
        self._on_clear = on_clear
        self._on_show_popover = on_show_popover
        self._on_cell_click = on_cell_click
        self._get_board_size = get_board_size
        self._get_direction = get_direction

        self.key_map, self.remove_keys = self.setup_key_mappings()

    def make_cell_gesture(self, callback):
        """Create a GestureClick controller for a cell.

        The returned gesture should be added to the cell widget by the caller.
        """
        gesture = Gtk.GestureClick.new()
        gesture.set_button(0)
        try:
            gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
        except AttributeError:
            gesture.set_exclusive(True)
        gesture.connect("released", callback)
        return gesture

    def make_cell_key_controller(self, row, col):
        """Create a key controller for a cell at (row, col)."""
        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", self.on_key_pressed, row, col)
        return controller

    def make_popover_key_controller(self, num_buttons, clear_button):
        """Create a key controller for the number-selection popover grid."""

        def on_key_pressed(controller, keyval, keycode, state):
            if keyval in self.key_map:
                num = self.key_map[keyval]
                if num in num_buttons:
                    num_buttons[num].emit("clicked")
                    return True
            if keyval in self.remove_keys:
                clear_button.emit("clicked")
                return True
            return False

        controller = Gtk.EventControllerKey()
        controller.connect("key-pressed", on_key_pressed)
        return controller

    def on_key_pressed(self, controller, keyval, keycode, state, row, col):
        ctrl = bool(state & Gdk.ModifierType.CONTROL_MASK)

        return (
            self._handle_arrow_keys(keyval, ctrl, row, col)
            or self._handle_number_keys(keyval, ctrl, row, col)
            or self._handle_unicode_digit(keyval, ctrl, row, col)
            or self._handle_enter_key(keyval, row, col)
            or self._handle_remove_keys(keyval, row, col)
        )

    def _handle_arrow_keys(self, keyval, ctrl, row, col):
        is_rtl = self._get_direction() == Gtk.TextDirection.RTL
        directions = {
            Gdk.KEY_Up: (-1, 0),
            Gdk.KEY_Down: (1, 0),
            Gdk.KEY_Left: (0, 1 if is_rtl else -1),
            Gdk.KEY_Right: (0, -1 if is_rtl else 1),
        }
        if keyval not in directions:
            return False

        dr, dc = directions[keyval]
        if ctrl:
            dr *= 3
            dc *= 3

        size = self._get_board_size()
        new_r, new_c = row + dr, col + dc
        if 0 <= new_r < size and 0 <= new_c < size:
            self._on_move(row, col, new_r, new_c)
        return True

    def _handle_number_keys(self, keyval, ctrl, row, col):
        num = self.key_map.get(keyval)
        if not num:
            return False
        self._on_fill(row, col, num, ctrl)
        return True

    def _handle_unicode_digit(self, keyval, ctrl, row, col):
        uni = Gdk.keyval_to_unicode(keyval)
        if uni == 0:
            return False
        try:
            digit = unicodedata.digit(chr(uni))
            if 1 <= digit <= 9:
                self._on_fill(row, col, str(digit), ctrl)
                return True
        except (ValueError, TypeError):
            pass
        return False

    def _handle_enter_key(self, keyval, row, col):
        if keyval in (Gdk.KEY_Return, Gdk.KEY_KP_Enter):
            self._on_show_popover(row, col)
            return True
        return False

    def _handle_remove_keys(self, keyval, row, col):
        if keyval not in self.remove_keys:
            return False
        self._on_clear(row, col, clear_all=(keyval == Gdk.KEY_Delete))
        return True

    def on_cell_clicked(self, gesture, n_press, x, y, row, col):
        button = self.gesture_get_button(gesture)
        if button not in (1, 3):
            return
        state = self.gesture_get_state(gesture)
        if self.should_ignore_click(button, state):
            return
        self._on_cell_click(row, col, button, n_press)

    @staticmethod
    def gesture_get_button(gesture):
        try:
            return gesture.get_current_button()
        except AttributeError:
            return None

    @staticmethod
    def gesture_get_state(gesture):
        try:
            return gesture.get_current_event_state()
        except AttributeError:
            return 0

    @staticmethod
    def should_ignore_click(button, state):
        """Detect ghost clicks when one mouse button is held and the other fires."""
        if button == 1 and (state & Gdk.ModifierType.BUTTON3_MASK):
            return True
        if button == 3 and (state & Gdk.ModifierType.BUTTON1_MASK):
            return True
        return False

    @staticmethod
    def setup_key_mappings():
        key_map = {getattr(Gdk, f"KEY_{i}"): str(i) for i in range(1, 10)}
        key_map.update({getattr(Gdk, f"KEY_KP_{i}"): str(i) for i in range(1, 10)})
        remove_keys = (Gdk.KEY_BackSpace, Gdk.KEY_Delete, Gdk.KEY_KP_Delete)
        return key_map, remove_keys
