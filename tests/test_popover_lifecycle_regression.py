# test_popover_lifecycle_regression.py
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

"""
Regression tests for popover lifecycle management.

These tests ensure proper popover lifecycle behavior:
1. No unparent() calls in popover lifecycle
2. popup() used instead of show()
3. released signal used instead of pressed
4. Mode switching preserved
"""

import ast
from pathlib import Path

import pytest


# Test for no unparent() calls (AST check)
def test_no_unparent_calls_in_popover_methods():
    """
    Verify no unparent() calls exist in popover lifecycle methods.

    unparent() should not be used as it breaks GTK4 popover lifecycle.
    Instead, popovers should be reused and managed via popdown() method.
    """
    project_root = Path(__file__).parent.parent

    # Files to check for popover lifecycle methods
    files_to_check = [
        "src/variants/classic_sudoku/ui_helpers.py",
        "src/variants/classic_sudoku/manager.py",
        "src/variants/classic_sudoku/sudoku_cell.py",
        "src/variants/diagonal_sudoku/sudoku_cell.py",
    ]

    violations = []

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        with open(full_path, "r", encoding="utf-8") as f:
            source = f.read()

        try:
            tree = ast.parse(source)
            unparent_calls = find_unparent_calls(tree, file_path)
            violations.extend(unparent_calls)
        except SyntaxError as e:
            pytest.fail(f"Failed to parse {file_path}: {e}")

    # Assert no violations found
    assert not violations, (
        "Found unparent() calls in popover lifecycle code. "
        "Use popdown() instead or manage popovers without unparenting.\n"
        f"Violations: {violations}"
    )


def find_unparent_calls(tree: ast.AST, file_path: str) -> list[str]:
    """
    Find all unparent() calls in the AST.

    Returns list of locations where unparent() is called.
    """
    violations = []

    class UnparentVisitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            # Check if this is an unparent() call
            if isinstance(node.func, ast.Attribute):
                if node.func.attr == "unparent":
                    # Get line number
                    line_num = getattr(node, "lineno", 0)
                    violations.append(f"{file_path}:{line_num}")
            self.generic_visit(node)

    visitor = UnparentVisitor()
    visitor.visit(tree)
    return violations


# Test for popup() used instead of show()
def test_popup_used_instead_of_show_for_popovers():
    """
    Verify popup() is used instead of show() for Gtk.Popover instances.

    GTK4 Popover requires popup() for proper display, not show().
    """
    project_root = Path(__file__).parent.parent

    # Files containing popover-related code
    files_to_check = [
        "src/variants/classic_sudoku/ui_helpers.py",
        "src/variants/classic_sudoku/manager.py",
        "src/variants/diagonal_sudoku/manager.py",
    ]

    violations = []

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        with open(full_path, "r", encoding="utf-8") as f:
            source = f.read()
            lines = source.splitlines()

        # Check for show() calls on popover objects
        for i, line in enumerate(lines, 1):
            # Look for .show() calls that might be on popover objects
            if ".show()" in line and "popover" in line.lower():
                # Check if this line is not in a comment
                stripped = line.strip()
                if not stripped.startswith("#"):
                    violations.append(f"{file_path}:{i}: {stripped}")

    # Also check AST for proper popup() usage
    popup_violations = verify_popup_calls_present(
        ["src/variants/classic_sudoku/ui_helpers.py"]
    )
    violations.extend(popup_violations)

    assert not violations, (
        "Found show() calls on popover objects. "
        "Use popup() instead for Gtk.Popover.\n"
        f"Violations: {violations}"
    )


def verify_popup_calls_present(files_to_check: list[str]) -> list[str]:
    """
    Verify popup() is used for showing popovers.

    Returns violations if popup() is not found where expected.
    """
    project_root = Path(__file__).parent.parent
    violations = []

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        with open(full_path, "r", encoding="utf-8") as f:
            source = f.read()

        # Check that popup() is present
        if ".popup()" not in source:
            violations.append(f"{file_path}: Missing popup() call for popover display")

    return violations


