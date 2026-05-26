# src/core/ui_utils.py
# Copyright 2026 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk, GLib


def schedule_feedback_clear(
    widget: Gtk.Widget,
    css_class: str,
    delay_ms: int,previous_source_id: int | None = None,
) -> int:
    """Applies a CSS class to a widget and schedules its removal.

    Args:
        widget: The GTK widget to highlight.
        css_class: The CSS class to apply and later remove.
        delay_ms: Delay in milliseconds before removing the class.
        previous_source_id: An existing timeout source ID to cancel before
            scheduling a new one. Pass ``self._feedback_source_id`` to avoid
            stacking timeouts.

    Returns:
        The new GLib timeout source ID. Store it and pass it as
        ``previous_source_id`` on the next call, or cancel it with
        ``GLib.source_remove(source_id)``.
    """
    if previous_source_id is not None:
        GLib.source_remove(previous_source_id)

    widget.get_style_context().add_class(css_class)
    return GLib.timeout_add(
        delay_ms,
        lambda: (widget.get_style_context().remove_class(css_class), False)[1],
    )
