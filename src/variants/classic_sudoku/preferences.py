# classic_sudoku/preferences.py
# Copyright 2025 sepehr-rs
# SPDX-License-Identifier: GPL-3.0-or-later

from ...core.preferences import CoreSudokuPreferences

class ClassicSudokuPreferences(CoreSudokuPreferences):
    variant_defaults = {
        "highlight_block": True,
        "highlight_related_cells": True,
    }

    def __init__(self):
        super().__init__()
        self.name = "Classic Sudoku"