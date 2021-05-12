from pyqtgraph.Qt import QtGui, QtCore
import string 
import random
import smtplib, ssl


## - package imports --
from utils import get_users
from loc_def import user_path
from config.paths import *
from utils import get_pyhomecage_email
from utils import get_tasks



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




        self.load_framework_button = QtGui.QPushButton('Load Pycontrol \nframework', self)
        self.load_framework_button.clicked.connect(self.load_framework)


        self.load_ac_framework_button = QtGui.QPushButton('Load Access control \nframework', self)
        self.load_ac_framework_button.clicked.connect(self.load_ac_framework)

        self.load_hardware_definition_button = QtGui.QPushButton('Load hardware definition',self)
        self.load_hardware_definition_button.clicked.connect(self.load_hardware_definition)

        self.disable_flashdrive_button = QtGui.QPushButton('Disable flashdrive')
        self.disable_flashdrive_button.clicked.connect(self.disable_flashdrive)
        layout2 = QtGui.QVBoxLayout(self)
        layout2.addWidget(self.load_framework_button)
        layout2.addWidget(self.load_hardware_definition_button)
        layout2.addWidget(self.disable_flashdrive_button)
        layout2.addWidget(self.load_ac_framework_button)


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
        self.calibration_weight.setPlaceholderText("Enter calibration weight in g") 
        self.buttonCal = QtGui.QPushButton('callibrate', self)
        self.buttonCal.clicked.connect(self.callibrate)

        self.min_session_time = QtGui.QLineEdit("")
        self.min_session_time.setPlaceholderText("Enter min session time in s") 
        self.button_mst = QtQgui.QPushButton("Set min session time ",self)
        self.button_mst.clicked.connect(self.set_min_session_time)



        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)



        layout = QtGui.QVBoxLayout()

        layout.addWidget(self.buttonWeigh)
        layout.addWidget(self.buttonTare)
        layout.addWidget(self.calibration_weight)
        layout.addWidget(self.buttonCal)
        layout.addWidget(self.buttonDone)
        layout.addWidget(self.min_session_time)
        layout.addWidget(self.button_mst)

        layoutH.addLayout(layout2)
        layoutH.addLayout(layout)
        layoutH.addWidget(self.log_textbox)

    def set_min_session_time(self):
        mst = self.min_session_time.text()
        try:
            mst = float(mst)
        except:
            mst = False
        
        if mst:
            str_ = 'set_min_session_time:'+str(mst)
            self.ac.serial.write(str_.encode())

            self.log_textbox.moveCursor(QtGui.QTextCursor.End)
            self.log_textbox.insertPlainText('Setting min session time to ' + str(mst*1000) +'ms\n')
            self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        else:
            self.log_textbox.insertPlainText('Something went wrong')

    def load_ac_framework(self):
        self.log_textbox.insertPlainText('Loading access control framework...')
        self.GUI.controllers[self.setup_id].AC.reset()
        self.GUI.controllers[self.setup_id].AC.load_framework()
        self.log_textbox.insertPlainText('done!')
    def load_framework(self):
        self.log_textbox.insertPlainText('Loading framework...')
        self.GUI.controllers[self.setup_id].PYC.load_framework()
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText('done!')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)  
    def disable_flashdrive(self):
        self.GUI.controllers[self.setup_id].PYC.disable_flashdrive()

    def load_hardware_definition(self):
        hwd_path = QtGui.QFileDialog.getOpenFileName(self, 'Select hardware definition:',
                os.path.join(config_dir, 'hardware_definition.py'), filter='*.py')[0]


        self.log_textbox.insertPlainText('uploading hardware definition...')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

        self.GUI.controllers[self.setup_id].PYC.load_hardware_definition(hwd_path)
        self.log_textbox.insertPlainText('done!')
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
        self.ac.GUI.setup_window_tab.configure_box_dialog = None  #sorry
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


