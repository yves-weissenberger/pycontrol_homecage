import os
import time
from functools import partial
from typing import List, Optional

import numpy as np
from pyqtgraph import Qt
from pyqtgraph.Qt import QtCore, QtGui
from serial import SerialException
import pandas as pd

from pycontrol_homecage.com.access_control import Access_control
##### TA code imports
from pycontrol_homecage.com.pycboard import PyboardError, Pycboard, _djb2_file
# from com.data_logger import Data_logger
from pycontrol_homecage.com.system_handler import system_controller
from pycontrol_homecage.dialogs import calibrate_dialog
from pycontrol_homecage.utils import (TableCheckbox, cbox_set_item, cbox_update_options,
                                      find_setups, get_tasks, null_resize)
import pycontrol_homecage.db as database

# ######################################################################
# ###################      Experiment Table      #######################
# ######################################################################


class variables_table(QtGui.QTableWidget):
    " Table that tracks what variables a mouse currently running in a task has"

    def __init__(self, parent = None):
        super(QtGui.QTableWidget, self).__init__(1, 7, parent=parent)
        self.setHorizontalHeaderLabels(['Variable', 'Subject', 'Value', 'Persistent', 'Summary', 'Set', ''])
        self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(5, QtGui.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)
        add_button = QtGui.QPushButton('   add   ')
        self.setCellWidget(0, 5, add_button)
        self.n_variables = 0
        self.variable_names = []
        self.available_variables = []
        self.assigned = {v_name: [] for v_name in self.variable_names}  # Which subjects have values assigned for each variable.
        self.subject_variable_names = {}

    def remove_variable(self, variable_n: int) -> None:
        self.removeRow(variable_n)
        self.n_variables -= 1
        self.update_available()
        null_resize(self)

    def reset(self):
        '''Clear all rows of table.'''
        for i in reversed(range(self.n_variables)):
            self.removeRow(i)
        self.n_variables = 0
        self.assigned = {v_name: [] for v_name in self.variable_names} 

    def add_variable(self, var_dict: dict = None) -> None:

        '''Add a row to the variables table.'''
        variable_cbox = QtGui.QComboBox()
        variable_cbox.activated.connect(self.update_available)
        subject_cbox = QtGui.QComboBox()
        subject_cbox.activated.connect(self.update_available)
        persistent = TableCheckbox()
        summary = TableCheckbox()
        set_var = TableCheckbox()
        
        set_var.checkbox.stateChanged.connect(partial(self.setVar_changed, self.n_variables))
        persistent.checkbox.stateChanged.connect(partial(self.persistent_changed, self.n_variables))
        remove_button = QtGui.QPushButton('remove')
        ind = QtCore.QPersistentModelIndex(self.model().index(self.n_variables, 2))
        remove_button.clicked.connect(lambda :self.remove_variable(ind.row()))
        add_button = QtGui.QPushButton('   add   ')
        add_button.clicked.connect(self.add_variable)
        self.insertRow(self.n_variables+1)
        self.setCellWidget(self.n_variables  ,0, variable_cbox)
        self.setCellWidget(self.n_variables  ,1, subject_cbox)
        self.setCellWidget(self.n_variables  ,3, persistent)
        self.setCellWidget(self.n_variables  ,4, summary)
        self.setCellWidget(self.n_variables  ,5, set_var)
        self.setCellWidget(self.n_variables  ,6, remove_button)
        self.setCellWidget(self.n_variables+1,6, add_button)
        if var_dict: # Set cell values from provided dictionary.
            variable_cbox.addItems([var_dict['name']])
            subject_cbox.addItems([var_dict['subject']])
            value_item = QtGui.QTableWidgetItem()
            value_item.setText(var_dict['value'])
            self.setItem(self.n_variables, 2, value_item)
            persistent.setChecked(var_dict['persistent'])
            summary.setChecked(var_dict['summary'])
            set_var.setChecked(var_dict['set'])
        else:
            variable_cbox.addItems(['select variable']+self.available_variables)
            if self.n_variables > 0: # Set variable to previous variable if available.
                v_name = str(self.cellWidget(self.n_variables-1, 0).currentText())
                if v_name in self.available_variables:
                    cbox_set_item(variable_cbox, v_name)
                    subject_cbox.addItems(self.available_subjects(v_name))
        self.n_variables += 1
        self.update_available()
        null_resize(self)
    
    def persistent_changed(self, row: int) -> None:
        """ A variables cannot be both persistent and set"""
        #print("updateing",row)
        self.cellWidget(row,5).setChecked(False)
        self.item(row,2).setText("auto")

    def setVar_changed(self, row: int) -> None:
        self.cellWidget(row, 3).setChecked(False)

    def update_available(self, i=None):
        # Find out what variable-subject combinations already assigned.
        self.assigned = {v_name: [] for v_name in self.variable_names}

        # to maintain consistency with main pycontrol, the way this works
        # is by setting variables assigned that 
        for v_name in self.variable_names:
            for subject, vars_ in self.subject_variable_names.items():

                if v_name not in vars_:
                    self.assigned[v_name].append(subject)

        # print(self.assigned)
        for v in range(self.n_variables):
            v_name = self.cellWidget(v, 0).currentText()
            s_name = self.cellWidget(v, 1).currentText()
            if s_name and s_name not in self.subjects_in_group + ['all']:
                cbox_set_item(self.cellWidget(v, 1), '', insert=True)
                continue
            if v_name != 'select variable' and s_name:
                self.assigned[v_name].append(s_name)
        # Update the variables available:
        fully_asigned_variables = [v_n for v_n in self.assigned.keys()
                                   if 'all' in self.assigned[v_n]]
        if self.subjects_in_group:
            fully_asigned_variables += [v_n for v_n in self.assigned.keys()
                                        if set(self.assigned[v_n]) == set(self.subjects_in_group)]
        self.available_variables = sorted(list(
            set(self.variable_names) - set(fully_asigned_variables)), key=str.lower)
        # Update the available options in the variable and subject comboboxes.

        for v in range(self.n_variables):
            v_name = self.cellWidget(v, 0).currentText()
            s_name = self.cellWidget(v, 1).currentText()
            cbox_update_options(self.cellWidget(v, 0), self.available_variables)
            if v_name != 'select variable':
                # If variable has no subjects assigned, set subjects to 'all'.
                if not self.assigned[v_name]:
                    self.cellWidget(v, 1).addItems(['all'])
                    self.assigned[v_name] = ['all']
                    self.available_variables.remove(v_name)
                cbox_update_options(self.cellWidget(v, 1), self.available_subjects(v_name, s_name))

    def set_available_subjects(self, subjects: List[str]):
        self.subjects_in_group = subjects

    def set_variable_names(self, variable_names: List[str]):
        """ """
        if not self.variable_names:
            self.variable_names = variable_names
        else:
            # print(self.variable_names,variable_names)
            self.variable_names.extend(variable_names)
            self.variable_names = list(set(self.variable_names))

    def set_variable_names_by_subject(self, subject: str, variable_names: List[str]) -> None:
        """ Allow tracking of which subject has which variables available
            to them in principle
        """
        self.subject_variable_names[subject] = variable_names

    def available_subjects(self, v_name, s_name=None):
        '''Return sorted list of the subjects that are available for selection
        for the specified variable v_name given that subject s_name is already
        selected.'''
        if (not self.assigned[v_name]) or self.assigned[v_name] == [s_name]:
            available_subjects = ['all'] + sorted(self.subjects_in_group)
        else:
            available_subjects = sorted(list(set(self.subjects_in_group) -
                                             set(self.assigned[v_name])))
        return available_subjects

    def variables_list(self):
        '''Return the variables table contents as a list of dictionaries.'''
        return [{'name'  : str(self.cellWidget(v, 0).currentText()),
                 'subject'   : str(self.cellWidget(v, 1).currentText()),
                 'value'     : str(self.item(v, 2).text()) if self.item(v, 2) else '',
                 'persistent': self.cellWidget(v, 3).isChecked(),
                 'summary'   : self.cellWidget(v, 4).isChecked(),
                 'set'       : self.cellWidget(v, 5).isChecked()}
                 for v in range(self.n_variables)]


