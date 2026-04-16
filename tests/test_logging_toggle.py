# SPDX-License-Identifier: GPL-3.0-or-later

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _module_cleanup():
    yield
    sys.modules.pop("src.log_utils", None)
    sys.modules.pop("src.base.debug_settings", None)
    sys.modules.pop("src.screens.about_dialog", None)
    sys.modules.pop("gi", None)
    sys.modules.pop("gi.repository", None)
    sys.modules.pop("gi.repository.Gtk", None)
    sys.modules.pop("gi.repository.Adw", None)


def _install_fake_gi() -> None:
    gi = ModuleType("gi")
    repository = ModuleType("gi.repository")

    Gtk = ModuleType("Gtk")
    Gtk.Align = type("Align", (), {"CENTER": 0})
    Gtk.Switch = type("Switch", (), {})

    Adw = ModuleType("Adw")
    Adw.PreferencesWindow = type("PreferencesWindow", (), {})
    Adw.PreferencesPage = type("PreferencesPage", (), {})
    Adw.PreferencesGroup = type("PreferencesGroup", (), {})
    Adw.ActionRow = type("ActionRow", (), {})

    repository.Gtk = Gtk
    repository.Adw = Adw
    gi.repository = repository

    sys.modules["gi"] = gi
    sys.modules["gi.repository"] = repository
    sys.modules["gi.repository.Gtk"] = Gtk
    sys.modules["gi.repository.Adw"] = Adw


def _install_fake_log_utils(
    mock_set_debug_logging: MagicMock,
    mock_is_debug_logging_enabled: MagicMock,
) -> None:
    fake = ModuleType("src.log_utils")
    fake.set_debug_logging = mock_set_debug_logging
    fake.is_debug_logging_enabled = mock_is_debug_logging_enabled
    sys.modules["src.log_utils"] = fake


def _install_fake_debug_settings(mock_save_preference: MagicMock) -> None:
    fake = ModuleType("src.base.debug_settings")
    fake.save_debug_logging_preference = mock_save_preference
    sys.modules["src.base.debug_settings"] = fake


def _import_about_dialog():
    sys.modules.pop("src.screens.about_dialog", None)
    return importlib.import_module("src.screens.about_dialog")


def test_debug_logging_toggle_enables_calls_save_and_set_debug_logging():
    mock_set_debug_logging = MagicMock()
    mock_is_debug_logging_enabled = MagicMock(return_value=False)
    mock_save_preference = MagicMock()

    _install_fake_gi()
    _install_fake_log_utils(mock_set_debug_logging, mock_is_debug_logging_enabled)
    _install_fake_debug_settings(mock_save_preference)

    module = _import_about_dialog()
    module.log_utils.set_debug_logging = mock_set_debug_logging
    module.log_utils.is_debug_logging_enabled = mock_is_debug_logging_enabled
    module.save_debug_logging_preference = mock_save_preference
    dialog = module.SudokuAboutDialog.__new__(module.SudokuAboutDialog)

    switch = MagicMock()
    switch.get_active.return_value = True

    dialog._on_debug_logging_toggled(switch, None)

    mock_save_preference.assert_called_once_with(True)
    mock_set_debug_logging.assert_called_once_with(True)


def test_debug_logging_toggle_disables_calls_save_and_set_debug_logging():
    mock_set_debug_logging = MagicMock()
    mock_is_debug_logging_enabled = MagicMock(return_value=True)
    mock_save_preference = MagicMock()

    _install_fake_gi()
    _install_fake_log_utils(mock_set_debug_logging, mock_is_debug_logging_enabled)
    _install_fake_debug_settings(mock_save_preference)

    module = _import_about_dialog()
    module.log_utils.set_debug_logging = mock_set_debug_logging
    module.log_utils.is_debug_logging_enabled = mock_is_debug_logging_enabled
    module.save_debug_logging_preference = mock_save_preference
    dialog = module.SudokuAboutDialog.__new__(module.SudokuAboutDialog)

    switch = MagicMock()
    switch.get_active.return_value = False

    dialog._on_debug_logging_toggled(switch, None)

    mock_save_preference.assert_called_once_with(False)
    mock_set_debug_logging.assert_called_once_with(False)


def test_debug_logging_toggle_save_failure_still_sets_runtime_logging():
    mock_set_debug_logging = MagicMock()
    mock_is_debug_logging_enabled = MagicMock(return_value=True)
    mock_save_preference = MagicMock(side_effect=OSError("disk is read-only"))

    _install_fake_gi()
    _install_fake_log_utils(mock_set_debug_logging, mock_is_debug_logging_enabled)
    _install_fake_debug_settings(mock_save_preference)

    module = _import_about_dialog()
    module.log_utils.set_debug_logging = mock_set_debug_logging
    module.log_utils.is_debug_logging_enabled = mock_is_debug_logging_enabled
    module.save_debug_logging_preference = mock_save_preference
    dialog = module.SudokuAboutDialog.__new__(module.SudokuAboutDialog)

    switch = MagicMock()
    switch.get_active.return_value = True

    dialog._on_debug_logging_toggled(switch, None)

    mock_save_preference.assert_called_once_with(True)
    mock_set_debug_logging.assert_called_once_with(True)
