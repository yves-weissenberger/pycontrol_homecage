import numpy as np
import pandas as pd
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph import Qt
from pyqtgraph import mkPen
import pyqtgraph as pg
import sys, os, pickle, time
import copy as cp
import pandas as pd

#imports for interacting with serial ports
from serial.tools import list_ports



from mouse_overview import mouse_window
from setup_view_tab import setups_tab
from schedule_manager import scheduler
from system_overview import system_tab
from dialogs import login_dialog, add_user_dialog
from experiment_tab import experiment_tab
from loc_def import all_paths, create_paths
from new_experiment_dialog import new_experiment_dialog
from utils import load_data_csv
import com
from tables import cageTable, experiment_overview_table
from dialogs import are_you_sure_dialog, cage_summary_dialog, configure_box_dialog, box_conn_dialog


## Here want to implement a GUI for managing the homecage datasets. Thoughts on how to structure it. I think natural way is to ]
# create a central landing interface that presents and lvie updates some basic features of the behavior sufficient to tell you 
#if you need up check in on a page and then detailed information about each cage in tabs. 

#The other thing that would be a real asset is if you could set custom scripts to run such that those would be updated.
#Should the overview be by mouse or by cage?





class Visualizator(QtGui.QMainWindow):


    def __init__(self):
        super().__init__()


        self.connected_boards = []
        self.connected_access_controls = []
        self.controllers = {}
        self.GUI_filepath = os.path.dirname(os.path.abspath(__file__))
        self.app = None # Overwritten with QtGui.QApplication instance in main.
        self.active_user = None
        self.task_df,self.exp_df,self.setup_df,self.mouse_df = load_data_csv()


        ROOT,task_dir,experiment_dir,setup_dir,mice_dir,data_dir,AC_logger_dir,protocol_dir = all_paths

        self.paths = {'ROOT': ROOT,
                      'task_dir': task_dir,
                      'experiment_dir': experiment_dir,
                      'setup_dir': setup_dir,
                      'mice_dir': mice_dir,
                      'data_dir': data_dir,
                      'AC_logger_dir': AC_logger_dir,
                      'protocol_dir': protocol_dir}

        self.setup_df['connected'] = False


        self.tab_widget = QtGui.QTabWidget(self)



        ################ Setup the tabs ##################
        self.mouse_window_tab = mouse_window(self)
        self.setup_window_tab = setups_tab(self)
        self.schedule_tab = scheduler(self)
        self.system_tab = system_tab(self)
        self.experiment_tab = experiment_tab(self)

        self.tab_widget.addTab(self.system_tab,'System Overview')
        self.tab_widget.addTab(self.experiment_tab,'Experiments')
        self.tab_widget.addTab(self.mouse_window_tab,'Mouse Overview')
        self.tab_widget.addTab(self.setup_window_tab,'Setup Overview')
        self.tab_widget.addTab(self.schedule_tab,'Task scheduler')

        ##################################################


        ################ Setup the tabs ##################

        self.login = login_dialog()
        self.add_user = add_user_dialog()

        self.system_tab.login_button.clicked.connect(self.change_user)
        self.system_tab.add_user_button.clicked.connect(self.add_user_)


        self.setGeometry(10, 30, 700, 800) # Left, top, width, height.
        self.setCentralWidget(self.tab_widget)
        self.show()

        self.refresh_timer = QtCore.QTimer() # Timer to regularly call refresh() when not running.
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(100)

        self.refresh()    # Refresh tasks and ports lists.


    def refresh(self):
        #print(self.setup_window_tab.callibrate_dialog)
        for k,SC in self.controllers.items():
            SC.check_for_data()

            if self.system_tab.plot_isactive:
                self.system_tab.experiment_plot.update()

        self.setup_window_tab._refresh()
        self.system_tab._refresh()

    def change_user(self):
        self.login.exec_()
        self.active_user = self.login.userID
        self.setWindowTitle('Logged in as {}'.format(self.active_user))

    def print_msg(self,msg,ac_pyc=None,setup_ID=None):
        self.system_tab.write_to_log(msg)
        if ac_pyc=='pyc':
            pass
            #if
            #self.system_tab.experiment_plot.


    def add_user_(self):
        self.add_user.exec_()
        self.login = login_dialog()


##########################################################
#####################     Main    ########################
##########################################################


if __name__ == "__main__":

    create_paths(all_paths)

    app = QtGui.QApplication(sys.argv)
    gui = Visualizator()
    gui.app = app # To allow app functions to be called from GUI.
    sys.exit(app.exec_())