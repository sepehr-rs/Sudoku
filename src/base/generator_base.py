from abc import ABC, abstractmethod
import multiprocessing as mp


class GeneratorBase(ABC):
    """Abstract puzzle generator with optional multiprocessing."""

    def generate(self, difficulty: float, timeout: int = 5):
        """
        Run the variant's `_generate_impl` in a subprocess with timeout.
        Returns (puzzle, solution).
        """
        queue = mp.Queue()
        process = mp.Process(target=self._generate_worker, args=(queue, difficulty))
        process.start()
        process.join(timeout)

        if process.is_alive():
            process.terminate()
            process.join()
            raise TimeoutError("Puzzle generation timed out")

        if not queue.empty():
            return queue.get()
        raise RuntimeError("Failed to generate puzzle")

    def _generate_worker(self, queue, difficulty: float):
        puzzle, solution = self._generate_impl(difficulty)
        queue.put((puzzle, solution))

    @abstractmethod
    def _generate_impl(self, difficulty: float):
        """
        Must be implemented by variants.
        Return (puzzle, solution) as 2D lists.
        """
        pass
