from pyqtgraph.Qt import QtGui
from pycontrol_homecage.utils import get_users


class are_you_sure_dialog(QtGui.QDialog):

    def __init__(self, parent=None):

        super(are_you_sure_dialog, self).__init__(parent)

        self.setGeometry(10, 30, 300, 100)  # Left, top, width, height.
        self.users = get_users()

        self.yesButton = QtGui.QPushButton('Yes', self)
        self.noButton = QtGui.QPushButton('No', self)

        self.yesButton.clicked.connect(self.handleYes)
        self.noButton.clicked.connect(self.handleNo)

        self.Question = QtGui.QLabel()
        self.Question.setText("Are you sure?")
        self._set_dialog_layout()

    def _set_dialog_layout(self) -> None:
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.addWidget(self.noButton)
        self.buttonLayout.addWidget(self.yesButton)

        layoutV = QtGui.QVBoxLayout(self)
        layoutV.addWidget(self.Question)
        layoutV.addLayout(self.buttonLayout)

    def handleYes(self) -> None:
        self.GO = True
        self.accept()

    def handleNo(self) -> None:
        self.GO = False
        self.accept()