class experiment_overview_table(QtGui.QTableWidget):
    " Table for system tab that shows all experiments currently running"

    def __init__(self, only_active: bool = False, parent=None):

        super(QtGui.QTableWidget, self).__init__(1, 7, parent=parent)

        self.header_names = ['Select', 'Name', 'Setups', 'User', 
                             'Active', 'Protocol', 'Subjects',
                             'n_subjects'
                             ]
        self._set_headers()
        self.only_active = only_active

        self.fill_table()

    def _set_headers(self):

        self.setHorizontalHeaderLabels(self.header_names)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        self.select_col_ix = self.header_names.index("Select")

    def fill_table(self):

        self.clearContents()
        if self.only_active:
            self.setRowCount(sum(database.exp_df['Active']))
        else:
            self.setRowCount(len(database.exp_df))

        self.buttons = []
        row_index = 0
        for _, row in database.exp_df.iterrows():
            if ((not self.only_active) or (self.only_active and row['Active'])):
                for col_index in range(self.columnCount()):

                    try:
                        cHeader = self.header_names[col_index]

                        self.setItem(row_index, col_index, Qt.QtWidgets.QTableWidgetItem(str(row[cHeader])))
                    except KeyError:
                        pass

                chkBoxItem = QtGui.QTableWidgetItem()
                chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
                self.setItem(row_index, self.select_col_ix, chkBoxItem)
                row_index += 1

    def get_checked_experiments(self) -> List[str]:
        """Check which experiments the user has checked

        Returns:
            List[str]: Names of selected experiments
        """
        selected_experiments = []
        for rowN in range(self.rowCount()):
            if self(rowN, 0).checkState() == 2:  # 2 is checked state
                expName = self.item(rowN, self.header_names.index('Name')).text()
                selected_experiments.append(expName)

        return selected_experiments

    def end_experiments(self, experiment_names: List[str]) -> None:
        """ End experiment by switching off handlers for relevant setups, closing files and updating setup, experiment
            databases.

        Args:
            experiment_names (List[str]): names of experiments to be ended
        """
        for exp_name in experiment_names:
            for setup in database.exp_df.loc[database.exp_df['Name'] == exp_name, 'Setups'].values:
                setup = eval(setup)[0]

                if database.controllers.items():  # if there are any controllers
                    print(exp_name)
                    handler_ = [setup_ for k, setup_ in database.controllers.items() if k == setup][0]

                    handler_.PYC.stop_framework()
                    time.sleep(.05)
                    handler_.PYC.process_data()
                    handler_.close_files()
                    handler_.PYC.reset()

                    database.exp_df.loc[database.exp_df['Name'] == exp_name, 'Active'] = False
                    database.setup_df.loc[database.setup_df['Setup_ID'] == setup, 'Experiment'] = None
                    database.setup_df.to_csv(database.setup_df.file_location)
                    database.exp_df.to_csv(database.exp_df.file_location)

                    print("CLOSED")

                for subject in eval(database.exp_df.loc[database.exp_df['Name'] == exp_name, 'Subjects'].values[0]):
                    database.mouse_df.loc[database.mouse_df['Mouse_ID'] == subject, 'in_system'] = False

