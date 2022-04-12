from pyqtgraph.Qt import QtGui
import random
import smtplib
import ssl

from pycontrol_homecage.utils import get_users, get_pyhomecage_email
from pycontrol_homecage.utils.loc_def import user_path


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