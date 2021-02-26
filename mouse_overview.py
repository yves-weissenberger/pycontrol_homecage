import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import Qt
from pyqtgraph import mkPen
import pyqtgraph as pg
import sys, os, pickle, time
import copy as cp
from datetime import datetime
import json

from dialogs import are_you_sure_dialog, mouse_summary_dialog
from tables import mouse_adder_table, MouseTable, variables_table
from utils import get_variables_from_taskfile, get_variables_and_values_from_taskfile
from loc_def import main_path


class mouse_window(QtGui.QWidget):

    def __init__(self, parent=None):

        super(QtGui.QWidget, self).__init__(parent)

        self.GUI = self.parent()

        self.remove_mouse_button = QtGui.QPushButton('Remove Mouse')
        self.remove_mouse_button.clicked.connect(self.remove_mouse)
        self.update_mouse_button = QtGui.QPushButton('Update Mouse')

        self.mouse_summary_button = QtGui.QPushButton('Get Mouse Summary')
        self.mouse_summary_button.clicked.connect(self.get_summary)

        self.mouse_manager_layout = QtGui.QHBoxLayout()
        self.mouse_manager_layout.addWidget(self.remove_mouse_button)
        self.mouse_manager_layout.addWidget(self.update_mouse_button)
        self.mouse_manager_layout.addWidget(self.mouse_summary_button)


        #Setups table
        self.mouse_table_label = QtGui.QLabel()
        self.mouse_table_label.setText("Mice in setup")

        self.scrollable_mouse =  QtGui.QScrollArea()
        self.scrollable_mouse.setWidgetResizable(True)
        self.scrollable_mouse.horizontalScrollBar().setEnabled(False)




        self.list_of_mice = MouseTable(self.GUI,self)
        self.scrollable_mouse.setWidget(self.list_of_mice)

        # Buttons to control stuff
        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addWidget(self.mouse_table_label)
        self.Vlayout.addLayout(self.mouse_manager_layout)

        self.Vlayout.addWidget(self.scrollable_mouse)



        #### Deal with variables of the tasks
        self.variables_table = variables_table(GUI=self.GUI)
        self.filter_categories = ['Experiment','User','Mouse_ID','RFID']
        self.variables_box = QtGui.QGroupBox('Variables')
        self.vars_hlayout1 = QtGui.QHBoxLayout(self)
        self.vars_vlayout1 = QtGui.QVBoxLayout(self)

        self.vars_combo  = QtGui.QComboBox()
        self.vars_combo.addItems(['Filter by'] + self.filter_categories)
        self.vars_combo.activated.connect(self.update_available_vfilt)

        self.vars_combo_sel  = QtGui.QComboBox()
        self.vars_combo_sel.addItems([''])

        self.vars_update_button = QtGui.QPushButton('Update Variables')
        self.show_all_vars_checkbox = QtGui.QCheckBox("Show all variables")
        self.show_all_vars_checkbox.setChecked(True)
        #self.show_all_vars_checkboxself.stateChanged.connect(lambda: self.show_all_vars_checkboxself:

        self.vars_combo_sel.activated.connect(self.update_variables_filt)
        #self.task_combo.currentIndexChanged.connect(self.picked_task)
        self.vars_hlayout1.addWidget(self.vars_combo)
        self.vars_hlayout1.addWidget(self.vars_combo_sel)
        self.vars_hlayout1.addWidget(self.show_all_vars_checkbox)
        self.vars_hlayout1.addWidget(self.vars_update_button)
        self.vars_vlayout1.addLayout(self.vars_hlayout1)
        self.vars_vlayout1.addWidget(self.variables_table)

        self.variables_box.setLayout(self.vars_vlayout1)


        self.Vlayout.addWidget(self.variables_box)  #THIS NEEDS TO GO. THIS WILL NEVER HAPPEN. CHANGE TO VARIABLES TABLE


    def update_variables_filt(self):

        filtby = str(self.vars_combo.currentText())
        self.variables_table.clearContents()
        if filtby=='RFID':
            sel_RFID = str(self.vars_combo_sel.currentText())
            mouseTask = self.GUI.mouse_df.loc[self.GUI.mouse_df['RFID']==int(sel_RFID),'Task'].values[0] + '.py'
            task_dir = os.path.join(main_path,'tasks')
            task_path = os.path.join(task_dir,mouseTask)
            variables =  get_variables_and_values_from_taskfile(task_path)
            if self.show_all_vars_checkbox.isChecked():
                #print(variables)
                for k,v in variables.items():
                    var_dict = {'name':k,
                                'subject': sel_RFID,
                                'value': v,
                                'persistent': False,
                                'summary': False}
                    self.variables_table.add_variable(var_dict)
            #else:




    def update_available_vfilt(self):
        "Change what you are filtering variables you show by"
        filtby = str(self.vars_combo.currentText())

        if filtby in ('Mouse_ID','RFID'):
            self.vars_combo_sel.clear()
            dat = self.GUI.mouse_df[filtby]
            self.vars_combo_sel.addItems(['Select'] + [str(i) for i in dat.values])
            

    def remove_mouse(self):
        """ Remove mouse from df and CSV file"""
        isChecked = []
        RFID_index = self.list_of_mice.header_names.index("RFID")
        #print("RFID_index",RFID_index)
        for row in range(self.list_of_mice.rowCount()):
            if self.list_of_mice.item(row,0).checkState()==2:
                isChecked.append(float(self.list_of_mice.item(row,RFID_index).text()))   #because its a float in the mouse_df
            #isChecked.append(self.list_of_mice.item(row,0).checkState()==2)
        #print(isChecked)
        #print(type(self.GUI.mouse_df['RFID'].values[0]))
        if isChecked:
            sure = are_you_sure_dialog()
            sure.exec_()
            if sure.GO:
                for ch_ in isChecked:
                    #if 
                    print("GO",ch_)
                    fl = self.GUI.mouse_df.file_location
                    ix_ = self.GUI.mouse_df.index[self.GUI.mouse_df['RFID']==ch_]
                    #print("INDEX",ix_)
                    self.GUI.mouse_df = self.GUI.mouse_df.drop(ix_)
                    self.GUI.mouse_df.file_location = fl  #because the file location is not part of the class so when using drop this is removed
                    self.GUI.mouse_df.to_csv(self.GUI.mouse_df.file_location)

                    print(self.GUI.mouse_df)
                    self.list_of_mice.fill_table()
        else:
            pass


    def get_summary(self):
        """ Get summary information for the set of selected mice """


        isChecked = []
        for row in range(self.list_of_mice.rowCount()):
            checked = self.list_of_mice.item(row,0).checkState()==2
            isChecked.append(checked)

        if np.any(isChecked):
            sd = mouse_summary_dialog()
            sd.show()
            sd.exec_()



