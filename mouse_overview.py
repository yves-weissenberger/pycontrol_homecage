import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import Qt
from pyqtgraph import mkPen
import pyqtgraph as pg
import sys, os, pickle, time
import copy as cp
from datetime import datetime


from dialogs import are_you_sure_dialog, mouse_summary_dialog
from tables import mouse_adder_table, MouseTable

class mouse_window(QtGui.QWidget):

    def __init__(self, parent=None):

        super(QtGui.QWidget, self).__init__(parent)

        self.GUI = self.parent()

        self.add_mouse_button = QtGui.QPushButton('Add Mouse')
        self.add_mouse_button.clicked.connect(self.add_mouse)
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


        self.add_mouse_table = mouse_adder_table(self.GUI )


        self.list_of_mice = MouseTable(self.GUI,self)
        self.scrollable_mouse.setWidget(self.list_of_mice)

        # Buttons to control stuff
        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addWidget(self.add_mouse_button)
        self.Vlayout.addWidget(self.add_mouse_table)

        self.Vlayout.addWidget(self.mouse_table_label)
        self.Vlayout.addLayout(self.mouse_manager_layout)

        self.Vlayout.addWidget(self.scrollable_mouse)


    def add_mouse(self):
        #print(self.GUI.mouse_df)
        mouse_dat = []
        entry_nr = len(self.GUI.mouse_df)

        #add a check to see that something about the mouse has been filled in
        if not all([self.add_mouse_table.item(0,kk) is None for kk in range(self.add_mouse_table.columnCount())]):

            #first fill row with NA
            self.GUI.mouse_df.loc[entry_nr] = ['NA']*len(self.GUI.mouse_df.columns)

            #Then fill in provided information
            for kk,hdr_ in enumerate(self.add_mouse_table.header_names):
                if self.add_mouse_table.item(0,kk) is not None:
                    self.GUI.mouse_df.loc[entry_nr][hdr_] = self.add_mouse_table.item(0,kk).text()

            self.GUI.mouse_df.loc[entry_nr]['Start_date'] = datetime.now().strftime("%d/%m/%Y %H:%M:%S").replace(' ','_')
            self.GUI.mouse_df.loc[entry_nr]['User'] = self.GUI.active_user

        self.add_mouse_table.clearContents()

        self.list_of_mice.fill_table()
        self.GUI.mouse_df.to_csv(self.GUI.mouse_df.file_location)
        #print(self.GUI.mouse_df)


    def remove_mouse(self):
        """ Remove mouse from df and CSV file"""
        isChecked = []
        for row in range(self.list_of_mice.rowCount()):
            isChecked.append(self.list_of_mice.item(row,0).checkState()==2)

        if np.any(isChecked):
            sure = are_you_sure_dialog()
            sure.exec_()
            if sure.GO:
                fl = self.GUI.mouse_df.file_location
                self.GUI.mouse_df = self.GUI.mouse_df.drop(self.GUI.mouse_df.index[isChecked])
                self.GUI.mouse_df.file_location = fl
                #print(self.GUI.mouse_df)
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



