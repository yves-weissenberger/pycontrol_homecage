from pyqtgraph.Qt import QtGui, QtCore
from utils import get_users
from loc_def import user_path
from config.paths import *


class calibrate_dialog(QtGui.QDialog):

    """ Simple dialog that allows you to tare and callibrate the scales"""

    def __init__(self, ac=None):

        super(calibrate_dialog, self).__init__(None)

        self.ac = ac
        self.reject = self._done


        self.setGeometry(10, 30, 400, 200) # Left, top, width, height.

        self.buttonDone = QtGui.QPushButton('Done')
        self.buttonDone.clicked.connect(self._done)

        self.buttonTare = QtGui.QPushButton('Tare', self)
        self.buttonTare.clicked.connect(self.tare)

        self.buttonWeigh = QtGui.QPushButton('Weigh', self)
        self.buttonWeigh.clicked.connect(self.weigh)


        self.calibration_weight = QtGui.QLineEdit("")
        self.buttonCal = QtGui.QPushButton('callibrate', self)
        self.buttonCal.clicked.connect(self.callibrate)




        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)



        layout = QtGui.QVBoxLayout()

        layout.addWidget(self.buttonWeigh)
        layout.addWidget(self.buttonTare)
        layout.addWidget(self.calibration_weight)
        layout.addWidget(self.buttonCal)
        layout.addWidget(self.buttonDone)

        layoutH = QtGui.QHBoxLayout(self)

        layoutH.addLayout(layout)
        layoutH.addWidget(self.log_textbox)



    def tare(self):
        self.ac.serial.write(b'tare')

    def callibrate(self):
        cw = self.calibration_weight.text()
        str_ = 'calibrate:'+cw
        self.ac.serial.write(str_.encode())

        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText('Target calibration weight: ' + str(cw) +'g\n')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

    def weigh(self):
        self.ac.serial.write(b'weigh')

    def _done(self):
        self.ac.GUI.setup_window_tab.callibrate_dialog = None  #sorry
        self.accept()

    def print_msg(self,msg):
        "print weighing messages"
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

        if 'calT' in msg:
            self.log_textbox.insertPlainText('Weight after Tare: ' + msg.replace('calT:','')+'g\n')
        elif 'calW' in msg:
            self.log_textbox.insertPlainText('Weight: ' + msg.replace('calW:','')+'g\n')
        if 'calC' in msg:
            self.log_textbox.insertPlainText('Measured post-calibration weight: ' + msg.replace('calC:','')+'g\n')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)


class box_conn_dialog(QtGui.QDialog):
    def __init__(self,parent=None):
        super(box_conn_dialog,self).__init__(parent)
        self.textbox = QtGui.QLineEdit(self)
        self.textbox.setText("You must be connected to the setup to update it")
        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.textbox)


class configure_box_dialog(QtGui.QDialog):
    """ Dialog window that allows you to upload harware definitions etc """ 
    def __init__(self,setup_id,GUI,parent=None):
        super(configure_box_dialog,self).__init__(parent)
        self.setGeometry(10, 30, 500, 200) # Left, top, width, height.
        self.setup_id = setup_id
        self.GUI = GUI
        layoutH = QtGui.QHBoxLayout(self)




        self.load_framework_button = QtGui.QPushButton('Load framework', self)
        self.load_framework_button.clicked.connect(self.load_framework)
        self.load_hardware_definition_button = QtGui.QPushButton('Load hardware definition',self)
        self.load_hardware_definition_button.clicked.connect(self.load_hardware_definition)

        self.disable_flashdrive_button = QtGui.QPushButton('Disable flashdrive')
        self.disable_flashdrive_button.clicked.connect(self.disable_flashdrive)
        layout2 = QtGui.QVBoxLayout(self)
        layout2.addWidget(self.load_framework_button)
        layout2.addWidget(self.load_hardware_definition_button)
        layout2.addWidget(self.disable_flashdrive_button)


        self.ac = self.GUI.controllers[self.setup_id].AC
        self.reject = self._done


        #self.setGeometry(10, 30, 400, 200) # Left, top, width, height.

        self.buttonDone = QtGui.QPushButton('Done')
        self.buttonDone.clicked.connect(self._done)

        self.buttonTare = QtGui.QPushButton('Tare', self)
        self.buttonTare.clicked.connect(self.tare)

        self.buttonWeigh = QtGui.QPushButton('Weigh', self)
        self.buttonWeigh.clicked.connect(self.weigh)


        self.calibration_weight = QtGui.QLineEdit("")
        self.buttonCal = QtGui.QPushButton('callibrate', self)
        self.buttonCal.clicked.connect(self.callibrate)




        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)



        layout = QtGui.QVBoxLayout()

        layout.addWidget(self.buttonWeigh)
        layout.addWidget(self.buttonTare)
        layout.addWidget(self.calibration_weight)
        layout.addWidget(self.buttonCal)
        layout.addWidget(self.buttonDone)

        layoutH.addLayout(layout2)
        layoutH.addLayout(layout)
        layoutH.addWidget(self.log_textbox)


    def load_framework(self):
         self.GUI.controllers[self.setup_id].PYC.load_framework()


    def disable_flashdrive(self):
        self.GUI.controllers[self.setup_id].PYC.disable_flashdrive()

    def load_hardware_definition(self):
        hwd_path = QtGui.QFileDialog.getOpenFileName(self, 'Select hardware definition:',
                os.path.join(config_dir, 'hardware_definition.py'), filter='*.py')[0]
        self.GUI.controllers[self.setup_id].PYC.load_hardware_definition(hwd_path)

        #setup.load_hardware_definition(hwd_path)


    def tare(self):
        self.ac.serial.write(b'tare')

    def callibrate(self):
        cw = self.calibration_weight.text()
        str_ = 'calibrate:'+cw
        self.ac.serial.write(str_.encode())

        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText('Target calibration weight: ' + str(cw) +'g\n')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

    def weigh(self):
        self.ac.serial.write(b'weigh')

    def _done(self):
        self.ac.GUI.setup_window_tab.callibrate_dialog = None  #sorry
        self.accept()

    def print_msg(self,msg):
        "print weighing messages"
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

        if 'calT' in msg:
            self.log_textbox.insertPlainText('Weight after Tare: ' + msg.replace('calT:','')+'g\n')
        elif 'calW' in msg:
            self.log_textbox.insertPlainText('Weight: ' + msg.replace('calW:','')+'g\n')
        if 'calC' in msg:
            self.log_textbox.insertPlainText('Measured post-calibration weight: ' + msg.replace('calC:','')+'g\n')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)