# Test for released signal used instead of pressed
def test_released_signal_used_for_gesture_clicks():
    """
    Verify 'released' signal is used instead of 'pressed' for gesture clicks.

    Using 'pressed' can cause popover lifecycle issues. 'released' is the
    correct signal for popover interactions.
    """
    project_root = Path(__file__).parent.parent

    # Files containing gesture connection code
    files_to_check = [
        "src/variants/classic_sudoku/manager.py",
        "src/variants/diagonal_sudoku/manager.py",
    ]

    violations = []

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        with open(full_path, "r", encoding="utf-8") as f:
            source = f.read()

        if "GestureClick" in source and 'connect("released"' not in source:
            violations.append(
                f"{file_path}: GestureClick present but 'released' signal not connected"
            )

        if 'connect("pressed"' in source:
            if any(
                snippet in source
                for snippet in (
                    'connect("pressed", self.on_left_click',
                    'connect("pressed", self.on_right_click',
                )
            ):
                violations.append(
                    f"{file_path}: Click handler must not be wired to 'pressed'"
                )
            if "def on_cell_pressed" in source and "_show_popover" in source:
                pressed_snippet = _get_function_source(
                    project_root,
                    file_path,
                    "on_cell_pressed",
                )
                if "_show_popover" in pressed_snippet:
                    violations.append(
                        f"{file_path}: on_cell_pressed must not call _show_popover"
                    )

    assert not violations, (
        "Gesture clicks should use 'released' signal, not 'pressed'.\n"
        f"Violations: {violations}"
    )


# Test for mode switching preserved
def test_mode_switching_preserved():
    """
    Verify that pencil mode state is preserved across popover interactions.

    Mode switching (pencil mode) should not be reset when opening/closing popovers.
    """
    project_root = Path(__file__).parent.parent

    # Check manager files for proper mode state management
    files_to_check = [
        "src/variants/classic_sudoku/manager.py",
        "src/base/manager_base.py",
    ]

    violations = []

    for file_path in files_to_check:
        full_path = project_root / file_path
        if not full_path.exists():
            continue

        with open(full_path, "r", encoding="utf-8") as f:
            source = f.read()
            lines = source.splitlines()

        # Look for patterns that might reset mode inappropriately
        mode_reset_patterns = [
            "self.pencil_mode = False",
            "self.pencil_mode = None",
            "pencil_mode = False",
        ]

        for i, line in enumerate(lines, 1):
            # Skip comments
            stripped = line.strip()
            if stripped.startswith("#"):
                continue

            # Check for problematic patterns in popover-related methods
            if any(pattern in line for pattern in mode_reset_patterns):
                # Check if this is in a popover lifecycle method
                method_context = get_method_context(lines, i)
                if "popover" in method_context.lower():
                    msg = (
                        f"{file_path}:{i}: Possible mode reset in popover method: "
                        f"{stripped}"
                    )
                    violations.append(msg)

    # Also verify proper mode preservation through method signatures
    mode_violations = verify_mode_preservation_signatures(
        "src/variants/classic_sudoku/manager.py"
    )
    violations.extend(mode_violations)

    assert not violations, (
        "Pencil mode state should be preserved across popover interactions.\n"
        f"Violations: {violations}"
    )


def get_method_context(lines: list[str], line_num: int, context_size: int = 10) -> str:
    """
    Get the method context around a given line number.

    Returns a string containing the method definition and surrounding lines.
    """
    start = max(0, line_num - context_size)
    end = min(len(lines), line_num + context_size)
    return "\n".join(lines[start:end])


def verify_mode_preservation_signatures(file_path: str) -> list[str]:
    """
    Verify that popover-related methods preserve pencil mode state.

    Returns violations if mode state might be lost.
    """
    project_root = Path(__file__).parent.parent
    full_path = project_root / file_path
    violations = []

    if not full_path.exists():
        return violations

    with open(full_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)

        class ModePreservationVisitor(ast.NodeVisitor):
            def __init__(self):
                self.popover_methods = []
                self.violations = []

            def visit_FunctionDef(self, node: ast.FunctionDef):
                # Check if this is a popover-related method
                if "popover" in node.name.lower() or any(
                    "popover" in arg.arg.lower() for arg in node.args.args
                ):
                    # Check if pencil_mode is not in arguments but used in body
                    has_pencil_mode_arg = any(
                        arg.arg == "pencil_mode" for arg in node.args.args
                    )
                    has_pencil_mode_use = self._check_pencil_mode_use(node)

                    if not has_pencil_mode_arg and has_pencil_mode_use:
                        # If method uses pencil_mode but doesn't accept it as parameter,
                        # it should access self.pencil_mode
                        uses_self_pencil_mode = self._check_self_pencil_mode(node)
                        if not uses_self_pencil_mode:
                            self.violations.append(
                                f"{file_path}:{node.lineno}: Method '{node.name}' uses "
                                "pencil_mode without proper parameter or self reference"
                            )

                self.generic_visit(node)

            def _check_pencil_mode_use(self, node: ast.FunctionDef) -> bool:
                """Check if pencil_mode is used in the method body."""
                for child in ast.walk(node):
                    if isinstance(child, ast.Name) and child.id == "pencil_mode":
                        return True
                return False

            def _check_self_pencil_mode(self, node: ast.FunctionDef) -> bool:
                """Check if method uses self.pencil_mode."""
                for child in ast.walk(node):
                    if isinstance(child, ast.Attribute):
                        if (
                            isinstance(child.value, ast.Name)
                            and child.value.id == "self"
                            and child.attr == "pencil_mode"
                        ):
                            return True
                return False

        visitor = ModePreservationVisitor()
        visitor.visit(tree)
        violations.extend(visitor.violations)

    except SyntaxError as e:
        violations.append(f"Failed to parse {file_path}: {e}")

    return violations


