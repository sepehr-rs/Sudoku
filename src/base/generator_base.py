# generator_base.py
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
    def _generate_impl(
        self, difficulty: float
    ) -> tuple[list[list[int]], list[list[int]]]:
        """
        Must be implemented by variants.
        Return (puzzle, solution) as 2D lists.
        """
        pass
