import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import Qt
from pyqtgraph import mkPen
import pyqtgraph as pg
import sys, os, pickle, time
import copy as cp

from new_experiment_dialog import new_experiment_dialog
from tables import cageTable, experiment_overview_table

from plotting import Experiment_plot


class system_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI = self.parent()
        self.plot_isactive = False


        # ------------------------------ #
        # ----------- Users ------------ #
        # ------------------------------ #
        self.user_groupbox = QtGui.QGroupBox('Users')

        self.user_label = QtGui.QLabel()
        self.user_label.setText("Users")

        self.Hlayout_users = QtGui.QHBoxLayout()

        self.login_button = QtGui.QPushButton('Login')
        self.add_user_button = QtGui.QPushButton('Add User')
        self.logout_button = QtGui.QPushButton('Logout')

        self.Hlayout_users.addWidget(self.login_button)
        self.Hlayout_users.addWidget(self.add_user_button)
        self.Hlayout_users.addWidget(self.logout_button)
        self.user_groupbox.setLayout(self.Hlayout_users)


        self.add_box_button = QtGui.QPushButton('Add Box')


        # ------------------------------ #
        # -------- Experiments  -------- #
        # ------------------------------ #


        #Experiments Table
        self.experiment_groupbox = QtGui.QGroupBox("Experiments")
        self.scrollable_experiments =  QtGui.QScrollArea()
        self.scrollable_experiments.setWidgetResizable(True)
        self.list_of_experiments = experiment_overview_table(GUI=self.GUI,only_active=True)
        self.scrollable_experiments.setWidget(self.list_of_experiments)

        # Buttons to control stuff
        self.start_experiment_button = QtGui.QPushButton('Start New Experiment')
        self.start_experiment_button.clicked.connect(self.start_new_experiment)

        self.end_experiment_button = QtGui.QPushButton('End Experiment')
        self.end_experiment_button.clicked.connect(self.end_experiment)

        self.Hlayout_exp_buttons = QtGui.QHBoxLayout()
        self.Hlayout_exp_buttons.addWidget(self.start_experiment_button)
        self.Hlayout_exp_buttons.addWidget(self.end_experiment_button)

        self.Vlayout_exp = QtGui.QVBoxLayout(self)
        self.Vlayout_exp.addLayout(self.Hlayout_exp_buttons)
        self.Vlayout_exp.addWidget(self.scrollable_experiments)

        self.experiment_groupbox.setLayout(self.Vlayout_exp)


        # ------------------------ #
        # -------- Setups  ------- #
        # ------------------------ #

        #Setups table
        self.setup_groupbox = QtGui.QGroupBox("Setups")
        self.scrollable_setups =  QtGui.QScrollArea()
        self.scrollable_setups.setWidgetResizable(True)
        self.list_of_setups = cageTable(self.GUI)
        self.scrollable_setups.setWidget(self.list_of_setups)

        # Buttons to control stuff
        self.show_setup_plot = QtGui.QPushButton('Show Plot')
        self.show_setup_plot.clicked.connect(self.activate_plot)
        self.filter_setup_combo = QtGui.QComboBox()
        self.filter_setup_combo.addItems(['Filter by'])

        self.Hlayout_setup_buttons = QtGui.QHBoxLayout()
        self.Hlayout_setup_buttons.addWidget(self.show_setup_plot)
        self.Hlayout_setup_buttons.addWidget(self.filter_setup_combo)

        self.setup_label = QtGui.QLabel()
        self.setup_label.setText("Setups")

        self.Vlayout_setup = QtGui.QVBoxLayout()
        self.Vlayout_setup.addLayout(self.Hlayout_setup_buttons)
        self.Vlayout_setup.addWidget(QtGui.QLabel("Table of Setups"))
        self.Vlayout_setup.addWidget(self.scrollable_setups)
        self.setup_groupbox.setLayout(self.Vlayout_setup)


        # ----------------------------------- #
        # -------- Central print log  ------- #
        # ----------------------------------- #

        self.log_groupbox = QtGui.QGroupBox("Log")

        self.log_hlayout = QtGui.QHBoxLayout()


        self.log_active = QtGui.QCheckBox("Print to log")
        self.log_active.setChecked(True)


        self.filter_exp = QtGui.QCheckBox("Filter by experiment")
        self.filter_exp.setChecked(False)
        #self.filter_exp.stateChanged.connect(self._enable_prot_sel)

        self.filter_setup = QtGui.QCheckBox("Filter by setup")
        self.filter_setup.setChecked(False)
        #self.filter_setup.stateChanged.connect(self._enable_prot_sel)

        self.log_hlayout.addWidget(self.log_active)
        self.log_hlayout.addWidget(self.filter_exp)
        self.log_hlayout.addWidget(self.filter_setup)

        self.log_textbox = QtGui.QPlainTextEdit()
        self.log_textbox.setMaximumBlockCount(500) 
        self.log_textbox.setFont(QtGui.QFont('Courier', 12))
        self.log_textbox.setReadOnly(True)

        self.log_layout = QtGui.QVBoxLayout()
        self.log_layout.addLayout(self.log_hlayout)
        self.log_layout.addWidget(self.log_textbox)

        self.log_groupbox.setLayout(self.log_layout)
        # ------------------------------------ #
        # -------- Vertical stacking  -------- #
        # ------------------------------------ #

        self.Vlayout = QtGui.QVBoxLayout(self)

        #self.Vlayout.addWidget(self.user_label)
        #self.Vlayout.addLayout(self.Hlayout_users)
        self.Vlayout.addWidget(self.user_groupbox)

        self.Vlayout.addWidget(self.experiment_groupbox)
        #self.Vlayout.addWidget(self.setup_label)
        #self.Vlayout.addLayout(self.Hlayout_setup_buttons)

        self.Vlayout.addWidget(self.setup_groupbox)
        self.Vlayout.addWidget(self.log_groupbox)


    def activate_plot(self):
        " start plotting incoming data from an experiment"

        if len(self.GUI.exp_df)>0: #check first if an experiment is running

            self.experiment_plot = Experiment_plot()

            experiment = {'subjects': {},
                          'sm_infos': {},
                          'handlers':{} }
            #check which mice are training right now
            for kk,row in self.GUI.setup_df.iterrows():
                if row['Mouse_training']!='none':
                    #k = str(len(experiment['subjects']))
                    experiment['subjects'][row['Setup_ID']] = row['Mouse_training']
                    handler_ = [setup for k,setup in self.GUI.controllers.items() if k==row['Setup_ID']][0]
                    experiment['sm_infos'][row['Setup_ID']] = handler_.PYC.sm_info
                    experiment['handlers'][row['Setup_ID']] = handler_


            self.experiment_plot.setup_experiment(experiment)

            self.experiment_plot.set_state_machines(experiment)

            for ix_,hKey in enumerate(sorted(experiment['handlers'].keys())):
                experiment['handlers'][hKey].data_consumers = [self.experiment_plot.subject_plots[ix_]]

            self.experiment_plot.show()
            self.experiment_plot.start_experiment()
            self.plot_isactive = True


    def start_new_experiment(self):

        self.new_experiment_config = new_experiment_dialog(self.GUI)
        self.new_experiment_config.exec_()



    def end_experiment(self):
        #if False:
        #print("END")
        for rowN in range(self.list_of_experiments.rowCount()):

            if self.list_of_experiments.item(rowN,0).checkState()==2:
                #print("FOUND")
                expName = self.list_of_experiments.item(rowN,self.list_of_experiments.header_names.index('Name')).text()
                for setup in self.GUI.exp_df.loc[self.GUI.exp_df['Name']==expName,'Setups'].values:
                    setup = eval(setup)[0]

                    if self.GUI.controllers.items():  #if there are any controllers
                        print(expName)
                        handler_ = [setup_ for k,setup_ in self.GUI.controllers.items() if k==setup][0]
                        
                        handler_.PYC.stop_framework()
                        time.sleep(.05)
                        handler_.PYC.process_data()
                        handler_.close_files()
                        handler_.PYC.reset()
                        handler_.PYC.close()
                        handler_.AC.close()
                        del self.GUI.controllers[setup]
                        self.GUI.exp_df.loc[self.GUI.exp_df['Name']==expName,'Active'] = False
                        #print(self.GUI.controllers)
                        print("CLOSED")

                       
                #self.GUI.exp_df
            else:
                pass
        #print(self.list_of_experiments.only_active)
        self.list_of_experiments.fill_table()
        print(self.GUI.experiment_tab.list_of_experiments.only_active)
        self.GUI.experiment_tab.list_of_experiments.fill_table()

        #pass

    def write_to_log(self,msg,from_sys=None):

        if self.log_active.isChecked():
            if type(msg)==str:
                if 'Wbase' not in msg:
                    self.log_textbox.moveCursor(QtGui.QTextCursor.End)
                    self.log_textbox.insertPlainText(msg +'\n')
                    self.log_textbox.moveCursor(QtGui.QTextCursor.End)
            elif type(msg)==list:
                for msg_ in msg:
                    #print(msg_)
                    #print(msg_)
                    if 'Wbase' not in msg:
                        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
                        self.log_textbox.insertPlainText(str(msg_) +'\n')
                        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        else:
            pass

    def _refresh(self):
        pass

#A class implementing experiments tables
class ExperimentsTable(QtGui.QTableWidget):
    def __init__(self, parent=None):
        super(QtGui.QTableWidget, self).__init__(1,3, parent=parent)
        self.setHorizontalHeaderLabels(['Experiment', 'User', ''])
        self.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
        self.horizontalHeader().setResizeMode(2, QtGui.QHeaderView.ResizeToContents)
        self.verticalHeader().setVisible(False)




#class