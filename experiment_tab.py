import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import Qt
from pyqtgraph import mkPen
import pyqtgraph as pg
import sys, os, pickle, time
import copy as cp
from tables import cageTable, experiment_overview_table


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

    def stop_experiment(self):
        #update the relevant mouse tables
        #update the experiment table
        
        pass
