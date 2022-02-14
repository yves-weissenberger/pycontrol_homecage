from pyqtgraph.Qt import QtGui
import os
import json


from pycontrol_homecage.homecage_config.paths import tasks_dir


from pycontrol_homecage.utils import get_variables_from_taskfile, get_tasks
from pycontrol_homecage.loc_def import protocol_dir
from pycontrol_homecage.tables import protocol_table

class scheduler(QtGui.QWidget):

    " In this tab create schedules for tasks "

    def __init__(self, parent=None):

        super(QtGui.QWidget, self).__init__(parent)

        self.GUI = self.parent()

        self.prot_dict = {}
        self.stage_dict = {}
        self.task_variables = []

        #add stage to protocol
        self.ATP = QtGui.QGroupBox("Add stage to protocol")


        self.protocol_namer = QtGui.QLineEdit("")
        self.protocol_namer_button = QtGui.QPushButton("Set protocol name")
        self.protocol_namer_button.clicked.connect(self.set_protocol_name)

        self.clear_button = QtGui.QPushButton("Clear")
        self.clear_button.clicked.connect(self.clear_all)

        self.save_button = QtGui.QPushButton("Save Protocol")
        self.save_button.clicked.connect(self.save)

        self.add_stage_button = QtGui.QPushButton("Add task stage")
        self.add_stage_button.clicked.connect(self.add_stage)


        self.task_combo  = QtGui.QComboBox()

        self.task_set_button = QtGui.QPushButton("Set")
        self.task_set_button.clicked.connect(self.set_stage_task)
        self.task_set_button.setEnabled(False)

        self.available_tasks = get_tasks(self.GUI.GUI_filepath)
        self.task_combo.addItems(['Select Task'] + self.available_tasks)
        self.task_combo.currentIndexChanged.connect(self.picked_task)

        #track value stuff
        self.trackV_label = QtGui.QLabel("Track value")
        self.trackV_combo = QtGui.QComboBox()
        self.trackV_add = QtGui.QPushButton("Add")
        self.trackV_add.clicked.connect(self.trackV_change)

        self.trackV_combo.setEnabled(False)

        #threshold value stuff
        self.threshV_label = QtGui.QLabel("Threshold")
        self.threshV_combo = QtGui.QComboBox()
        self.threshV_add = QtGui.QPushButton("Add")
        self.threshV_add.clicked.connect(self.threshV_change)

        self.threshV_combo.setEnabled(False)
        self.threshV_value = QtGui.QLineEdit()


        ## Default value stuff
        self.defaultV_label = QtGui.QLabel("Default value")
        self.defaultV_combo = QtGui.QComboBox()
        self.defaultV_add = QtGui.QPushButton("Add")
        self.defaultV_value = QtGui.QLineEdit()

        self.defaultV_combo.setEnabled(False)


        self.Hlayout1 = QtGui.QHBoxLayout()
        self.Hlayout2 = QtGui.QHBoxLayout()
        self.Hlayout3 = QtGui.QHBoxLayout()
        self.Hlayout4 = QtGui.QHBoxLayout()

        self.Hlayout1.addWidget(self.protocol_namer)
        self.Hlayout1.addWidget(self.protocol_namer_button)
        self.Hlayout1.addWidget(self.task_combo)
        self.Hlayout1.addWidget(self.task_set_button)

        self.Hlayout2.addWidget(self.threshV_label)
        self.Hlayout2.addWidget(self.threshV_combo)
        self.Hlayout2.addWidget(self.threshV_value)
        self.Hlayout2.addWidget(self.threshV_add)


        self.Hlayout3.addWidget(self.defaultV_label)
        self.Hlayout3.addWidget(self.defaultV_combo)
        self.Hlayout3.addWidget(self.defaultV_value)
        self.Hlayout3.addWidget(self.defaultV_add)

        self.Hlayout4.addWidget(self.trackV_label)
        self.Hlayout4.addWidget(self.trackV_combo)
        self.Hlayout4.addWidget(self.trackV_add)
        #self.Hlayout4.addWidget(self.add_stage_button)

        self.Vlayout_add = QtGui.QVBoxLayout()
        self.Vlayout_add.addLayout(self.Hlayout1)
        self.Vlayout_add.addLayout(self.Hlayout2)
        self.Vlayout_add.addLayout(self.Hlayout3)
        self.Vlayout_add.addLayout(self.Hlayout4)
        self.Vlayout_add.addWidget(self.add_stage_button)

        self.ATP.setLayout(self.Vlayout_add)



        self.protocol_table = protocol_table(GUI=self.GUI,tab=self)

        self.dummy_overview = QtGui.QGroupBox('Current Stage Overview')
        self.dummy_layout = QtGui.QVBoxLayout()
        self.protocol_table_dummy = protocol_table(GUI=self.GUI,tab=self,nRows=1)
        self.dummy_layout.addWidget(self.protocol_table_dummy)
        self.dummy_overview.setLayout(self.dummy_layout)

        self.Vlayout = QtGui.QVBoxLayout(self)

        self.Vlayout.addWidget(self.ATP,4)
        self.Vlayout.addWidget(self.dummy_overview,1)
        self.Vlayout.addWidget(self.protocol_table,10)

        self.save_clear_layout = QtGui.QHBoxLayout()
        self.save_clear_layout.addWidget(self.clear_button)
        self.save_clear_layout.addWidget(self.save_button)
        self.Vlayout.addLayout(self.save_clear_layout)


    def set_stage_task(self):

        "set task for a given stage"
        pth = os.path.join(tasks_dir,self.task_combo.currentText()+'.py')

        self.stage_dict = {'stage_nr': len(self.prot_dict),
                           'task': self.task_combo.currentText(),
                           'trackV': [],
                           'threshV':[],
                           'defaultV': [],
                           'done': False}

        self.task_variables = get_variables_from_taskfile(pth)

        self.trackV_combo.addItems(['Select'] + [i.replace('v.','') for i in self.task_variables if i not in self.stage_dict['trackV']])
        self.threshV_combo.addItems(['Select'] + [i.replace('v.','') for i in self.task_variables if i not in self.stage_dict['threshV']])
        self.defaultV_combo.addItems(['Select'] + [i.replace('v.','') for i in self.task_variables if i not in self.stage_dict['defaultV']])

        self.defaultV_combo.setEnabled(True)
        self.trackV_combo.setEnabled(True)
        self.threshV_combo.setEnabled(True)
        self.protocol_table_dummy.fill_row(self.stage_dict)



    def add_stage(self):
        """ Add Stage """

        self.prot_dict[str(len(self.prot_dict))] = self.stage_dict.copy()
        self.protocol_table.fill_table(self.prot_dict)

        self.reset()



    def trackV_change(self):
        
        self.stage_dict['trackV'].append(self.trackV_combo.currentText())
        self.trackV_combo.clear()
        self.trackV_combo.addItems(['Select'] + [i.replace('v.','') for i in self.task_variables if i not in self.stage_dict['trackV']])
        self.trackV_combo.setCurrentIndex(0)
        self.protocol_table_dummy.fill_row(self.stage_dict)

    def threshV_change(self):
        self.stage_dict['threshV'].append([self.threshV_combo.currentText(),
                                           self.threshV_value.text()])
        self.threshV_combo.clear()
        self.threshV_combo.addItems(['Select'] + [i.replace('v.','') for i in self.task_variables if i not in self.stage_dict['threshV'][0]])
        self.threshV_combo.setCurrentIndex(0)
        self.protocol_table_dummy.fill_row(self.stage_dict)

    def defaultV_change(self):
        self.stage_dict['defaultV'].append([self.defaultV_combo.currentText(),
                                            self.defaultV_value.text()])
        self.defaultV_combo.clear()
        self.defaultV_combo.addItems(['Select'] + [i.replace('v.','') for i in self.task_variables if i not in self.stage_dict['defaultV'][0]])
        self.defaultV_combo.setCurrentIndex(0)
        self.protocol_table_dummy.fill_row(self.stage_dict)

    def picked_task(self):
        'stupid helper to only allow selecting task once one has been selected'
        if self.task_combo.currentText()!='Select Task':
            self.task_set_button.setEnabled(True)

    def set_protocol_name(self):

        self.protocol_name = self.protocol_namer.text()
        self.protocol_namer.setEnabled(False)

    def reset(self):
        self.task_variables = []
        self.stage_dict = {}

        self.trackV_combo.clear()

        self.defaultV_combo.clear()
        self.defaultV_value.clear()

        self.threshV_combo.clear()
        self.threshV_value.clear()

        self.task_combo.setCurrentIndex(0)
        self.defaultV_combo.setEnabled(False)
        self.trackV_combo.setEnabled(False)
        self.threshV_combo.setEnabled(False)
        self.protocol_table_dummy.reset()

    def clear_all(self):
        " Start a new protocol"
        self.protocol_name = ''
        self.protocol_namer.clear()
        self.protocol_namer.setEnabled(True)
        self.prot_dict = {}
        self.stage_dict = {}
        self.task_variables = []
        self.protocol_table.reset()

        self.reset()

    def _refresh(self):
        pass
    def save(self):
        pth = os.path.join(protocol_dir,self.protocol_name + '.prot')
        print(pth)
        with open(pth, 'w') as outfile:
            json.dump(self.prot_dict, outfile)

