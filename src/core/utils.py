# src/core/ui_utils.py
# Copyright 2026 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from gi.repository import Gtk, GLib


# def _remove():
#     widget.get_style_context().remove_class(css_class)
#     return False


def schedule_feedback_clear(
    widget: Gtk.Widget,
    css_class: str,
    delay_ms: int,
    previous_source_id: int | None = None,
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
    return GLib.timeout_add(delay_ms, _remove)


# TODO: Rework these:
# def get_remaining_valid_inputs(self) -> dict:
#     """
#     Return how many times each value (1–9) can still be correctly placed.

#     Starts from 9 for each value and subtracts once for every correct
#     user input and once for every pre-filled puzzle cell containing that value.

#     Returns:
#         A dict mapping each value 1–9 to its remaining placement count,
#         or an empty dict if the puzzle or user inputs are not set.
#     """

#     if not self.puzzle or not self.user_inputs:
#         return {}

#     # Count numbers in solution
#     remaining_valid_inputs = {i: 9 for i in range(1, 10)}

#     # Count numbers in the user input
#     for row in range(0, 9):
#         for column in range(0, 9):
#             if not self.get_input(row, column):
#                 continue
#             if not int(self.get_input(row, column)) == self.get_correct_value(
#                 row, column
#             ):
#                 continue
#             else:
#                 remaining_valid_inputs[int(self.get_input(row, column))] -= 1

#     # Substitute remaining_valid_inputs from pre-set values in the puzzle
#     for row in range(0, 9):
#         for column in range(0, 9):
#             if not self.puzzle[row][column]:
#                 continue
#             remaining_valid_inputs[self.puzzle[row][column]] -= 1

#     return remaining_valid_inputs
# @abstractmethod
# def is_solved(self) -> bool:
#     pass

# @abstractmethod
# def is_conflicting(self, value: int, regions: dict[str, set[int]]) -> bool:
#     """
#     Check whether `value` conflicts with any of the given regions.

#     Each region is a set of values already present in that area of the board.
#     Subclasses define which regions are relevant (e.g. block, diagonal, color).

#     Args:
#         value: The candidate value to check.
#         row: Values already in the cell's row.
#         col: Values already in the cell's column.
#         **regions: Additional variant-specific regions (e.g. block, diagonal).

#     Returns:
#         True if `value` is already present in any region, False otherwise.
#     """
#     pass
