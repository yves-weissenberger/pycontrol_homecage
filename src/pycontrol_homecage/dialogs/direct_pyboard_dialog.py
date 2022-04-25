from pyqtgraph.Qt import QtGui

from pycontrol_homecage.utils import get_tasks
import pycontrol_homecage.db as database


class direct_pyboard_dialog(QtGui.QDialog):
    """ In this dialog, the idea is that you can directly run scripts on
        the pyboard. This is useful for e.g. flushing solenoids or testing
        a task.
     """

    def __init__(self, setup_id, GUI, parent=None):
        super(direct_pyboard_dialog, self).__init__(parent)
        self.setGeometry(10, 30, 500, 200)  # Left, top, width, height.
        self.setup_id = setup_id
        self.selected_task = 'None'
        self.GUI = GUI
        layoutH = QtGui.QHBoxLayout(self)

        #
        self.PYC = database.controllers[self.setup_id].PYC
        if not database.controllers[self.setup_id].data_consumers:
            database.controllers[self.setup_id].data_consumers = [self]
        else:
            database.controllers[self.setup_id].data_consumers.append(self)
        database.controllers[self.setup_id]
        self.reject = self._done

        # self.setGeometry(10, 30, 400, 200) # Left, top, width, height.
        self.task_combo = QtGui.QComboBox()
        self.task_combo.addItems(['None'] + get_tasks())

        self.start_stop_button = QtGui.QPushButton('Start')
        self.start_stop_button.clicked.connect(self.start_stop)

        # self.onClose_chechbox = QtGui.Qte
        self.onClose_chechbox = QtGui.QCheckBox("Stop task when closing dialog?")
        self.onClose_chechbox.setChecked(True)

        layout2 = QtGui.QVBoxLayout(self)
        layout2.addWidget(self.task_combo)
        layout2.addWidget(self.onClose_chechbox)
        layout2.addWidget(self.start_stop_button)

        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)

        layoutH.addLayout(layout2)
        layoutH.addWidget(self.log_textbox)

    def start_stop(self):
        """ Button that allows you to start and stop task"""

        if self.start_stop_button.text() == "Start":
            self.selected_task = self.task_combo.currentText()
            if self.task_combo.currentText() != 'None':
                self.process_data("Uploading: " + str(self.selected_task))
                self.PYC.setup_state_machine(sm_name=self.selected_task)
                self.PYC.start_framework()
            self.start_stop_button.setText("Stop")
        elif self.start_stop_button.text() == "Stop":
            self.PYC.stop_framework()
            self.start_stop_button.setText("Start")

    def _done(self) -> None:

        del database.controllers[self.setup_id].data_consumers[-1]  # remove this dialog from the data consumers of the system handler
        if self.onClose_chechbox.isChecked():
            self.PYC.stop_framework()  # stop the framework
        self.accept()   # close the dialog

    def process_data(self, msg):
        "function to accept data from the system handler"
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText(str(msg)+'\n')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
