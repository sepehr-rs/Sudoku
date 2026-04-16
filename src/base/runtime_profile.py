# runtime_profile.py
# SPDX-License-Identifier: GPL-3.0-or-later

import os


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def default_debug_logging_enabled() -> bool:
    override = _parse_bool(os.environ.get("SUDOKU_DEBUG_LOGGING_DEFAULT"))
    if override is not None:
        return override

    flatpak_id = os.environ.get("FLATPAK_ID", "")
    if flatpak_id.endswith(".Devel"):
        return True

    return False
