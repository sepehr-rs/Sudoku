from ....base.board_base import BoardBase
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
