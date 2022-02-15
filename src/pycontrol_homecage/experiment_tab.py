from typing import List, Optional

import pandas as pd
from pyqtgraph.Qt import QtGui


from pycontrol_homecage.tables import experiment_overview_table
from pycontrol_homecage.dialogs import are_you_sure_dialog
import pycontrol_homecage.db as database


class experiment_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI = self.parent()

        self._setup_buttons()
        self._set_button_layout()
        self.list_of_experiments = experiment_overview_table(GUI=self.GUI, only_active=False)

        self._set_global_layout()

    def _setup_buttons(self) -> None:
        self.new_experiment_button = QtGui.QPushButton('Start new Experiment')
        self.restart_experiment_button = QtGui.QPushButton('Restart Experiment')
        self.restart_experiment_button.clicked.connect(self.restart_experiment)
        self.stop_experiment_button = QtGui.QPushButton('Stop Experiment')
        self.stop_experiment_button.clicked.connect(self.stop_experiment)

    def _set_button_layout(self) -> None:
        self.Hlayout = QtGui.QHBoxLayout()
        self.Hlayout.addWidget(self.new_experiment_button)
        self.Hlayout.addWidget(self.restart_experiment_button)
        self.Hlayout.addWidget(self.stop_experiment_button)

    def _set_global_layout(self) -> None:
        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addLayout(self.Hlayout)
        self.Vlayout.addWidget(self.list_of_experiments)

    def restart_experiment(self) -> None:
        """ Restart an experiment that is currently active that was running before """

        selected_experiment = self._get_experiment_check_status()

        if selected_experiment:
            sure = are_you_sure_dialog()
            sure.exec_()
            if sure.GO:
                exp_row = database.exp_df.loc[database.exp_df.exp_df['Name'] == selected_experiment]

                self._update_experiment_status(selected_experiment, True)

                mice_in_experiment = self._get_mice_in_experiment(exp_row)
                setups = self._get_setups_in_experiment(exp_row)

                self._update_mice(mice_in_exp=mice_in_experiment, assigned=True)
                self._update_setups(setups_in_exp=setups, experiment=selected_experiment)

                self._reset_tables()

    def stop_experiment(self):

        selected_experiment = self._get_experiment_check_status()

        # cannot abort multiple experiments simultaneously
        if selected_experiment:

            sure = are_you_sure_dialog()
            sure.exec_()
            if sure.GO:
                exp_row = database.exp_df.loc[database.exp_df['Name'] == selected_experiment]
                self._update_experiment_status(selected_experiment, False)

                mice_in_experiment = self._get_mice_in_experiment(exp_row)
                setups = self._get_setups_in_experiment(exp_row)

                self._update_mice(mice_in_exp=mice_in_experiment)
                self._update_setups(setups_in_exp=setups, experiment=None)

            self._reset_tables()

    def _update_experiment_status(self, experiment_name: str, status: bool) -> None:
        database.exp_df.loc[database.exp_df['Name'] == experiment_name, 'Active'] = status

    def _get_mice_in_experiment(self, exp_row: pd.Series) -> List[str]:
        return eval(exp_row['Subjects'].values[0])

    def _get_setups_in_experiment(self, exp_row: pd.Series) -> List[str]:
        # setups = eval(exp_row['Setups'].values[0].replace(' ',',')) this may be better
        return eval(exp_row['Setups'].values[0])

    def _get_experiment_check_status(self) -> Optional[str]:
        isChecked = []
        checked_ids = []
        name_col = self.list_of_experiments.header_names.index("Name")

        for row in range(self.list_of_experiments.rowCount()):
            checked = self.list_of_experiments.item(row, 0).checkState() == 2
            if checked:
                checked_ids.append(self.list_of_experiments.item(row, name_col).text())
                isChecked.append(checked)

        return checked_ids[0] if checked_ids else None

    def _reset_tables(self):
        self.GUI.system_tab.list_of_experiments.fill_table()
        self.GUI.system_tab.list_of_setups.fill_table()

        self.GUI.experiment_tab.list_of_experiments.fill_table()
        self.GUI.mouse_window_tab.list_of_mice.fill_table()
        self.GUI.setup_window_tab.list_of_setups.fill_table()

    def _update_mice(self, mice_in_exp: List[str], assigned: bool = False):

        for mouse in mice_in_exp:

            database.mouse_df.loc[database.mouse_df['Mouse_ID'] == mouse, 'is_assigned'] = assigned
            database.mouse_df.loc[database.mouse_df['Mouse_ID'] == mouse, 'in_system'] = assigned
            database.mouse_df.to_csv(database.mouse_df.file_location)

    def _update_setups(self, setups_in_exp, experiment=None):
        for setup in setups_in_exp:
            database.setup_df.loc[database.setup_df['Setup_ID'] == setup, 'Experiment'] = experiment
            # this is what is checked in the new experiment dialog
            database.setup_df.loc[database.setup_df['Setup_ID'] == setup, 'in_use'] = experiment is not None
            database.setup_df.to_csv(database.setup_df.file_location)

    def _refresh(self):
        pass

    def _get_checks(self, table):
        pass
