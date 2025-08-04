from gi.repository import Gtk


class HowToPlayDialog(Gtk.Dialog):
    def __init__(self, parent):
        super().__init__(title="How to Play Sudoku", transient_for=parent, modal=True)
        self.set_default_size(500, 400)

        content_area = self.get_content_area()
        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.set_vexpand(True)

        content_area.append(scrolled_window)

        textview = Gtk.TextView()
        textview.get_style_context().add_class("sudoku-dialog")
        textview.set_editable(False)
        textview.set_cursor_visible(False)
        textview.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        textview.set_margin_top(10)
        textview.set_margin_bottom(10)
        textview.set_margin_start(10)
        textview.set_margin_end(10)

        instructions = (
            "Welcome to Sudoku!\n\n"
            "The goal is to fill the grid so that every row, column, "
            "and 3x3 box contains the numbers 1 through 9 without repeats.\n\n"
            "How to play:\n"
            "- Click on an empty cell to select it.\n"
            "- Use your keyboard or pencil tool to input a number.\n"
            "- Use the pencil tool to make notes.\n"
            "- Use the backspace key to clear a cell.\n"
            "- Try to solve the puzzle logically.\n\n"
            "Good luck and have fun!"
        )
        buffer = textview.get_buffer()
        buffer.set_text(instructions)

        scrolled_window.set_child(textview)

        self.add_buttons("OK", Gtk.ResponseType.OK)
