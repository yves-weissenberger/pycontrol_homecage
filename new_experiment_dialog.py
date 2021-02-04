import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import Qt
from pyqtgraph import mkPen
import pyqtgraph as pg
import sys, os, pickle, time, re
import copy as cp
from datetime import datetime
import pandas as pd


#YW code
from dialogs import are_you_sure_dialog
from tables import mouse_adder_table, MouseTable
from utils import get_tasks
from com.data_logger import Data_logger
from tables import mouse_list_table, cage_list_table
from loc_def import data_dir, mice_dir, protocol_dir
#TA code
from com.pycboard import Pycboard, PyboardError, _djb2_file
from com.data_logger import Data_logger

class new_experiment_dialog(QtGui.QDialog):

    def __init__(self,GUI, parent=None):
        super(new_experiment_dialog, self).__init__(parent)

        self.GUI = GUI
        self.setGeometry(100, 30, 1300, 600) # Left, top, width, height.

        self.df_setup_tmp = pd.DataFrame(columns=['COM','COM_AC','Setup_ID',
                                             'in_use','connected','User','Experiment',
                                             'Protocol','Mouse_training','Door','n_mice'])

        self.df_mouse_tmp = pd.DataFrame(columns=['Mouse_ID','RFID','Sex','Age','Experiment',
                                             'Protocol','Stage','Task','User','Start_date','Current_weight',
                                             'Start_weight','is_training','is_assigned',
                                             'training_log','Setup_ID','in_system'])




        self.used_setups = []
        self.used_mice = []
        self.global_task = True
        self.running_protocol = False


        self.left_column = QtGui.QVBoxLayout()


        #### Data related to experiment
        self.exp_name_groupbox = QtGui.QGroupBox('Status')

        self.expLabel = QtGui.QLabel()
        self.expLabel.setText("Experiment Name:")

        self.expName = QtGui.QLineEdit()

        self.protVtask = QtGui.QCheckBox("Run Protocol")
        self.protVtask.setChecked(False)
        self.protVtask.stateChanged.connect(self._prot_or_task)


        self.shared_protocol = QtGui.QCheckBox("Share Protocol")
        self.shared_protocol.setChecked(True)
        self.shared_protocol.stateChanged.connect(self._enable_prot_sel)

        self.protocol_combo = QtGui.QComboBox()
        self.available_tasks = get_tasks(self.GUI.GUI_filepath)
        self.protocol_combo.addItems(['Select Task'] + self.available_tasks)


        self.exp_GOButton = QtGui.QPushButton()  #First stage of specifying experiment whereby set name and (potentially) protocol
        self.exp_GOButton.setText("Set")  
        self.exp_GOButton.clicked.connect(self.set_name)

        self.name_layout = QtGui.QHBoxLayout()
        self.name_layout2 = QtGui.QHBoxLayout()
        self.name_layout.addWidget(self.expLabel)
        self.name_layout.addWidget(self.expName)
        self.name_layout.addWidget(self.shared_protocol)
        self.name_layout.addWidget(self.protVtask)

        self.name_layout2.addWidget(self.protocol_combo)
        self.name_layout2.addWidget(self.exp_GOButton)

        self.nameVlayout = QtGui.QVBoxLayout()
        self.nameVlayout.addLayout(self.name_layout)
        self.nameVlayout.addLayout(self.name_layout2)
        self.exp_name_groupbox.setLayout(self.nameVlayout)



        ## Column to add setups to the experiment
        self.setup_groupbox = QtGui.QGroupBox('Setups')

        self.setups_column = QtGui.QVBoxLayout()

        #populate this column

        #Controls for adding a setup to an experiment
        self.CAT = QtGui.QGroupBox('Add Setup')#cage_setup_table(GUI=self.GUI,exp_dialog=self)
        self.cat_layout = QtGui.QHBoxLayout()

        self.setup_combo = QtGui.QComboBox()
        self.available_setups = [rw['Setup_ID'] for kk,rw in self.GUI.setup_df.iterrows() if rw['connected'] 
                                                                                        and not rw['in_use']]
        self.setup_combo.addItems(['Select Setup'] + self.available_setups)
        self.setup_combo.currentTextChanged.connect(self.on_scb_changed)


        self.add_button = QtGui.QPushButton()
        self.add_button.setText("Add Setup")
        self.add_button.setEnabled(False)
        self.prot_label = Qt.QtWidgets.QLabel("Protocol:          ")   #protocol label
        self.exp_label = Qt.QtWidgets.QLabel("Experiemnt:         ")   #experiment label

        self.cat_layout.addWidget(self.setup_combo)
        self.cat_layout.addWidget(self.exp_label)
        self.cat_layout.addWidget(self.prot_label)

        self.cat_layout.addWidget(self.add_button)

        self.add_button.clicked.connect(self.add_cage)

        self.CAT.setLayout(self.cat_layout)


        #####################################################
        #############     Overview of setups     ############
        #####################################################
        self.CLT = cage_list_table(GUI=self.GUI,tab=self)
        self.setups_column.addWidget(self.CAT,1)
        self.setups_column.addWidget(self.CLT,10)
        self.setup_groupbox.setLayout(self.setups_column)
        self.setup_groupbox.setEnabled(False)
        #self.CLT

        self.left_column.addWidget(self.exp_name_groupbox)
        self.left_column.addWidget(self.setup_groupbox)


        ###############################################################
        ###############################################################


        ####################################################
        #############      Mouse Adder Box      ############
        ####################################################

        self.MAT = QtGui.QGroupBox("Add Mouse")

        self.mat_layout = QtGui.QVBoxLayout()
        self.matL1 = QtGui.QHBoxLayout()
        self.matL2 = QtGui.QHBoxLayout()

        self.mouse_name_label = QtGui.QLabel("Mouse_ID:")
        self.mouse_name = QtGui.QLineEdit("")

        self.RFID_label = QtGui.QLabel("RFID:")
        self.RFID = QtGui.QLineEdit("")



        self.sex_label = QtGui.QLabel("Sex:")
        self.sex = QtGui.QComboBox()
        self.sex.addItems(['F','M',])

        self.age_label = QtGui.QLabel("Age (weeks):")
        self.age = QtGui.QLineEdit("")

        self.weight_label = QtGui.QLabel("Weight (g):")
        self.weight = QtGui.QLineEdit("")

        self.add_mouse_button = QtGui.QPushButton("Add Mouse")
        self.add_mouse_button.clicked.connect(self.add_mouse)

        self.mouse_prot = QtGui.QComboBox()
        self.mouse_prot.addItems(['Select Task'] + self.available_tasks)
        



        self.matL1.addWidget(self.mouse_name_label)
        self.matL1.addWidget(self.mouse_name)

        self.matL1.addWidget(self.RFID_label)
        self.matL1.addWidget(self.RFID)

        self.matL1.addWidget(self.sex_label)
        self.matL1.addWidget(self.sex)

        self.matL2.addWidget(self.mouse_prot)
        self.matL2.addWidget(self.age_label)
        self.matL2.addWidget(self.age)

        self.matL2.addWidget(self.weight_label)
        self.matL2.addWidget(self.weight)
        self.matL2.addWidget(self.add_mouse_button)

        self.mat_layout.addLayout(self.matL1)
        self.mat_layout.addLayout(self.matL2)
        self.MAT.setLayout(self.mat_layout)
        #self.MAT.setEnabled(False)


        self.MICE = QtGui.QGroupBox('Mouse Overview')
        self.mice_column = QtGui.QVBoxLayout()
        self.MLT = mouse_list_table(GUI=self.GUI,tab=self)

        self.mice_column.addWidget(self.MAT)
        self.mice_column.addWidget(self.MLT)
        self.MICE.setLayout(self.mice_column)



        ####################################################
        #############      Run Experiments      ############
        ####################################################

        self.runGroup = QtGui.QGroupBox("Run")
        self.run_layout = QtGui.QHBoxLayout()
        self.run_button = QtGui.QPushButton('Run Protocol')
        self.run_button.clicked.connect(self.run_experiment)
        self.run_layout.addWidget(self.run_button)
        self.runGroup.setLayout(self.run_layout)

        self.right_column = QtGui.QVBoxLayout()
        self.right_column.addWidget(self.MICE)
        self.right_column.addWidget(self.runGroup)


        self.all_columns = QtGui.QHBoxLayout()
        self.all_columns.addLayout(self.left_column)
        self.all_columns.addLayout(self.right_column)




        self.vLayout = QtGui.QVBoxLayout(self)
        self.vLayout.addLayout(self.name_layout)
        self.vLayout.addLayout(self.all_columns)

        self.MICE.setEnabled(False)


    def _enable_prot_sel(self):

        if self.shared_protocol.isChecked():
            self.protocol_combo.setEnabled(True)
            self.exp_GOButton.setEnabled(False)
            self.global_task = True
        elif self.shared_protocol.isChecked()==False:
            self.protocol_combo.setEnabled(False)
            self.exp_GOButton.setEnabled(True)
            self.global_task = False

    def add_mouse(self):

        entry_nr = len(self.df_mouse_tmp)

        self.df_mouse_tmp.loc[entry_nr] = ['NA']*len(self.df_mouse_tmp.columns)

        self.df_mouse_tmp.loc[entry_nr]['Mouse_ID'] = self.mouse_name.text()
        self.df_mouse_tmp.loc[entry_nr]['RFID'] = self.RFID.text()
        self.df_mouse_tmp.loc[entry_nr]['Sex'] = self.sex.currentText()
        self.df_mouse_tmp.loc[entry_nr]['Age'] = self.age.text()
        self.df_mouse_tmp.loc[entry_nr]['Experiment'] = self.set_experiment_name

        if self.running_protocol: #if you are going to run a whole protocol
            self.df_mouse_tmp.loc[entry_nr]['Protocol'] = self.mouse_prot.currentText()
            self.df_mouse_tmp.loc[entry_nr]['Task'] = 'NA'
            self.df_mouse_tmp.loc[entry_nr]['Stage'] = 0
        else: #if you are just running a task
            self.df_mouse_tmp.loc[entry_nr]['Task'] = self.mouse_prot.currentText()
            self.df_mouse_tmp.loc[entry_nr]['Protocol'] = str(time.time()).replace('.','') + '_task'
            self.df_mouse_tmp.loc[entry_nr]['Stage'] = 'NA'

        self.df_mouse_tmp.loc[entry_nr]['User'] = self.GUI.active_user
        self.df_mouse_tmp.loc[entry_nr]['Start_date'] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
        self.df_mouse_tmp.loc[entry_nr]['Start_weight'] = self.weight.text()
        self.df_mouse_tmp.loc[entry_nr]['Current_weight'] = self.weight.text()

        self.df_mouse_tmp.loc[entry_nr]['is_training'] = False
        self.df_mouse_tmp.loc[entry_nr]['is_assigned'] = True
        self.df_mouse_tmp.loc[entry_nr]['Setup_ID'] = self.CLT.selected_setups[0]
        self.MLT.fill_table()


    def _prot_or_task(self):
        
        if self.protVtask.isChecked():
            self.running_protocol = True
            self.protocol_combo.clear()
            self.available_tasks = [i for i in os.listdir(protocol_dir) if '.prot' in i]
            self.protocol_combo.addItems(['Select Protocol'] + self.available_tasks)

        else:
            self.running_protocol = False
            self.protocol_combo.clear()
            self.available_tasks = get_tasks(self.GUI.GUI_filepath)
            self.protocol_combo.addItems(['Select Task'] + self.available_tasks)


    def on_scb_changed(self):
        self.add_button.setEnabled(True)

    def set_name(self):
        #print(self.expName.text(),self.protocol_combo.currentIndex())
        if (self.expName.text()!='') and ((self.protocol_combo.currentIndex()!=0) or (self.shared_protocol.isChecked()==False)):
            self.setup_groupbox.setEnabled(True)
            self.exp_name_groupbox.setEnabled(False)
            if (self.shared_protocol.isChecked()==True):
                self.set_protocol = self.protocol_combo.currentText()
            else:
                self.set_protocol = None

            self.set_experiment_name = self.expName.text()
            self.prot_label.setText('Protocol: {}'.format(self.set_protocol))
            self.exp_label.setText('Experiment: {}'.format(self.set_experiment_name))
            #self.CAT._update_exp_params(self.set_protocol,self.set_experiment_name)


    def add_cage(self):
        if self.setup_combo.currentIndex()!=0:
            entry_nr = len(self.df_setup_tmp)

            #first fill row with NA
            self.df_setup_tmp.loc[entry_nr] = ['NA']*len(self.df_setup_tmp.columns)

            COM = str(self.setup_combo.currentText())

            self.df_setup_tmp.loc[entry_nr]['Setup_ID'] = COM#str(time.time())#COM  #TESTCODE
            self.df_setup_tmp.loc[entry_nr]['Experiment'] = self.set_experiment_name
            self.df_setup_tmp.loc[entry_nr]['Protocol'] = self.set_protocol
            #print(111,self.GUI.setup_df['COM']==COM,self.GUI.setup_df['COM'])
            #print(self.GUI.setup_df.loc[self.GUI.setup_df['COM']==COM])

            for col_name in self.GUI.setup_df.columns:
                if col_name not in ['Setup_ID','Experiment','Protocol']:
                    val_ = self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID']==COM][col_name]

                    self.df_setup_tmp.loc[entry_nr][col_name] =  val_.values[0]




        #print(self.exp_dialog.df_setup_tmp)
        self.CLT.fill_table()

    def _create_mouse_exp_log(self,mouse_ID):

        #information is
        df_ = pd.DataFrame(columns=['entry_time','exit_time','weight','task','Variables','data_path'])
        pth_ = os.path.join(mice_dir,mouse_ID+'.csv')
        df_.to_csv(pth_)

    def run_experiment(self):
        
        """ ADD WARNING IF YOU ARE DUPLICATING MOUSE NAMES OR RFIDS!!!!


        """
        ## Create all the paths for data
        print("RUN EXPERIMENT")
        exp_path = os.path.join(data_dir,self.set_experiment_name)
        if not os.path.isdir(exp_path):
            os.mkdir(exp_path)

            #update mouse information
            for ix,row in self.df_mouse_tmp.iterrows():
                mouse_exp_path = os.path.join(exp_path,row['Mouse_ID'])
                os.mkdir(mouse_exp_path)


                mouse_exp_task_path = os.path.join(mouse_exp_path,row['Protocol'])
                os.mkdir(mouse_exp_task_path)

                entry_nr = len(self.GUI.mouse_df)

                self.GUI.mouse_df.loc[entry_nr] = ['NA']*len(self.GUI.mouse_df.columns)
                #self.GUI.mouse_df.loc[entry_nr]
                for col in self.GUI.mouse_df.columns:
                    self.GUI.mouse_df.loc[entry_nr][col] = row[col]

                self._create_mouse_exp_log(row['Mouse_ID'])

            print("HERE")
            print(self.GUI.mouse_df)
            #self.GUI.mouse_df.to_csv(self.GUI.mouse_df.file_location)
            self.GUI.mouse_window_tab.list_of_mice.fill_table()


            #update experiment information
            entry_nr = len(self.GUI.exp_df)
            self.GUI.exp_df.loc[entry_nr] = ['NA']*len(self.GUI.exp_df.columns)
            self.GUI.exp_df.loc[entry_nr]['Name'] = self.set_experiment_name
            self.GUI.exp_df.loc[entry_nr]['Setups'] = self.df_setup_tmp['Setup_ID'].values
            self.GUI.exp_df.loc[entry_nr]['User'] = self.GUI.active_user
            self.GUI.exp_df.loc[entry_nr]['Protocol'] = self.set_protocol
            self.GUI.exp_df.loc[entry_nr]['Subjects'] = self.df_mouse_tmp['Mouse_ID'].values

            for stup in self.df_setup_tmp['Setup_ID'].values:

                self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID']==stup]['User'] = self.GUI.active_user

                self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID']==stup,'in_use'] = 'Y'


                self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID']==stup,'Experiment'] = self.set_experiment_name
                self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID']==stup,'AC_state'] = 'allow_entry'
                self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID']==stup,'Door_Mag'] = '0111'
                self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID']==stup,'Door_Sensor'] = '1111'
                self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID']==stup,'Protocol'] = self.set_protocol

                mices_ = self.df_mouse_tmp['Mouse_ID'].loc[self.df_mouse_tmp['Setup_ID']==stup].values
                self.GUI.setup_df.loc[self.GUI.setup_df['Setup_ID']==stup,'mice_in_setup'] = str(mices_)[1:-1]

            print(self.GUI.setup_df)
            self.GUI.setup_window_tab.list_of_setups.fill_table()
            self.GUI.system_tab.list_of_setups.fill_table()
            self.GUI.system_tab.list_of_experiments.fill_table()

            self.accept()

        else:
            #PRINT WARNING MESSAGE, CHECKSUM OR OTHER INDICATION THAT SOMETHING HAS GONE WRONG
            pass

