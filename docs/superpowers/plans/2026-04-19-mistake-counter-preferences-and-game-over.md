# Mistake Counter Preferences and Game Over Page — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a preferences toggle + customizable limit for the mistake counter, plus a Game Over page that triggers at the limit with Try Again / New Game / Main Menu actions.

**Architecture:** Extend `general_defaults` with a typed-dict preference schema that coexists with the current bool/list format. Enforcement happens in `ManagerBase._increment_mistake_count`, which calls a new `_trigger_game_over` that swaps the stack to a new `GameOverPage` (mirroring the existing `FinishedPage`). Save-file behavior is unchanged; continue flow branches to Game Over when a loaded save is already over limit.

**Tech Stack:** Python 3, GTK 4 + Libadwaita (`Adw.SpinRow`, `Adw.ActionRow`, `Gtk.Template`), Blueprint, Meson, pytest (with mocked `gi.repository`).

**Spec:** `docs/superpowers/specs/2026-04-19-mistake-counter-preferences-and-game-over-design.md`

---

## File Structure

**New:**
- `src/screens/game_over_page.py` — `GameOverPage` template class (illustration + title + subtitle + stats + buttons)
- `data/blueprints/game-over-page.blp` — blueprint for the page
- `data/illustrations/game-over-dark.svg` — user-provided (path wired now)
- `data/illustrations/game-over-light.svg` — user-provided (path wired now)
- `tests/test_preferences_schema.py` — unit tests for typed preference lookup

**Modified:**
- `src/base/preferences.py` — typed preference schema (dict format)
- `src/screens/preferences_page.py` — render `Adw.SpinRow` + `depends_on` sensitivity binding
- `src/screens/preferences_dialog.py` — keep signature; wire subtitle refresh hook via window
- `src/base/manager_base.py` — enforcement + `_trigger_game_over` + load-flow branch
- `src/variants/classic_sudoku/manager.py` — override `_cleanup_active_grid`
- `src/window.py` — register `GameOverPage`, add template child, button handlers, subtitle refresh on prefs close
- `data/blueprints/window.blp` — add `$GameOverPage game_over_page {}` stack child
- `data/blueprints/meson.build` — add `game-over-page.blp` to `blueprint_files`
- `data/sudokugame.gresource.xml.in` — register compiled UI + SVG illustrations
- `src/screens/meson.build` — add `game_over_page.py`
- `tests/test_mistake_counter.py` — add limit/trigger/continue/try-again tests

---

## Task 1: Typed preference schema — storage and lookup

**Files:**
- Modify: `src/base/preferences.py`
- Create: `tests/test_preferences_schema.py`

**Context:** Existing `general_defaults` uses bare bools and `[subtitle, bool]` lists. We need to support a structured dict format that carries type (`"bool"` or `"int"`), `default`, `min`/`max` (int only), `subtitle`, and `depends_on`. The format must coexist with existing entries — unchanged callsites for existing bools/lists.

Internal representation: at `Preferences.__init__`, convert dict-typed entries to `{"schema": <original dict>, "value": <default>}` in the instance copy. `general(key, default)` returns `value` for such entries.

**Steps:**

- [ ] **Step 1: Write failing test for typed-bool preference lookup**

Create `tests/test_preferences_schema.py`:

```python
"""Tests for typed preference schema (dict-format entries)."""

import sys
from unittest.mock import MagicMock

sys.modules["gi"] = MagicMock()
sys.modules["gi.repository"] = MagicMock()
sys.modules["gi.repository.Gtk"] = MagicMock()
sys.modules["gi.repository.Adw"] = MagicMock()
sys.modules["sudoku"] = MagicMock()
sys.modules["sudoku.base_sudoku"] = MagicMock()

import pytest  # noqa: E402

from src.base.preferences import Preferences  # noqa: E402


class _TestPrefs(Preferences):
    general_defaults = {
        "legacy_bool": True,
        "legacy_list": ["subtitle text", False],
        "typed_bool": {
            "type": "bool",
            "default": True,
            "subtitle": "Typed bool",
        },
        "typed_int": {
            "type": "int",
            "default": 3,
            "min": 1,
            "max": 99,
            "subtitle": "Typed int",
            "depends_on": "typed_bool",
        },
    }

    def __init__(self):
        super().__init__()
        self.name = "Test"


def test_typed_bool_returns_default_value():
    prefs = _TestPrefs()
    assert prefs.general("typed_bool") is True


def test_typed_int_returns_default_value():
    prefs = _TestPrefs()
    assert prefs.general("typed_int") == 3


def test_legacy_bool_unchanged():
    prefs = _TestPrefs()
    assert prefs.general("legacy_bool") is True


def test_legacy_list_unchanged():
    prefs = _TestPrefs()
    assert prefs.general("legacy_list") == ["subtitle text", False]


def test_missing_key_returns_default_argument():
    prefs = _TestPrefs()
    assert prefs.general("unknown", default="fallback") == "fallback"


def test_typed_value_is_mutable_per_instance():
    prefs_a = _TestPrefs()
    prefs_b = _TestPrefs()
    entry = prefs_a.general_defaults["typed_int"]
    entry["value"] = 7
    assert prefs_a.general("typed_int") == 7
    assert prefs_b.general("typed_int") == 3


def test_schema_metadata_preserved():
    prefs = _TestPrefs()
    entry = prefs.general_defaults["typed_int"]
    assert entry["schema"]["type"] == "int"
    assert entry["schema"]["min"] == 1
    assert entry["schema"]["max"] == 99
    assert entry["schema"]["depends_on"] == "typed_bool"
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `pytest tests/test_preferences_schema.py -v`
Expected: FAIL. Typed-dict values are returned as raw dicts, not unwrapped.

- [ ] **Step 3: Update `src/base/preferences.py` to normalize typed entries**

Replace the file contents with:

```python
# preferences.py
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

from abc import ABC
from copy import deepcopy


def _is_schema_dict(value) -> bool:
    return isinstance(value, dict) and "type" in value and "default" in value


def _normalize_entry(value):
    """Convert a schema dict to {"schema": ..., "value": default}.

    Leaves bool, list, and already-normalized entries unchanged.
    """
    if _is_schema_dict(value):
        return {"schema": deepcopy(value), "value": deepcopy(value["default"])}
    return deepcopy(value)


def _unwrap(entry):
    if isinstance(entry, dict) and "schema" in entry and "value" in entry:
        return entry["value"]
    return entry


class Preferences(ABC):
    general_defaults = {
        "casual_mode": [
            "Highlight when input does not match the correct solution",
            True,
        ],
        "prevent_conflicting_pencil_notes": False,
        "highlight_row": True,
        "highlight_column": True,
    }

    variant_defaults = {}

    def __init__(self):
        cls = type(self)
        self.general_defaults = {
            key: _normalize_entry(value) for key, value in cls.general_defaults.items()
        }
        self.variant_defaults = deepcopy(cls.variant_defaults)
        self.name = ""

    def general(self, key, default=False):
        if key not in self.general_defaults:
            return default
        return _unwrap(self.general_defaults[key])

    def variant(self, key, default=False):
        return self.variant_defaults.get(key, default)
```

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `pytest tests/test_preferences_schema.py -v`
Expected: all PASS.

- [ ] **Step 5: Run the full test suite to confirm no regressions**

Run: `pytest tests -q`
Expected: all PASS (including existing `tests/test_mistake_counter.py`).

- [ ] **Step 6: Commit**

```bash
git add src/base/preferences.py tests/test_preferences_schema.py
git commit -m "$(cat <<'EOF'
Add typed preference schema with int/bool support

