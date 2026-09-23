# shared/utils.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk, GLib


def schedule_feedback_clear(
    widget: Gtk.Widget,
    css_class: str,
    delay_ms: int,
    previous_source_id: int | None = None,
) -> int:
    """Apply a CSS class to a widget and schedule its removal after a delay.

    Returns the new GLib timeout source ID so the caller can cancel it later.
    """
    if previous_source_id is not None:
        GLib.source_remove(previous_source_id)

    widget.get_style_context().add_class(css_class)

    def _remove():
        widget.get_style_context().remove_class(css_class)
        return False

    return GLib.timeout_add(delay_ms, _remove)


def clear_cell_feedback(widget: Gtk.Widget, *css_classes: str):
    """Remove one or more CSS classes from a widget and clear its tooltip."""
    ctx = widget.get_style_context()
    for cls in css_classes:
        ctx.remove_class(cls)
    widget.set_tooltip_text("")