# ######################################################################
# ##############      For setting up a new protocol      ###############
# ######################################################################
class protocol_table(QtGui.QTableWidget):

    def __init__(self, GUI, tab, nRows=None, parent=None):

        super(QtGui.QTableWidget, self).__init__(1, 6, parent=parent)
        self.set_headers()
        if nRows:
            self.setRowCount(nRows)
            self.nRows = nRows
            #self.horizontalHeader().setSectionResizeMode(1)
        else:
            self.nRows = 1

    def set_headers(self):

        self.header_names = ['Stage','Task','Tracked','Threshold(s)','Default(s)','Delete']
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        self.set_resizemode_for_headers()
    
    def set_resizemode_for_headers(self):
        for h_ix in range(len(self.header_names)-1):
            self.horizontalHeader().setResizeMode(h_ix, QtGui.QHeaderView.Stretch)

    def fill_table(self, dat):
        " Here pass prot_dict"

        self.nRows = len(dat)

        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        for i in range(1, len(self.header_names)-1):
            self.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)

        if self.nRows:
            self.setRowCount(self.nRows)

        for k in dat.keys():
            self.fill_row(dat[k], row=int(k))

    def fill_row(self, dat, row=None):
        "Here pass "

        if not row:
            row = 0
            self.reset_()

        for k in dat.keys():
            if ('thresh' in k) or ('default' in k):
                Vtmp = Qt.QtWidgets.QTableWidgetItem(self._translate(dat[k]))
            else:
                Vtmp = Qt.QtWidgets.QTableWidgetItem(str(dat[k]))

            if k == 'threshV':
                self.setItem(row, self.header_names.index('Threshold(s)'), Vtmp)
            elif k == 'defaultV':
                self.setItem(row, self.header_names.index('Default(s)'), Vtmp)
            elif k == 'trackV':
                self.setItem(row, self.header_names.index('Tracked'), Vtmp)
            elif k == 'stage_nr':
                self.setItem(row, self.header_names.index('Stage'), Vtmp)
            elif k == 'task':
                self.setItem(row, self.header_names.index('Task'), Vtmp)

        self.resizeRowToContents(row)

    def _translate(self, x):
        ret = ''
        if len(x):
            for x_ in x:
                ret = ret + str(x_[0]) + ': ' + str(x_[1]) + '\n'
        return ret

    def reset_(self):

        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)

        for i in range(1, len(self.header_names)-1):
            self.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)

        if self.nRows:
            self.setRowCount(self.nRows)