Allows preference entries to be declared as dicts with type, default,
min/max, subtitle, and depends_on metadata. Existing bool and
[subtitle, bool] entries continue to work unchanged.

The normalized form stored on the instance is
{"schema": <original>, "value": <default>}; Preferences.general()
unwraps and returns the plain value.
EOF
)"
```

---

## Task 2: Add mistake counter preferences to general defaults

**Files:**
- Modify: `src/base/preferences.py:24-32`
- Modify: `tests/test_preferences_schema.py`

**Context:** With the typed schema in place, declare the two new preferences: `mistake_counter_enabled` (bool, default True) and `mistake_limit` (int 1–99, default 3, depends_on the toggle).

**Steps:**

- [ ] **Step 1: Add failing test for the new defaults in the real preference base**

Append to `tests/test_preferences_schema.py`:

```python
class _RealBasePrefs(Preferences):
    """Uses the real Preferences.general_defaults (no override)."""

    def __init__(self):
        super().__init__()
        self.name = "Real"


def test_mistake_counter_enabled_default_is_true():
    prefs = _RealBasePrefs()
    assert prefs.general("mistake_counter_enabled") is True


def test_mistake_limit_default_is_three():
    prefs = _RealBasePrefs()
    assert prefs.general("mistake_limit") == 3


def test_mistake_limit_has_bounds_metadata():
    prefs = _RealBasePrefs()
    entry = prefs.general_defaults["mistake_limit"]
    assert entry["schema"]["min"] == 1
    assert entry["schema"]["max"] == 99
    assert entry["schema"]["depends_on"] == "mistake_counter_enabled"
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `pytest tests/test_preferences_schema.py::test_mistake_counter_enabled_default_is_true tests/test_preferences_schema.py::test_mistake_limit_default_is_three tests/test_preferences_schema.py::test_mistake_limit_has_bounds_metadata -v`
Expected: FAIL. Keys not yet present.

- [ ] **Step 3: Add the two preferences to `Preferences.general_defaults`**

Edit `src/base/preferences.py`, replacing the `general_defaults` class attribute:

```python
    general_defaults = {
        "casual_mode": [
            "Highlight when input does not match the correct solution",
            True,
        ],
        "prevent_conflicting_pencil_notes": False,
        "highlight_row": True,
        "highlight_column": True,
        "mistake_counter_enabled": {
            "type": "bool",
            "default": True,
            "subtitle": "Track mistakes and end the game at the limit",
        },
        "mistake_limit": {
            "type": "int",
            "default": 3,
            "min": 1,
            "max": 99,
            "subtitle": "Maximum mistakes before Game Over",
            "depends_on": "mistake_counter_enabled",
        },
    }
```

- [ ] **Step 4: Run the full test suite**

Run: `pytest tests -q`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add src/base/preferences.py tests/test_preferences_schema.py
git commit -m "$(cat <<'EOF'
Add mistake_counter_enabled and mistake_limit preferences

mistake_counter_enabled: bool, default True. Toggles tracking,
subtitle display, and limit enforcement.

mistake_limit: int 1-99, default 3, depends_on
mistake_counter_enabled. Controls the Game Over threshold.
EOF
)"
```

---

## Task 3: Render typed preferences (Adw.SpinRow + depends_on)

**Files:**
- Modify: `src/screens/preferences_page.py`

**Context:** `GeneralPreferencesPage` currently only renders `Gtk.Switch` from bool/list entries. Add branches for typed-dict entries:
- `type == "bool"` → `Adw.SwitchRow` with subtitle
- `type == "int"` → `Adw.SpinRow` with `Gtk.Adjustment` bound to min/max
- `depends_on` → bind controlling widget's `active` → dependent row's `sensitive` (resolved after all rows exist so order doesn't matter)

Storage model: for typed entries, writes go to `entry["value"]`; for bools/lists, keep existing semantics.

GTK behavior isn't covered by the unit suite (modules are mocked); this task is verified manually and by a small logic test for the write-back paths.

**Steps:**

- [ ] **Step 1: Write a failing test for the write-back path on typed int**

Append to `tests/test_preferences_schema.py`:

```python
def test_mutating_typed_int_value_is_visible_through_general():
    prefs = _RealBasePrefs()
    prefs.general_defaults["mistake_limit"]["value"] = 5
    assert prefs.general("mistake_limit") == 5


def test_mutating_typed_bool_value_is_visible_through_general():
    prefs = _RealBasePrefs()
    prefs.general_defaults["mistake_counter_enabled"]["value"] = False
    assert prefs.general("mistake_counter_enabled") is False
```

- [ ] **Step 2: Run the tests to confirm they pass already (mutation path already works from Task 1)**

Run: `pytest tests/test_preferences_schema.py -v`
Expected: all PASS. These tests lock in the contract `GeneralPreferencesPage` will rely on.

- [ ] **Step 3: Replace `src/screens/preferences_page.py` with the extended renderer**

Full file:

```python
# screens/preferences_page.py
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

from gi.repository import Gtk, Adw, GObject


def _is_typed_entry(entry):
    return isinstance(entry, dict) and "schema" in entry and "value" in entry


class VariantPreferencesPage(Adw.PreferencesGroup):
    def __init__(self, variant_preferences, name, auto_save_function):
        super().__init__(title=name)
        self.variant_preferences = variant_preferences
        self.controls = {}
        self.auto_save_function = auto_save_function

        for key, default in self.variant_preferences.items():
            row = Adw.ActionRow(title=key.replace("_", " ").title())

            switch = Gtk.Switch(valign=Gtk.Align.CENTER)
            switch.set_active(self.variant_preferences.get(key, default))
            switch.connect("notify::active", self.on_toggle_changed, key)

            row.add_suffix(switch)
            row.set_activatable_widget(switch)

            self.add(row)
            self.controls[key] = switch

    def on_toggle_changed(self, switch, gparam, key):
        self.variant_preferences[key] = switch.get_active()
        self.auto_save_function()


