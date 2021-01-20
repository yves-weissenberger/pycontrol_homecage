import numpy as np
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import Qt
from pyqtgraph import mkPen
import pyqtgraph as pg
import sys, os, pickle, time
import copy as cp


#Ok in this tab want to get an overview of the experiments. The most important thing to
#be able to do here in the first instance is to change the protocol being run.

class experiment_tab(QtGui.QWidget):

    def __init__(self, parent=None):
        super(QtGui.QWidget, self).__init__(parent)

        self.GUI = self.parent()

        self.Hlayout = QtGui.QHBoxLayout()
        self.Hlayout.addWidget(QtGui.QPushButton('Start New Experiment'))



        self.Vlayout = QtGui.QVBoxLayout(self)
        self.Vlayout.addLayout(self.Hlayout)

