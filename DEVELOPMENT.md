# Development Guidelines

This document captures coding conventions and best practices for contributing to Sudoku. These guidelines emerged from PR review discussions and help keep the codebase consistent and maintainable.

## Testing Philosophy

Prefer behavior-based tests over structural checks. Tests should validate what the code does, not how it's written.

**Do:**
- Test user-visible behavior and outcomes
- Validate correct program state after operations
- Focus on integration and end-to-end scenarios

**Don't:**
- Write AST-based validators to check code structure
- Add CI gates that enforce "code shape" without clear value
- Test implementation details that can change without affecting behavior

Rationale: Structural tests are brittle. When the implementation changes but behavior stays the same, structural tests fail even though the code is correct. Behavior-based tests are more resilient and actually verify that the software works.

## Assertions

Never use `assert` statements in non-test code. Assertions can be disabled at runtime with the `-O` flag, which bypasses critical checks. Use explicit exceptions instead.

**Do:**
```python
def set_cell_value(self, cell, value):
    if cell is None:
        raise ValueError("cell cannot be None")
    if not 1 <= value <= 9:
        raise ValueError(f"value must be 1-9, got {value}")
    # ...
```

**Don't:**
```python
def set_cell_value(self, cell, value):
    assert cell is not None, "cell cannot be None"
    assert 1 <= value <= 9, f"value must be 1-9"
    # ...
```

**Exception Types:**
- `ValueError` / `TypeError` for bad inputs or incorrect argument types
- `RuntimeError` for illegal state transitions or invalid operations given current state
- `AssertionError` only as an explicit `raise AssertionError(...)` when signaling a true invariant bug that should never happen

## Exception Handling

Avoid broad exception catching in production code. Narrow exception handling makes code more predictable and prevents swallowing unexpected errors.

**Do:**
```python
try:
    self.popover.popup()
except (AttributeError, TypeError) as e:
    # Handle specific GTK API differences or version mismatches
    logging.debug(f"Popover popup failed: {e}", exc_info=True)
```

**Don't:**
```python
try:
    self.popover.popup()
except Exception:
    pass  # Too broad - hides bugs
```

When intentionally suppressing an exception (for cleanup code, UI glue, or best-effort operations):
- Log at `DEBUG` level with full stack trace
- Be explicit about why suppression is acceptable
- Add comments explaining the rationale

```python
# Best-effort cleanup during widget teardown
try:
    self.popover.popdown()
except (AttributeError, RuntimeError) as e:
    # Popover may already be destroyed or not attached
    logging.debug(f"Popover cleanup skipped: {e}", exc_info=True)
```

## GTK Popover Lifecycle

Proper popover lifecycle management prevents memory leaks and visual glitches. Use the GTK-provided popup/popdown methods instead of manual parenting.

**Do:**
```python
class CellHandler:
    def __init__(self):
        # Shared popover for all cells (prevents resource growth)
        self.popover = Gtk.Popover()
        self.popover.connect("closed", self._on_popover_closed)

    def show_for_cell(self, cell):
        self.popover.set_parent(cell)
        self.popover.popup()

    def hide(self):
        self.popover.popdown()
```

**Don't:**
```python
# Bad: per-cell popovers leak memory
def create_popover(self, cell):
    popover = Gtk.Popover()
    popover.set_parent(cell)
    popover.show()  # Wrong method for popovers
    return popover

# Bad: manual lifecycle control
def hide_popover(self):
    self.popover.unparent()  # Don't use unparent as lifecycle mechanism
```

**Rationale:**
- `popup()`/`popdown()` are the correct methods for popover visibility
- `unparent()` should not be used for lifecycle management
- Shared popovers reduce resource usage versus creating one per cell
- Connecting signals once on a shared popover prevents multiple connections

## Keyboard Focus and Popover Dismissal

Keyboard navigation is part of UX correctness. Focus restoration depends on how the popover was closed.

**Focus Restoration Rules:**
- Restore focus on **passive close**: user clicks outside, presses Escape, or closes via Done button
- Do NOT restore focus after **action buttons**: clicking a number or Clear (action has been taken)

**Do:**
```python
def _on_popover_closed(self, popover):
    # Check if closed via passive means (not action button)
    if not self._action_triggered:
        self._restore_focus_to_cell()
    self._action_triggered = False
```

**Implementation Notes:**
- Connect the close handler once on a shared popover
- Set a flag when action buttons are clicked to skip focus restoration
- Test keyboard flow: open popover, navigate, close via Escape, verify focus returns

## GTK Warning Handling

Do not suppress GTK warnings by default. Warnings often indicate real issues that should be investigated.

**Specific Guidance:**
- `Gtk-WARNING: Broken accounting of active state`: This is a known upstream GTK issue in some versions
- Do not add exception handlers to silence this warning
- Track it as an upstream bug and revisit when GTK updates
- A debug toggle can be added later if the logs become unusable

**Rationale:**
- Suppressing warnings hides real problems
- GTK warnings often point to API misuse or state corruption
- Let logs remain noisy until the root cause is understood

## Review Checklist

Before submitting a PR, verify:

- [ ] No `assert` statements in non-test code
- [ ] No bare `except Exception:` in changed files
- [ ] Popovers use `popup()`/`popdown()`, not `show()` or `unparent()`
- [ ] Focus behavior verified for keyboard flow after popover close
- [ ] Tests validate behavior rather than structure
- [ ] Exception handling is narrow and well-documented
- [ ] GTK warnings are not suppressed without clear justification

## Related Documents

- [CONTRIBUTING.md](CONTRIBUTING.md) - General contribution guidelines
- [README.md](README.md) - Project overview and features
