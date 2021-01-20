import numpy as np
import pandas as pd
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import Qt
from pyqtgraph.Qt import QtWidgets
from pyqtgraph import mkPen
import pyqtgraph as pg
import sys, os, pickle, time
import copy as cp
from datetime import datetime
import time
import re
from serial import SerialException


from dialogs import calibrate_dialog
from utils import find_setups
from utils import get_tasks



##### TA code imports
from com.pycboard import Pycboard, PyboardError, _djb2_file
#from com.data_logger import Data_logger
from com.system_handler import system_controller
from com.access_control import Access_control

#######################################################################
####################      Experiment Table      #######################
#######################################################################

class experiment_overview_table(QtGui.QTableWidget):
    " Table for system tab that shows all experiments currently running"

    def __init__(self, GUI, tab=None,parent=None):
        super(QtGui.QTableWidget, self).__init__(1,7, parent=parent)
        self.header_names = ['Select','Name','Setups','User','Protocol','Subjects','n_subjects']

        self.tab = tab
        self.GUI = GUI
        self.setHorizontalHeaderLabels(self.header_names)
        #for i in range(8):
        #    self.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)

        self.select_nr = self.header_names.index("Select")



        self.fill_table()


    def fill_table(self):
        #print(self.GUI.setup_df)
        self.setRowCount(len(self.GUI.exp_df))

        self.buttons = []
        for row_index, row in self.GUI.exp_df.iterrows():    

            for col_index in range(self.columnCount()):
                #print(index,col,row[col])
                try:
                    cHeader = self.header_names[col_index]
                    #print(cHeader,row)
                    self.setItem(row_index,col_index,Qt.QtWidgets.QTableWidgetItem(str(row[cHeader])))
                except KeyError:
                    pass

           

            chkBoxItem = QtGui.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)   
            self.setItem(row_index,self.select_nr,chkBoxItem)

