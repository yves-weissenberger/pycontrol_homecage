import numpy as np
from pyqtgraph.Qt import QtGui
import os
import pandas as pd
import json

from pycontrol_homecage.dialogs import are_you_sure_dialog, mouse_summary_dialog
from pycontrol_homecage.tables import MouseTable, variables_table
from pycontrol_homecage.utils import get_variables_and_values_from_taskfile
import pycontrol_homecage.db as database


class mouse_tab(QtGui.QWidget):

    def __init__(self, parent: QtGui.QMainWindow = None):

        super(QtGui.QWidget, self).__init__(parent)

        self.GUI = self.parent()

        self.init_buttons()

        self.set_button_layout()

        self.init_mouse_table()
        
        # Buttons to control stuff
        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addWidget(self.mouse_table_label)
        self.Vlayout.addLayout(self.mouse_manager_layout)

        self.Vlayout.addWidget(self.scrollable_mouse)



        #### Deal with variables of the tasks
        self.variables_table = variables_table()
        self.filter_categories = ['Experiment', 'User', 'Mouse_ID', 'RFID']
        self.variables_box = QtGui.QGroupBox('Variables')
        self.vars_hlayout1 = QtGui.QHBoxLayout(self)
        self.vars_vlayout1 = QtGui.QVBoxLayout(self)

        self.vars_combo = QtGui.QComboBox()
        self.vars_combo.addItems(['Filter by'] + self.filter_categories)
        self.vars_combo.activated.connect(self.update_available_vfilt)

        self.vars_combo_sel = QtGui.QComboBox()
        self.vars_combo_sel.addItems([''])

        self.vars_update_button = QtGui.QPushButton('Update Variables')
        self.vars_update_button.clicked.connect(self.update_variables_table)
        self.show_all_vars_checkbox = QtGui.QCheckBox("Show all variables")
        self.show_all_vars_checkbox.setChecked(True)

        self.vars_combo_sel.activated.connect(self.update_variables_filt)
        self.vars_hlayout1.addWidget(self.vars_combo)
        self.vars_hlayout1.addWidget(self.vars_combo_sel)
        self.vars_hlayout1.addWidget(self.show_all_vars_checkbox)
        self.vars_hlayout1.addWidget(self.vars_update_button)
        self.vars_vlayout1.addLayout(self.vars_hlayout1)
        self.vars_vlayout1.addWidget(self.variables_table)

        self.variables_box.setLayout(self.vars_vlayout1)
        self.Vlayout.addWidget(self.variables_box)  #THIS NEEDS TO GO. THIS WILL NEVER HAPPEN. CHANGE TO VARIABLES TABLE

    def init_buttons(self) -> None:
        self.remove_mouse_button = QtGui.QPushButton('Remove Mouse')
        self.remove_mouse_button.clicked.connect(self.remove_mouse)
        self.update_mouse_button = QtGui.QPushButton('Update Mouse')
        self.mouse_summary_button = QtGui.QPushButton('Get Mouse Summary')
        self.mouse_summary_button.clicked.connect(self.get_summary)

    def set_button_layout(self) -> None:
        self.mouse_manager_layout = QtGui.QHBoxLayout()
        self.mouse_manager_layout.addWidget(self.remove_mouse_button)
        self.mouse_manager_layout.addWidget(self.update_mouse_button)
        self.mouse_manager_layout.addWidget(self.mouse_summary_button)

    def init_mouse_table(self) -> None:
        """Initialise a table that shows which mice are currently in the system
        """
        self.mouse_table_label = QtGui.QLabel()
        self.mouse_table_label.setText("Mice in setup")

        self.scrollable_mouse = QtGui.QScrollArea()
        self.scrollable_mouse.setWidgetResizable(True)
        self.scrollable_mouse.horizontalScrollBar().setEnabled(False)
        self.list_of_mice = MouseTable(self.GUI, self)
        self.scrollable_mouse.setWidget(self.list_of_mice)

    def init_mouse_variables_table(self) -> None:
        return None

    def update_variables_table(self):

        """ This function updates variables in the mousetable for future use 
            REMEMBER TO CHECK TYPES OF DICT ELEMENTS ONCE THIS IS RUNNING!!!!
        """
        self.variables_table.setEnabled(False)  #after update of variables table, turn this off

        all_variables = self.variables_table.variables_list()
        unique_mice = list(set([i['subject'] for i in all_variables]))

        for ms_rfid in unique_mice:

            #persistent variables persist over sessions
            #all_variables =  self.variables_table.subject_variable_names[ms_rfid]
            persistent_variables_dict = dict([(str(i['name']),i['value'].strip()) for i in all_variables
                                            if ((i['subject']==ms_rfid) and
                                            (i['persistent']))])
            #summary variables are send with the data 
            summary_variables_dict = dict([(str(i['name']),i['value'].strip()) for i in all_variables
                                     if ((i['subject']==ms_rfid) and
                                     (i['summary']))])
            #set variables are different to default values in the task file but not persistent across sessions
            set_variables_dict = dict([(str(i['name']), i['value'].strip()) for i in all_variables
                                       if ((i['subject'] == ms_rfid) and
                                       not (i['persistent'])
                                       and i['set'])
                                       ]
                                      )

            database.mouse_df.loc[database.mouse_df['RFID'] == float(ms_rfid), 'summary_variables'] = json.dumps(summary_variables_dict)
            database.mouse_df.loc[database.mouse_df['RFID'] == float(ms_rfid), 'persistent_variables'] = json.dumps(persistent_variables_dict)
            database.mouse_df.loc[database.mouse_df['RFID'] == float(ms_rfid), 'set_variables'] = json.dumps(set_variables_dict)

            database.mouse_df.to_csv(database.mouse_df.file_location)



    def update_variables_filt(self):
        self.variables_table.setEnabled(True)
        filtby = str(self.vars_combo.currentText())
        self.variables_table.clearContents()
        if filtby == 'RFID':
            RFIDs = [str(self.vars_combo_sel.currentText())]

        elif filtby == 'Mouse_ID':
            ID = database.mouse_df.loc[database.mouse_df['Mouse_ID'] == self.vars_combo_sel.currentText(),'RFID'].values
            RFIDs = [str(i) for i in ID]
            # self.variables_table.set_available_subjects(RFIDs)
        elif filtby == 'Experiment':
            # OK THIS IS MORE COMPLICATED BECAUSE DIFFERENT MICE IN THE SAME EXPERIMENT MIGHT HAVE DIFFERENT VARIABLES
            RFIDs = list(set([str(i) for i in database.mouse_df.loc[database.mouse_df['Experiment'] == self.vars_combo_sel.currentText(),'RFID'].values]))
            # print(RFIDs)

        self.variables_table.set_available_subjects(RFIDs)
        for sel_RFID in RFIDs:

            mouseRow = database.mouse_df.loc[database.mouse_df['RFID'] == float(sel_RFID)]
            #print(mouseRow)
            mouseTask = mouseRow['Task'].values[0] + '.py'

            summary_variables = {}; persistent_variables = {}; set_variables = {}
            if not pd.isnull(mouseRow['summary_variables'].values):
                summary_variables = eval(mouseRow['summary_variables'].values[0])
            if not pd.isnull(mouseRow['persistent_variables'].values):
                persistent_variables = eval(mouseRow['persistent_variables'].values[0])
            if not pd.isnull(mouseRow['set_variables'].values):
                set_variables = eval(mouseRow['set_variables'].values[0])  # set variables are persistent variables that are not updated. Is this necessary?? YES
            
            task_dir = database.paths["task_dir"]
            task_path = os.path.join(task_dir, mouseTask)
            self.default_variables =  get_variables_and_values_from_taskfile(task_path)
            self.variable_names =  list(set(self.default_variables.keys()))  # get_variables_from_taskfile(task_path)
            self.variables_table.set_variable_names(self.variable_names)
            self.variables_table.set_variable_names_by_subject(sel_RFID,self.variable_names)
            #if you are showing all variables
            if self.show_all_vars_checkbox.isChecked():
                #for all variables
                for k,v in self.default_variables.items():
                    persistent = False; summary = False; set_var = False

                    #set varaible has lesser priority than persistent
                    if k in set_variables.keys():
                        v = set_variables[k]; set_var = True
                    #if the variable in persistent, store that it is persistent and store its value
                    if k in persistent_variables.keys():
                        v = persistent_variables[k]; persistent = True
                    if k in summary_variables.keys():
                        summary = True

                    var_dict = {'name':k,
                                'subject': sel_RFID,
                                'value': v,
                                'persistent': persistent,
                                'summary': summary,
                                'set': set_var}
                    self.variables_table.add_variable(var_dict)

    def update_available_vfilt(self):
        "Change what you are filtering variables you show by"
        filtby = str(self.vars_combo.currentText())
        self.vars_combo_sel.clear()
        if filtby in ('Mouse_ID', 'RFID'):
            self.vars_combo_sel.clear()
            dat = database.mouse_df[filtby]
            self.vars_combo_sel.addItems(['Select'] + [str(i) for i in dat.values])
        elif filtby == 'Experiment':
            dat = list(set(database.mouse_df[filtby].values))
            self.vars_combo_sel.addItems(['Select'] + [str(i) for i in dat])

    def remove_mouse(self):
        """ Remove mouse from df and CSV file"""
        isChecked = []
        RFID_index = self.list_of_mice.header_names.index("RFID")

        for row in range(self.list_of_mice.rowCount()):
            if self.list_of_mice.item(row, 0).checkState() == 2:
                isChecked.append(float(self.list_of_mice.item(row, RFID_index).text()))   # because its a float in the mouse_df

        if isChecked:
            sure = are_you_sure_dialog()
            sure.exec_()
            if sure.GO:
                for ch_ in isChecked:
                    database.mouse_df.loc[database.mouse_df['RFID'] == ch_, 'in_system'] = False
                    database.mouse_df.to_csv(database.mouse_df.file_location)

                    self.list_of_mice.fill_table()
        else:
            pass


    def get_summary(self):
        """ Get summary information for the set of selected mice """

        isChecked = []
        for row in range(self.list_of_mice.rowCount()):
            checked = self.list_of_mice.item(row, 0).checkState() == 2
            isChecked.append(checked)

        if np.any(isChecked):
            sd = mouse_summary_dialog()
            sd.show()
            sd.exec_()

    def _refresh(self):
        pass