class GeneralPreferencesPage(Adw.PreferencesGroup):
    def __init__(self, general_preferences, name, auto_save_function):
        super().__init__(title=name)
        self.general_preferences = general_preferences
        self.controls = {}
        self.auto_save_function = auto_save_function

        # Pass 1: create rows
        for key, value in self.general_preferences.items():
            row, control = self._build_row(key, value)
            if row is not None:
                self.add(row)
                self.controls[key] = control

        # Pass 2: wire depends_on bindings (requires controls to exist)
        for key, value in self.general_preferences.items():
            if not _is_typed_entry(value):
                continue
            depends_on = value["schema"].get("depends_on")
            if not depends_on:
                continue
            controller = self.controls.get(depends_on)
            dependent_row = self.controls.get(f"__row__{key}")
            if controller is None or dependent_row is None:
                continue
            controller.bind_property(
                "active",
                dependent_row,
                "sensitive",
                GObject.BindingFlags.SYNC_CREATE,
            )

    def _build_row(self, key, value):
        title = key.replace("_", " ").title()

        if _is_typed_entry(value):
            return self._build_typed_row(key, value, title)

        subtitle = None
        active = value
        if isinstance(value, list):
            subtitle = value[0]
            active = value[1]

        row = Adw.ActionRow(title=title)
        if subtitle:
            row.set_subtitle(subtitle)

        switch = Gtk.Switch(valign=Gtk.Align.CENTER)
        switch.set_active(active)
        switch.connect("notify::active", self._on_legacy_switch_changed, key)

        row.add_suffix(switch)
        row.set_activatable_widget(switch)

        self.controls[f"__row__{key}"] = row
        return row, switch

    def _build_typed_row(self, key, entry, title):
        schema = entry["schema"]
        subtitle = schema.get("subtitle")

        if schema["type"] == "bool":
            row = Adw.SwitchRow(title=title)
            if subtitle:
                row.set_subtitle(subtitle)
            row.set_active(bool(entry["value"]))
            row.connect("notify::active", self._on_typed_bool_changed, key)
            self.controls[f"__row__{key}"] = row
            return row, row

        if schema["type"] == "int":
            lower = int(schema.get("min", 0))
            upper = int(schema.get("max", 100))
            adjustment = Gtk.Adjustment(
                lower=lower,
                upper=upper,
                step_increment=1,
                page_increment=1,
                value=int(entry["value"]),
            )
            row = Adw.SpinRow(title=title, adjustment=adjustment, digits=0)
            if subtitle:
                row.set_subtitle(subtitle)
            row.connect("notify::value", self._on_typed_int_changed, key)
            self.controls[f"__row__{key}"] = row
            return row, row

        return None, None

    def _on_legacy_switch_changed(self, switch, gparam, key):
        value = self.general_preferences[key]
        if isinstance(value, list):
            value[1] = switch.get_active()
        else:
            self.general_preferences[key] = switch.get_active()
        self.auto_save_function()

    def _on_typed_bool_changed(self, row, gparam, key):
        self.general_preferences[key]["value"] = row.get_active()
        self.auto_save_function()

    def _on_typed_int_changed(self, row, gparam, key):
        self.general_preferences[key]["value"] = int(row.get_value())
        self.auto_save_function()
```

- [ ] **Step 4: Run the full test suite (guard against import regressions)**

Run: `pytest tests -q`
Expected: all PASS. (Preferences page is imported via mocked GTK stubs; the module should at least parse cleanly.)

- [ ] **Step 5: Build the app and manually verify the preferences UI**

Run (outside this plan, whichever build command the user normally uses, e.g. `meson compile -C builddir` + launch): open the Preferences dialog during a game.

Expected (manual check):
- "Mistake Counter Enabled" switch row with subtitle "Track mistakes..."
- "Mistake Limit" spin row 1–99 with subtitle "Maximum mistakes..."
- Toggling the switch off disables (greys out) the spin row immediately
- Toggling the switch back on re-enables the spin row
- Changing the spin value persists (close/reopen dialog, value retained)

- [ ] **Step 6: Commit**

```bash
git add src/screens/preferences_page.py
git commit -m "$(cat <<'EOF'
Render typed preferences with SpinRow and depends_on binding

GeneralPreferencesPage now recognizes typed-dict entries and renders
Adw.SwitchRow or Adw.SpinRow as appropriate. Rows declared with
depends_on have their sensitive property bound to the controlling
switch's active state, so the mistake limit greys out when the
counter toggle is off.

Existing bool and [subtitle, bool] entries continue to render as
Adw.ActionRow + Gtk.Switch and are unaffected.
EOF
)"
```

---

## Task 4: Subtitle respects counter preference; dialog-close refresh hook

**Files:**
- Modify: `src/window.py:299-328`
- Modify: `src/window.py:186-187` (`on_show_preferences`)

**Context:** `refresh_game_subtitle` currently always appends `• Mistakes: N`. Change to read `mistake_counter_enabled` from prefs and omit the mistakes piece when disabled. Also wire `on_show_preferences` so the subtitle is refreshed when the user closes the dialog (in case the toggle was flipped).

**Steps:**

- [ ] **Step 1: Write a failing test for subtitle formatting based on preference**

Append to `tests/test_mistake_counter.py`:

```python
def test_subtitle_includes_mistakes_when_counter_enabled(manager_with_board):
    from src.window import SudokuWindow
    from unittest.mock import MagicMock, PropertyMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return True
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())
    manager = manager_with_board
    manager.board.variant = "classic"
    manager.board.difficulty_label = "Easy"
    manager.board.mistake_count = 2

    window = SudokuWindow.__new__(SudokuWindow)
    window.manager = manager
    window.sudoku_window_title = MagicMock()
    window.main_menu_box = object()
    window.finished_page = object()
    window.loading_screen = object()
    window.pencil_toggle_button = MagicMock()
    window.pencil_toggle_button.get_active = MagicMock(return_value=False)
    window.stack = MagicMock()
    window.stack.get_visible_child = MagicMock(return_value=object())

    SudokuWindow.refresh_game_subtitle(window)

    args, _kwargs = window.sudoku_window_title.set_subtitle.call_args
    assert "Mistakes: 2" in args[0]


def test_subtitle_omits_mistakes_when_counter_disabled(manager_with_board):
    from src.window import SudokuWindow
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return False
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())
    manager = manager_with_board
    manager.board.variant = "classic"
    manager.board.difficulty_label = "Easy"
    manager.board.mistake_count = 2

    window = SudokuWindow.__new__(SudokuWindow)
    window.manager = manager
    window.sudoku_window_title = MagicMock()
    window.main_menu_box = object()
    window.finished_page = object()
    window.loading_screen = object()
    window.pencil_toggle_button = MagicMock()
    window.pencil_toggle_button.get_active = MagicMock(return_value=False)
    window.stack = MagicMock()
    window.stack.get_visible_child = MagicMock(return_value=object())

    SudokuWindow.refresh_game_subtitle(window)

    args, _kwargs = window.sudoku_window_title.set_subtitle.call_args
    assert "Mistakes" not in args[0]
    assert "Classic" in args[0]
    assert "Easy" in args[0]
```

- [ ] **Step 2: Run the new tests to confirm they fail**

Run: `pytest tests/test_mistake_counter.py::test_subtitle_omits_mistakes_when_counter_disabled tests/test_mistake_counter.py::test_subtitle_includes_mistakes_when_counter_enabled -v`
Expected: FAIL. Current subtitle unconditionally includes mistakes.

- [ ] **Step 3: Update `refresh_game_subtitle` in `src/window.py`**

Replace the body of `refresh_game_subtitle` (currently lines 299–328):

```python
    def refresh_game_subtitle(self):
        non_game_pages = {
            self.main_menu_box,
            self.finished_page,
            self.loading_screen,
        }
        game_over_page = getattr(self, "game_over_page", None)
        if game_over_page is not None:
            non_game_pages.add(game_over_page)

        visible = self.stack.get_visible_child()
        if (
            not self.sudoku_window_title
            or not self.manager
            or not self.manager.board
            or visible in non_game_pages
        ):
            return

        prefs = PreferencesManager.get_preferences()
        counter_enabled = (
            prefs.general("mistake_counter_enabled", default=True)
            if prefs is not None
            else True
        )
        mistake_count = getattr(self.manager.board, "mistake_count", 0)

        if self.pencil_toggle_button.get_active():
            if counter_enabled:
                self.sudoku_window_title.set_subtitle(
                    _("Pencil Mode • Mistakes: {count}").format(count=mistake_count)
                )
            else:
                self.sudoku_window_title.set_subtitle(_("Pencil Mode"))
            return

        if counter_enabled:
            self.sudoku_window_title.set_subtitle(
                _("{variant} • {difficulty} • Mistakes: {count}").format(
                    variant=self.manager.board.variant.capitalize(),
                    difficulty=self.manager.board.difficulty_label,
                    count=mistake_count,
                )
            )
        else:
            self.sudoku_window_title.set_subtitle(
                _("{variant} • {difficulty}").format(
                    variant=self.manager.board.variant.capitalize(),
                    difficulty=self.manager.board.difficulty_label,
                )
            )
