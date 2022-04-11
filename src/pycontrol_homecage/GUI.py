import sys
import os
from functools import partial

from pyqtgraph.Qt import QtGui

from pycontrol_homecage.main_gui import GUIApp
from pycontrol_homecage.loc_def import all_paths, create_paths
from pycontrol_homecage.utils import custom_excepthook


def initialise_excepthook():
    """Initialise a custom excepthook that prints errors to a log
       in addition to shutting down the program
    """
    pths__ = all_paths
    _, _, _, setup_dir, _, _, _, _ = pths__

    sys._excepthook = sys.excepthook

    exception_path = os.path.join(setup_dir, 'exception_store.txt')
    except_hook = partial(custom_excepthook, filepath=exception_path)
    sys.excepthook = except_hook


def main():
    app = QtGui.QApplication(sys.argv)
    gui = GUIApp()
    gui.app = app   # To allow app functions to be called from GUI.
    return app


if __name__ == "__main__":

    create_paths(all_paths)
    initialise_excepthook()

    app = main()
    sys.exit(app.exec_())
