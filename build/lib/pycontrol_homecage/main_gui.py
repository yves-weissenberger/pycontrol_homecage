import os

from pyqtgraph.Qt import QtGui, QtCore

from pycontrol_homecage.gui_tabs import mouse_tab
from pycontrol_homecage.gui_tabs import setups_tab
from pycontrol_homecage.gui_tabs import protocol_tab
from pycontrol_homecage.gui_tabs import system_tab
from pycontrol_homecage.gui_tabs import experiment_tab
from pycontrol_homecage.dialogs import login_dialog, add_user_dialog
import pycontrol_homecage.db as database


class GUIApp(QtGui.QMainWindow):

    def __init__(self):
        super().__init__()

        self.GUI_filepath = os.path.dirname(os.path.abspath(__file__))
        self.app = None  # Overwritten with QtGui.QApplication instance in main.
        self.active_user = None

        database.setup_df['connected'] = False

        self._init_tabs()
        self._add_tabs_to_widget()
        self._disable_gui_pre_login()

        self.login = login_dialog()
        self.add_user = add_user_dialog()

        self.system_tab.login_button.clicked.connect(self.change_user)
        self.system_tab.add_user_button.clicked.connect(self.add_user_)
        self.system_tab.logout_button.clicked.connect(self.logout_user)

        self.setGeometry(10, 30, 700, 800)   # Left, top, width, height.
        self.setCentralWidget(self.tab_widget)
        self.show()

        self._init_timer()
        self.refresh()    # Refresh tasks and ports lists.

    def _init_tabs(self) -> None:
        self.mouse_tab = mouse_tab(self)
        self.setup_tab = setups_tab(self)
        self.protocol_tab = protocol_tab(self)
        self.system_tab = system_tab(self)
        self.experiment_tab = experiment_tab(self)

    def _add_tabs_to_widget(self) -> None:
        self.tab_widget = QtGui.QTabWidget(self)
        self.tab_widget.addTab(self.system_tab, 'System Overview')
        self.tab_widget.addTab(self.experiment_tab, 'Experiments')
        self.tab_widget.addTab(self.mouse_tab, 'Mouse Overview')
        self.tab_widget.addTab(self.setup_tab, 'Setup Overview')
        self.tab_widget.addTab(self.protocol_tab, 'Protocols')

    def _disable_gui_pre_login(self) -> None:
        self.mouse_tab.setEnabled(False)
        self.setup_tab.setEnabled(False)
        self.protocol_tab.setEnabled(False)
        self.system_tab.setup_groupbox.setEnabled(False)
        self.system_tab.log_groupbox.setEnabled(False)
        self.system_tab.experiment_groupbox.setEnabled(False)
        self.experiment_tab.setEnabled(False)

    def _init_timer(self) -> None:
        # Timer to regularly call refresh() when not running.
        self.refresh_timer = QtCore.QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(100)

    def refresh(self) -> None:
        for k, SC in database.controllers.items():
            SC.check_for_data()

            if self.system_tab.plot_isactive:
                self.system_tab.experiment_plot.update()

        self.setup_tab._refresh()
        self.system_tab._refresh()
        self.experiment_tab._refresh()
        self.mouse_tab._refresh()
        self.protocol_tab._refresh()

    def change_user(self) -> None:
        self.login.exec_()
        self.active_user = self.login.userID
        if self.active_user:
            self.setWindowTitle('Logged in as {}'.format(self.active_user))
            self.mouse_tab.setEnabled(True)
            self.setup_tab.setEnabled(True)
            self.protocol_tab.setEnabled(True)
            self.system_tab.setup_groupbox.setEnabled(True)
            self.system_tab.log_groupbox.setEnabled(True)
            self.system_tab.experiment_groupbox.setEnabled(True)
            self.experiment_tab.setEnabled(True)

    def print_msg(self, msg: str, ac_pyc: str = None, setup_ID=None) -> None:
        self.system_tab.write_to_log(msg)
        if ac_pyc == 'pyc':
            pass

    def add_user_(self) -> None:
        self.add_user.exec_()
        self.login = login_dialog()

    def logout_user(self):
        self.active_user = None
        self.setWindowTitle('Not logged in')
        self.mouse_tab.setEnabled(False)
        self.setup_tab.setEnabled(False)
        self.protocol_tab.setEnabled(False)
        self.system_tab.setup_groupbox.setEnabled(False)
        self.system_tab.log_groupbox.setEnabled(False)
        self.system_tab.experiment_groupbox.setEnabled(False)
        self.system_tab.user_groupbox.setEnabled(True)
        self.experiment_tab.setEnabled(False)

    def _reset_tables(self):
        self.system_tab.list_of_experiments.fill_table()
        self.system_tab.list_of_setups.fill_table()
        self.experiment_tab.list_of_experiments.fill_table()
        self.mouse_tab.list_of_mice.fill_table()
        self.setup_tab.list_of_setups.fill_table()
