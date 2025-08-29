# game_board.py
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

import json
import os
import logging
import random
from sudoku import Sudoku as PySudoku
from pathlib import Path

GRID_SIZE = 9
BLOCK_SIZE = 3

EASY_DIFFICULTY = 0.2
MEDIUM_DIFFICULTY = 0.5
HARD_DIFFICULTY = 0.7
EXTREME_DIFFICULTY = 0.9


APP_ID = "io.github.sepehr_rs.Sudoku"
data_dir = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local/share"))
save_dir = data_dir / APP_ID
save_dir.mkdir(parents=True, exist_ok=True)
SAVE_PATH = save_dir / "save.json"


def optimized_difficulty_fast(self, difficulty):
    assert 0 <= difficulty < 1, "Difficulty must be between 0 and 1"

    solved_board = self.solve().board
    size = self.size
    total_cells = size * size

    indices = list(range(total_cells))
    random.shuffle(indices)
    problem_board = [row[:] for row in solved_board]

    def has_one_solution(board):
        counter = [0]

        def is_valid(b, r, c, num):
            for i in range(9):
                if b[r][i] == num or b[i][c] == num:
                    return False
            start_r, start_c = 3 * (r // 3), 3 * (c // 3)
            for i in range(start_r, start_r + 3):
                for j in range(start_c, start_c + 3):
                    if b[i][j] == num:
                        return False
            return True

        def count_solutions(pos=0):
            if counter[0] > 1:
                return
            if pos == total_cells:
                counter[0] += 1
                return

            r, c = divmod(pos, 9)
            if board[r][c] != 0:
                count_solutions(pos + 1)
            else:
                for num in range(1, 10):
                    if is_valid(board, r, c, num):
                        board[r][c] = num
                        count_solutions(pos + 1)
                        board[r][c] = 0

        count_solutions()
        return counter[0] == 1

    cells_to_remove = int(difficulty * total_cells)
    for idx in indices[:cells_to_remove]:
        row, col = divmod(idx, size)
        removed = problem_board[row][col]
        problem_board[row][col] = 0
        if not has_one_solution(problem_board):
            problem_board[row][col] = removed

    return PySudoku(self.width, self.height, problem_board, difficulty)


PySudoku.difficulty = optimized_difficulty_fast


class GameBoard:
    def __init__(
        self,
        difficulty: float,
        difficulty_label: str,
        puzzle=None,
        solution=None,
        user_inputs=None,
        notes=None,
    ):
        self.difficulty = difficulty
        self.difficulty_label = difficulty_label

        if puzzle and solution:
            self.puzzle = puzzle
            self.solution = solution
        else:
            random_seed = random.randint(1, 1000000)
            sudoku = PySudoku(3, seed=random_seed).difficulty(difficulty)
            self.puzzle = sudoku.board
            self.solution = sudoku.solve().board

        self.user_inputs = (
            user_inputs
            if user_inputs
            else [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        )
        self.notes = (
            notes
            if notes
            else [[list() for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        )

    def to_dict(self):
        return {
            "difficulty": self.difficulty,
            "difficulty_label": self.difficulty_label,
            "puzzle": self.puzzle,
            "solution": self.solution,
            "user_inputs": self.user_inputs,
            "notes": [[list(n) for n in row] for row in self.notes],
        }

    def is_clue(self, row: int, col: int) -> bool:
        return self.puzzle[row][col] is not None

    def set_input(self, row: int, col: int, value: str):
        self.user_inputs[row][col] = value

    def get_input(self, row: int, col: int):
        return self.user_inputs[row][col]

    def get_notes(self, row: int, col: int) -> set:
        return self.notes[row][col]

    def add_note(self, row: int, col: int, value: str):
        self.notes[row][col].append(value)

    def remove_note(self, row: int, col: int, value: str):
        if value in self.notes[row][col]:
            self.notes[row][col].remove(value)

    def clear_notes(self, row: int, col: int):
        self.notes[row][col].clear()

    def is_solved(self) -> bool:
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if not self.is_clue(row, col):
                    user_val = self.user_inputs[row][col]
                    correct_val = str(self.solution[row][col])
                    if user_val != correct_val:
                        return False
        return True

    def get_correct_value(self, row: int, col: int) -> str:
        return str(self.solution[row][col])

    def save_to_file(self, path=SAVE_PATH):
        try:
            with open(SAVE_PATH, "w") as f:
                json.dump(self.to_dict(), f)
        except Exception as e:
            logging.error(f"Failed to save game: {e}")

    @classmethod
    def load_from_file(cls, path=SAVE_PATH):
        try:
            with open(SAVE_PATH, "r") as f:
                data = json.load(f)

            notes = [[list(cell) for cell in row] for row in data["notes"]]
            difficulty_label = data.get("difficulty_label", "Unknown")
            return cls(
                difficulty=data["difficulty"],
                difficulty_label=difficulty_label,
                puzzle=data["puzzle"],
                solution=data["solution"],
                user_inputs=data["user_inputs"],
                notes=notes,
            )
        except Exception as e:
            logging.error(f"Error loading game: {e}")
            return None

    @classmethod
    def has_saved_game(cls, path=SAVE_PATH) -> bool:
        try:
            with open(path, "r"):
                return True
        except Exception:
            return False