#######################################################################
##############      For setting up a new experiment      ##############
#######################################################################


class cage_list_table(QtGui.QTableWidget):

    def __init__(self, GUI, tab,parent=None):
        super(QtGui.QTableWidget, self).__init__(1,12, parent=parent)
        self.header_names = ['Show mice','Shared Protocol','Protocol',
                             'COM','COM_AC','Setup_ID',
                             'in_use','connected','User','Experiment',
                             'Protocol','Mouse_training','Door','n_mice']


        self.GUI = GUI
        self.tab = tab

        self.share_task_in_setup = []

        self.setHorizontalHeaderLabels(self.header_names)
        self.verticalHeader().setVisible(False)
        #self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(Qt.QtWidgets.QTableView.SelectRows)
        self.cellChanged.connect(self.show_mice_in_setup)

        self.selected_setups = []

    def run_task(self):
        ""
        setup,task = self.sender().name

        board_ix = [i for i,brd in enumerate(self.GUI.connected_boards) if brd.serial_port==setup]

        self.task_hash = _djb2_file(os.path.join(self.GUI.GUI_filepath,'tasks', task + '.py'))
        self.GUI.connected_boards[int(board_ix[0])].setup_state_machine(task, uploaded=False)
        self.GUI.connected_boards[int(board_ix[0])].start_framework()


    def fill_table(self):

        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        self.setRowCount(len(self.tab.df_setup_tmp))
        
        for row_index, row in self.tab.df_setup_tmp.iterrows():
            self.share_task_in_setup.append(False)    

            for col_index in range(self.columnCount()-3):

                self.setItem(row_index,col_index+3,Qt.QtWidgets.QTableWidgetItem(str(row[col_index])))


            ## These should be set just as one for each column
            chkBoxItem = QtGui.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)
            self.setItem(row_index,0,chkBoxItem)


            chkBoxItem = QtGui.QTableWidgetItem()
            if self.tab.global_task:

                chkBoxItem.setFlags(QtCore.Qt.ItemIsEnabled)
            else:
                chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                chkBoxItem.setCheckState(QtCore.Qt.Unchecked)

            self.setItem(row_index,1,chkBoxItem)


            protocols = QtGui.QComboBox()

            self.available_tasks = get_tasks(database.paths['task_dir'])
            protocols.addItems(['Select Task'] + self.available_tasks)
            protocols.setEnabled(False)
            #QtGui.QTableWidgetItem()
            if self.tab.global_task:
                protocols.setEnabled(False)
                protocols.clear()
                protocols.addItems([self.tab.protocol_combo.currentText()])

                self.tab.mouse_prot.clear()
                self.tab.mouse_prot.addItems([self.tab.protocol_combo.currentText()])


            self.setCellWidget(row_index,2,protocols)





        self.selected_setups = []


    def show_mice_in_setup(self,row,col):
        #row = item.row()

        item = self.item(row, col)

        if col==1:
            if item.checkState()==2:
                if self.cellWidget(row,2) is not None:
                    self.cellWidget(row,2).setEnabled(True)
                    self.share_task_in_setup[row] = True
                    self.tab.mouse_prot.setEnabled(False)
                    self.tab.mouse_prot.clear()
                    self.tab.mouse_prot.addItems([self.cellWidget(row,2).currentText()])
            elif item.checkState()==0:
                if self.cellWidget(row,2) is not None:
                    self.cellWidget(row,2).setEnabled(False)
                    self.share_task_in_setup[row] = False
                    self.tab.mouse_prot.clear()
                    self.tab.mouse_prot.addItems(['Select Task'] + self.tab.available_tasks)
                    self.tab.mouse_prot.setEnabled(True)
        else:

            if col==0:
                if item.checkState()==2:
                    self.selected_setups.append(self.item(row,5).text())
                    if self.share_task_in_setup[row]:
                        self.tab.mouse_prot.setEnabled(False)
                        self.tab.mouse_prot.clear()
                        self.tab.mouse_prot.addItems([self.cellWidget(row,2).currentText()])

                if item.checkState()==0:
                    self.selected_setups = [i for i in self.selected_setups if i!=self.item(row,5).text()]
            
            if len(self.selected_setups)>0:
                self.tab.MICE.setEnabled(True)
                self.tab.add_mouse_button.setEnabled(True)

            else:
                self.tab.MICE.setEnabled(False)

            if len(self.selected_setups)>1:

                self.tab.add_mouse_button.setEnabled(False)

        self.tab.MLT.fill_table()



