# core/controller.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

import threading
import logging
from gi.repository import GLib, Gtk
from ..shared.grid_manager import GridManager
from ..shared.input_handler import InputHandler
from ..shared.popover_manager import PopoverManager
from ..shared.utils import clear_cell_feedback
from .preferences import PreferencesManager


class CoreSudokuController:
    def __init__(self, window, board_cls, generator, board_size, block_size):
        self.window = window
        self.board_cls = board_cls
        self.generator = generator
        self.board_size = board_size
        self.block_size = block_size
        self.board = None
        self.pencil_mode = False
        self.conflict_cells = []

        self.input_handler = InputHandler(
            on_move=self._on_move,
            on_fill=self._fill_cell,
            on_clear=self._clear_cell,
            on_show_popover=self._on_show_popover,
            on_cell_click=self._on_cell_click,
            get_board_size=lambda: self.board_size,
            get_direction=lambda: self.window.get_direction(),
        )

        self.popover_manager = PopoverManager(self.input_handler)
        self.grid_manager = GridManager()

    def _setup_grid(self):
        self.grid_manager.setup(
            self.window, self.board, self.input_handler, self.popover_manager
        )
        self.grid_manager.build_grid()
        self.popover_manager.set_parent_grid(self.grid_manager.parent_grid)

    #  Game lifecycle

    def start_game(self, difficulty: float, difficulty_label: str, variant: str):
        self.window.stack.set_visible_child(self.window.loading_screen)
        logging.info(
            f"Starting {variant.capitalize()} Sudoku game with difficulty: {difficulty}"
        )

        def worker():
            puzzle, solution = self.generator.generate(difficulty)
            GLib.idle_add(
                self._finish_start_game,
                puzzle,
                solution,
                difficulty,
                difficulty_label,
                variant,
            )

        threading.Thread(target=worker, daemon=True).start()

    def _finish_start_game(
        self, puzzle, solution, difficulty, difficulty_label, variant
    ):
        self.board = self.board_cls(
            generator=self.generator,
            puzzle=puzzle,
            solution=solution,
            difficulty=difficulty,
            difficulty_label=difficulty_label,
            variant=variant,
            block_size=self.block_size,
        )
        self._setup_grid()
        self.window.stack.set_visible_child(self.window.game_scrolled_window)

    def load_saved_game(self):
        self.board = self.board_cls.load(self.generator, self.block_size)
        if self.board:
            self._setup_grid()
            self._restore_game_state()
            self.window.stack.set_visible_child(self.window.game_scrolled_window)
            logging.info(f"Loaded saved {self.board.variant.capitalize()} Sudoku game.")
            if self.board.is_solved():
                self._show_puzzle_finished_dialog()
        else:
            logging.error("No saved game found.")

    def _restore_game_state(self):
        for r in range(self.board.size):
            for c in range(self.board.size):
                value = self.board.user_inputs[r][c]
                notes = self.board.notes[r][c]
                cell = self.grid_manager.cells[r][c]
                if value is not None:
                    cell.set_value(value)
                    correct = self.board.get_correct_value(r, c)
                    if value != correct:
                        cell.highlight("wrong")
                    else:
                        cell.set_editable(False)
                if notes:
                    cell.update_notes(notes)

    #  Cell input

    def _fill_cell(self, row, col, value, ctrl_is_pressed=False):
        cell = self.grid_manager.cells[row][col]
        if not cell.is_editable():
            return

        self._clear_conflicts()

        if self.pencil_mode or ctrl_is_pressed:
            if cell.get_value() is not None:
                return

            prefs = PreferencesManager.get_preferences()
            check_conflicts = (
                prefs.general("prevent_conflicting_pencil_notes", default=True)
                if prefs
                else True
            )

            if check_conflicts:
                conflicts = self.board.has_conflict(row, col, int(value))
                if conflicts:
                    for cr, cc in conflicts:
                        conflict_cell = self.grid_manager.cells[cr][cc]
                        conflict_cell.highlight("conflict")
                        self.conflict_cells.append(conflict_cell)
                    cell.start_feedback_timeout(self._clear_conflicts, delay=2000)
                    return

            self.board.toggle_note(row, col, value)
            cell.update_notes(self.board.get_notes(row, col))
            self.board.save()
            return

        cell.set_value(int(value))
        self.board.set_input(row, col, int(value))
        self.board.save()
        self.on_cell_filled(cell, int(value))

        if self.board.is_solved():
            self._show_puzzle_finished_dialog()

    def _clear_cell(self, row, col, clear_all=False):
        cell = self.grid_manager.cells[row][col]
        if not cell.is_editable():
            return

        if clear_all:
            self.board.clear_input(row, col)
            cell.clear()
            self.board.notes[row][col].clear()
        elif self.pencil_mode:
            current_notes = self.board.get_notes(row, col)
            if current_notes:
                last_note = sorted(current_notes, key=int)[-1]
                self.board.toggle_note(row, col, last_note)
                cell.update_notes(self.board.get_notes(row, col))
        else:
            self.board.clear_input(row, col)
            cell.clear()
            self.board.notes[row][col].clear()

        self.board.save()
        self._highlight_related(row, col)

    #  Cell click / focus

    def _on_cell_click(self, row, col, button, n_press):
        cell = self.grid_manager.cells[row][col]
        self._focus_cell(row, col)

        if cell.is_editable() and n_press == 1:
            self.popover_manager.show_popover(
                cell, self.board.get_remaining_valid_inputs(), button
            )
        else:
            cell.grab_focus()

    def _on_move(self, from_r, from_c, to_r, to_c):
        self._focus_cell(to_r, to_c)

    def _on_show_popover(self, row, col, button=0):
        cell = self.grid_manager.cells[row][col]
        if cell.is_editable():
            self.popover_manager.show_popover(
                cell, self.board.get_remaining_valid_inputs(), button
            )

    def _focus_cell(self, row, col):
        cell = self.grid_manager.cells[row][col]
        cell.grab_focus()
        self._highlight_related(row, col)

    def _highlight_related(self, row, col):
        cells = self.grid_manager.cells
        self._clear_highlights(cells)

        prefs = PreferencesManager.get_preferences()
        if not prefs:
            return

        selected_value = cells[row][col].get_value()
        if selected_value is None:
            self._highlight_neighborhood(cells, row, col, prefs)
        else:
            self._highlight_matching(cells, selected_value, prefs)

    def _clear_highlights(self, cells):
        for r in range(self.board_size):
            for c in range(self.board_size):
                cells[r][c].remove_highlight("highlight")

    def _highlight_neighborhood(self, cells, row, col, prefs):
        if prefs.general("highlight_row"):
            for i in range(self.board_size):
                cells[row][i].highlight("highlight")
        if prefs.general("highlight_column"):
            for i in range(self.board_size):
                cells[i][col].highlight("highlight")
        if prefs.variant("highlight_block"):
            bs = self.block_size
            br, bc = (row // bs) * bs, (col // bs) * bs
            for r in range(br, br + bs):
                for c in range(bc, bc + bs):
                    cells[r][c].highlight("highlight")

    def _highlight_matching(self, cells, value, prefs):
        if not prefs.variant("highlight_related_cells"):
            return
        for r in range(self.board_size):
            for c in range(self.board_size):
                if cells[r][c].get_value() == value:
                    cells[r][c].highlight("highlight")

    #  Feedback

    def on_cell_filled(self, cell, number: int):
        prefs = PreferencesManager.get_preferences()
        casual_mode = prefs.general("casual_mode") if prefs else False
        correct_value = self.board.get_correct_value(cell.row, cell.col)

        clear_cell_feedback(cell, "correct", "wrong")

        if casual_mode:
            if number == correct_value:
                self._handle_correct_input(cell)
            else:
                self._handle_wrong_input(cell, number)
            return

        new_conflicts = self.board.has_conflict(cell.row, cell.col, number)
        if new_conflicts:
            self._handle_wrong_input(cell, number, new_conflicts)

    def _handle_correct_input(self, cell):
        cell.set_editable(False)
        cell.highlight("correct")
        cell.set_tooltip_text("Correct")

        def _clear():
            clear_cell_feedback(cell, "correct")
            return False

        cell.start_feedback_timeout(_clear)

        prefs = PreferencesManager.get_preferences()
        auto_remove = (
            prefs.general("auto_remove_notes", default=True) if prefs else True
        )
        if auto_remove:
            affected = self.board.remove_note_from_related(
                cell.row, cell.col, cell.get_value()
            )
            for r, c in affected:
                self.grid_manager.cells[r][c].update_notes(self.board.get_notes(r, c))

    def _handle_wrong_input(self, cell, number, conflicts=None):
        cell.highlight("wrong")
        cell.set_tooltip_text("Wrong")

        prefs = PreferencesManager.get_preferences()
        mistake_limit = prefs.general("mistake_limit") if prefs else None
        if mistake_limit and mistake_limit.get("enabled"):
            self.board.mistakes += 1
            self.check_mistakes_limit()

        self.board.save()
        self._update_subtitle()

        if not conflicts:
            conflicts = self.board.has_conflict(cell.row, cell.col, number)
        if conflicts:
            for r, c in conflicts:
                self.grid_manager.cells[r][c].highlight("conflict")
                self.conflict_cells.append(self.grid_manager.cells[r][c])

        cell.start_feedback_timeout(self._clear_conflicts, delay=4000)

    def check_mistakes_limit(self):
        prefs = PreferencesManager.get_preferences()
        limit = prefs.general("mistake_limit") if prefs else None
        if limit and self.board.mistakes > limit.get("count", 3):
            self._show_puzzle_finished_dialog(self.window.game_over_page)

    def _update_subtitle(self):
        base = f"{self.board.variant.capitalize()} • {self.board.difficulty_label}"
        prefs = PreferencesManager.get_preferences()
        show_mistakes = prefs.general("mistake_limit")["enabled"] if prefs else False
        suffix = f" • Mistakes: {self.board.mistakes}" if show_mistakes else ""
        self.window.update_sudoku_window_subtitle(base + suffix)

    def _clear_conflicts(self):
        for cell in self.conflict_cells:
            cell.remove_highlight("conflict")
        self.conflict_cells.clear()

    #  Game over / finished

    def _show_puzzle_finished_dialog(self, page=None):
        self.popover_manager.invalidate()
        self.window.pencil_toggle_button.set_visible(False)
        if self.grid_manager.cells:
            for row in self.grid_manager.cells:
                for cell in row:
                    if cell:
                        cell.clear_feedback_timeout()
        while child := self.window.grid_container.get_first_child():
            self.window.grid_container.remove(child)
        target = page if page is not None else self.window.finished_page
        self.window.stack.set_visible_child(target)

    #  Pencil mode

    def on_pencil_toggled(self, button: Gtk.ToggleButton):
        self.pencil_mode = button.get_active()
        self.popover_manager.set_pencil_mode(self.pencil_mode)

    #  Unfocus

    def on_grid_unfocus(self):
        if self.grid_manager.cells:
            for row in self.grid_manager.cells:
                for cell in row:
                    cell.remove_highlight("highlight")
        self._clear_conflicts()

    #  Compact mode

    def apply_compact_mode(self, compact, mode):
        parent_spacing, block_spacing = (8, 2) if compact else (10, 4)
        parent_grid = self.grid_manager.parent_grid
        if parent_grid:
            parent_grid.set_row_spacing(parent_spacing)
            parent_grid.set_column_spacing(parent_spacing)

        for row in self.grid_manager.blocks:
            for block in row:
                block.set_row_spacing(block_spacing)
                block.set_column_spacing(block_spacing)

        for row in self.grid_manager.cells:
            for cell in row:
                if cell:
                    cell.set_compact(compact)

        w = self.window
        w.game_scrolled_window.set_vexpand(True)
        w.game_scrolled_window.set_hexpand(True)
        w.grid_container.set_hexpand(True)
        w.grid_container.set_vexpand(True)
        w.bp_bin.set_hexpand(True)
        w.bp_bin.set_vexpand(True)
        w.bp_bin.set_halign(Gtk.Align.FILL)
        w.bp_bin.set_valign(Gtk.Align.FILL)
        w.stack.set_hexpand(True)
        w.stack.set_vexpand(True)
        w.stack.set_halign(Gtk.Align.FILL)
        w.stack.set_valign(Gtk.Align.FILL)
