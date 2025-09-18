# src/base/board_base.py
import json
import os

class BoardBase:
    """Handles puzzle state, notes, persistence, and correctness."""

    DEFAULT_SAVE_PATH = os.path.expanduser("~/.local/share/io.github.sepehr_rs.Sudoku/save.json")

    def __init__(self, rules, generator, difficulty: float, difficulty_label: str):
        self.rules = rules
        self.generator = generator
        self.difficulty = difficulty
        self.difficulty_label = difficulty_label

        # Generate puzzle + solution if no existing puzzle provided
        self.puzzle, self.solution = generator.generate(difficulty)

        # Track user inputs & notes
        self.user_inputs = [[None for _ in range(self.rules.size)] for _ in range(self.rules.size)]
        self.notes = [[[] for _ in range(self.rules.size)] for _ in range(self.rules.size)]

    # --- User input methods ---
    def set_input(self, row, col, value):
        self.user_inputs[row][col] = value

    def get_input(self, row, col):
        return self.user_inputs[row][col]

    # --- Notes management ---
    def add_note(self, row, col, value):
        if value not in self.notes[row][col]:
            self.notes[row][col].append(value)

    def remove_note(self, row, col, value):
        if value in self.notes[row][col]:
            self.notes[row][col].remove(value)

    def clear_notes(self, row, col):
        self.notes[row][col].clear()

    def get_notes(self, row, col):
        return set(self.notes[row][col])

    # --- Clues / solution ---
    def is_clue(self, row, col):
        return self.puzzle[row][col] is not None

    def get_correct_value(self, row, col):
        return str(self.solution[row][col])

    def is_solved(self):
        for r in range(self.rules.size):
            for c in range(self.rules.size):
                if not self.is_clue(r, c):
                    if self.user_inputs[r][c] != str(self.solution[r][c]):
                        return False
        return True

    # --- Persistence ---
    def save_to_file(self, filename: str = None):
        filename = filename or self.DEFAULT_SAVE_PATH
        state = {
            "difficulty": self.difficulty,
            "difficulty_label": self.difficulty_label,
            "puzzle": self.puzzle,
            "solution": self.solution,
            "user_inputs": self.user_inputs,
            "notes": [[list(n) for n in row] for row in self.notes],
        }
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(state, f)

    def load_from_file(cls, filename: str = None):
        """Load a board from file and return a fully constructed board instance."""
        filename = filename or cls.DEFAULT_SAVE_PATH
        if not os.path.exists(filename):
            return None
        with open(filename, "r", encoding="utf-8") as f:
            state = json.load(f)

        # Create instance without generating a new puzzle
        self = cls.__new__(cls)  # bypass __init__
        self.rules = cls.__init__.__globals__["ClassicSudokuRules"]()
        self.generator = cls.__init__.__globals__["ClassicSudokuGenerator"]()
        self.difficulty = state["difficulty"]
        self.difficulty_label = state["difficulty_label"]
        self.puzzle = state["puzzle"]
        self.solution = state["solution"]
        self.user_inputs = state["user_inputs"]
        self.notes = state["notes"]
        return self

    @classmethod
    def has_saved_game(cls, filename: str = None):
        filename = filename or cls.DEFAULT_SAVE_PATH
        return os.path.exists(filename)