```

- [ ] **Step 4: Update `on_show_preferences` to refresh the subtitle on dialog close**

Replace:

```python
    def on_show_preferences(self, *_):
        PreferencesDialog(self, self.manager.board.save_to_file).present()
```

with:

```python
    def on_show_preferences(self, *_):
        def _on_save():
            self.manager.board.save_to_file()
            self.refresh_game_subtitle()

        dialog = PreferencesDialog(self, _on_save)
        dialog.connect("close-request", self._on_preferences_closed)
        dialog.present()

    def _on_preferences_closed(self, _dialog):
        self.refresh_game_subtitle()
        return False
```

- [ ] **Step 5: Run the tests to confirm they pass**

Run: `pytest tests/test_mistake_counter.py -v`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/window.py tests/test_mistake_counter.py
git commit -m "$(cat <<'EOF'
Respect mistake_counter_enabled in game subtitle

Subtitle omits the 'Mistakes: N' suffix when the counter is disabled.
Preferences dialog close now also triggers a subtitle refresh, so
flipping the toggle updates the header bar immediately.
EOF
)"
```

---

## Task 5: ManagerBase — limit enforcement + trigger stub

**Files:**
- Modify: `src/base/manager_base.py:141-154`
- Modify: `tests/test_mistake_counter.py`

**Context:** Extend `_increment_mistake_count` so that after incrementing (existing behavior), it checks the new preferences and calls `_trigger_game_over` when `count >= limit`. `_trigger_game_over` is a new base method with a minimal default implementation: pop active popover via subclass hook, clear the grid, hide the pencil toggle, populate and show `window.game_over_page`. Subclass hook `_cleanup_active_grid` defaults to a no-op.

This task wires the logic only; `window.game_over_page` is introduced structurally in later tasks but addressed via `getattr` until then so tests don't require the template child.

**Steps:**

- [ ] **Step 1: Write failing tests for triggering behavior**

Append to `tests/test_mistake_counter.py`:

```python
def test_increment_triggers_game_over_at_limit(manager_with_board):
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return True
            if key == "mistake_limit":
                return 2
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())
    manager = manager_with_board
    manager._trigger_game_over = MagicMock()

    manager._increment_mistake_count()
    assert not manager._trigger_game_over.called

    manager._increment_mistake_count()
    assert manager._trigger_game_over.called


def test_increment_does_not_trigger_when_counter_disabled(manager_with_board):
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return False
            if key == "mistake_limit":
                return 1
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())
    manager = manager_with_board
    manager._trigger_game_over = MagicMock()

    for _ in range(5):
        manager._increment_mistake_count()

    assert not manager._trigger_game_over.called


def test_increment_does_not_trigger_below_limit(manager_with_board):
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return True
            if key == "mistake_limit":
                return 5
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())
    manager = manager_with_board
    manager._trigger_game_over = MagicMock()

    for _ in range(4):
        manager._increment_mistake_count()

    assert not manager._trigger_game_over.called
    assert manager.board.mistake_count == 4
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `pytest tests/test_mistake_counter.py::test_increment_triggers_game_over_at_limit tests/test_mistake_counter.py::test_increment_does_not_trigger_when_counter_disabled tests/test_mistake_counter.py::test_increment_does_not_trigger_below_limit -v`
Expected: FAIL (no `_trigger_game_over` path yet).

- [ ] **Step 3: Extend `ManagerBase` in `src/base/manager_base.py`**

Replace the `_increment_mistake_count` method and add `_trigger_game_over` + `_cleanup_active_grid` + `_compute_game_over_stats`:

```python
    def _increment_mistake_count(self):
        if self.board is None:
            return

        current_count = getattr(self.board, "mistake_count", 0)
        self.board.mistake_count = int(current_count) + 1

        save = getattr(self.board, "save_to_file", None)
        if callable(save):
            save()

        refresh = getattr(self.window, "refresh_game_subtitle", None)
        if callable(refresh):
            refresh()

        prefs = PreferencesManager.get_preferences()
        if prefs is None:
            return

        enabled = prefs.general("mistake_counter_enabled", default=True)
        if not enabled:
            return

        limit = int(prefs.general("mistake_limit", default=3))
        if self.board.mistake_count >= limit:
            self._trigger_game_over()

    def _cleanup_active_grid(self):
        """Variant hook for clearing popovers / feedback before tearing the grid down."""
        pass

    def _trigger_game_over(self):
        self._cleanup_active_grid()

        pencil_toggle = getattr(self.window, "pencil_toggle_button", None)
        if pencil_toggle is not None:
            pencil_toggle.set_visible(False)

        grid_container = getattr(self.window, "grid_container", None)
        if grid_container is not None:
            while child := grid_container.get_first_child():
                grid_container.remove(child)

        game_over_page = getattr(self.window, "game_over_page", None)
        if game_over_page is None:
            return

        stats = self._compute_game_over_stats()
        populate = getattr(game_over_page, "populate", None)
        if callable(populate):
            populate(**stats)

        stack = getattr(self.window, "stack", None)
        if stack is not None:
            stack.set_visible_child(game_over_page)

    def _compute_game_over_stats(self):
        board = self.board
        mistakes = int(getattr(board, "mistake_count", 0)) if board is not None else 0
        difficulty = getattr(board, "difficulty_label", "") if board is not None else ""
        percent = 0

        if board is not None:
            try:
                size = int(board.rules.size)
                total_non_clues = 0
                filled_non_clues = 0
                for r in range(size):
                    for c in range(size):
                        is_clue_fn = getattr(board, "is_clue", None)
                        if callable(is_clue_fn) and is_clue_fn(r, c):
                            continue
                        total_non_clues += 1
                        cell_value = board.user_inputs[r][c]
                        if cell_value:
                            filled_non_clues += 1
                if total_non_clues > 0:
                    percent = round(filled_non_clues / total_non_clues * 100)
            except (AttributeError, TypeError, IndexError):
                percent = 0

        return {
            "mistakes": mistakes,
            "percent": percent,
            "difficulty": difficulty,
        }
```

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `pytest tests/test_mistake_counter.py -v`
Expected: all PASS.

- [ ] **Step 5: Run the full test suite**

Run: `pytest tests -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/base/manager_base.py tests/test_mistake_counter.py
git commit -m "$(cat <<'EOF'
Enforce mistake limit from ManagerBase._increment_mistake_count

On each increment, consult the preferences. When enabled and the
count has reached the limit, call _trigger_game_over, which clears
the grid, hides the pencil toggle, populates the Game Over page
(if registered), and swaps the stack visible child.

_cleanup_active_grid is a subclass hook; ClassicSudokuManager will
override in a follow-up to pop down its popover and clear cell
feedback timeouts.