#######################################################################
###############      For setting up a new protocol      ###############
#######################################################################
class protocol_table(QtGui.QTableWidget):

    def __init__(self, GUI, tab,nRows=None,parent=None):

        super(QtGui.QTableWidget, self).__init__(1,6, parent=parent)
        self.header_names = ['Stage','Task','Tracked','Threshold(s)','Default(s)','Delete']
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        for i in range(len(self.header_names)-1):
            self.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)

        if nRows:
            self.setRowCount(nRows)
            self.nRows = nRows
            #self.horizontalHeader().setSectionResizeMode(1)
        else:
            self.nRows = 1

    def fill_table(self,dat):
        " Here pass prot_dict"

        self.nRows = len(dat)


        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        for i in range(1,len(self.header_names)-1):
            self.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)

        if self.nRows:
            self.setRowCount(self.nRows)

        for k in dat.keys():
            self.fill_row(dat[k],row=int(k))

            


    def fill_row(self,dat,row=None):
        "Here pass "

        if not row:
            row = 0
            self.reset_()

            

        for k in dat.keys():
            if ('thresh' in k) or ('default' in k):
                Vtmp = Qt.QtWidgets.QTableWidgetItem(self._translate(dat[k]))
            else:
                Vtmp = Qt.QtWidgets.QTableWidgetItem(str(dat[k]))

            if k=='threshV':
                self.setItem(row,self.header_names.index('Threshold(s)'),Vtmp)
            elif k=='defaultV':
                self.setItem(row,self.header_names.index('Default(s)'),Vtmp)
            elif k=='trackV':
                self.setItem(row,self.header_names.index('Tracked'),Vtmp)
            elif k=='stage_nr':
                self.setItem(row,self.header_names.index('Stage'),Vtmp)
            elif k=='task':
                self.setItem(row,self.header_names.index('Task'),Vtmp)

        self.resizeRowToContents(row)


    def _translate(self,x):
        ret = ''
        if len(x):
            for x_ in x:
                ret = ret + str(x_[0]) + ': ' + str(x_[1]) + '\n'
        return ret


    def reset_(self):

        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)
        for i in range(1,len(self.header_names)-1):
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
        #task = self.task_combo.currentText()
        #setup = self.setup_combo.currentText()
        #print([brd.serial_port for i,brd in enumerate(self.GUI.connected_boards)])
        board_ix = [i for i,brd in enumerate(self.GUI.connected_boards) if brd.serial_port==setup]
        #print(board_ix)

        #print(self.GUI.GUI_filepath)
        self.task_hash = _djb2_file(os.path.join(self.GUI.GUI_filepath,'tasks', task + '.py'))
        self.GUI.connected_boards[int(board_ix[0])].setup_state_machine(task, uploaded=False)
        self.GUI.connected_boards[int(board_ix[0])].start_framework()


    def fill_table(self):
        #print(self.GUI.mouse_df)
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
            print(self.tab.global_task)
            if self.tab.global_task:
                #print('global')
                chkBoxItem.setFlags(QtCore.Qt.ItemIsEnabled)
            else:
                chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                chkBoxItem.setCheckState(QtCore.Qt.Unchecked)

            self.setItem(row_index,1,chkBoxItem)


            protocols = QtGui.QComboBox()

            self.available_tasks = get_tasks(self.GUI.GUI_filepath)
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
        print(row,'ROW',col,'COL')
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
                #print("ENABLED")
            else:
                self.tab.MICE.setEnabled(False)
                #print("DISABLED_EARLY")

            #print('NSEL',len(self.selected_setups),self.selected_setups)
            if len(self.selected_setups)>1:
                #print("DISABLED_AFTER")
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
        #print(self.GUI.mouse_df)
        self.clear()
        self.setHorizontalHeaderLabels(self.header_names)
        df = self.tab.df_mouse_tmp.loc[self.tab.df_mouse_tmp['Setup_ID'].isin(self.tab.CLT.selected_setups)]
        df.index = np.arange(len(df))
        print(self.tab.CLT.selected_setups)
        #print(df)

        df.reset_index(drop=True)
        self.setRowCount(len(df))

        for row_index, row in df.iterrows():    

            for col_index in range(self.columnCount()-1):
                #print(row_index,col_index)
                self.setItem(row_index,col_index+1,Qt.QtWidgets.QTableWidgetItem(str(row[col_index])))

            chkBoxItem = QtGui.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)   
            self.setItem(row_index,0,chkBoxItem)
##########################################################################
######################      For cage overview      ######################
##########################################################################



