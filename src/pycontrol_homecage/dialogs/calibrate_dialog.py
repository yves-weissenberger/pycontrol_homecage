from pyqtgraph.Qt import QtGui


class calibrate_dialog(QtGui.QDialog):

    """ Simple dialog that allows you to tare and callibrate the scales"""

    def __init__(self, ac=None):

        super(calibrate_dialog, self).__init__(None)

        self.ac = ac
        self.reject = self._done

        self.setGeometry(10, 30, 400, 200)  # Left, top, width, height.

        self._setup_buttons()
        self._setup_calibration_weight_lineedit()
        self._setup_layout()

    def _setup_buttons(self) -> None:
        self.buttonDone = QtGui.QPushButton('Done')
        self.buttonDone.clicked.connect(self._done)

        self.buttonTare = QtGui.QPushButton('Tare', self)
        self.buttonTare.clicked.connect(self.tare)

        self.buttonWeigh = QtGui.QPushButton('Weigh', self)
        self.buttonWeigh.clicked.connect(self.weigh)

        self.buttonCal = QtGui.QPushButton('callibrate', self)
        self.buttonCal.clicked.connect(self.callibrate)

    def _setup_calibration_weight_lineedit(self) -> None:

        self.calibration_weight = QtGui.QLineEdit("")
        self.log_textbox = QtGui.QTextEdit()
        self.log_textbox.setFont(QtGui.QFont('Courier', 9))
        self.log_textbox.setReadOnly(True)

    def _setup_layout(self) -> None:
        layout = QtGui.QVBoxLayout()
        layout.addWidget(self.buttonWeigh)
        layout.addWidget(self.buttonTare)
        layout.addWidget(self.calibration_weight)
        layout.addWidget(self.buttonCal)
        layout.addWidget(self.buttonDone)

        layoutH = QtGui.QHBoxLayout(self)

        layoutH.addLayout(layout)
        layoutH.addWidget(self.log_textbox)

    def tare(self) -> None:
        """ Tell access control module to tare the scales"""
        self.ac.serial.write(b'tare')

    def callibrate(self) -> None:
        """ Tell access control module to callibrate the scales"""
        cw = self.calibration_weight.text()
        str_ = 'calibrate:' + cw
        self.ac.serial.write(str_.encode())

        # write to
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
        self.log_textbox.insertPlainText('Target calibration weight: ' + str(cw) + 'g\n')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

    def weigh(self) -> None:
        self.ac.serial.write(b'weigh')

    def _done(self) -> None:
        self.accept()

    def print_msg(self, msg: str) -> None:
        "print weighing messages"
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)

        if 'calT' in msg:
            self.log_textbox.insertPlainText('Weight after Tare: ' + msg.replace('calT:', '')+'g\n')
        elif 'calW' in msg:
            self.log_textbox.insertPlainText('Weight: ' + msg.replace('calW:', '')+'g\n')
        if 'calC' in msg:
            self.log_textbox.insertPlainText('Measured post-calibration weight: ' + msg.replace('calC:', '')+'g\n')
        self.log_textbox.moveCursor(QtGui.QTextCursor.End)