_compute_game_over_stats returns mistakes, percent complete
(filled non-clue cells), and difficulty label.
EOF
)"
```

---

## Task 6: ClassicSudokuManager — cleanup override

**Files:**
- Modify: `src/variants/classic_sudoku/manager.py:536-549` (existing `_show_puzzle_finished_dialog`)

**Context:** Add `_cleanup_active_grid` to `ClassicSudokuManager` that performs the same pre-teardown cleanup that `_show_puzzle_finished_dialog` does: pop down the active popover, clear its cached references, and clear feedback timeouts on every cell. Then refactor `_show_puzzle_finished_dialog` to reuse it (DRY).

**Steps:**

- [ ] **Step 1: Write a failing test asserting the override is callable and clears feedback**

Append to `tests/test_mistake_counter.py`:

```python
def test_classic_cleanup_active_grid_clears_feedback(manager_with_board):
    manager = manager_with_board
    manager._popdown_active_popover = lambda: setattr(manager, "_popdown_called", True)

    calls = {"cells_cleared": 0}

    class _FeedbackCell:
        def clear_feedback_timeout(self):
            calls["cells_cleared"] += 1

    manager.cell_inputs = [[_FeedbackCell() for _ in range(3)] for _ in range(3)]

    manager._cleanup_active_grid()

    assert getattr(manager, "_popdown_called", False) is True
    assert calls["cells_cleared"] == 9
    assert manager._active_popover is None
    assert manager._cell_popover is None
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `pytest tests/test_mistake_counter.py::test_classic_cleanup_active_grid_clears_feedback -v`
Expected: FAIL (method not yet overridden on Classic; base is no-op).

- [ ] **Step 3: Add the override and refactor `_show_puzzle_finished_dialog`**

In `src/variants/classic_sudoku/manager.py`, add a method (near `_show_puzzle_finished_dialog`):

```python
    def _cleanup_active_grid(self):
        self._popdown_active_popover()
        self._active_popover = None
        self._cell_popover = None

        if hasattr(self, "cell_inputs") and self.cell_inputs:
            for row in self.cell_inputs:
                for cell in row:
                    if cell:
                        cell.clear_feedback_timeout()
```

Replace `_show_puzzle_finished_dialog` with:

```python
    def _show_puzzle_finished_dialog(self):
        self._cleanup_active_grid()
        self.window.pencil_toggle_button.set_visible(False)
        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)
        self.window.stack.set_visible_child(self.window.finished_page)
```

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `pytest tests/test_mistake_counter.py -v`
Expected: all PASS.

- [ ] **Step 5: Run the full test suite**

Run: `pytest tests -q`
Expected: all PASS.

- [ ] **Step 6: Commit**

```bash
git add src/variants/classic_sudoku/manager.py tests/test_mistake_counter.py
git commit -m "$(cat <<'EOF'
Extract _cleanup_active_grid on ClassicSudokuManager

Shared by _show_puzzle_finished_dialog (existing) and the upcoming
Game Over trigger. Pops the active popover, clears cached popover
references, and clears cell feedback timeouts.
EOF
)"
```

---

## Task 7: Game Over page blueprint, gresource, meson

**Files:**
- Create: `data/blueprints/game-over-page.blp`
- Modify: `data/blueprints/meson.build:3-9`
- Modify: `data/sudokugame.gresource.xml.in`

**Context:** Add the blueprint that mirrors `finished-page.blp` but with title + subtitle + stats block + three action buttons. Register compilation in meson and the compiled UI + two illustration SVGs in the gresource. SVG files are user-provided; register the paths now so the build succeeds once they are dropped in.

**Steps:**

- [ ] **Step 1: Create `data/blueprints/game-over-page.blp`**

```blueprint
using Gtk 4.0;
using Adw 1;

template $GameOverPage: Box {
  hexpand: true;
  vexpand: true;
  margin-bottom: 30;

  Box {
    orientation: vertical;
    spacing: 12;
    margin-bottom: 20;
    halign: fill;
    valign: center;
    hexpand: true;
    vexpand: true;

    Adw.Clamp {
      maximum-size: 1200;
      tightening-threshold: 300;

      Box {
        orientation: vertical;
        spacing: 18;

        Picture picture_contain {
          halign: center;
          valign: fill;
          hexpand: true;
          vexpand: true;
          margin-bottom: 20;
          can-shrink: true;
          content-fit: contain;
        }

        Label title_label {
          wrap: true;
          justify: center;
          styles [ "title-1" ]
        }

        Label subtitle_label {
          wrap: true;
          justify: center;
          styles [ "dim-label" ]
        }

        Box stats_box {
          orientation: horizontal;
          spacing: 24;
          halign: center;
          margin-top: 12;

          Box {
            orientation: vertical;
            spacing: 2;

            Label stats_mistakes_value {
              justify: center;
              styles [ "title-2" ]
            }

            Label stats_mistakes_label {
              justify: center;
              styles [ "caption", "dim-label" ]
            }
          }

          Box {
            orientation: vertical;
            spacing: 2;

            Label stats_progress_value {
              justify: center;
              styles [ "title-2" ]
            }

            Label stats_progress_label {
              justify: center;
              styles [ "caption", "dim-label" ]
            }
          }

          Box {
            orientation: vertical;
            spacing: 2;

            Label stats_difficulty_value {
              justify: center;
              styles [ "title-2" ]
            }

            Label stats_difficulty_label {
              justify: center;
              styles [ "caption", "dim-label" ]
            }
          }
        }

        Box actions_box {
          orientation: horizontal;
          spacing: 12;
          halign: center;
          margin-top: 18;

          Button try_again_button {
            label: _("Try Again");
            styles [ "suggested-action", "pill" ]
          }

          Button new_game_button {
            label: _("New Game");
            styles [ "pill" ]
          }

          Button main_menu_button {
            label: _("Main Menu");
            styles [ "pill" ]
          }
        }
      }
    }
  }
}
```

- [ ] **Step 2: Register the blueprint in `data/blueprints/meson.build`**

Replace the `blueprint_files = files(...)` block with:

```meson
blueprint_files = files(
  'window.blp',
  'shortcuts-overlay.blp',
  'finished-page.blp',
  'game-over-page.blp',
  'how-to-play-dialog.blp',
  'loading-screen.blp'
)
```

- [ ] **Step 3: Register the compiled UI + illustrations in `data/sudokugame.gresource.xml.in`**

Replace the file contents with:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<gresources>
  <gresource prefix="/io/github/sepehr_rs/Sudoku">
    <file alias="style.css">style.css</file>
    <file alias="style-dark.css">style-dark.css</file>
    <file preprocess="xml-stripblanks">blueprints/window.ui</file>
    <file preprocess="xml-stripblanks">blueprints/shortcuts-overlay.ui</file>
    <file preprocess="xml-stripblanks">blueprints/finished-page.ui</file>
    <file preprocess="xml-stripblanks">blueprints/game-over-page.ui</file>
    <file preprocess="xml-stripblanks">blueprints/loading-screen.ui</file>
    <file preprocess="xml-stripblanks">blueprints/how-to-play-dialog.ui</file>
  </gresource>

  <gresource prefix="/io/github/sepehr_rs/Sudoku">
    <file preprocess="xml-stripblanks">icons/scalable/actions/back-symbolic.svg</file>
  </gresource>


  <gresource prefix="/io/github/sepehr_rs/Sudoku/illustrations">
    <file preprocess="xml-stripblanks" alias="puzzle-complete-celebration-dark.svg">illustrations/puzzle-complete-celebration-dark.svg</file>
    <file preprocess="xml-stripblanks" alias="puzzle-complete-celebration-light.svg">illustrations/puzzle-complete-celebration-light.svg</file>
    <file preprocess="xml-stripblanks" alias="game-over-dark.svg">illustrations/game-over-dark.svg</file>
    <file preprocess="xml-stripblanks" alias="game-over-light.svg">illustrations/game-over-light.svg</file>
    <file preprocess="xml-stripblanks" alias="basics.svg">illustrations/basics.svg</file>
    <file preprocess="xml-stripblanks" alias="rows-and-columns.svg">illustrations/rows-and-columns.svg</file>
    <file preprocess="xml-stripblanks" alias="blocks.svg">illustrations/blocks.svg</file>
    <file preprocess="xml-stripblanks" alias="mistake.svg">illustrations/mistake.svg</file>
    <file preprocess="xml-stripblanks" alias="pencil-mode.svg">illustrations/pencil-mode.svg</file>
    <file preprocess="xml-stripblanks" alias="casual.svg">illustrations/casual.svg</file>
  </gresource>

