# Mistake Counter Preferences and Game Over Page

**Status:** Draft
**Date:** 2026-04-19
**Branch:** `frank/issue-36-mistake-counter`
**Related:** Issue #36, PR implementing mistake counter functionality

## Goal

Extend the existing mistake counter feature with:

1. A preference to enable or disable the mistake counter feature as a whole.
2. A customizable mistake limit (1–99).
3. A dedicated Game Over page shown when the limit is reached, with options to
   retry the current puzzle, start a new game, or return to the main menu.

## Non-Goals

- Migrating existing bool/list preferences into the new typed preference schema.
- Hints, undo, pause, or any other features tied to the mistake limit.
- Telemetry or statistics history beyond the single Game Over screen.
- Game Over animation or sound effects.
- Localization work beyond wrapping new user-facing strings in `_()`.
- Confirmation dialogs on "Try Again" or "New Game".

## Success Criteria

- Fresh install: counter enabled with limit 3; Game Over triggers on the third mistake.
- Toggling the counter preference off hides the subtitle counter, disables tracking,
  and prevents Game Over from triggering.
- The limit spin row is visibly disabled when the counter toggle is off.
- "Try Again" returns to the same puzzle with `mistake_count = 0` and all user
  inputs cleared; clues remain.
- "Main Menu" after Game Over: the Continue button re-opens the Game Over screen
  (save file persists mistake count).
- Existing tests still pass; new tests described below pass.
- Lint and type-check remain clean.

## Architecture Overview

Five touchpoints, one new page module.

```
Preferences (src/base/preferences.py)
  └── general_defaults gains mistake_counter_enabled + mistake_limit
       using a new typed-dict format, coexisting with existing bool/list entries

PreferencesPage (src/screens/preferences_page.py)
  └── Detect dict-typed values; render Adw.SpinRow for int, Gtk.Switch for bool.
  └── Honor depends_on: bind controlling switch's active state to dependent
      row's sensitive state.

ManagerBase (src/base/manager_base.py)
  └── _increment_mistake_count now reads prefs; if enabled and
      count >= limit, calls _trigger_game_over.
  └── _trigger_game_over (new) cleans up grid UI and navigates the stack.

SudokuWindow (src/window.py)
  └── refresh_game_subtitle omits "Mistakes: N" when counter disabled.
  └── New stack child game_over_page.
  └── Continue flow branches to Game Over when loaded save is over limit.
  └── Handlers on_try_again, on_new_game, on_back_to_menu wired to buttons.

GameOverPage (src/screens/game_over_page.py + data/blueprints/game-over-page.blp)
  └── Mirrors FinishedPage pattern: illustration, title, subtitle, stats,
      three action buttons.
```

## Preferences Schema

`src/base/preferences.py` extends `general_defaults`:

```python
general_defaults = {
    "casual_mode": ["Highlight when input does not match...", True],
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

### Storage

Existing bool and `[subtitle, bool]` entries remain unchanged. New dict-typed
entries are converted at `Preferences.__init__` time into an internal
representation that holds both the immutable schema and the current value.

Option (chosen): rewrite each dict entry in the instance copy as
`{"schema": <original dict>, "value": <default>}` so lookups and mutations
stay uniform. `general(key, default)` returns `entry["value"]` when the entry
is this structured dict; otherwise falls back to existing behavior.

### Rendering

`GeneralPreferencesPage` detects the value type per key:

- `bool` → `Adw.ActionRow` + `Gtk.Switch` (existing path).
- `list` with `[subtitle, bool]` → same, with subtitle (existing path).
- Structured dict with `schema.type == "bool"` → `Adw.SwitchRow` with subtitle.
- Structured dict with `schema.type == "int"` → `Adw.SpinRow` with
  `adjustment = Gtk.Adjustment(lower=min, upper=max, step_increment=1,
  page_increment=1)`.

`depends_on` binding: when both rows are created, bind the depending row's
`sensitive` property to the controlling widget's `active` property
(using `GObject.Binding` or a `notify::active` signal handler). The controlling
row need not come first in the dict; resolve bindings after all rows are
instantiated.

### Callsite semantics

`prefs.general("mistake_counter_enabled", default=True)` returns a plain bool.
`prefs.general("mistake_limit", default=3)` returns a plain int. Existing
callsites are unaffected.

## Mistake Limit Enforcement

`ManagerBase._increment_mistake_count` (existing method, extended):

```python
def _increment_mistake_count(self):
    if self.board is None:
        return

    self.board.mistake_count = int(getattr(self.board, "mistake_count", 0)) + 1
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
    limit = prefs.general("mistake_limit", default=3)
    if self.board.mistake_count >= int(limit):
        self._trigger_game_over()
