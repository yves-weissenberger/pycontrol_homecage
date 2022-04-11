from pyqtgraph.Qt import QtGui

from pycontrol_homecage.new_experiment_menu import new_experiment_dialog
from pycontrol_homecage.tables import cageTable, experiment_overview_table
from pycontrol_homecage.plotting import Experiment_plot
import pycontrol_homecage.db as database


class system_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI = self.parent()
        self.plot_isactive = False

        self._init_user_groupbox()

        self._init_experiment_groupbox()

        self._init_setup_groupbox()

        self._init_log_groupbox()
        # ------------------------------------ #
        # -------- Vertical stacking  -------- #
        # ------------------------------------ #

        self._set_global_layout()

    def _init_user_groupbox(self):

        self.user_groupbox = QtGui.QGroupBox('Users')

        self.user_label = QtGui.QLabel()
        self.user_label.setText("Users")

        self.login_button = QtGui.QPushButton('Login')
        self.add_user_button = QtGui.QPushButton('Add User')
        self.logout_button = QtGui.QPushButton('Logout')

    def _set_user_layout(self) -> None:
        self.Hlayout_users = QtGui.QHBoxLayout()
        self.Hlayout_users.addWidget(self.login_button)
        self.Hlayout_users.addWidget(self.add_user_button)
        self.Hlayout_users.addWidget(self.logout_button)
        self.user_groupbox.setLayout(self.Hlayout_users)

    def _init_experiment_groupbox(self):

        self.experiment_groupbox = QtGui.QGroupBox("Experiments")
        self.scrollable_experiments = QtGui.QScrollArea()
        self.scrollable_experiments.setWidgetResizable(True)
        self.list_of_experiments = experiment_overview_table(only_active=True)
        self.scrollable_experiments.setWidget(self.list_of_experiments)

        self._init_experiment_buttons()

        self._set_experiment_layout()

    def _init_experiment_buttons(self):
        self.start_experiment_button = QtGui.QPushButton('Start New Experiment')
        self.start_experiment_button.clicked.connect(self.start_new_experiment)

        self.end_experiment_button = QtGui.QPushButton('End Experiment')
        self.end_experiment_button.clicked.connect(self.end_experiment)

    def _set_experiment_layout(self):
        self.Hlayout_exp_buttons = QtGui.QHBoxLayout()
        self.Hlayout_exp_buttons.addWidget(self.start_experiment_button)
        self.Hlayout_exp_buttons.addWidget(self.end_experiment_button)

        self.Vlayout_exp = QtGui.QVBoxLayout(self)
        self.Vlayout_exp.addLayout(self.Hlayout_exp_buttons)
        self.Vlayout_exp.addWidget(self.scrollable_experiments)

        self.experiment_groupbox.setLayout(self.Vlayout_exp)

    def _init_setup_groupbox(self) -> None:
        self.setup_groupbox = QtGui.QGroupBox("Setups")
        self.scrollable_setups = QtGui.QScrollArea()
        self.scrollable_setups.setWidgetResizable(True)
        self.list_of_setups = cageTable(self.GUI)
        self.scrollable_setups.setWidget(self.list_of_setups)

        # Buttons to control stuff
        self.show_setup_plot = QtGui.QPushButton('Show Plot')
        self.show_setup_plot.clicked.connect(self.activate_plot)
        self.filter_setup_combo = QtGui.QComboBox()
        self.filter_setup_combo.addItems(['Filter by'])

        self.setup_label = QtGui.QLabel()
        self.setup_label.setText("Setups")

        self._set_setup_layout()

    def _set_setup_layout(self) -> None:

        self.Hlayout_setup_buttons = QtGui.QHBoxLayout()
        self.Hlayout_setup_buttons.addWidget(self.show_setup_plot)
        self.Hlayout_setup_buttons.addWidget(self.filter_setup_combo)

        self.Vlayout_setup = QtGui.QVBoxLayout()
        self.Vlayout_setup.addLayout(self.Hlayout_setup_buttons)
        self.Vlayout_setup.addWidget(QtGui.QLabel("Table of Setups"))
        self.Vlayout_setup.addWidget(self.scrollable_setups)
        self.setup_groupbox.setLayout(self.Vlayout_setup)

    def _init_log_groupbox(self) -> None:
        self.log_groupbox = QtGui.QGroupBox("Log")

        self.log_active = QtGui.QCheckBox("Print to log")
        self.log_active.setChecked(True)

        self.filter_exp = QtGui.QCheckBox("Filter by experiment")
        self.filter_exp.setChecked(False)
        self.filter_setup = QtGui.QCheckBox("Filter by setup")
        self.filter_setup.setChecked(False)

        self.log_textbox = QtGui.QPlainTextEdit()
        self.log_textbox.setMaximumBlockCount(500)
        self.log_textbox.setFont(QtGui.QFont('Courier', 12))
        self.log_textbox.setReadOnly(True)
        self._set_log_layout()

    def _set_log_layout(self) -> None:

        self.log_hlayout = QtGui.QHBoxLayout()
        self.log_hlayout.addWidget(self.log_active)
        self.log_hlayout.addWidget(self.filter_exp)
        self.log_hlayout.addWidget(self.filter_setup)

        self.log_layout = QtGui.QVBoxLayout()
        self.log_layout.addLayout(self.log_hlayout)
        self.log_layout.addWidget(self.log_textbox)
        self.log_groupbox.setLayout(self.log_layout)

    def _set_global_layout(self) -> None:
        self.Vlayout = QtGui.QVBoxLayout(self)

        self.Vlayout.addWidget(self.user_groupbox)
        self.Vlayout.addWidget(self.experiment_groupbox)
        self.Vlayout.addWidget(self.setup_groupbox)
        self.Vlayout.addWidget(self.log_groupbox)

    def activate_plot(self):
        " start plotting incoming data from an experiment"

        if len(database.exp_df) > 0:  # check first if an experiment is running

            self.experiment_plot = Experiment_plot()

            experiment = {'subjects': {},
                          'sm_infos': {},
                          'handlers': {}
                          }
            # check which mice are training right now
            for _, row in database.setup_df.iterrows():
                if row['Mouse_training'] != 'none':
                    # k = str(len(experiment['subjects']))
                    experiment['subjects'][row['Setup_ID']] = row['Mouse_training']
                    handler_ = [setup for k, setup in database.controllers.items() if k == row['Setup_ID']][0]
                    experiment['sm_infos'][row['Setup_ID']] = handler_.PYC.sm_info
                    experiment['handlers'][row['Setup_ID']] = handler_

            self.experiment_plot.setup_experiment(experiment)

            self.experiment_plot.set_state_machines(experiment)

            for ix_, hKey in enumerate(sorted(experiment['handlers'].keys())):
                experiment['handlers'][hKey].data_consumers = [self.experiment_plot.subject_plots[ix_]]

            self.experiment_plot.show()
            self.experiment_plot.start_experiment()
            self.plot_isactive = True

    def start_new_experiment(self) -> None:
        """ This creates a new experiment which refers to a cohort of mice
            performing a set of tasks.
        """
        self.new_experiment_config = new_experiment_dialog(self.GUI)
        self.new_experiment_config.exec_()

    def end_experiment(self):

        selected_experiments = self.list_of_experiments.get_checked_experiments()
        if selected_experiments:
            self.list_of_experiments.end_experiments(selected_experiments)

        self.list_of_experiments.fill_table()

        self.GUI.experiment_tab.list_of_experiments.fill_table()
        self.GUI.setup_window_tab.list_of_setups.fill_table()

    def write_to_log(self, msg, from_sys=None):

        if self.log_active.isChecked():
            if type(msg) == str:
                if 'Wbase' not in msg:
                    self.log_textbox.moveCursor(QtGui.QTextCursor.End)
                    self.log_textbox.insertPlainText(msg + '\n')
                    self.log_textbox.moveCursor(QtGui.QTextCursor.End)
            elif type(msg) == list:
                for msg_ in msg:
                    if 'Wbase' not in msg:
                        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
                        self.log_textbox.insertPlainText(str(msg_) + '\n')
                        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        else:
            pass

    def _refresh(self):
        pass