</gresources>
```

- [ ] **Step 4: Drop placeholder SVGs so the build succeeds before user-provided art arrives**

Create `data/illustrations/game-over-dark.svg` and `data/illustrations/game-over-light.svg` with minimal placeholder content (a user-provided asset will replace these before merge):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 128 128" width="128" height="128">
  <rect width="128" height="128" fill="none"/>
  <circle cx="64" cy="64" r="48" fill="currentColor" fill-opacity="0.12" stroke="currentColor" stroke-width="2"/>
  <path d="M 44 44 L 84 84 M 84 44 L 44 84" stroke="currentColor" stroke-width="6" stroke-linecap="round"/>
</svg>
```

Use the same content for both dark and light placeholders (dark/light differentiation is user-supplied art).

- [ ] **Step 5: Verify build still works (manual)**

Run (whatever the user's normal build is, e.g.): `meson compile -C builddir`
Expected: compiles cleanly; `blueprints/game-over-page.ui` is produced; gresource includes it.

- [ ] **Step 6: Run the full test suite (should be unaffected)**

Run: `pytest tests -q`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add data/blueprints/game-over-page.blp data/blueprints/meson.build data/sudokugame.gresource.xml.in data/illustrations/game-over-dark.svg data/illustrations/game-over-light.svg
git commit -m "$(cat <<'EOF'
Add Game Over page blueprint, resources, and placeholder art

Blueprint mirrors finished-page layout: illustration, title,
subtitle, three-column stats block, and Try Again / New Game /
Main Menu action buttons. Placeholder SVGs are committed so the
build passes; they will be replaced with user-provided art before
merge.
EOF
)"
```

---

## Task 8: Game Over page Python class

**Files:**
- Create: `src/screens/game_over_page.py`
- Modify: `src/screens/meson.build:3-11`

**Context:** Template class that loads `blueprints/game-over-page.ui`, handles dark/light illustration swapping (same pattern as `FinishedPage`), and exposes a `populate(mistakes, percent, difficulty)` method. Buttons are exposed as template children; `SudokuWindow` will connect signals in the next task.

**Steps:**

- [ ] **Step 1: Write failing test for `populate`**

Append to `tests/test_mistake_counter.py`:

```python
def test_game_over_page_populate_sets_stats():
    from src.screens.game_over_page import GameOverPage
    from unittest.mock import MagicMock

    page = GameOverPage.__new__(GameOverPage)
    page.subtitle_label = MagicMock()
    page.stats_mistakes_value = MagicMock()
    page.stats_progress_value = MagicMock()
    page.stats_difficulty_value = MagicMock()

    page.populate(mistakes=3, percent=47, difficulty="Medium")

    page.subtitle_label.set_label.assert_called_once()
    subtitle_arg = page.subtitle_label.set_label.call_args[0][0]
    assert "3" in subtitle_arg

    page.stats_mistakes_value.set_label.assert_called_once_with("3")
    page.stats_progress_value.set_label.assert_called_once_with("47%")
    page.stats_difficulty_value.set_label.assert_called_once_with("Medium")
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `pytest tests/test_mistake_counter.py::test_game_over_page_populate_sets_stats -v`
Expected: FAIL (module not found).

- [ ] **Step 3: Create `src/screens/game_over_page.py`**

```python
# game_over_page.py
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

from gi.repository import Gtk, Adw
from gettext import gettext as _


@Gtk.Template(resource_path="/io/github/sepehr_rs/Sudoku/blueprints/game-over-page.ui")
class GameOverPage(Gtk.Box):
    __gtype_name__ = "GameOverPage"

    dark_picture = (
        "/io/github/sepehr_rs/Sudoku/illustrations/game-over-dark.svg"
    )
    light_picture = (
        "/io/github/sepehr_rs/Sudoku/illustrations/game-over-light.svg"
    )

    picture_contain = Gtk.Template.Child()
    title_label = Gtk.Template.Child()
    subtitle_label = Gtk.Template.Child()
    stats_mistakes_value = Gtk.Template.Child()
    stats_mistakes_label = Gtk.Template.Child()
    stats_progress_value = Gtk.Template.Child()
    stats_progress_label = Gtk.Template.Child()
    stats_difficulty_value = Gtk.Template.Child()
    stats_difficulty_label = Gtk.Template.Child()
    try_again_button = Gtk.Template.Child()
    new_game_button = Gtk.Template.Child()
    main_menu_button = Gtk.Template.Child()

    def __init__(self):
        super().__init__()
        self._style_manager = Adw.StyleManager.get_default()
        self._style_manager.connect("notify::dark", self._update_picture)
        self.connect("map", self._on_map)

        self.title_label.set_label(_("Game Over"))
        self.stats_mistakes_label.set_label(_("Mistakes"))
        self.stats_progress_label.set_label(_("Complete"))
        self.stats_difficulty_label.set_label(_("Difficulty"))

    def populate(self, mistakes: int, percent: int, difficulty: str):
        self.subtitle_label.set_label(
            _("You reached {count} mistakes").format(count=mistakes)
        )
        self.stats_mistakes_value.set_label(str(mistakes))
        self.stats_progress_value.set_label(f"{percent}%")
        self.stats_difficulty_value.set_label(difficulty)

    def _on_map(self, _widget):
        self._update_picture()

    def _update_picture(self, *args):
        if self._style_manager.get_dark():
            self.picture_contain.set_resource(self.dark_picture)
        else:
            self.picture_contain.set_resource(self.light_picture)
```

- [ ] **Step 4: Register in `src/screens/meson.build`**

Replace the `services_sources` list with:

```meson
services_sources = [
    'finished_page.py',
    'game_over_page.py',
    'help_dialog.py',
    'shortcuts_overlay.py',
    'loading_screen.py',
    'preferences_dialog.py',
    'preferences_page.py',
    'game_setup_dialog.py'
]
```

- [ ] **Step 5: Run the test to confirm it passes**

Run: `pytest tests/test_mistake_counter.py::test_game_over_page_populate_sets_stats -v`
Expected: PASS.

- [ ] **Step 6: Run the full test suite**

Run: `pytest tests -q`
Expected: all PASS.

- [ ] **Step 7: Commit**

```bash
git add src/screens/game_over_page.py src/screens/meson.build
git commit -m "$(cat <<'EOF'
Add GameOverPage template class

Mirrors FinishedPage pattern with dark/light illustration swapping.
populate(mistakes, percent, difficulty) sets the subtitle and three
stat labels. Buttons are exposed as template children for
SudokuWindow to wire signals.
EOF
)"
```

