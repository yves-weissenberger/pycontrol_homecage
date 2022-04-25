import sys
import os
from functools import partial

from pyqtgraph.Qt import QtGui

import pycontrol_homecage.db as database
from pycontrol_homecage.main_gui import GUIApp
from pycontrol_homecage.utils import custom_excepthook


def initialise_excepthook() -> None:
    """Initialise a custom excepthook that prints errors to a log
       in addition to shutting down the program
    """


    sys._excepthook = sys.excepthook

    exception_path = os.path.join(database.paths["setup_dir"], 'exception_store.txt')
    except_hook = partial(custom_excepthook, filepath=exception_path)
    sys.excepthook = except_hook


def main() -> None:
    app = QtGui.QApplication(sys.argv)
    gui = GUIApp()
    gui.app = app   # To allow app functions to be called from GUI.
    return app


if __name__ == "__main__":

    create_paths(all_paths)
    initialise_excepthook()

    app = main()
    sys.exit(app.exec_())
