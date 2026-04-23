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
import os
from logging.handlers import RotatingFileHandler
from uuid import uuid4

from gi.repository import GLib  # pyright: ignore[reportAttributeAccessIssue]

from .base.log_paths import get_log_file_path


_logging_configured = False
_log_buffer_handler = None
_session_id = None
_startup_header_logged = False


def get_session_id() -> str:
    """Get the current session UUID.

    Returns:
        str: The session UUID, generated on first access.
    """
    global _session_id
    if _session_id is None:
        _session_id = str(uuid4())
    return _session_id


def set_debug_logging(enabled: bool) -> None:
    """Adjust the file handler logging level based on debug mode.

    Args:
        enabled: If True, set file handler level to DEBUG.
                 If False, set file handler level to INFO.
    """
    root_logger = logging.getLogger()
    for handler in root_logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.setLevel(logging.DEBUG if enabled else logging.INFO)


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


def glib_log_handler(domain, level, message, _user_data):
    """Route GLib/GTK log messages into Python logging."""
    if level & (GLib.LogLevelFlags.LEVEL_ERROR | GLib.LogLevelFlags.LEVEL_CRITICAL):
        logging.error(f"[{domain}] {message}")
    elif level & GLib.LogLevelFlags.LEVEL_WARNING:
        logging.warning(f"[{domain}] {message}")
    elif level & GLib.LogLevelFlags.LEVEL_INFO:
        logging.info(f"[{domain}] {message}")
    else:
        logging.debug(f"[{domain}] {message}")


def _glib_log_writer(log_level, fields, n_fields=None, user_data=None):
    if user_data is None and n_fields is not None and not isinstance(n_fields, int):
        user_data = n_fields
    return GLib.log_writer_default(log_level, fields, user_data)


def _get_initial_file_log_level():
    """Get the initial log level for file handler from environment or default."""
    level_str = os.environ.get('SUDOKU_LOG_LEVEL', '').upper()
    if level_str == 'DEBUG':
        return logging.DEBUG
    elif level_str == 'INFO':
        return logging.INFO
    elif level_str == 'WARNING':
        return logging.WARNING
    elif level_str == 'ERROR':
        return logging.ERROR
    return logging.INFO


def _ensure_buffer_handler(root_logger: logging.Logger) -> LogBufferHandler:
    global _log_buffer_handler

    if (
        _log_buffer_handler is not None
        and _log_buffer_handler in root_logger.handlers
        and isinstance(_log_buffer_handler, LogBufferHandler)
    ):
        _log_buffer_handler.setFormatter(logging.Formatter("%(message)s"))
        return _log_buffer_handler

    handler = next(
        (h for h in root_logger.handlers if isinstance(h, LogBufferHandler)),
        None,
    )
    if handler is None:
        handler = LogBufferHandler()

    handler.setFormatter(logging.Formatter("%(message)s"))
    if handler not in root_logger.handlers:
        root_logger.addHandler(handler)

    _log_buffer_handler = handler
    return handler


def _configure_glib_logging() -> None:
    GLib.log_set_writer_func(_glib_log_writer, None)
    for domain in ("Gtk", "GLib", "Gdk", "Adwaita", None):
        GLib.log_set_handler(
            domain, GLib.LogLevelFlags.LEVEL_MASK, glib_log_handler, None
        )


def _ensure_file_handler(root_logger: logging.Logger, log_file_path: str) -> None:
    try:
        log_file_dir = os.path.dirname(log_file_path)
        if log_file_dir:
            os.makedirs(log_file_dir, exist_ok=True)

        abs_log_file_path = os.path.abspath(log_file_path)
        for handler in root_logger.handlers:
            if (
                isinstance(handler, RotatingFileHandler)
                and getattr(handler, "baseFilename", None) == abs_log_file_path
            ):
                return

        file_handler = RotatingFileHandler(
            log_file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(_get_initial_file_log_level())
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s %(levelname)s %(name)s: %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        root_logger.addHandler(file_handler)
    except Exception:
        logging.getLogger(__name__).warning(
            "Failed to set up rotating file logging; continuing with in-memory logs",
            exc_info=True,
        )


def _log_startup_header_once(version: str | None, log_file_path: str) -> None:
    global _startup_header_logged
    if _startup_header_logged:
        return

    _startup_header_logged = True
    sid = get_session_id()
    pid = os.getpid()
    ver = version if version else "unknown"
    log_file = get_log_file_path() or log_file_path
    logging.info(
        "session_start session_id=%s pid=%s version=%s log_file=%s",
        sid,
        pid,
        ver,
        log_file,
    )


def setup_logging(version: str | None = None):
    """Configure logging for the application.

    - Attach LogBufferHandler (in-memory logs).
    - Register GLib log handler for Gtk/Gdk/Adwaita/etc.
    - Redirect stderr into logging.
    """
    global _logging_configured

    root_logger = logging.getLogger()

    if not _logging_configured:
        logging.basicConfig(level=logging.DEBUG)  # Capture DEBUG+
        root_logger.setLevel(logging.DEBUG)

        _ensure_buffer_handler(root_logger)
        _configure_glib_logging()

        _logging_configured = True

    buffer_handler = _ensure_buffer_handler(root_logger)
    log_file_path = get_log_file_path()
    _ensure_file_handler(root_logger, log_file_path)
    _log_startup_header_once(version, log_file_path)
    return buffer_handler