---

## Task 9: Window integration — stack child, template registration, button handlers

**Files:**
- Modify: `data/blueprints/window.blp:106-109`
- Modify: `src/window.py` (imports, `_TEMPLATE_WIDGET_TYPES`, template child, `on_stack_page_changed`, `__init__` wiring)

**Context:** Add `game_over_page` to the window's stack and connect all three action buttons in `__init__`. `on_stack_page_changed` must treat `game_over_page` as a non-game page (hides pencil toggle, disables preferences menu, hides hamburger, shows back arrow). `on_try_again` resets the board state and rebuilds the grid; "New Game" reuses `on_new_game_clicked`; "Main Menu" reuses `on_back_to_menu`.

**Steps:**

- [ ] **Step 1: Write failing test for `on_try_again` behavior**

Append to `tests/test_mistake_counter.py`:

```python
def test_on_try_again_resets_count_inputs_and_notes(manager_with_board):
    from src.window import SudokuWindow
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return True
            if key == "mistake_limit":
                return 3
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())

    manager = manager_with_board
    manager.board.mistake_count = 3
    for r in range(9):
        for c in range(9):
            manager.board.user_inputs[r][c] = "5"
            manager.board.notes[r][c] = {"1", "2"}
    manager.board.is_clue = MagicMock(return_value=False)
    manager.build_grid = MagicMock()
    manager._restore_game_state = MagicMock()

    window = SudokuWindow.__new__(SudokuWindow)
    window.manager = manager
    window.stack = MagicMock()
    window.pencil_toggle_button = MagicMock()
    window.pencil_toggle_button.get_active = MagicMock(return_value=False)
    window.sudoku_window_title = MagicMock()
    window.main_menu_box = object()
    window.finished_page = object()
    window.loading_screen = object()
    window.game_scrolled_window = object()
    window.game_over_page = object()

    SudokuWindow.on_try_again(window, None)

    assert manager.board.mistake_count == 0
    for r in range(9):
        for c in range(9):
            assert manager.board.user_inputs[r][c] is None
            assert manager.board.notes[r][c] == set()
    manager.board.save_to_file.assert_called()
    manager.build_grid.assert_called()
    window.stack.set_visible_child.assert_called_with(window.game_scrolled_window)
```

- [ ] **Step 2: Run the test to confirm it fails**

Run: `pytest tests/test_mistake_counter.py::test_on_try_again_resets_count_inputs_and_notes -v`
Expected: FAIL (`on_try_again` not defined on `SudokuWindow`).

- [ ] **Step 3: Update `data/blueprints/window.blp` — add the stack child**

Replace lines 105–108 (inside the `Stack stack { ... }` block, after `$FinishedPage finished_page {}` and `$LoadingScreen loading_screen {}`):

```blueprint
        $FinishedPage finished_page {}

        $GameOverPage game_over_page {}

        $LoadingScreen loading_screen {}
```

- [ ] **Step 4: Update `src/window.py` — imports, template widgets, template child, handlers**

Import the class — replace the existing import line:

```python
from .screens.finished_page import FinishedPage  # noqa: F401
from .screens.loading_screen import LoadingScreen  # noqa: F401
```

with:

```python
from .screens.finished_page import FinishedPage  # noqa: F401
from .screens.game_over_page import GameOverPage  # noqa: F401
from .screens.loading_screen import LoadingScreen  # noqa: F401
```

Update `_TEMPLATE_WIDGET_TYPES`:

```python
_TEMPLATE_WIDGET_TYPES = (FinishedPage, GameOverPage, LoadingScreen)
```

Add the template child after the existing `finished_page` child (around line 47):

```python
    finished_page = Gtk.Template.Child()
    game_over_page = Gtk.Template.Child()
    loading_screen = Gtk.Template.Child()
```

In `SudokuWindow.__init__`, after `self._build_primary_menu(show_preferences=False)` (line 76), add:

```python
        self._wire_game_over_buttons()
```

And define the helper + three handlers anywhere in the class (suggested: after `_build_primary_menu`):

```python
    def _wire_game_over_buttons(self):
        self.game_over_page.try_again_button.connect("clicked", self.on_try_again)
        self.game_over_page.new_game_button.connect("clicked", self.on_new_game_clicked)
        self.game_over_page.main_menu_button.connect("clicked", self.on_back_to_menu)

    def on_try_again(self, _button):
        if not self.manager or not self.manager.board:
            return
        board = self.manager.board

        board.mistake_count = 0
        try:
            size = int(board.rules.size)
        except AttributeError:
            size = len(board.user_inputs)

        for r in range(size):
            for c in range(size):
                board.user_inputs[r][c] = None
                board.notes[r][c] = set()

        save = getattr(board, "save_to_file", None)
        if callable(save):
            save()

        build = getattr(self.manager, "build_grid", None)
        if callable(build):
            build()

        restore = getattr(self.manager, "_restore_game_state", None)
        if callable(restore):
            restore()

        self.stack.set_visible_child(self.game_scrolled_window)
        self.pencil_toggle_button.set_visible(True)
        self.refresh_game_subtitle()
```

Update `on_stack_page_changed` — change the two `in (..., self.finished_page)` tuples to also include `self.game_over_page`:

```python
        if visible in (
            self.main_menu_box,
            self.loading_screen,
            self.finished_page,
            self.game_over_page,
        ):
            self._force_disable_pencil_mode()
            self.sudoku_window_title.set_subtitle("")

        is_game_page = visible not in (
            self.main_menu_box,
            self.loading_screen,
            self.finished_page,
            self.game_over_page,
        )
        is_menu_or_loading = visible in (self.main_menu_box, self.loading_screen)
```

(Leave the rest of `on_stack_page_changed` as-is.)

- [ ] **Step 5: Run the test to confirm it passes**

Run: `pytest tests/test_mistake_counter.py::test_on_try_again_resets_count_inputs_and_notes -v`
Expected: PASS.

- [ ] **Step 6: Run the full test suite**

Run: `pytest tests -q`
Expected: all PASS.

- [ ] **Step 7: Manual verification (build + run)**

Build the app, open a game, intentionally make enough mistakes to hit the default limit (3). Expected (manual):
- Game Over page displays with the three stats
- Try Again returns to a fresh grid of the same puzzle; mistakes reset to 0
- New Game opens the Game Setup dialog
- Main Menu returns to the main screen; pencil toggle hidden on Game Over
- Back arrow in header still works on Game Over page

- [ ] **Step 8: Commit**

```bash
git add data/blueprints/window.blp src/window.py tests/test_mistake_counter.py
git commit -m "$(cat <<'EOF'
Wire Game Over page into the window stack

Adds $GameOverPage to window.blp, registers it in the window template,
and connects Try Again / New Game / Main Menu buttons.

on_try_again: zeroes mistake_count, clears user_inputs and notes,
saves the board, rebuilds the grid, and returns to the game view.

on_stack_page_changed now treats the Game Over page as a non-game
page (hides pencil toggle, disables preferences, shows back arrow).
EOF
)"
```

---

## Task 10: Continue flow — branch to Game Over on loaded save over limit

**Files:**
- Modify: `src/base/manager_base.py:36-53`
- Modify: `tests/test_mistake_counter.py`

**Context:** When a user taps Continue and the save's `mistake_count` is already at or above the current limit, skip the normal game view and show the Game Over page directly. This honors the choice that save files persist through Game Over (save state X from the spec).

