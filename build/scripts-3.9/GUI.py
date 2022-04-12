import sys
import os
from functools import partial

from pyqtgraph.Qt import QtGui

from pycontrol_homecage.main_gui import GUIApp
from pycontrol_homecage.utils.loc_def import all_paths, create_paths
from pycontrol_homecage.utils import custom_excepthook


def initialise_excepthook() -> None:
    """Initialise a custom excepthook that prints errors to a log
       in addition to shutting down the program
    """
    print(all_paths)
    _, _, _, setup_dir, _, _, _, _ = all_paths

    sys._excepthook = sys.excepthook

    exception_path = os.path.join(setup_dir, 'exception_store.txt')
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
