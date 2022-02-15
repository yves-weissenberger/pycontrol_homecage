from pyqtgraph.Qt import QtGui, QtCore

import sys, os
from functools import partial
#imports for interacting with serial ports
from datetime import datetime
import traceback

from pycontrol_homecage.mouse_overview import mouse_window
from pycontrol_homecage.setup_view_tab import setups_tab
from pycontrol_homecage.schedule_manager import scheduler
from pycontrol_homecage.system_overview import system_tab
from pycontrol_homecage.experiment_tab import experiment_tab
from pycontrol_homecage.loc_def import all_paths, create_paths
from pycontrol_homecage.utils import load_data_csv
from pycontrol_homecage.dialogs import login_dialog, add_user_dialog
## Here want to implement a GUI for managing the homecage datasets. Thoughts on how to structure it. I think natural way is to ]
# create a central landing interface that presents and lvie updates some basic features of the behavior sufficient to tell you 
#if you need up check in on a page and then detailed information about each cage in tabs. 

#The other thing that would be a real asset is if you could set custom scripts to run such that those would be updated.
#Should the overview be by mouse or by cage?


sys._excepthook = sys.excepthook
def custom_excepthook(type_, exception, traceback_,filepath):
    """ This is supposed to be a custom exception hook that prints
        exceptions to a file so that they can then be used as alerts 
        for an email daemon
    """
    now = datetime.strftime(datetime.now(),'%Y-%m-%d-%H%M%S')

    with open(filepath,'a') as f:
        f.write('----------------- \n')
        f.write(repr(type_))
        f.write(repr(exception))
        traceback.print_exception(type_, exception, traceback_,file=f)
        f.write(now + '\n')
    sys._excepthook(type_, exception, traceback)

    


class Visualizator(QtGui.QMainWindow):

    def __init__(self):
        super().__init__()

        #1+s
        self.connected_boards = []
        self.connected_access_controls = []
        self.controllers = {}
        self.GUI_filepath = os.path.dirname(os.path.abspath(__file__))
        self.app = None # Overwritten with QtGui.QApplication instance in main.
        self.active_user = None
        self.task_df,self.exp_df,self.setup_df,self.mouse_df = load_data_csv()

        self._store_paths()

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

        self.mouse_window_tab.setEnabled(False)
        self.setup_window_tab.setEnabled(False)
        self.schedule_tab.setEnabled(False)
        self.system_tab.setup_groupbox.setEnabled(False)
        self.system_tab.log_groupbox.setEnabled(False)
        self.system_tab.experiment_groupbox.setEnabled(False)
        #self.system_tab.
        self.experiment_tab.setEnabled(False)
        ################ Setup the tabs ##################
        
        self.login = login_dialog()
        self.add_user = add_user_dialog()

        self.system_tab.login_button.clicked.connect(self.change_user)
        self.system_tab.add_user_button.clicked.connect(self.add_user_)
        self.system_tab.logout_button.clicked.connect(self.logout_user)

        self.setGeometry(10, 30, 700, 800) # Left, top, width, height.
        self.setCentralWidget(self.tab_widget)
        self.show()

        self.refresh_timer = QtCore.QTimer() # Timer to regularly call refresh() when not running.
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(100)

        self.refresh()    # Refresh tasks and ports lists.

    def _store_paths(self) -> None:
        ROOT,task_dir,experiment_dir,setup_dir,mice_dir,data_dir,AC_logger_dir,protocol_dir = all_paths

        self.paths = {'ROOT': ROOT,
                      'task_dir': task_dir,
                      'experiment_dir': experiment_dir,
                      'setup_dir': setup_dir,
                      'mice_dir': mice_dir,
                      'data_dir': data_dir,
                      'AC_logger_dir': AC_logger_dir,
                      'protocol_dir': protocol_dir}


    def refresh(self) -> None:
        #print(self.setup_window_tab.callibrate_dialog)
        for k,SC in self.controllers.items():
            SC.check_for_data()

            if self.system_tab.plot_isactive:
                self.system_tab.experiment_plot.update()

        self.setup_window_tab._refresh()
        self.system_tab._refresh()
        self.experiment_tab._refresh()
        self.mouse_window_tab._refresh()
        self.schedule_tab._refresh()

    def change_user(self) -> None:
        self.login.exec_()
        self.active_user = self.login.userID
        if self.active_user:
            self.setWindowTitle('Logged in as {}'.format(self.active_user))
            self.mouse_window_tab.setEnabled(True)
            self.setup_window_tab.setEnabled(True)
            self.schedule_tab.setEnabled(True)
            self.system_tab.setup_groupbox.setEnabled(True)
            self.system_tab.log_groupbox.setEnabled(True)
            self.system_tab.experiment_groupbox.setEnabled(True)
            self.experiment_tab.setEnabled(True)
    
    def print_msg(self,msg,ac_pyc=None,setup_ID=None) -> None:
        self.system_tab.write_to_log(msg)
        if ac_pyc=='pyc':
            pass
            #if
            #self.system_tab.experiment_plot.


    def add_user_(self) -> None:
        self.add_user.exec_()
        self.login = login_dialog()

    def logout_user(self):
        self.active_user = None
        self.setWindowTitle('Not logged in')
        self.mouse_window_tab.setEnabled(False)
        self.setup_window_tab.setEnabled(False)
        self.schedule_tab.setEnabled(False)
        self.system_tab.setup_groupbox.setEnabled(False)
        self.system_tab.log_groupbox.setEnabled(False)
        self.system_tab.experiment_groupbox.setEnabled(False)
        self.system_tab.user_groupbox.setEnabled(True)
        self.experiment_tab.setEnabled(False)
##########################################################
#####################     Main    ########################
##########################################################


if __name__ == "__main__":

    create_paths(all_paths)
    pths__ = all_paths
    ROOT,task_dir,experiment_dir,setup_dir,mice_dir,data_dir,AC_logger_dir,protocol_dir = pths__
    exception_path = os.path.join(setup_dir,'exception_store.txt')
    except_hook = partial(custom_excepthook,filepath=exception_path)
    sys.excepthook = except_hook
    
    app = QtGui.QApplication(sys.argv)
    gui = Visualizator()
    gui.app = app # To allow app functions to be called from GUI.
    sys.exit(app.exec_())