from abc import ABC, abstractmethod


class RulesBase(ABC):
    @property
    @abstractmethod
    def size(self) -> int:
        pass

    @property
    @abstractmethod
    def block_size(self) -> int:
        pass

    @abstractmethod
    def is_valid(self, grid, row, col, value) -> bool:
        pass

    @abstractmethod
    def is_solved(self, user_inputs, solution) -> bool:
        pass