class mouse_list_table(QtGui.QTableWidget):
    """ This table contains information about all mice currently running in the
        system """
    def __init__(self, tab, GUI,parent=None):
        super(QtGui.QTableWidget, self).__init__(1,17, parent=parent)
        self.header_names = ['','Mouse_ID', 'RFID', 'Sex', 'Age', 'Experiment', 'Protocol','Stage','Task', 'User', 
                            'Start_date', 'Current_weight', 'Start_weight', 'is_training',
                            'is_assigned', 'training_log', 'Setup_ID']

        self.GUI = GUI
        self.tab = tab
        self.setHorizontalHeaderLabels(self.header_names)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        self.fill_table()

    def fill_table(self):

        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        df = self.tab.df_mouse_tmp.loc[self.tab.df_mouse_tmp['Setup_ID'].isin(self.tab.CLT.selected_setups)]
        df.index = np.arange(len(df))

        df.reset_index(drop=True)
        self.setRowCount(len(df))

        for row_index, row in df.iterrows():    

            for col_index in range(self.columnCount()-1):

                self.setItem(row_index,col_index+1,Qt.QtWidgets.QTableWidgetItem(str(row[col_index])))

            chkBoxItem = QtGui.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)   
            self.setItem(row_index,0,chkBoxItem)
##########################################################################
######################      For cage overview      ######################
##########################################################################