```

`ManagerBase._trigger_game_over` (new; base implementation):

```python
def _trigger_game_over(self):
    self._cleanup_active_grid()  # variants override for popover cleanup
    self.window.pencil_toggle_button.set_visible(False)

    while child := self.window.grid_container.get_first_child():
        self.window.grid_container.remove(child)

    stats = self._compute_game_over_stats()
    self.window.game_over_page.populate(**stats)
    self.window.stack.set_visible_child(self.window.game_over_page)
```

`_cleanup_active_grid` is a no-op on `ManagerBase`; `ClassicSudokuManager`
overrides to pop down the active popover and clear cell feedback timeouts,
matching the existing `_show_puzzle_finished_dialog` cleanup.

`_compute_game_over_stats` returns:

```python
{
    "mistakes": int(self.board.mistake_count),
    "percent": <0..100 int>,
    "difficulty": self.board.difficulty_label,
}
```

`percent` is computed as `filled_non_clue_cells / total_non_clue_cells * 100`,
rounded to the nearest int, with `total_non_clue_cells == 0` yielding 0.

## Subtitle Behavior

`SudokuWindow.refresh_game_subtitle` consults prefs:

- If `mistake_counter_enabled` is false: subtitle uses the pre-counter format,
  e.g. `"Classic • Easy"` or `"Pencil Mode"`.
- If true: existing behavior, appending `• Mistakes: N`.

Enabling or disabling the preference causes the next `refresh_game_subtitle`
call to reflect the change. `PreferencesDialog` already passes
`save_to_file` as `auto_save_function`; `refresh_game_subtitle` is additionally
called after the dialog closes, so subtitle updates promptly when a user
flips the toggle. (Implementation detail: attach to the dialog's close signal
in `on_show_preferences`.)

## Game Over Page

### Blueprint (`data/blueprints/game-over-page.blp`)

Structure mirrors `finished-page.blp`:

```
using Gtk 4.0;
using Adw 1;

