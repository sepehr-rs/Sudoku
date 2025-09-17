# src/base/ui_helpers.py
from gi.repository import Gtk, Gdk

class UIHelpers:
    @staticmethod
    def create_number_button(label: str, callback, *args):
        button = Gtk.Button(label=label)
        button.set_size_request(40, 40)
        button.connect("clicked", callback, *args)
        return button

    @staticmethod
    def setup_key_mappings():
        key_map = {getattr(Gdk, f"KEY_{i}"): str(i) for i in range(1, 10)}
        key_map.update({getattr(Gdk, f"KEY_KP_{i}"): str(i) for i in range(1, 10)})
        remove_keys = (Gdk.KEY_BackSpace, Gdk.KEY_Delete, Gdk.KEY_KP_Delete)
        return key_map, remove_keys