class direct_pyboard_dialog(QtGui.QDialog):
    """ In this dialog, the idea is that you can directly run scripts on
        the pyboard. This is useful for e.g. flushing solenoids or testing
        a task.
     """ 
    def __init__(self,setup_id,GUI,parent=None):
        super(direct_pyboard_dialog,self).__init__(parent)
        self.setGeometry(10, 30, 500, 200) # Left, top, width, height.
        self.setup_id = setup_id
        self.selected_task = 'None'
        self.GUI = GUI
        layoutH = QtGui.QHBoxLayout(self)

        #
        self.PYC = self.GUI.controllers[self.setup_id].PYC
        if not self.GUI.controllers[self.setup_id].data_consumers:
            self.GUI.controllers[self.setup_id].data_consumers = [self]
        else:
            self.GUI.controllers[self.setup_id].data_consumers.append(self)
        self.GUI.controllers[self.setup_id]
        self.reject = self._done


        #self.setGeometry(10, 30, 400, 200) # Left, top, width, height.
        self.task_combo = QtGui.QComboBox()
        self.task_combo.addItems(['None'] + get_tasks(self.GUI.GUI_filepath))

        self.start_stop_button = QtGui.QPushButton('Start')
        self.start_stop_button.clicked.connect(self.start_stop)

        #self.onClose_chechbox = QtGui.Qte
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

        if self.start_stop_button.text()=="Start":
            self.selected_task = self.task_combo.currentText()
            if self.task_combo.currentText()!='None':
                self.process_data("Uploading: " + str(self.selected_task))
                self.PYC.setup_state_machine(sm_name=self.selected_task)
                self.PYC.start_framework()
            self.start_stop_button.setText("Stop")
        elif self.start_stop_button.text()=="Stop":
            self.PYC.stop_framework()
            self.start_stop_button.setText("Start")




    def _done(self):
        del self.GUI.controllers[self.setup_id].data_consumers[-1]  #remove this dialog from the data consumers of the system handler
        if self.onClose_chechbox.isChecked():
            self.PYC.stop_framework()  #stop the framework
        self.accept()   #close the dialog


    def process_data(self,msg):
        "function to accept data from the system handler"
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText(str(msg)+'\n')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)


class add_user_dialog(QtGui.QDialog):
    def __init__(self, parent=None):

        super(add_user_dialog, self).__init__(parent)


        self.setGeometry(10, 30, 300, 200) # Left, top, width, height.
        self.label = QtGui.QLabel("""You must create an account linked to an email that you frequently check.
                                The homecage system will send you daily updated about your subjects which 
                                MUST be checked to ensure there are no welfare concerns. Therefore we will
                                do an email confirmation thing to register
                            """)
        self.textName = QtGui.QLineEdit("User Name")
        self.textEmail = QtGui.QLineEdit("User email")
        self.addUserButton = QtGui.QPushButton('Send code', self)
        self.addUserButton.clicked.connect(self.send_code)

        self.confirm_email = QtGui.QLineEdit("Enter code")
        self.confirmCodeButton = QtGui.QPushButton('Confirm', self)
        self.confirmCodeButton.clicked.connect(self.handleLogin)
        #self.addUserButton.clicked.connect(self.handleLogin)
        self.users = get_users()


        layout = QtGui.QVBoxLayout(self)

        hlayout = QtGui.QHBoxLayout()
        hlayout.addWidget(self.textName)
        hlayout.addWidget(self.textEmail)
        hlayout.addWidget(self.addUserButton)

        hlayout2 = QtGui.QHBoxLayout(self)
        hlayout2.addWidget(self.confirm_email)
        hlayout2.addWidget(self.confirmCodeButton)
        layout.addWidget(self.label)
        layout.addLayout(hlayout)
        layout.addLayout(hlayout2)
        

    def send_code(self):
        letters = string.ascii_lowercase
        self.code = ''.join(random.choice(letters) for i in range(20))
        self.receiver_email = str(self.textEmail.text())
        self.user = str(self.textName.text())
        sender_email,password = get_pyhomecage_email()

        self.textName.setEnabled(False)
        self.textEmail.setEnabled(False)
        port = 587  # For starttls
        smtp_server = "smtp.gmail.com"
        receiver_email = self.textEmail.text()

        #print(send_mouse_df)
        message = """\
        Subject: Pyhomecage email confirmation code,

        """ + str(self.code)
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, port) as server:
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)

    def handleLogin(self):
        self.users = get_users()
        if str(self.confirm_email.text())==str(self.code):
            ###FIX TO IGNORE CASE         #####!!!!!!!!!!!!!!!!!
            if self.user.lower() not in [i.lower() for i in self.users]:
                with open(user_path, 'a') as file:
                    user_details = "user_data:{'"+str(self.user) + "':' " + str(self.receiver_email) + "'}"
                    file.writelines('\n'+user_details)
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

