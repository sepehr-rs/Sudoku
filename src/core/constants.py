# src/shared/constants.py
# Copyright 2026 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from dataclasses import dataclass


@dataclass
class SudokuConstants:
    block_size: int = 3

SUDOKU_CONSTANTS = SudokuConstants()