**Steps:**

- [ ] **Step 1: Write failing test for continue flow**

Append to `tests/test_mistake_counter.py`:

```python
def test_load_saved_game_shows_game_over_when_over_limit(manager_with_board):
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return True
            if key == "mistake_limit":
                return 3
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())

    manager = manager_with_board
    manager.board.mistake_count = 3
    manager.board.is_solved = MagicMock(return_value=False)
    manager.board_cls = MagicMock()
    manager.board_cls.load_from_file = MagicMock(return_value=manager.board)
    manager.build_grid = MagicMock()
    manager._restore_game_state = MagicMock()
    manager._trigger_game_over = MagicMock()

    manager.window.refresh_game_subtitle = MagicMock()
    manager.window.sudoku_window_title = MagicMock()
    manager.window.stack = MagicMock()
    manager.window.game_scrolled_window = object()

    manager.load_saved_game()

    assert manager._trigger_game_over.called
    # Stack should not have been set to the normal game view
    calls = manager.window.stack.set_visible_child.call_args_list
    for call in calls:
        assert call.args[0] is not manager.window.game_scrolled_window


def test_load_saved_game_shows_normal_view_when_under_limit(manager_with_board):
    from unittest.mock import MagicMock

    class _Prefs:
        def general(self, key, default=False):
            if key == "mistake_counter_enabled":
                return True
            if key == "mistake_limit":
                return 3
            if key == "casual_mode":
                return ["desc", True]
            return default

    PreferencesManager.set_preferences(_Prefs())

    manager = manager_with_board
    manager.board.mistake_count = 1
    manager.board.is_solved = MagicMock(return_value=False)
    manager.board_cls = MagicMock()
    manager.board_cls.load_from_file = MagicMock(return_value=manager.board)
    manager.build_grid = MagicMock()
    manager._restore_game_state = MagicMock()
    manager._trigger_game_over = MagicMock()

    manager.window.refresh_game_subtitle = MagicMock()
    manager.window.sudoku_window_title = MagicMock()
    manager.window.stack = MagicMock()
    manager.window.game_scrolled_window = object()

    manager.load_saved_game()

    assert not manager._trigger_game_over.called
    manager.window.stack.set_visible_child.assert_called_with(
        manager.window.game_scrolled_window
    )
```

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `pytest tests/test_mistake_counter.py::test_load_saved_game_shows_game_over_when_over_limit tests/test_mistake_counter.py::test_load_saved_game_shows_normal_view_when_under_limit -v`
Expected: FAIL. Current `load_saved_game` always shows `game_scrolled_window`.

- [ ] **Step 3: Update `ManagerBase.load_saved_game` in `src/base/manager_base.py`**

Replace the method body:

```python
    def load_saved_game(self):
        self.board = self.board_cls.load_from_file()
        if self.board is None:
            logging.error("No saved game found")
            return

        refresh = getattr(self.window, "refresh_game_subtitle", None)
        if callable(refresh):
            refresh()
        else:
            self.window.sudoku_window_title.set_subtitle(
                f"{self.board.variant.capitalize()} • {self.board.difficulty_label}"
            )

        self.build_grid()
        self._restore_game_state()

        if self.board.is_solved():
            self._show_puzzle_finished_dialog()
            logging.info(f"Loaded completed {self.board.variant.capitalize()} Sudoku game")
            return

        prefs = PreferencesManager.get_preferences()
        if prefs is not None:
            enabled = prefs.general("mistake_counter_enabled", default=True)
            if enabled:
                limit = int(prefs.general("mistake_limit", default=3))
                if int(getattr(self.board, "mistake_count", 0)) >= limit:
                    self._trigger_game_over()
                    logging.info(
                        f"Loaded {self.board.variant.capitalize()} Sudoku game in "
                        "Game Over state"
                    )
                    return

        self.window.stack.set_visible_child(self.window.game_scrolled_window)
        logging.info(f"Loaded saved {self.board.variant.capitalize()} Sudoku game")
```

- [ ] **Step 4: Run the tests to confirm they pass**

Run: `pytest tests/test_mistake_counter.py -v`
Expected: all PASS.

- [ ] **Step 5: Run the full test suite**

Run: `pytest tests -q`
Expected: all PASS.

- [ ] **Step 6: Manual verification**

1. Start a game, make 3 mistakes → Game Over page.
2. Click Main Menu → Continue button visible.
3. Click Continue → Game Over page shown directly (not the grid).
4. Click Try Again → returns to fresh grid of same puzzle, count 0.

- [ ] **Step 7: Commit**

```bash
git add src/base/manager_base.py tests/test_mistake_counter.py
git commit -m "$(cat <<'EOF'
Branch Continue flow to Game Over when loaded save is over limit

After load_from_file, if counter is enabled and mistake_count >= limit,
trigger the Game Over page directly. Solved puzzles still take the
finished-dialog path as before.
EOF
)"
```

---

## Task 11: Final integration checks

**Files:** None directly.

**Context:** Final lint, type-check, and full test-suite pass. Verify the feature end-to-end against each success criterion from the spec.

**Steps:**

- [ ] **Step 1: Run the full test suite**

Run: `pytest tests -q`
Expected: all PASS.

- [ ] **Step 2: Run lint** (use whichever linter the project uses — infer from `meson.build` / CI; if unsure, ask the user)

Expected: clean.

- [ ] **Step 3: Run type-check if present**

Expected: clean. (Pyright is mentioned in earlier commits; run if configured.)

- [ ] **Step 4: Build the app**

Run (user's normal build command, e.g.): `meson compile -C builddir`
Expected: clean.

- [ ] **Step 5: End-to-end manual verification against spec success criteria**

Walk each bullet from the spec's Success Criteria section:
- Fresh install (remove `saves/board.json`): start game, hit 3 mistakes → Game Over
- Open Preferences, toggle "Mistake Counter Enabled" off → subtitle no longer shows mistakes; limit row greyed out
- Toggle back on → subtitle shows mistakes; limit row editable
- Change limit to 5, make 4 mistakes: no Game Over; 5th: Game Over
- On Game Over: Try Again → same puzzle, fresh; New Game → setup dialog; Main Menu → menu; Continue button re-opens Game Over

- [ ] **Step 6: Confirm placeholder SVGs are committed and note to user**

After merge the user provides real `game-over-dark.svg` / `game-over-light.svg` to drop in at `data/illustrations/`. No code change required.

- [ ] **Step 7: No commit for this task unless lint/type-check fixes are needed.**

---

## Self-Review Checklist (completed)

**Spec coverage:**
- Preference toggle → Tasks 1–3
- Customizable limit → Tasks 1–3
- Limit enforcement → Task 5
- Game Over page (blueprint + class) → Tasks 7–8
- Try Again / New Game / Main Menu actions → Task 9
- Subtitle respects toggle → Task 4
- Save persistence + Continue routing → Task 10
- Classic manager cleanup override → Task 6
- Integration + manual verification → Task 11

All success criteria map to tasks; no gaps.

**Placeholder scan:** none — every code step contains full content, all tests include assertions, all commands include expected output.

**Type consistency:** `_increment_mistake_count`, `_trigger_game_over`, `_cleanup_active_grid`, `_compute_game_over_stats`, `populate(mistakes, percent, difficulty)`, `on_try_again(self, _button)`, `game_over_page` (both `Gtk.Template.Child` name and attribute lookups), illustration paths — all consistent across tasks.