class cageTable(QtGui.QTableWidget):
    """ This table contains information about the setups curren """
    def __init__(self, tab=None):
        super(QtGui.QTableWidget, self).__init__(1,12, parent=None)
        self.header_names = ['Select','Setup_ID','Connection','Experiment',
                             'Protocol','Mouse_training',
                             'COM','COM_AC', 'in_use','connected', 'User',
                             'AC_state','Door_Mag','Door_Sensor',
                             'n_mice','mice_in_setup']

        self.tab = tab
        self.setHorizontalHeaderLabels(self.header_names)
        #for i in range(8):
        #    self.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)

        self.select_col_ix = self.header_names.index("Select")
        self.connect_col_ix = self.header_names.index("Connection")  # column index of connect button

        self.fill_table()

    def fill_table(self) -> None:
        self.clearContents()
        self.setRowCount(len(database.setup_df))

        self.buttons = []
        for row_index, row in database.setup_df.iterrows():    

            self.fill_table_row(row_index, row)


    def fill_table_row(self, row_index, row):

        self.populate_cells_from_database(row_index, row)

        button = self._build_connect_button(row)
        self.buttons.append(button)

        if self.tab is None:  #if this is the table in system overview
            button.setEnabled(False)

        self.setCellWidget(row_index, self.connect_col_ix, button)

        chkBoxItem = QtGui.QTableWidgetItem()
        chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
        chkBoxItem.setCheckState(QtCore.Qt.Unchecked)   
        self.setItem(row_index, self.select_col_ix, chkBoxItem)

    def populate_cells_from_database(self, row_index: int, row: pd.Series):
        for col_index in range(self.columnCount()):
            try:
                cHeader = self.header_names[col_index]
                self.setItem(row_index, col_index, Qt.QtWidgets.QTableWidgetItem(str(row[cHeader])))
            except KeyError:
                pass

    def _build_connect_button(self, row: pd.Series):
        """ Set properties of button that allows you to connect to the serial ports
            controlling one of the setups 
        """
        if row['connected']:
            buttonText = 'Connected'
        else:
            buttonText = 'Connect'
        
        button = QtGui.QPushButton(buttonText)
        button.name = [row['Setup_ID'], row['COM'], row['COM_AC']]
        button.clicked.connect(self.connect)
        return button

    def connect(self):

        try:
            setup_id, com_,comAC_ = self.sender().name

            print_func = partial(print, flush=True)
            SC = system_controller(print_func=print_func,GUI=self.GUI,setup_id=setup_id)
            #DL = Data_logger(print_func=print,GUI=self.GUI)
            board = Pycboard(com_, print_func=print_func, data_logger=SC)

            board.load_framework()
            time.sleep(0.05)
            database.connected_boards.append(board)
            ac = Access_control(comAC_,print_func=print_func,data_logger=SC,GUI=self.GUI)
            time.sleep(0.05)
            SC.add_PYC(board)
            SC.add_AC(ac)

            ac.load_framework()
            database.connected_access_controls.append(ac)
            #self.GUI.data_loggers.append(self.data_logger)
            #self.sender().setText("Connected")

            send_name = self.sender().name
            self._fill_setup_df_row(send_name)
            database.controllers[setup_id] = SC
            time.sleep(0.05)
            self.tab.callibrate_dialog = calibrate_dialog(ac=ac)
            self.tab.callibrate_dialog.exec_()
            self.sender().setEnabled(False)
            self.fill_table()
            self.GUI.system_tab.list_of_setups.fill_table()


        except (PyboardError,SerialException) as e:   

            print(e, flush=True)
            print("Failed to connect", flush=True)

    def _fill_setup_df_row(self, send_name):
        " Just fill that row of the df"
        _, com_, _ = send_name
        database.setup_df['connected'].loc[database.setup_df['COM']==com_] = True
        database.setup_df['in_use'].loc[database.setup_df['COM']==com_] = False
        database.setup_df['connected'].loc[database.setup_df['COM']==com_] = True
        database.setup_df['n_mice'].loc[database.setup_df['COM']==com_] = 0



    def _refresh(self):
        ports = find_setups()

        ac_nr = self.header_names.index("COM")
        setup_nr = self.header_names.index("COM_AC")
        for r in range(self.rowCount()):
            if (self.item(r,ac_nr).text() in ports) and (self.item(r,setup_nr).text() in ports):
                self.cellWidget(r,self.connect_col_ix).setEnabled(True)
            else:
                self.cellWidget(r,self.connect_col_ix).setEnabled(False)
                 


