# tests/test_input_handler.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest.mock import MagicMock, patch

from gi.repository import Gtk, Gdk

from src.shared.input_handler import InputHandler


def _make_handler(**overrides):
    defaults = dict(
        on_move=MagicMock(),
        on_fill=MagicMock(),
        on_clear=MagicMock(),
        on_show_popover=MagicMock(),
        on_cell_click=MagicMock(),
        get_board_size=lambda: 9,
        get_direction=lambda: Gtk.TextDirection.LTR,
    )
    defaults.update(overrides)
    return InputHandler(**defaults)


class TestKeyMappings:
    def test_digit_keys_mapped(self):
        for i in range(1, 10):
            keyval = getattr(Gdk, f"KEY_{i}")
            assert InputHandler.setup_key_mappings()[0][keyval] == str(i)

    def test_numpad_keys_mapped(self):
        for i in range(1, 10):
            keyval = getattr(Gdk, f"KEY_KP_{i}")
            assert InputHandler.setup_key_mappings()[0][keyval] == str(i)

    def test_remove_keys_include_backspace_and_delete(self):
        _, remove_keys = InputHandler.setup_key_mappings()
        assert Gdk.KEY_BackSpace in remove_keys
        assert Gdk.KEY_Delete in remove_keys
        assert Gdk.KEY_KP_Delete in remove_keys


class TestArrowNavigation:
    @patch.object(Gdk.ModifierType, "CONTROL_MASK", 4)
    def test_arrow_down(self):
        h, on_move = _make_handler(), None
        h._on_move = on_move = MagicMock()
        h2 = _make_handler(on_move=on_move)
        h2.on_key_pressed(None, Gdk.KEY_Down, 0, 0, 3, 3)
        on_move.assert_called_once_with(3, 3, 4, 3)

    @patch.object(Gdk.ModifierType, "CONTROL_MASK", 4)
    def test_arrow_up(self):
        on_move = MagicMock()
        h = _make_handler(on_move=on_move)
        h.on_key_pressed(None, Gdk.KEY_Up, 0, 0, 3, 3)
        on_move.assert_called_once_with(3, 3, 2, 3)

    @patch.object(Gdk.ModifierType, "CONTROL_MASK", 4)
    def test_arrow_right(self):
        on_move = MagicMock()
        h = _make_handler(on_move=on_move)
        h.on_key_pressed(None, Gdk.KEY_Right, 0, 0, 3, 3)
        on_move.assert_called_once_with(3, 3, 3, 4)

    @patch.object(Gdk.ModifierType, "CONTROL_MASK", 4)
    def test_ctrl_right_jumps_by_block(self):
        on_move = MagicMock()
        h = _make_handler(on_move=on_move)
        h.on_key_pressed(None, Gdk.KEY_Right, 0, 4, 3, 3)
        on_move.assert_called_once_with(3, 3, 3, 6)

    @patch.object(Gdk.ModifierType, "CONTROL_MASK", 4)
    def test_arrow_blocked_at_boundary(self):
        on_move = MagicMock()
        h = _make_handler(on_move=on_move)
        h.on_key_pressed(None, Gdk.KEY_Up, 0, 0, 0, 0)
        on_move.assert_not_called()


class TestNumberKeys:
    @patch.object(Gdk.ModifierType, "CONTROL_MASK", 4)
    def test_digit_key_fills(self):
        on_fill = MagicMock()
        h = _make_handler(on_fill=on_fill)
        h.on_key_pressed(None, Gdk.KEY_5, 0, 0, 2, 3)
        on_fill.assert_called_once_with(2, 3, "5", False)

    @patch.object(Gdk.ModifierType, "CONTROL_MASK", 4)
    def test_ctrl_digit_fills_with_ctrl(self):
        on_fill = MagicMock()
        h = _make_handler(on_fill=on_fill)
        h.on_key_pressed(None, Gdk.KEY_5, 0, 4, 2, 3)
        on_fill.assert_called_once_with(2, 3, "5", True)


class TestUnicodeDigits:
    def test_non_digit_key_returns_false(self):
        h = _make_handler()
        result = h._handle_unicode_digit(Gdk.KEY_a, False, 0, 0)
        assert result is False


class TestEnterAndRemoveKeys:
    def test_enter_opens_popover(self):
        on_show_popover = MagicMock()
        h = _make_handler(on_show_popover=on_show_popover)
        h.on_key_pressed(None, Gdk.KEY_Return, 0, 0, 2, 3)
        on_show_popover.assert_called_once_with(2, 3)

    def test_backspace_clears(self):
        on_clear = MagicMock()
        h = _make_handler(on_clear=on_clear)
        h.on_key_pressed(None, Gdk.KEY_BackSpace, 0, 0, 2, 3)
        on_clear.assert_called_once_with(2, 3, clear_all=False)

    def test_delete_clears_all(self):
        on_clear = MagicMock()
        h = _make_handler(on_clear=on_clear)
        h.on_key_pressed(None, Gdk.KEY_Delete, 0, 0, 2, 3)
        on_clear.assert_called_once_with(2, 3, clear_all=True)


class TestCellClick:
    def test_left_click_routes(self):
        on_cell_click = MagicMock()
        h = _make_handler(on_cell_click=on_cell_click)
        h._on_cell_click(3, 5, 1, 1)
        on_cell_click.assert_called_once_with(3, 5, 1, 1)

    def test_right_click_routes(self):
        on_cell_click = MagicMock()
        h = _make_handler(on_cell_click=on_cell_click)
        h._on_cell_click(3, 5, 3, 1)
        on_cell_click.assert_called_once_with(3, 5, 3, 1)