class cageTable(QtGui.QTableWidget):
    """ This table contains information about all mice currently running in the
        system """
    def __init__(self, GUI,tab=None):
        super(QtGui.QTableWidget, self).__init__(1,12, parent=None)
        self.header_names = ['Select','Setup_ID','Connection','Experiment','Protocol','Mouse_training',
                             'COM','COM_AC', 'in_use','connected', 'User',
                             'AC_state','Door_Mag','Door_Sensor',
                             'n_mice','mice_in_setup']

        self.tab = tab
        self.GUI = GUI
        self.setHorizontalHeaderLabels(self.header_names)
        #for i in range(8):
        #    self.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)

        self.select_nr = self.header_names.index("Select")
        self.connect_nr = self.header_names.index("Connection")



        self.fill_table()

    def fill_table(self):
        #print(self.GUI.setup_df)
        self.setRowCount(len(self.GUI.setup_df))

        self.buttons = []
        for row_index, row in self.GUI.setup_df.iterrows():    

            for col_index in range(self.columnCount()):
                #print(index,col,row[col])
                try:
                    cHeader = self.header_names[col_index]
                    #print(cHeader,row)
                    self.setItem(row_index,col_index,Qt.QtWidgets.QTableWidgetItem(str(row[cHeader])))
                except KeyError:
                    pass

           
            button = QtGui.QPushButton('Connect')
            button.name = [row['Setup_ID'],row['COM'],row['COM_AC']]
            button.clicked.connect(self.connect)
            self.buttons.append(button)

            if self.tab is None:  #if this is the table in system overview
                button.setEnabled(False)


            self.setCellWidget(row_index,self.connect_nr,button)

            chkBoxItem = QtGui.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)   
            self.setItem(row_index,self.select_nr,chkBoxItem)


    def connect(self):

        try:
            #print(self.sender().name)
            setup_id, com_,comAC_ = self.sender().name
            #print(com_,comAC_)
            SC = system_controller(print_func=print,GUI=self.GUI,setup_id=setup_id)
            #DL = Data_logger(print_func=print,GUI=self.GUI)
            board = Pycboard(com_, print_func=print, data_logger=SC)

            board.load_framework()
            time.sleep(0.05)
            self.GUI.connected_boards.append(board)
            ac = Access_control(comAC_,print_func=print,data_logger=SC,GUI=self.GUI)
            time.sleep(0.05)
            SC.add_PYC(board)
            SC.add_AC(ac)

            ac.load_framework()
            self.GUI.connected_access_controls.append(ac)
            #self.GUI.data_loggers.append(self.data_logger)
            self.sender().setText("Connected")

            send_name = self.sender().name
            self._fill_setup_df_row(send_name)
            self.GUI.controllers[setup_id] = SC
            time.sleep(0.05)
            self.tab.callibrate_dialog = calibrate_dialog(ac=ac)
            self.tab.callibrate_dialog.exec_()
            self.sender().setEnabled(False)
            self.fill_table()

        except (PyboardError,SerialException) as e:   

            print(e)
            print("Failed to connect")

    def _fill_setup_df_row(self,send_name):
        " Just fill that row of the df"
        setup_id,com_,comAC_ = send_name
        self.GUI.setup_df['connected'].loc[self.GUI.setup_df['COM']==com_] = True
        self.GUI.setup_df['in_use'].loc[self.GUI.setup_df['COM']==com_] = False
        self.GUI.setup_df['connected'].loc[self.GUI.setup_df['COM']==com_] = True
        self.GUI.setup_df['n_mice'].loc[self.GUI.setup_df['COM']==com_] = 0



    def _refresh(self):
        ports = find_setups(self.GUI)

        ac_nr = self.header_names.index("COM")
        setup_nr = self.header_names.index("COM_AC")
        for r in range(self.rowCount()):
            if (self.item(r,ac_nr).text() in ports) and (self.item(r,setup_nr).text() in ports):
                self.cellWidget(r,self.connect_nr).setEnabled(True)
                #self.cellWidget(r,self.connect_nr).setText("Connected")
            else:
                self.cellWidget(r,self.connect_nr).setEnabled(False)
                 


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
        self.header_names = ['','Mouse_ID', 'RFID', 'Sex', 'Age', 'Experiment', 'Protocol', 'User', 
                            'Start_date', 'Current_weight', 'Start_weight', 'is_training',
                            'is_assigned', 'training_log', 'Setup_ID']

        self.GUI = GUI
        self.setHorizontalHeaderLabels(self.header_names)
        #for i in range(8):
        #    self.horizontalHeader().setResizeMode(i, QtGui.QHeaderView.Stretch)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(Qt.QtWidgets.QTableWidget.NoEditTriggers)

        self.fill_table()

    def fill_table(self):
        #print(self.GUI.mouse_df)
        self.setRowCount(len(self.GUI.mouse_df))

        for row_index, row in self.GUI.mouse_df.iterrows():    

            for col_index in range(self.columnCount()-1):
                #print(index,col,row[col])
                self.setItem(row_index,col_index+1,Qt.QtWidgets.QTableWidgetItem(str(row[col_index])))
            #items = [QtGui.QStandardItem(field)for field in row]
            #print(items)
            #self.model.appendRow(items)
            chkBoxItem = QtGui.QTableWidgetItem()
            chkBoxItem.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            chkBoxItem.setCheckState(QtCore.Qt.Unchecked)   
            self.setItem(row_index,0,chkBoxItem)


