import os
import time

import pytest


if os.environ.get("SUDOKU_FD_TEST") != "1":
    pytest.skip("SUDOKU_FD_TEST!=1", allow_module_level=True)


if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
    pytest.skip("No display available", allow_module_level=True)


def _fd_count() -> int:
    return len(os.listdir("/proc/self/fd"))


def _drain_events(glib):
    ctx = glib.MainContext.default()
    start = time.time()
    while ctx.pending():
        ctx.iteration(False)
        if time.time() - start > 2.0:
            break


def test_fd_count_bounded_when_reusing_one_popover():
    import gi

    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk, Gdk, GLib

    win = Gtk.Window()
    grid = Gtk.Grid()
    win.set_child(grid)
    win.set_default_size(600, 600)

    buttons = []
    for i in range(81):
        b = Gtk.Button(label=str(i))
        grid.attach(b, i % 9, i // 9, 1, 1)
        buttons.append(b)

    win.present()
    _drain_events(GLib)

    popover = Gtk.Popover(position=Gtk.PositionType.BOTTOM)
    popover.set_has_arrow(False)
    popover.set_parent(grid)

    first = buttons[0]
    x0, y0 = first.translate_coordinates(grid, 0, 0)
    alloc0 = first.get_allocation()
    rect0 = Gdk.Rectangle()
    rect0.x = int(x0)
    rect0.y = int(y0)
    rect0.width = int(alloc0.width)
    rect0.height = int(alloc0.height)
    popover.set_pointing_to(rect0)
    popover.set_child(Gtk.Label(label="x"))
    popover.popup()
    _drain_events(GLib)
    baseline = _fd_count()
    popover.popdown()
    _drain_events(GLib)

    max_fds = baseline
    for b in buttons[1:]:
        x, y = b.translate_coordinates(grid, 0, 0)
        alloc = b.get_allocation()
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = int(alloc.width)
        rect.height = int(alloc.height)
        popover.set_pointing_to(rect)
        popover.popup()
        _drain_events(GLib)
        max_fds = max(max_fds, _fd_count())
        popover.popdown()
        _drain_events(GLib)

    assert (max_fds - baseline) < 200

    win.destroy()
