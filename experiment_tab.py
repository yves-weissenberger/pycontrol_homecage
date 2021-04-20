import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import Qt
from pyqtgraph import mkPen
import pyqtgraph as pg
import sys, os, pickle, time
import copy as cp
from tables import cageTable, experiment_overview_table

from dialogs import are_you_sure_dialog
#Ok in this tab want to get an overview of the experiments. The most important thing to
#be able to do here in the first instance is to change the protocol being run.

class experiment_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI = self.parent()

        self.Hlayout = QtGui.QHBoxLayout()
        self.new_experiment_button = QtGui.QPushButton('Start new Experiment')
        self.restart_experiment_button = QtGui.QPushButton('Restart Experiment')
        self.stop_experiment_button = QtGui.QPushButton('Stop Experiment')
        self.stop_experiment_button.clicked.connect(self.stop_experiment)
        self.Hlayout.addWidget(self.new_experiment_button)
        self.Hlayout.addWidget(self.restart_experiment_button)
        self.Hlayout.addWidget(self.stop_experiment_button)

        self.list_of_experiments = experiment_overview_table(GUI=self.GUI,only_active=False)



        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addLayout(self.Hlayout)
        self.Vlayout.addWidget(self.list_of_experiments)

    def _refresh(self):
        pass

    def restart_experiment(self):
        pass
    def stop_experiment(self):
        #update the relevant mouse tables
        #update the experiment table
        #update the setups table
        isChecked = []
        checked_ids =[]
        name_col = self.list_of_experiments.header_names.index("Name")

        for row in range(self.list_of_experiments.rowCount()):
            checked = self.list_of_experiments.item(row,0).checkState()==2
            if checked:
                checked_ids.append(self.list_of_experiments.item(row,name_col.text()))
            isChecked.append(checked)

        if len(isChecked)==1:
            sure = are_you_sure_dialog()
            sure.exec_()
            if sure.GO:
                exp_row = self.GUI.exp_df.loc[self.GUI.exp_df['Name']==checked_ids[0]]
                self.GUI.exp_df.loc[self.GUI.exp_df['Name']==checked_ids[0],'Active'] = False
                mice_in_experiment = exp_row['subjects']
                setups = exp_row['Setups']
                self._update_mice(mice_in_exp=mice_in_experiment)
                self._update_setups(setups_in_exp=setups)
        else:
            pass

        pass
    
    def _update_mice(self,mice_in_exp):
        for mouse in mice_in_exp:
            #This is not correct!!!!
            self.GUI.mouse_df.loc[self.GUI.mouse_df['Mouse_ID'],'Protocol'] = None
            self.GUI.mouse_df.loc[self.GUI.mouse_df['Mouse_ID'],'is_assigned'] = False
            self.GUI.mouse_df.to_csv(self.GUI.mouse_df.file_location)

    def _update_setups(self,setups_in_exp):
        for setup in setups_in_exp:
            self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID'],'Experiment'] = None
            self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID'],'in_use'] = False  #this is what is checked in the new experiment dialog
            self.GUI.setup_df.to_csv(self.GUI.setup_df.file_location)
