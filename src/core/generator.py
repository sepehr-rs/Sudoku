# generator.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from abc import ABC, abstractmethod
import multiprocessing as mp


class GeneratorCore(ABC):
    """Abstract puzzle generator with optional multiprocessing."""

    def generate(
        self, difficulty: float, timeout: int = 5
    ) -> tuple[list[list[int]], list[list[int]]]:
        """Run the variant's `_generate_impl` in a subprocess with timeout."""
        queue = mp.Queue()
        process = mp.Process(target=self._generate_worker, args=(queue, difficulty))
        process.start()
        process.join(timeout)
        if process.is_alive():
            process.terminate()
            process.join()
            raise TimeoutError("Puzzle generation timed out")

        if not queue.empty():
            error, result = queue.get()
            if error is not None:
                raise RuntimeError("Puzzle generation failed") from error
            return result

        raise RuntimeError("Failed to generate puzzle")

    def _generate_worker(self, queue: mp.Queue, difficulty: float) -> None:
        try:
            puzzle, solution = self._generate_impl(difficulty)
            queue.put((None, (puzzle, solution)))
        except Exception as e:
            queue.put((e, None))

    @abstractmethod
    def _generate_impl(
        self, difficulty: float
    ) -> tuple[list[list[int]], list[list[int]]]:
        """Must be implemented by variants. Return (puzzle, solution) as 2D lists."""
        pass
