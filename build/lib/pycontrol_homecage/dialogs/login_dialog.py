from pyqtgraph.Qt import QtGui
from pycontrol_homecage.utils import get_users


class login_dialog(QtGui.QDialog):
    """ Simple dialog window so that you can log in """
    def __init__(self, parent=None):
        super(login_dialog, self).__init__(parent)

        self.setGeometry(10, 30, 300, 200)  # Left, top, width, height.

        self.userID = None
        self.buttonLogin = QtGui.QPushButton('Login', self)
        self.buttonLogin.clicked.connect(self.handleLogin)
        self.combo = QtGui.QComboBox()
        self.users = get_users()
        self.combo.addItems(['Select User'] + self.users)

        layout = QtGui.QVBoxLayout(self)
        layout.addWidget(self.combo)

    def handleLogin(self):
        if self.combo.currentText() != 'Select User':
            self.userID = self.combo.currentText()
            self.accept()
