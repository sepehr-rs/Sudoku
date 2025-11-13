from gi.repository import Gtk, Adw
from gettext import gettext as _

EASY_DIFFICULTY = 0.2
MEDIUM_DIFFICULTY = 0.5
HARD_DIFFICULTY = 0.7
EXTREME_DIFFICULTY = 0.9


class GameSetupDialog(Adw.Dialog):
    def __init__(self, on_select, **kwargs):
        super().__init__(**kwargs)
        self.set_title(_("New Game"))
        self.set_content_width(410)
        self.set_content_height(490)

        self.on_select = on_select
        self.selected_variant = "classic"
        self.selected_difficulty = EASY_DIFFICULTY
        self._radio_groups = {}

        toolbar_view = Adw.ToolbarView.new()
        toolbar_view.add_top_bar(Adw.HeaderBar())

        main_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=16,
            margin_top=12,
            margin_start=12,
            margin_end=12,
            margin_bottom=12,
        )

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_child(main_box)
        toolbar_view.set_content(scroll)

        variant_list = Gtk.ListBox()
        variant_list.add_css_class("boxed-list")
        main_box.append(variant_list)
        self._create_radio_list(
            variant_list,
            [(_("Classic Sudoku"), "classic"), (_("Diagonal Sudoku"), "diagonal")],
            "variant",
            self.selected_variant,
        )

        difficulty_list = Gtk.ListBox()
        difficulty_list.add_css_class("boxed-list")
        main_box.append(difficulty_list)
        self._create_radio_list(
            difficulty_list,
            [
                (_("Easy"), EASY_DIFFICULTY),
                (_("Medium"), MEDIUM_DIFFICULTY),
                (_("Hard"), HARD_DIFFICULTY),
                (_("Extreme"), EXTREME_DIFFICULTY),
            ],
            "difficulty",
            self.selected_difficulty,
        )

        btn = Gtk.Button(label=_("Start Game"))
        btn.add_css_class("pill")
        btn.add_css_class("suggested-action")
        btn.set_halign(Gtk.Align.CENTER)
        btn.set_hexpand(False)
        btn.connect("clicked", self._on_confirm_clicked)
        main_box.append(btn)
        self.connect("realize", lambda *_: self.set_focus(btn))
        self.set_child(toolbar_view)

    def _create_radio_list(self, listbox, items, group_name, default=None):
        self._radio_groups[group_name] = []
        group = None
        for label, value in items:
            btn = Gtk.CheckButton()
            btn.add_css_class("radio")
            if group:
                btn.set_group(group)
            else:
                group = btn
            if value == default:
                btn.set_active(True)
            btn.connect("toggled", self._on_radio_toggled, group_name, value)

            row = Adw.ActionRow(title=label)
            row.add_prefix(btn)
            row.connect("activated", lambda _r, b=btn: b.set_active(True))
            row.set_activatable_widget(btn)
            listbox.append(row)
            self._radio_groups[group_name].append(btn)

    def _on_radio_toggled(self, button, group_name, value):
        if button.get_active():
            setattr(self, f"selected_{group_name}", value)

    def _on_confirm_clicked(self, _):
        self.on_select(self.selected_variant, self.selected_difficulty)
        self.close()