class login_dialog(QtGui.QDialog):
    """ Simple dialog window so that you can log in """
    def __init__(self, parent=None):
        super(login_dialog, self).__init__(parent)


        self.setGeometry(10, 30, 300, 200) # Left, top, width, height.

        self.userID = None
        self.buttonLogin = QtGui.QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handleLogin)
        self.combo = QtGui.QComboBox()
        self.users = get_users()
        self.combo.addItems(['Select User'] + self.users)



        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.combo)


    def handleLogin(self):
        if self.combo.currentText()!='Select User':
            self.userID = self.combo.currentText()
            self.accept()




class add_user_dialog(QtGui.QDialog):
    def __init__(self, parent=None):

        super(add_user_dialog, self).__init__(parent)


        self.setGeometry(10, 30, 300, 200) # Left, top, width, height.

        self.textName = QtGui.QLineEdit(self)
        self.textEmail = QtGui.QLineEdit(self)
        self.addUserButton = QtGui.QPushButton('Add User', self)
        self.addUserButton.clicked.connect(self.handleLogin)
        self.users = get_users()


        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.textName)
        layout.addWidget(self.addUserButton)


    def handleLogin(self):
        self.users = get_users()
        prop_user = self.textName.text()

        ###FIX TO IGNORE CASE         #####!!!!!!!!!!!!!!!!!
        if prop_user.lower() not in [i.lower() for i in self.users]:
            with open(user_path, 'a') as file:
                file.writelines('\n'+prop_user)
        self.accept()



class are_you_sure_dialog(QtGui.QDialog):

    def __init__(self, parent=None):

        super(are_you_sure_dialog, self).__init__(parent)


        self.setGeometry(10, 30, 300, 100) # Left, top, width, height.

        self.buttonLayout =  QtGui.QHBoxLayout()
        self.yesButton = QtGui.QPushButton('Yes', self)
        self.noButton = QtGui.QPushButton('No', self)
        self.buttonLayout.addWidget(self.noButton)
        self.buttonLayout.addWidget(self.yesButton)

        self.yesButton.clicked.connect(self.handleYes)
        self.noButton.clicked.connect(self.handleNo)

        self.users = get_users()

        self.Question = QtGui.QLabel()
        self.Question.setText("Are you sure?")


        layoutV = QtGui.QVBoxLayout(self)
        layoutV.addWidget(self.Question)
        layoutV.addLayout(self.buttonLayout)


    def handleYes(self):
        self.GO = True
        self.accept()

    def handleNo(self):
        self.GO = False
        self.accept()




#########################################################################################################
################################            -- Summary Dialogs --        ################################
#########################################################################################################



class mouse_summary_dialog(QtGui.QDialog):
    def __init__(self, parent=None):

        super(mouse_summary_dialog, self).__init__(parent)


        self.setGeometry(10, 30, 300, 200) # Left, top, width, height.

        self.textName = QtGui.QLabel(self)
        self.textName.setText("Bleep bloop all sorts of summary information about")

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.textName)


class cage_summary_dialog(QtGui.QDialog):
    def __init__(self, parent=None):

        super(mouse_summary_dialog, self).__init__(parent)


        self.setGeometry(10, 30, 300, 200) # Left, top, width, height.

        self.textName = QtGui.QLabel(self)
        self.textName.setText("Bleep bloop all sorts of summary information about")

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.textName)

