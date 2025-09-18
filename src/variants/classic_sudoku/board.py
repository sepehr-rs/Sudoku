import json, os
from ...base.board_base import BoardBase
from .rules import ClassicSudokuRules
from .generator import ClassicSudokuGenerator


class ClassicSudokuBoard(BoardBase):
    def __init__(self, difficulty: float, difficulty_label: str):
        super().__init__(
            ClassicSudokuRules(),
            ClassicSudokuGenerator(),
            difficulty,
            difficulty_label
        )

    @classmethod
    def load_from_file(cls, filename: str = None):
        filename = filename or cls.DEFAULT_SAVE_PATH
        if not os.path.exists(filename):
            return None

        with open(filename, "r", encoding="utf-8") as f:
            state = json.load(f)

        self = cls.__new__(cls)
        self.rules = ClassicSudokuRules()
        self.generator = ClassicSudokuGenerator()
        self.difficulty = state["difficulty"]
        self.difficulty_label = state["difficulty_label"]
        self.puzzle = state["puzzle"]
        self.solution = state["solution"]
        self.user_inputs = state["user_inputs"]
        self.notes = [[set(n) for n in row] for row in state["notes"]]
        return self

    def is_solved(self):
        for r in range(self.rules.size):
            for c in range(self.rules.size):
                if not self.is_clue(r, c):
                    if self.user_inputs[r][c] != str(self.solution[r][c]):
                        return False
        return True