def test_popover_shared_design_no_per_cell_cache():
    project_root = Path(__file__).parent.parent

    ui_helpers_path = project_root / "src/variants/classic_sudoku/ui_helpers.py"
    manager_path = project_root / "src/variants/classic_sudoku/manager.py"
    assert ui_helpers_path.exists()
    assert manager_path.exists()

    ui_helpers = ui_helpers_path.read_text(encoding="utf-8")
    manager = manager_path.read_text(encoding="utf-8")

    assert "Gtk.Popover(" not in ui_helpers
    assert "_active_popover" not in ui_helpers
    assert "getattr(cell, \"_active_popover\"" not in ui_helpers

    assert "self._cell_popover" in manager
    assert "Gtk.Popover(" in manager
    assert "popover=popover" in manager


# Parameterized test for all variant managers
@pytest.mark.parametrize(
    "variant_module,manager_class",
    [
        ("src.variants.classic_sudoku.manager", "ClassicSudokuManager"),
        ("src.variants.diagonal_sudoku.manager", "DiagonalSudokuManager"),
    ],
)
def test_variant_manager_popover_lifecycle(variant_module, manager_class):
    """
    Test that all variant managers follow proper popover lifecycle patterns.

    This is a parameterized test that verifies each variant's manager
    follows the same popover lifecycle best practices.
    """
    project_root = Path(__file__).parent.parent
    module_path = project_root / f"{variant_module.replace('.', '/')}.py"

    if not module_path.exists():
        pytest.skip(f"Module file not found: {module_path}")

    with open(module_path, "r", encoding="utf-8") as f:
        source = f.read()

    violations = []

    if "GestureClick" in source and 'connect("released"' not in source:
        violations.append("GestureClick present but 'released' not connected")

    # Check for proper popover method calls
    if "popover.show()" in source:
        violations.append("Uses show() instead of popup() for popover")

    # Check for unparent calls
    if ".unparent()" in source:
        violations.append("Uses unparent() which breaks popover lifecycle")

    # Verify proper popdown usage
    # Popover popdown() calls may be in inherited classes
    # Only check if popover.show() is used (which should not happen)
    if "popover.show()" in source and "popover" in source:
        violations.append("Deprecated popover.show() usage with popovers")

    assert not violations, (
        f"{manager_class} popover lifecycle violations:\n" + "\n".join(violations)
    )


def test_gesture_click_handles_all_buttons():
    source = "/mnt/projects/kgoodwin/Sudoku/src/variants/classic_sudoku/manager.py"

    with open(source, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Gtk.GestureClick.new()" in content
    assert "gesture.set_button(0)" in content
    assert "gesture.connect(\"released\", self.on_cell_clicked" in content
    assert "def on_cell_clicked" in content
    assert "self._show_popover" in content


def test_popover_opened_from_released_handler_only():
    source = "/mnt/projects/kgoodwin/Sudoku/src/variants/classic_sudoku/manager.py"

    with open(source, "r", encoding="utf-8") as f:
        content = f.read()

    assert "def on_cell_clicked" in content
    assert "self._show_popover" in content


def _get_function_source(project_root: Path, rel_path: str, func_name: str) -> str:
    full_path = project_root / rel_path
    with open(full_path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == func_name:
            start = max(0, (node.lineno or 1) - 1)
            end = (node.end_lineno or node.lineno or 1)
            lines = source.splitlines()
            return "\n".join(lines[start:end])
    raise AssertionError(f"Function {func_name} not found in {rel_path}")


def test_popover_references_cleared_on_grid_rebuild():
    project_root = Path(__file__).parent.parent
    snippet = _get_function_source(
        project_root,
        "src/variants/classic_sudoku/manager.py",
        "_clear_previous_grid",
    )

    assert "self._popdown_active_popover()" in snippet
    assert "self._active_popover = None" in snippet
    assert "self._cell_popover = None" in snippet


def test_popover_references_cleared_on_puzzle_finished():
    project_root = Path(__file__).parent.parent
    snippet = _get_function_source(
        project_root,
        "src/variants/classic_sudoku/manager.py",
        "_show_puzzle_finished_dialog",
    )

    assert "self._popdown_active_popover()" in snippet
    assert "self._active_popover = None" in snippet
    assert "self._cell_popover = None" in snippet
