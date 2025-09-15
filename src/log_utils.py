# log_utils.py
#
# Copyright 2025 sepehr-rs
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import io
import sys
from gi.repository import GLib


class LogBufferHandler(logging.Handler):
    """Custom logging handler that stores logs in memory."""

    def __init__(self):
        super().__init__()
        self.log_stream = io.StringIO()

    def emit(self, record):
        msg = self.format(record)
        self.log_stream.write(msg + "\n")

    def get_logs(self):
        return self.log_stream.getvalue()


def glib_log_handler(domain, level, message, user_data):
    """Route GLib/GTK log messages into Python logging."""
    if level & (GLib.LogLevelFlags.LEVEL_ERROR | GLib.LogLevelFlags.LEVEL_CRITICAL):
        logging.error(f"[{domain}] {message}")
    elif level & GLib.LogLevelFlags.LEVEL_WARNING:
        logging.warning(f"[{domain}] {message}")
    elif level & GLib.LogLevelFlags.LEVEL_INFO:
        logging.info(f"[{domain}] {message}")
    else:
        logging.debug(f"[{domain}] {message}")


class StderrLogger:
    """Redirect stderr output into logging (DEBUG level)."""

    def write(self, msg):
        if msg.strip():
            logging.debug(f"[stderr] {msg.strip()}")

    def flush(self):  # Needed for compatibility
        pass


def setup_logging():
    """Configure logging for the application.

    - Attach LogBufferHandler (in-memory logs).
    - Register GLib log handler for Gtk/Gdk/Adwaita/etc.
    - Redirect stderr into logging.
    """
    log_handler = LogBufferHandler()
    logging.basicConfig(level=logging.DEBUG)  # Capture DEBUG+
    root_logger = logging.getLogger()
    root_logger.addHandler(log_handler)

    for domain in ("Gtk", "GLib", "Gdk", "Adwaita", None):
        GLib.log_set_handler(
            domain, GLib.LogLevelFlags.LEVEL_MASK, glib_log_handler, None
        )

    sys.stderr = StderrLogger()

    return log_handler
