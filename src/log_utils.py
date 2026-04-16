# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import io
import os
from logging.handlers import RotatingFileHandler
from uuid import uuid4

from gi.repository import GLib  # pyright: ignore[reportAttributeAccessIssue]

from .base.debug_settings import load_debug_logging_preference
from .base.log_paths import get_log_file_path
from .base.preferences_manager import PreferencesManager
from .base.runtime_profile import default_debug_logging_enabled


_logging_configured = False
_log_buffer_handler = None
_session_id = None
_startup_header_logged = False
_exc_info_enabled = True


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
    """Adjust runtime logging verbosity based on debug mode.

    Args:
        enabled: If True, set root and file handler levels to DEBUG
                 and keep exception traces in logs.
                 If False, set levels to INFO and suppress exception traces.
    """
    global _exc_info_enabled

    target_level = logging.DEBUG if enabled else logging.INFO
    _exc_info_enabled = enabled

    root_logger = logging.getLogger()
    root_logger.setLevel(target_level)
    for handler in root_logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.setLevel(target_level)

    if enabled:
        log_preferences_snapshot("debug_enabled")


def is_debug_logging_enabled() -> bool:
    root_logger = logging.getLogger()

    for handler in root_logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            return handler.level <= logging.DEBUG

    return root_logger.getEffectiveLevel() <= logging.DEBUG


def log_preferences_snapshot(trigger: str) -> None:
    if not is_debug_logging_enabled():
        return

    prefs = PreferencesManager.get_preferences()
    if prefs is None:
        logging.debug("preferences_snapshot trigger=%s status=unavailable", trigger)
        return

    variant_name = getattr(prefs, "name", "unknown")
    general_defaults = getattr(prefs, "general_defaults", {})
    variant_defaults = getattr(prefs, "variant_defaults", {})

    logging.debug(
        "preferences_snapshot trigger=%s variant=%s general=%s variant_prefs=%s",
        trigger,
        variant_name,
        general_defaults,
        variant_defaults,
    )


def log_preference_change(scope: str, key: str, value: object) -> None:
    if not is_debug_logging_enabled():
        return

    logging.debug(
        "preference_changed scope=%s key=%s value=%s",
        scope,
        key,
        value,
    )


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
        logging.error("[%s] %s", domain, message)
    elif level & GLib.LogLevelFlags.LEVEL_WARNING:
        logging.warning("[%s] %s", domain, message)
    elif level & GLib.LogLevelFlags.LEVEL_INFO:
        logging.info("[%s] %s", domain, message)
    else:
        logging.debug("[%s] %s", domain, message)


def _glib_log_writer(log_level, fields, n_fields=None, user_data=None):
    if user_data is None and n_fields is not None and not isinstance(n_fields, int):
        user_data = n_fields
    return GLib.log_writer_default(log_level, fields, user_data)


class ExcInfoFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if _exc_info_enabled:
            return True

        record.exc_info = None
        record.exc_text = None
        return True


def _ensure_exc_info_filter(handler: logging.Handler) -> None:
    if any(isinstance(existing, ExcInfoFilter) for existing in handler.filters):
        return
    handler.addFilter(ExcInfoFilter())


def _parse_log_level(level_str: str) -> int | None:
    normalized = level_str.upper()
    if normalized == 'DEBUG':
        return logging.DEBUG
    if normalized == 'INFO':
        return logging.INFO
    if normalized == 'WARNING':
        return logging.WARNING
    if normalized == 'ERROR':
        return logging.ERROR
    return None


def _get_initial_runtime_level() -> int:
    env_level = _parse_log_level(os.environ.get('SUDOKU_LOG_LEVEL', ''))
    if env_level is not None:
        return env_level

    persisted_enabled = load_debug_logging_preference()
    if persisted_enabled is not None:
        return logging.DEBUG if persisted_enabled else logging.INFO

    return logging.DEBUG if default_debug_logging_enabled() else logging.INFO


def _get_initial_file_log_level():
    """Get the initial log level for file handler from environment or default."""
    return _get_initial_runtime_level()


def _ensure_buffer_handler(root_logger: logging.Logger) -> LogBufferHandler:
    global _log_buffer_handler

    if (
        _log_buffer_handler is not None
        and _log_buffer_handler in root_logger.handlers
        and isinstance(_log_buffer_handler, LogBufferHandler)
    ):
        _log_buffer_handler.setFormatter(logging.Formatter("%(message)s"))
        _ensure_exc_info_filter(_log_buffer_handler)
        return _log_buffer_handler

    handler = next(
        (h for h in root_logger.handlers if isinstance(h, LogBufferHandler)),
        None,
    )
    if handler is None:
        handler = LogBufferHandler()

    handler.setFormatter(logging.Formatter("%(message)s"))
    _ensure_exc_info_filter(handler)
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
        _ensure_exc_info_filter(file_handler)
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
    PreferencesManager.set_preferences_loaded_hook(log_preferences_snapshot)
    initial_level = _get_initial_runtime_level()

    if not _logging_configured:
        logging.basicConfig(level=initial_level)
        root_logger.setLevel(initial_level)

        set_debug_logging(initial_level <= logging.DEBUG)

        _ensure_buffer_handler(root_logger)
        _configure_glib_logging()

        _logging_configured = True
    else:
        set_debug_logging(initial_level <= logging.DEBUG)

    buffer_handler = _ensure_buffer_handler(root_logger)
    log_file_path = get_log_file_path()
    _ensure_file_handler(root_logger, log_file_path)
    _log_startup_header_once(version, log_file_path)
    return buffer_handler
