import os
import sys
from unittest.mock import MagicMock


if os.environ.get("SUDOKU_FD_TEST") != "1":
    sys.modules["gi"] = MagicMock()
    sys.modules["gi.repository"] = MagicMock()
    sys.modules["gi.repository.Gtk"] = MagicMock()
    sys.modules["gi.repository.Gdk"] = MagicMock()
    sys.modules["gi.repository.GLib"] = MagicMock()
    sys.modules["gi.repository.Adw"] = MagicMock()
