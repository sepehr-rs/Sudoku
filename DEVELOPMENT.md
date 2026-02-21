# Development Notes

This file captures a few project-specific pitfalls that have come up in reviews.

## GTK Popover Lifecycle (Sudoku Cells)

- Reuse a single `Gtk.Popover` instance for all cells.
- Use `popup()` / `popdown()` for visibility; avoid `show()` and `unparent()` as lifecycle mechanisms.
- Connect `"closed"` once on the shared popover.

The goal is to avoid resource growth (e.g. file descriptors) and inconsistent popover teardown.

## Keyboard Focus After Popover Close

Focus restoration is part of UX correctness for keyboard play.

- Restore focus to the originating cell on passive dismissal (click outside, Escape, Done).
- Do not force focus restoration after action buttons (number / clear), since the action already advances state.

Implementation lives in `src/variants/classic_sudoku/manager.py` via the shared popover and the
`_restore_focus_on_popover_close` / `_last_popover_cell` state.

## Tests

- Prefer behavior-based tests.
- The FD regression test is `tests/test_fd_growth_shared_popover.py` (gated behind `SUDOKU_FD_TEST=1`).