##########################################################################
######################      For mouse overview      ######################
##########################################################################

class mouse_adder_table(QtGui.QTableWidget):
    """ This table contains information about all mice currently running in the
        system """
    def __init__(self, GUI,parent=None):
        super(QtGui.QTableWidget, self).__init__(1,7, parent=parent)

        self.header_names = ['Mouse_ID', 'RFID', 'Sex', 'Age', 'Experiment', 
                             'Start_weight','Setup_ID']
        self.setHorizontalHeaderLabels(self.header_names)
        #for i in range(8):
        #    self.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.GUI = GUI





class MouseTable(QtGui.QTableWidget):
    """ This table contains information about all mice currently running in the
        system """
    def __init__(self, GUI,parent=None):
        super(QtGui.QTableWidget, self).__init__(1,15, parent=parent)
        self.header_names = ['','Mouse_ID', 'RFID', 'Sex', 'Age', 'Experiment', 'Task','Protocol', 'User', 
                            'Start_date', 'Current_weight', 'Start_weight', 'is_training',
                            'is_assigned', 'training_log', 'Setup_ID']

        self.GUI = GUI
        self.setHorizontalHeaderLabels(self.header_names)
        #for i in range(8):
        #    self.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        self.loaded = False

        self.fill_table()
        self.loaded = True
    def fill_table(self):
        #print(database.mouse_df)
        #self.setRowCount(0)
        self.setRowCount(len(database.mouse_df))
        df_cols = database.mouse_df.columns

        #print(df_cols)
        for row_index, row in database.mouse_df.iterrows():    

            for col_index in range(self.columnCount()-1):  
                col_name = df_cols[col_index]
                if col_name in self.header_names:
                    table_col_ix = self.header_names.index(df_cols[col_index])
                    if col_name=='Task':
                        task_combo = QtGui.QComboBox()
                        task_combo.activated.connect(partial(self.update_task_combo,task_combo))
                        task_combo.installEventFilter(self)
                        task_combo.RFID = row['RFID']
                        cTask = database.mouse_df.loc[database.mouse_df['RFID']==row['RFID'],'Task'].values[0]
                        task_combo.addItems([cTask] + get_tasks(database.paths['task_dir']))

                        self.setCellWidget(row_index,table_col_ix,task_combo)

                        task_combo.currentTextChanged.connect(partial(self.change_mouse_task,task_combo))


                    else:
                        self.setItem(row_index,table_col_ix,Qt.QtWidgets.QTableWidgetItem(str(row[col_index])))
            #items = [QtGui.QStandardItem(field)for field in row]
            #print(items)
            #self.model.appendRow(items)
            chkBoxItem = QtGui.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)   
            self.setItem(row_index,0,chkBoxItem)



    def update_task_combo(self, combo: QtGui.QComboBox) -> None:
        cTask = combo.currentText()
        combo.clear()
        combo.addItems([cTask] + get_tasks(database.paths['task_dir']))


    def change_mouse_task(self, combo: QtGui.QComboBox) -> None:
        """ Change task mouse is doing """
        rfid = combo.RFID

        #if self.loaded:  #workaround (sorry)

        #print('UPDATED TASK VIA TABLE')
        database.mouse_df.loc[database.mouse_df['RFID']==rfid,'Task'] = combo.currentText()  #need to update the table of the individual mouses training record as well??
        database.mouse_df.to_csv(database.mouse_df.file_location)