template $GameOverPage: Box {
  hexpand: true;
  vexpand: true;
  margin-bottom: 30;

  Box {
    orientation: vertical;
    spacing: 12;
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

          Box {
            orientation: vertical;
            Label stats_mistakes_value  { styles [ "title-2" ] }
            Label stats_mistakes_label  { styles [ "caption" ] }
          }
          Box {
            orientation: vertical;
            Label stats_progress_value  { styles [ "title-2" ] }
            Label stats_progress_label  { styles [ "caption" ] }
          }
          Box {
            orientation: vertical;
            Label stats_difficulty_value  { styles [ "title-2" ] }
            Label stats_difficulty_label  { styles [ "caption" ] }
          }
        }

        Box actions_box {
          orientation: horizontal;
          spacing: 12;
          halign: center;
          margin-top: 12;

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

### Class (`src/screens/game_over_page.py`)

```python
@Gtk.Template(resource_path="/io/github/sepehr_rs/Sudoku/blueprints/game-over-page.ui")
class GameOverPage(Gtk.Box):
    __gtype_name__ = "GameOverPage"

    dark_picture  = "/io/github/sepehr_rs/Sudoku/illustrations/game-over-dark.svg"
    light_picture = "/io/github/sepehr_rs/Sudoku/illustrations/game-over-light.svg"

    picture_contain        = Gtk.Template.Child()
    title_label            = Gtk.Template.Child()
    subtitle_label         = Gtk.Template.Child()
    stats_mistakes_value   = Gtk.Template.Child()
    stats_mistakes_label   = Gtk.Template.Child()
    stats_progress_value   = Gtk.Template.Child()
    stats_progress_label   = Gtk.Template.Child()
    stats_difficulty_value = Gtk.Template.Child()
    stats_difficulty_label = Gtk.Template.Child()
    try_again_button       = Gtk.Template.Child()
    new_game_button        = Gtk.Template.Child()
    main_menu_button       = Gtk.Template.Child()

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

Button click handlers are connected by `SudokuWindow` on construction so the
page class stays UI-only.

### Illustrations

User provides `data/illustrations/game-over-dark.svg` and
`game-over-light.svg` before merge. Paths are wired in the class constants
above and registered in `data/sudokugame.gresource.xml.in`.

### gresource and meson

Add entries for:

- `blueprints/game-over-page.ui` (generated from `.blp` during build)
- `illustrations/game-over-dark.svg`
- `illustrations/game-over-light.svg`

Update `data/blueprints/meson.build` to include the new blueprint compile step.

## Window Integration

`src/window.py` changes:

- Import `GameOverPage` and add it to `_TEMPLATE_WIDGET_TYPES`.
- Add `game_over_page = Gtk.Template.Child()`.
- `data/blueprints/window.blp` adds a stack child for the Game Over page.
- `on_stack_page_changed`: add `self.game_over_page` to the non-game-page
  set (alongside `main_menu_box`, `loading_screen`, `finished_page`). This
  disables the pencil toggle, hides the Preferences menu entry, etc.
- Connect button signals in `__init__` after template realize:
  `self.game_over_page.try_again_button.connect("clicked", self.on_try_again)`,
  and similarly for `new_game_button` and `main_menu_button`.
- `on_try_again`:
  ```python
  def on_try_again(self, _button):
      board = self.manager.board
      board.mistake_count = 0
      size = board.rules.size
      for r in range(size):
          for c in range(size):
              board.user_inputs[r][c] = 0
              board.notes[r][c] = set()
      board.save_to_file()
      self.manager.build_grid()
      self.manager._restore_game_state()
      self.stack.set_visible_child(self.game_scrolled_window)
      self.pencil_toggle_button.set_visible(True)
      self.refresh_game_subtitle()
  ```
- `on_new_game` from Game Over → delegate to existing `on_new_game_clicked`.
- `main_menu_button` → delegate to existing `on_back_to_menu`.
- `on_show_preferences`: after `PreferencesDialog.present()`, connect
  `close-request` to call `refresh_game_subtitle` so toggling the counter
  updates the subtitle live.

### Continue flow branching

`ManagerBase.load_saved_game` already handles the solved-puzzle case. Extend:

```python
if self.board.is_solved():
    self._show_puzzle_finished_dialog()
    return

prefs = PreferencesManager.get_preferences()
if prefs is not None:
    enabled = prefs.general("mistake_counter_enabled", default=True)
    limit = prefs.general("mistake_limit", default=3)
    if enabled and int(getattr(self.board, "mistake_count", 0)) >= int(limit):
        self._trigger_game_over()
        return

self.window.stack.set_visible_child(self.window.game_scrolled_window)
```

(Preserve existing subtitle refresh call.)

## Edge Cases

- **Limit lowered mid-game.** Enforcement is strictly `count >= limit` on each
  mistake; preference changes do not retroactively trigger Game Over. The next
  wrong input triggers it if `count >= new_limit`.
- **Counter disabled mid-game.** Subtitle drops the counter on next refresh.
  Saved `mistake_count` preserved. No Game Over triggered until re-enabled
  and a new mistake brings `count >= limit`.
- **Non-casual mode.** `on_cell_filled` only increments on visible conflicts
  in non-casual mode. The Game Over path is independent of casual/non-casual;
  feature works identically in both.
- **Upgrade from prior save with `mistake_count >= 3`.** Chosen behavior X:
  Continue goes straight to Game Over. Accepted tradeoff.
- **Solving vs. Game Over at last allowed input.** Correct input path does
  not call `_increment_mistake_count`; only wrong inputs can trigger Game
  Over. A correct input that solves the puzzle always takes the finished
  dialog path regardless of current mistake count.

## Testing

Extend `tests/test_mistake_counter.py`:

- `test_game_over_triggered_when_count_reaches_limit`
- `test_game_over_not_triggered_when_counter_disabled`
- `test_game_over_not_triggered_below_limit`
- `test_subtitle_omits_mistakes_when_counter_disabled`
- `test_continue_loads_game_over_when_saved_count_over_limit`
- `test_try_again_resets_mistake_count_and_user_inputs`
- `test_try_again_preserves_clues`

New `tests/test_preferences_schema.py` (or add to existing prefs test):

- `test_typed_bool_preference_returns_default`
- `test_typed_int_preference_returns_default`
- `test_typed_int_preference_respects_min_max`
- `test_preferences_general_lookup_is_uniform_across_types`
- `test_depends_on_metadata_is_preserved`

GTK-dependent behaviors (spin row sensitivity binding, Game Over navigation)
are verified manually per existing project convention; pure-logic tests cover
the preference schema and manager enforcement paths.

## File Inventory

New:

- `src/screens/game_over_page.py`
- `data/blueprints/game-over-page.blp`
- `data/illustrations/game-over-dark.svg` (user-provided)
- `data/illustrations/game-over-light.svg` (user-provided)

Modified:

- `src/base/preferences.py`
- `src/screens/preferences_page.py`
- `src/screens/preferences_dialog.py` (minor: no functional change expected)
- `src/base/manager_base.py`
- `src/variants/classic_sudoku/manager.py` (override `_cleanup_active_grid`)
- `src/window.py`
- `data/blueprints/window.blp`
- `data/blueprints/meson.build`
- `data/sudokugame.gresource.xml.in`
- `src/screens/meson.build`
- `tests/test_mistake_counter.py`
- `tests/test_preferences_schema.py` (may be new)

## Open Items

None at spec-approval time. User provides Game Over SVGs before merge; spec
assumes the two files at `data/illustrations/game-over-{dark,light}.svg`.
