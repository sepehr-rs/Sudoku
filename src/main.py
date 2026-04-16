# SPDX-License-Identifier: GPL-3.0-or-later

import sys

from .application import SudokuApplication
from .log_utils import setup_logging


def main(version):
    setup_logging(version)
    app = SudokuApplication(version)
    return app.run(sys.argv)
